"""Optional audio reviewer. Responses are evidence, never executable edits."""

import base64
import fcntl
import json
import math
import os
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from runtime import digest, write_json


def reserve(ledger_path, limit, amount, request_id):
    if not all(math.isfinite(x) and x > 0 for x in (limit, amount)):
        raise ValueError("budget and reservation must be finite and positive")
    path = Path(ledger_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        data = (
            json.loads(path.read_text())
            if path.exists()
            else {"limit_usd": limit, "requests": {}}
        )
        if limit != data["limit_usd"]:
            raise ValueError("existing ledger limit cannot be changed by a request")
        if request_id in data["requests"]:
            raise ValueError("request already reserved")
        total = sum(
            item["charged_or_reserved_usd"] for item in data["requests"].values()
        )
        if total + amount > limit:
            raise ValueError("auxiliary model budget exhausted")
        data["requests"][request_id] = {
            "state": "reserved",
            "charged_or_reserved_usd": amount,
        }
        write_json(path, data)


def settle(ledger_path, request_id, cost):
    if (
        isinstance(cost, bool)
        or not isinstance(cost, (float, int))
        or not math.isfinite(cost)
        or cost < 0
    ):
        raise ValueError("provider did not return a valid charge; reservation retained")
    path = Path(ledger_path)
    with path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        data = json.loads(path.read_text())
        if data["requests"].get(request_id, {}).get("state") != "reserved":
            raise ValueError("only an existing reservation can be settled")
        data["requests"][request_id] = {
            "state": "settled",
            "charged_or_reserved_usd": cost,
        }
        write_json(path, data)


def openrouter(job, audio, args):
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise ValueError("OPENROUTER_API_KEY is not configured")
    for _, path in audio:
        if path.suffix.lower() not in (".wav", ".mp3", ".flac", ".ogg", ".m4a"):
            raise ValueError("unsupported audio extension")
    with urllib.request.urlopen(
        "https://openrouter.ai/api/v1/models", timeout=30
    ) as response:
        models = json.load(response)["data"]
    model = next((m for m in models if m["id"] == args.model), None)
    if model is None or "audio" not in model["architecture"]["input_modalities"]:
        raise ValueError("selected model does not advertise audio input")
    prices = [model["pricing"], *model["pricing"].get("overrides", [])]
    input_rate = max(float(p.get(k, 0)) for p in prices for k in ("prompt", "audio"))
    output_rate = max(float(p.get("completion", 0)) for p in prices)
    # Reserve the entire advertised context, not an optimistic audio-token
    # estimate. Unknown/failed charges keep their reservation and cannot retry
    # around the shared cap. Successful provider usage releases unused budget.
    ceiling = model["context_length"] * input_rate + 2048 * output_rate
    ceiling += float(model["pricing"].get("request", 0))
    request_id = uuid.uuid4().hex
    reserve(args.ledger, args.budget_usd, max(ceiling, 0.001), request_id)
    content = [{"type": "text", "text": job["prompt"]}]
    for label, path in audio:
        content += [
            {"type": "text", "text": f"Audio {label}:"},
            {
                "type": "input_audio",
                "input_audio": {
                    "data": base64.b64encode(path.read_bytes()).decode(),
                    "format": path.suffix.lower()[1:],
                },
            },
        ]
    body = {
        "model": args.model,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 2048,
        "temperature": 0,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "audio_review",
                "strict": True,
                "schema": job["schema"],
            },
        },
    }
    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        raise ValueError(
            f"OpenRouter HTTP {error.code}; budget reservation retained"
        ) from None
    usage = result.get("usage", {})
    if usage.get("cost") is not None:
        settle(args.ledger, request_id, usage["cost"])
    answer = json.loads(result["choices"][0]["message"]["content"])
    return {
        "answer": answer,
        "usage": usage,
        "request_id": request_id,
        "generation_id": result.get("id"),
        "pricing": model["pricing"],
    }


def assist(args):
    manifest = args.input.resolve()
    job = json.loads(manifest.read_text())
    if job.get("version") != 1:
        raise ValueError("unsupported audio review job")
    audio = [
        (a["label"], (manifest.parent / a["path"]).resolve(strict=True))
        for a in job["audio"]
    ]
    if not audio or len(audio) > 4:
        raise ValueError("provide one to four explicitly labeled audio files")
    started = time.monotonic()
    if args.provider == "openrouter":
        if args.ledger is None:
            raise ValueError("OpenRouter requires a shared budget ledger")
        response = openrouter(job, audio, args)
    else:
        if not args.model:
            raise ValueError("choose an explicit Antigravity model")
        # The CLI sandbox refuses native media reads outside its working
        # directory. Stage only the named media, never neighboring scores or
        # reference answers, and retain this minimal input bundle for audit.
        staging = Path(tempfile.mkdtemp(prefix="audio-input-", dir=manifest.parent))
        staged = []
        for index, (label, path) in enumerate(audio):
            target = staging / f"audio-{index}{path.suffix.lower()}"
            shutil.copyfile(path, target)
            staged.append((label, target))
        # Bare @paths did not attach audio in the verified CLI. Read the files
        # through the native media tool; prohibit command-based answer leakage.
        prompt = (
            job["prompt"]
            + "\nOpen these audio files using the native file/audio tool:\n"
        )
        prompt += "\n".join(f"{label}: {path}" for label, path in staged)
        prompt += "\nRead only these files. Do not run commands, inspect other files, search, or edit anything. If native audio is unavailable, explicitly abstain."
        completed = subprocess.run(
            [
                "agy",
                "--model",
                args.model,
                "--mode",
                "plan",
                "--sandbox",
                "--print-timeout",
                "150s",
                "--output-format",
                "json",
                "--json-schema",
                json.dumps(job["schema"]),
                "-p",
                prompt,
            ],
            cwd=staging,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        if completed.returncode:
            raise ValueError(f"Antigravity exited {completed.returncode}")
        result = json.loads(completed.stdout)
        # Keep unsuccessful provider results as well: a zero process exit can
        # still mean a timeout, missing media or absent structured output.
        response_path = (
            manifest.parent / f"antigravity-response-{uuid.uuid4().hex}.json"
        )
        write_json(response_path, result)
        if result.get("status") != "SUCCESS" or not isinstance(
            result.get("structured_output"), dict
        ):
            raise ValueError(
                f"Antigravity returned no successful structured review; see {response_path}"
            )
        response = {
            "answer": result["structured_output"],
            "usage": result.get("usage"),
            "conversation_id": result.get("conversation_id"),
            "additional_api_cost_usd": 0,
            "provider_response": str(response_path),
            "staged_audio_directory": str(staging),
        }
    return {
        "version": 1,
        "provider": args.provider,
        "model": args.model,
        "input_sha256": digest(manifest),
        "audio": [{"label": label, "sha256": digest(path)} for label, path in audio],
        "review_status": "auxiliary_model_opinion",
        "elapsed_seconds": time.monotonic() - started,
        **response,
    }
