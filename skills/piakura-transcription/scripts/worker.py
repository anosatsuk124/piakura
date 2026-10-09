"""Deploy and control a directory-confined SSH transcription batch worker."""

import argparse
import base64
import fcntl
import io
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tarfile
import time
import uuid
from pathlib import Path

from runtime import contained, digest, isolated_env, write_json
from setup_runtime import environment, family_for
from weights import CHECKPOINTS, import_weights

SCRIPT = Path(__file__).resolve().parent
MARKER = ".piakura-worker"
# Inside the piakura worker image (containers/worker/Dockerfile) the worker
# root is the volume at /data and the container itself is the sandbox.
CONTAINER = os.environ.get("PIAKURA_CONTAINER") == "1"
CONTAINER_ROOT = Path("/data")
IMAGE_REPOSITORY = "ghcr.io/anosatsuk124/piakura-worker"
MODELS = [
    "yourmt3",
    "muscriptor-small",
    "muscriptor-medium",
    "basic-pitch",
    "rosvot",
    "sheetsage2",
]
SSH_OPTIONS = [
    "-T",
    "-o",
    "BatchMode=yes",
    "-o",
    "StrictHostKeyChecking=yes",
    "-o",
    "UpdateHostKeys=no",
    "-o",
    "ConnectTimeout=15",
    "-o",
    "ControlMaster=no",
    "-o",
    "ControlPath=none",
]

ROOT_PART = re.compile(r"[A-Za-z0-9._-]{1,64}")

# This bootstrap is intentionally limited to one new directory under existing
# real directories of the remote home, and a verified release bundle. No
# remote shell redirects or tar extraction.
BOOTSTRAP = """
import base64, hashlib, json, os, pathlib, re, sys
payload=json.load(sys.stdin)
relative=pathlib.PurePosixPath(payload["root"])
parts=relative.parts
if relative.is_absolute() or not parts or any(p in (".","..") or not re.fullmatch(r"[A-Za-z0-9._-]{1,64}",p) for p in parts): raise ValueError("invalid worker root")
root=pathlib.Path.home()
for part in parts[:-1]:
 root=root/part
 if root.is_symlink() or not root.is_dir(): raise ValueError("worker root parents must be existing real directories")
root=root/parts[-1]
marker=root/".piakura-worker"
if root.is_symlink(): raise ValueError("symlink root refused")
if root.exists():
 if marker.is_symlink() or not marker.is_file() or marker.read_text()!="v1\\n": raise ValueError("unowned directory refused")
else:
 root.mkdir(mode=0o700);marker.write_text("v1\\n")
files=payload["files"]
hasher=hashlib.sha256()
for relative in sorted(files):
 p=pathlib.PurePosixPath(relative)
 if p.is_absolute() or ".." in p.parts: raise ValueError("invalid bundle path")
 data=base64.b64decode(files[relative],validate=True)
 hasher.update(relative.encode()+b"\\0"+data)
release=hasher.hexdigest()
target=root/"releases"/release
for relative in sorted(files):
 p=target/relative
 for parent in (p,*p.parents):
  if parent==root: break
  if parent.is_symlink(): raise ValueError("symlink inside worker refused")
 data=base64.b64decode(files[relative],validate=True)
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  if p.read_bytes()!=data: raise ValueError("release collision")
 else:
  with p.open("xb") as stream:stream.write(data)
print(json.dumps({"root":str(root),"release":release}))
"""


def validate_root(root):
    root = Path(root).absolute()
    if CONTAINER:
        if root != CONTAINER_ROOT or not (root / MARKER).is_file():
            raise ValueError("container worker root must be the initialized /data")
        return root
    try:
        parts = root.relative_to(Path.home()).parts
    except ValueError:
        raise ValueError("worker root must be inside the home directory") from None
    if not parts or not all(ROOT_PART.fullmatch(p) and p != ".." for p in parts):
        raise ValueError("invalid worker root")
    path = Path.home()
    for part in parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("worker root must not pass through a symlink")
    marker = contained(root, root / MARKER)
    if not marker.is_file():
        raise ValueError("unowned worker directory")
    if marker.read_text() != "v1\n":
        raise ValueError("unowned worker directory")
    return root


def job_path(root, job_id):
    if not re.fullmatch(r"[0-9a-f]{32}", job_id):
        raise ValueError("invalid job ID")
    return contained(root, root / "jobs" / job_id)


def sandbox(root, command, cwd):
    if CONTAINER:
        # The container already confines writes to /data and /tmp; bubblewrap
        # cannot create namespaces under Docker's default seccomp profile.
        return ["env", f"--chdir={cwd}", *command]
    # / is read-only; the only persistent writable bind is the authorized root.
    # Temporary and tool state paths are redirected by isolated_env as well.
    return [
        "bwrap",
        "--ro-bind",
        "/",
        "/",
        "--bind",
        str(root),
        str(root),
        "--dev-bind",
        "/dev",
        "/dev",
        "--proc",
        "/proc",
        "--unshare-pid",
        "--new-session",
        "--die-with-parent",
        "--chdir",
        str(cwd),
        "--",
        *command,
    ]


def remote_mise():
    # Distributions install mise in /usr/bin; its official installer uses
    # ~/.local/bin. Pass the binary itself rather than widening PATH, so other
    # user tools in those directories cannot shadow python3 in the sandbox.
    search = [str(Path.home() / ".local/bin"), "/usr/local/bin", "/usr/bin", "/bin"]
    return shutil.which("mise", path=os.pathsep.join(search))


def init_container_root(root):
    """Mark a fresh volume as this worker's root; refuse a foreign one."""
    if not CONTAINER or Path(root) != CONTAINER_ROOT:
        raise ValueError("init is only for the container worker's /data")
    marker = CONTAINER_ROOT / MARKER
    if not marker.exists():
        if any(p.name != "lost+found" for p in CONTAINER_ROOT.iterdir()):
            raise ValueError("the volume holds other data; use a new volume")
        marker.write_text("v1\n")
    elif marker.read_text() != "v1\n":
        raise ValueError("unowned worker volume")
    return {"root": str(CONTAINER_ROOT), "release": IMAGE_REPOSITORY}


def remote(args):
    if args.action == "init":
        print(json.dumps(init_container_root(args.root)))
        return
    root = validate_root(args.root)
    env = isolated_env(root)
    env["PATH"] = "/usr/local/bin:/usr/bin:/bin" if CONTAINER else "/usr/bin:/bin"
    mise = remote_mise()
    if mise:
        env["PIAKURA_MISE"] = mise
    if CONTAINER:
        env["PIAKURA_CONTAINER"] = "1"
        env["PIAKURA_UV"] = os.environ.get("PIAKURA_UV", "")
    if args.action == "import-weights":
        with contained(root, root / "weights.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            print(import_weights(root, args.model, sys.stdin.buffer))
        return
    if args.action == "setup":
        family = family_for(args.model)
        with contained(root, root / "setup.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            subprocess.run(
                sandbox(
                    root,
                    [
                        "python3",
                        "-B",
                        str(SCRIPT / "setup_runtime.py"),
                        family,
                        "--runtime",
                        str(root),
                    ],
                    SCRIPT,
                ),
                env=env,
                check=True,
            )
        return
    if args.action == "create":
        request = json.load(sys.stdin)
        if request.get("model") not in MODELS or request.get("device") not in (
            "cpu",
            "cuda",
        ):
            raise ValueError("invalid model/device")
        if not re.fullmatch(r"[0-9a-f]{64}", request.get("input_sha256", "")):
            raise ValueError("invalid input hash")
        if not 1 <= request.get("timeout_seconds", 0) <= 86400:
            raise ValueError("timeout must be 1..86400 seconds")
        job_id = uuid.uuid4().hex
        job = job_path(root, job_id)
        job.mkdir(parents=True, mode=0o700)
        request.update(id=job_id, release=SCRIPT.name, created=time.time())
        write_json(job / "request.json", request)
        write_json(job / "status.json", {"state": "created", "id": job_id})
        print(json.dumps({"id": job_id}))
        return
    job = job_path(root, args.job)
    request = json.loads((job / "request.json").read_text())
    if args.action == "upload":
        path = contained(root, job / "input.audio")
        with path.open("xb") as stream:
            shutil.copyfileobj(sys.stdin.buffer, stream)
        if digest(path) != request["input_sha256"]:
            raise ValueError("uploaded input checksum mismatch")
        print(json.dumps({"uploaded": args.job}))
    elif args.action == "start":
        # Serialize concurrent start requests before publishing queued state.
        with contained(root, job / "start.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if json.loads((job / "status.json").read_text())["state"] != "created":
                raise ValueError("job already started; create a new job for retries")
            if digest(job / "input.audio") != request["input_sha256"]:
                raise ValueError("input checksum mismatch")
            command = [
                sys.executable,
                "-B",
                str(SCRIPT / "worker.py"),
                "_remote",
                "run",
                "--root",
                str(root),
                "--job",
                args.job,
            ]
            write_json(job / "status.json", {"state": "queued", "id": args.job})
            if args.no_spawn:
                # A container exits with its main process, so the client starts
                # the runner in its own detached container instead.
                print(json.dumps({"id": args.job, "queued": True}))
                return
            with (job / "runner.log").open("ab") as log:
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=log,
                    start_new_session=True,
                    env=env,
                )
            print(json.dumps({"id": args.job, "pid": process.pid}))
    elif args.action == "run":
        run_job(root, job, request, env)
    elif args.action == "status":
        print((job / "status.json").read_text())
    elif args.action == "cancel":
        # The runner consumes this flag and terminates only its own child group.
        # Never send a signal to a stale PID from a previous login/session.
        (job / "cancel").touch(exist_ok=True)
        print(json.dumps({"id": args.job, "cancel_requested": True}))
    elif args.action == "fetch":
        with tarfile.open(fileobj=sys.stdout.buffer, mode="w|") as archive:
            for path in sorted(job.rglob("*")):
                if path.is_symlink():
                    raise ValueError("symlink output refused")
                if path.is_file() and path.name != "input.audio":
                    archive.add(
                        path, arcname=str(path.relative_to(job)), recursive=False
                    )


def run_job(root, job, request, env):
    started = time.monotonic()
    state = {"id": request["id"], "state": "queued", "release": request["release"]}
    with contained(root, root / "gpu.lock").open("w") as lock:
        while True:
            if (job / "cancel").exists():
                state["state"] = "cancelled"
                write_json(job / "status.json", state)
                return
            if time.monotonic() - started > request["timeout_seconds"]:
                state.update(state="failed", error="queue timeout")
                write_json(job / "status.json", state)
                return
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                time.sleep(1)
        try:
            if request["device"] == "cuda":
                output = subprocess.check_output(
                    [
                        "nvidia-smi",
                        "--query-gpu=memory.free",
                        "--format=csv,noheader,nounits",
                    ],
                    text=True,
                )
                free = int(output.splitlines()[0])
                state["initial_free_vram_mib"] = free
                if free < 3072:
                    raise ValueError(
                        "less than 3 GiB VRAM free; job deferred without touching other processes"
                    )
            python = environment(root, request["model"]) / "bin/python"
            if not python.is_file():
                raise ValueError(
                    "backend environment missing; deploy with --backend first"
                )
            output_dir = job / "output"
            output_dir.mkdir()
            command = sandbox(
                root,
                [
                    str(python),
                    "-B",
                    str(SCRIPT / "backend.py"),
                    request["model"],
                    str(job / "input.audio"),
                    str(output_dir / "raw.mid"),
                    "--runtime",
                    str(root),
                    "--device",
                    request["device"],
                ],
                job,
            )
            state.update(state="running", started=time.time())
            write_json(job / "status.json", state)
            with (job / "inference.log").open("wb") as log:
                process = subprocess.Popen(
                    command,
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=log,
                    start_new_session=True,
                )
                while process.poll() is None:
                    if (
                        job / "cancel"
                    ).exists() or time.monotonic() - started > request[
                        "timeout_seconds"
                    ]:
                        os.killpg(process.pid, signal.SIGTERM)
                        try:
                            process.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            os.killpg(process.pid, signal.SIGKILL)
                            process.wait()
                        state["state"] = (
                            "cancelled" if (job / "cancel").exists() else "failed"
                        )
                        state["error"] = (
                            "cancelled"
                            if state["state"] == "cancelled"
                            else "execution timeout"
                        )
                        break
                    time.sleep(1)
                else:
                    if process.returncode != 0:
                        raise ValueError(
                            f"inference exited {process.returncode}; see inference.log"
                        )
                    if (output_dir / "raw.mid").read_bytes()[:4] != b"MThd":
                        raise ValueError("missing or invalid MIDI output")
                    hashes = {
                        str(p.relative_to(job)): digest(p)
                        for p in sorted(output_dir.rglob("*"))
                        if p.is_file()
                    }
                    write_json(job / "checksums.json", hashes)
                    state["state"] = "succeeded"
        except (ValueError, OSError, subprocess.SubprocessError) as error:
            state.update(state="failed", error=str(error))
        state["elapsed_seconds"] = time.monotonic() - started
        write_json(job / "status.json", state)


def ssh(host, command, **kwargs):
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.@:-]*", host):
        raise ValueError("invalid SSH host")
    return subprocess.run(
        ["ssh", *SSH_OPTIONS, host, shlex.join(command)], check=True, **kwargs
    )


def default_state(host):
    if os.environ.get("PIAKURA_WORKER_STATE"):
        return Path(os.environ["PIAKURA_WORKER_STATE"])
    state = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local/state")
    name = re.sub(r"[^A-Za-z0-9._-]", "_", host) + ".json"
    return Path(state) / "piakura" / "workers" / name


def home_relative(root):
    return str(root).removeprefix("~/")


IMAGE_PATTERN = re.compile(r"[a-z0-9][a-z0-9./_-]*(:[\w.-]+)?(@sha256:[0-9a-f]{64})?")
VOLUME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")


def default_image():
    # An installed skill pins the image of its own release.
    version = SCRIPT.parent / "VERSION"
    if version.is_file():
        return f"{IMAGE_REPOSITORY}:{version.read_text().strip()}"
    return None


def docker_run(image, volume, action, *extra, name=None, gpus=False, network=None):
    """A docker run of one _remote action with the container sandbox flags."""
    if not IMAGE_PATTERN.fullmatch(image or "") or not VOLUME_PATTERN.fullmatch(volume):
        raise ValueError("invalid image or volume name")
    command = ["docker", "run", "--rm", "-i"]
    if name:
        command += ["-d", "--name", name]
    command += [
        "--pull",
        "never",
        "--read-only",
        "--tmpfs",
        "/tmp",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "-v",
        f"{volume}:{CONTAINER_ROOT}",
    ]
    if gpus:
        command += ["--gpus", "all"]
    if network:
        command += ["--network", network]
    return [*command, image, "_remote", action, "--root", str(CONTAINER_ROOT), *extra]


def inference_network(model, choice):
    # SheetSage2 downloads its encoder while it runs; every other backend has
    # everything after setup and runs without a network.
    return None if model == "sheetsage2" or choice == "default" else "none"


def client(args):
    container = args.transport != "ssh"
    if args.transport != "docker" and not args.host:
        raise ValueError("--host or PIAKURA_TRANSCRIPTION_HOST is required")
    if container:
        args.image = args.image or default_image()
        if not args.image:
            raise ValueError("--image or PIAKURA_WORKER_IMAGE is required here")
    where = args.host if args.transport != "docker" else "local-docker"
    args.state = args.state or default_state(where)

    def transport(command, **kwargs):
        if args.transport == "docker":
            return subprocess.run(command, check=True, **kwargs)
        return ssh(args.host, command, **kwargs)

    if args.action == "deploy" and container:
        # A release tag names one image, so an image this Docker already has
        # (pulled before, loaded from a file, or built here as the release
        # workflow does) is used as is. Pulling it anyway failed without
        # access to the registry, and a tag pushed only after testing is not
        # there yet.
        try:
            transport(
                ["docker", "image", "inspect", args.image],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            transport(["docker", "pull", args.image], stdout=subprocess.DEVNULL)
        reply = transport(
            docker_run(args.image, args.volume, "init"), capture_output=True
        )
        deployment = {
            **json.loads(reply.stdout),
            "image": args.image,
            "volume": args.volume,
        }
        args.state.parent.mkdir(parents=True, exist_ok=True)
        write_json(
            args.state, {**deployment, "host": where, "transport": args.transport}
        )
        print(json.dumps(deployment), flush=True)
        if not args.backend:
            return
        args.action = "setup"
    elif args.action == "deploy":
        paths = list(SCRIPT.glob("*.py")) + list(
            (SCRIPT / "environments").glob("*.lock")
        )
        files = {
            str(p.relative_to(SCRIPT)): base64.b64encode(p.read_bytes()).decode()
            for p in paths
        }
        reply = ssh(
            args.host,
            ["python3", "-B", "-c", BOOTSTRAP],
            input=json.dumps(
                {"root": home_relative(args.root), "files": files}
            ).encode(),
            capture_output=True,
        )
        deployment = json.loads(reply.stdout)
        args.state.parent.mkdir(parents=True, exist_ok=True)
        write_json(args.state, {**deployment, "host": args.host})
        print(json.dumps(deployment), flush=True)
        if args.backend:
            args.action = "setup"
        else:
            return
    deployment = json.loads(args.state.read_text())
    if (
        deployment["host"] != where
        or deployment.get("transport", "ssh") != args.transport
    ):
        raise ValueError("deployment host or transport mismatch")
    root, release = deployment["root"], deployment["release"]
    script = f"{root}/releases/{release}/worker.py"

    def call(action, *extra, **kwargs):
        if container:
            image, volume = deployment["image"], deployment["volume"]
            return transport(docker_run(image, volume, action, *extra), **kwargs)
        return ssh(
            args.host,
            ["python3", "-B", script, "_remote", action, "--root", root, *extra],
            **kwargs,
        )

    if args.action == "import-weights":
        with args.checkpoint.open("rb") as stream:
            call("import-weights", "--model", args.model, stdin=stream)
    elif args.action == "setup":
        call("setup", "--model", args.backend)
    elif args.action == "submit":
        request = {
            "model": args.model,
            "device": args.device,
            "input_sha256": digest(args.input),
            "timeout_seconds": args.timeout,
        }
        reply = call("create", input=json.dumps(request).encode(), capture_output=True)
        job_id = json.loads(reply.stdout)["id"]
        with args.input.open("rb") as stream:
            call("upload", "--job", job_id, stdin=stream, stdout=subprocess.DEVNULL)
        if container:
            call("start", "--job", job_id, "--no-spawn", stdout=subprocess.DEVNULL)
            runner = docker_run(
                deployment["image"],
                deployment["volume"],
                "run",
                "--job",
                job_id,
                name=f"piakura-job-{job_id}",
                gpus=args.device == "cuda",
                network=inference_network(args.model, args.inference_network),
            )
            transport(runner, stdout=subprocess.DEVNULL)
            print(json.dumps({"id": job_id}))
        else:
            call("start", "--job", job_id)
    elif args.action in ("status", "cancel"):
        call(args.action, "--job", args.job)
    elif args.action == "fetch":
        if args.output.exists():
            raise ValueError(
                "fetch destination must be new; previous results are immutable"
            )
        reply = call("fetch", "--job", args.job, capture_output=True)
        args.output.mkdir(parents=True)
        with tarfile.open(fileobj=io.BytesIO(reply.stdout)) as archive:
            for member in archive:
                path = contained(args.output, args.output / member.name)
                if not member.isfile():
                    raise ValueError("non-file archive member refused")
                path.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as source, path.open("xb") as dest:
                    shutil.copyfileobj(source, dest)
        checksums = args.output / "checksums.json"
        if checksums.exists():
            for path, expected in json.loads(checksums.read_text()).items():
                if digest(contained(args.output, args.output / path)) != expected:
                    raise ValueError("fetched output checksum mismatch")
        print(
            json.dumps(
                {
                    "output": str(args.output),
                    "status": json.loads((args.output / "status.json").read_text()),
                }
            )
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    if len(sys.argv) > 1 and sys.argv[1] == "_remote":
        parser.add_argument("internal")
        parser.add_argument(
            "action",
            choices=[
                "init",
                "import-weights",
                "setup",
                "create",
                "upload",
                "start",
                "run",
                "status",
                "fetch",
                "cancel",
            ],
        )
        parser.add_argument("--root", type=Path, required=True)
        parser.add_argument("--job")
        parser.add_argument("--model", choices=MODELS)
        parser.add_argument("--no-spawn", action="store_true")
        remote(parser.parse_args())
        return
    parser.add_argument("--host", default=os.environ.get("PIAKURA_TRANSCRIPTION_HOST"))
    parser.add_argument(
        "--transport",
        choices=["ssh", "ssh-docker", "docker"],
        default="ssh",
        help="ssh: deployed release; ssh-docker or docker: the worker image",
    )
    parser.add_argument("--image", default=os.environ.get("PIAKURA_WORKER_IMAGE"))
    parser.add_argument("--volume", default="piakura-worker")
    parser.add_argument(
        "--inference-network", choices=["none", "default"], default="none"
    )
    parser.add_argument(
        "--state",
        type=Path,
        help="deployment record (default: PIAKURA_WORKER_STATE or "
        "$XDG_STATE_HOME/piakura/workers/<host>.json)",
    )
    sub = parser.add_subparsers(dest="action", required=True)
    deploy = sub.add_parser("deploy")
    deploy.add_argument(
        "--root",
        default=os.environ.get("PIAKURA_WORKER_ROOT", "piakura-worker"),
        help="worker directory relative to the remote home; parents must exist",
    )
    deploy.add_argument("--backend", choices=MODELS)
    weights = sub.add_parser("import-weights")
    weights.add_argument("model", choices=CHECKPOINTS)
    weights.add_argument("checkpoint", type=Path)
    submit = sub.add_parser("submit")
    submit.add_argument("input", type=Path)
    submit.add_argument("--model", choices=MODELS, default="yourmt3")
    submit.add_argument("--device", choices=["cpu", "cuda"], default="cuda")
    submit.add_argument("--timeout", type=int, default=3600)
    for action in ("status", "cancel", "fetch"):
        command = sub.add_parser(action)
        command.add_argument("job")
        if action == "fetch":
            command.add_argument("output", type=Path)
    client(parser.parse_args())


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"worker: {error}", file=sys.stderr)
        sys.exit(2)
