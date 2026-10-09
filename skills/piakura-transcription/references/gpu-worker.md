# Authorized SSH GPU worker

Use only a host and directory authorized by the user. This worker deploys into one directory under the remote home, given relative to it with `--root` (default `piakura-worker`, or `PIAKURA_WORKER_ROOT`). Its parent directories must already exist as real directories; an existing worker directory must carry the worker's ownership marker. All installations, weights, inputs, outputs, logs, caches and temporary files stay inside it. Setup and inference run with the host filesystem read-only except that directory; bubblewrap is required, with no unsandboxed fallback.

The host must be Linux and already provide key-based SSH access (with its host key in `known_hosts`; give a port or user through a `~/.ssh/config` Host alias), Python 3.9 or later, mise (in `PATH`, `/usr/local/bin` or `~/.local/bin`), bubblewrap and the NVIDIA driver. `piakura doctor --ssh HOST` checks these read-only. The worker installs its own pinned Python/uv and model environments within its root. It changes neither system packages nor shell profiles. Do not use sudo, system services, a global Docker cache or kill unrelated GPU processes to make room.

```bash
bash scripts/worker.sh --host HOST deploy --root piakura-worker --backend yourmt3
bash scripts/worker.sh --host HOST submit "$WORK/excerpt/audio.wav" --model yourmt3 --device cuda
# Use the returned job ID:
bash scripts/worker.sh --host HOST status JOB_ID
bash scripts/worker.sh --host HOST fetch JOB_ID "$WORK/gpu-attempt"
bash scripts/worker.sh --host HOST cancel JOB_ID
```

`PIAKURA_TRANSCRIPTION_HOST` can supply the host. Local deployment metadata lives in `$XDG_STATE_HOME/piakura/workers/<host>.json` (`PIAKURA_WORKER_STATE` or `--state` select another file). Releases are content-addressed so a running job keeps its original code. Deploy again to install changed code. A backend environment is reusable only for the same dependency-lock hash.

Use the host and owned directory the user authorized, and the job's `device`. When the GPU is busy, follow the job's `gpu_unavailable` choice rather than switching to CPU on your own. Preserve a failed job; a retry is a new attempt.

Only one worker job runs at a time. The timeout covers queue and execution. CUDA jobs check free VRAM before starting; insufficient memory becomes a recorded failure, leaving other processes untouched. On a shared 8 GB GPU start with medium/small or YourMT3, batch 1 and FP16. Test supported CUDA kernels and memory with a short self-authored recording before a full song; neither an 8GB label nor a small checkpoint proves a full inference will fit.

SSH disconnection does not discard a started job. `status` reports created/queued/running/succeeded/failed/cancelled. Cancellation writes a request consumed by the runner, which terminates only its own child process group. A retry is a new job, preserving the old error and input hash. A machine reboot may leave a running status stale; inspect that job's logs and rerun as a new job instead of assuming success.

Fetch uses a new local destination, rejects path traversal/symlinks and checks hashes of successful outputs. Fetch failed jobs too when diagnosing errors. The raw MIDI still needs Go parsing and both round-trips before musical editing. Remove only specific owned job files when cleanup is explicitly requested; never clean the host's other projects or caches.

## Container worker (experimental)

With `how: container` the same jobs run in the piakura worker image (`ghcr.io/anosatsuk124/piakura-worker:<version>`, the version of this skill) instead of a deployed release. The image holds only Python, uv and these scripts; environments and weights are downloaded into a Docker volume on first use. Each step runs as `docker run --rm` with a read-only root, no capabilities, `no-new-privileges` and a non-root user, and only the volume (`/data`) is writable. Inference runs with `--network none`, except SheetSage2, which downloads during inference.

```bash
W="bash scripts/worker.sh --transport ssh-docker --host HOST"   # or --transport docker on this machine
$W deploy --backend yourmt3          # pull if missing, initialize the volume, set up
$W submit "$WORK/excerpt/audio.wav" --model yourmt3 --device cuda
$W status JOB_ID
$W fetch JOB_ID "$WORK/gpu-attempt"
```

The host needs Docker, and the NVIDIA Container Toolkit for `--device cuda`. Membership in the `docker` group is equivalent to root on that host; say so before the user chooses it. While the image is private, pulling it needs a login to `ghcr.io` with read access (`docker login ghcr.io`); an image that host's Docker already has (pulled before, or loaded with `docker load`) is used without one. `--volume` names another volume, and an existing volume is used only if piakura initialized it. Long jobs run in a detached container named `piakura-job-<id>`; `cancel` asks the runner to stop as before. Docker Desktop on macOS has no GPU, so prefer `--transport ssh-docker` to a Linux GPU host there.
