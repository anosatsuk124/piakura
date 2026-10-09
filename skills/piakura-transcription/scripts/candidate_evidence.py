"""Phrase-sized evidence for reconstruction; scores retain their native meaning.

This reads Go note sidecars, never MIDI. It proposes neither a winning pitch nor
a score edit. See references/candidate-evidence.md for the manifest contract.
"""

import bisect
import json
import math
from collections import defaultdict
from pathlib import Path

from runtime import digest


def number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def validate_frames(times, rows, score_kind):
    if len(times) != len(rows) or not times:
        raise ValueError("frame times and rows must be nonempty and equal length")
    if score_kind not in (
        "activation",
        "salience",
        "softmax",
        "voicing",
        "periodicity",
    ):
        raise ValueError("unsupported uncalibrated score kind")
    previous = -math.inf
    for time, row in zip(times, rows, strict=True):
        if number(time, "frame time") <= previous:
            raise ValueError("frame times must strictly increase")
        previous = time
        for pitch, score in row:
            if not 0 <= number(pitch, "pitch") <= 127:
                raise ValueError("pitch outside MIDI range")
            if not 0 <= number(score, "score") <= 1:
                raise ValueError("scores must be in [0, 1], not raw logits")


def summarize_frames(evidence, start, end, pitch=None):
    times, rows = evidence["times"], evidence["rows"]
    first, last = bisect.bisect_left(times, start), bisect.bisect_left(times, end)
    totals = defaultdict(float)
    nonempty = 0
    support = 0.0
    for row in rows[first:last]:
        nonempty += bool(row)
        # Neighboring sub-semitone bins are alternatives, not independent votes.
        frame = defaultdict(float)
        for value, score in row:
            rounded = math.floor(value + 0.5)
            frame[rounded] = max(frame[rounded], score)
        for value, score in frame.items():
            totals[value] += score
        if pitch is not None:
            support += max((s for p, s in row if abs(p - pitch) <= 0.5), default=0)
    count = last - first
    ranked = sorted(totals.items(), key=lambda x: (-x[1], x[0]))[:3]
    return {
        "artifact_id": evidence["id"],
        "score_kind": evidence["score_kind"],
        "frame_count": count,
        "nonempty_frame_fraction": nonempty / count if count else None,
        "top_pitches": [{"midi": p, "mean_score": s / count} for p, s in ranked],
        "candidate_pitch_mean_score": support / count
        if count and pitch is not None
        else None,
        "calibrated_probability": None,
    }


def uncovered_runs(evidence, notes, start, end, minimum=0.04):
    """Expose unexplained voiced contours without converting them into notes."""
    if evidence.get("monophonic") is not True:
        return []
    threshold = evidence.get("review_threshold")
    if threshold is None:
        return []
    number(threshold, "review threshold")
    if not 0 <= threshold <= 1:
        raise ValueError("review threshold outside [0, 1]")
    times, rows = evidence["times"], evidence["rows"]
    runs = []
    current = None
    for i, (time, row) in enumerate(zip(times, rows, strict=True)):
        if not start <= time < end:
            continue
        next_time = min(times[i + 1], end) if i + 1 < len(times) else time
        strongest = max(row, key=lambda p: p[1]) if row else None
        missing = (
            strongest is not None
            and strongest[1] >= threshold
            and not any(
                n["start_seconds"] <= time < n["end_seconds"]
                and abs(n["pitch"] - strongest[0]) <= 0.5
                for n in notes
            )
        )
        pitch = math.floor(strongest[0] + 0.5) if missing else None
        if current and (
            pitch != current["pitch"] or time > current["end_seconds"] + 1e-8
        ):
            runs.append(current)
            current = None
        if missing:
            if current is None:
                current = {
                    "pitch": pitch,
                    "start_seconds": time,
                    "end_seconds": next_time,
                }
            else:
                current["end_seconds"] = next_time
    if current:
        runs.append(current)
    return [
        {**r, "artifact_id": evidence["id"], "status": "unexplained_contour"}
        for r in runs
        if r["end_seconds"] - r["start_seconds"] >= minimum - 1e-9
    ]


def boundary_peaks(evidence, start, end):
    """Expose native local maxima, without converting them into note attacks."""
    times, scores = evidence["times"], evidence["scores"]
    return [
        {
            "artifact_id": evidence["id"],
            "event_type": evidence["event_type"],
            "seconds": times[i],
            "score": scores[i],
            "score_kind": evidence["score_kind"],
            "calibrated_probability": None,
        }
        for i in range(1, len(times) - 1)
        if start <= times[i] < end
        and scores[i] >= evidence["review_threshold"]
        and scores[i] > scores[i - 1]
        and scores[i] >= scores[i + 1]
    ]


def load_boundaries(spec, path):
    if spec["format"] == "json":
        data = json.loads(path.read_text())
        times, scores = data["times"], data["scores"]
    elif spec["format"] == "npz":
        import numpy as np

        with np.load(path, allow_pickle=False) as data:
            times = data[spec.get("times", "times")].tolist()
            scores = data[spec.get("scores", "boundary_score")].tolist()
    else:
        raise ValueError("unsupported boundary format")
    if spec["score_kind"] not in ("sigmoid", "activation") or spec[
        "event_type"
    ] not in (
        "note_onset",
        "note_boundary",
    ):
        raise ValueError("declare native boundary score and event semantics")
    threshold = number(spec["review_threshold"], "boundary review threshold")
    if not 0 <= threshold <= 1:
        raise ValueError("boundary review threshold outside [0, 1]")
    offset = number(spec.get("source_offset_seconds", 0), "source offset")
    times = [number(t, "boundary time") + offset for t in times]
    # Reuse clock/range validation; the dummy pitch carries no musical meaning.
    validate_frames(times, [[(0, s)] for s in scores], "activation")
    return {**spec, "times": times, "scores": scores}


def phrase_packet(phrase, notes, frames, duration, padding=1, boundaries=()):
    start = number(phrase["start_seconds"], "phrase start")
    end = number(phrase["end_seconds"], "phrase end")
    if not 0 <= start < end <= duration:
        raise ValueError("phrase outside recording")
    left, right = max(0, start - padding), min(duration, end + padding)
    selected = [
        n for n in notes if n["start_seconds"] < right and n["end_seconds"] > left
    ]
    peaks = [
        p for evidence in boundaries for p in boundary_peaks(evidence, left, right)
    ]
    annotated = []
    for note in selected:
        annotated.append(
            {
                **note,
                "context_only": not start <= note["start_seconds"] < end,
                "nearby_boundaries": [
                    p
                    for p in peaks
                    if abs(p["seconds"] - note["start_seconds"]) <= 0.12
                ],
                "acoustic_support": [
                    summarize_frames(
                        f,
                        max(left, note["start_seconds"]),
                        min(right, note["end_seconds"]),
                        note["pitch"],
                    )
                    for f in frames
                ],
            }
        )
    return {
        **phrase,
        "context_start_seconds": left,
        "context_end_seconds": right,
        "notes": annotated,
        "frame_summaries": [summarize_frames(f, start, end) for f in frames],
        "boundary_candidates": peaks,
        "unexplained_contours": [
            {**r, "candidate_id": candidate}
            for candidate in sorted(
                {n.get("artifact_id", "candidate") for n in notes} or {"candidate"}
            )
            for f in frames
            for r in uncovered_runs(
                f,
                [n for n in selected if n.get("artifact_id", "candidate") == candidate],
                start,
                end,
            )
        ],
        "theory_hypotheses": phrase.get("theory_hypotheses", []),
        "review_status": "unreviewed",
    }


def load_frames(spec, path):
    offset = number(spec.get("source_offset_seconds", 0), "source offset")
    if spec["format"] == "pitch-json":
        data = json.loads(path.read_text())
        times = [t + offset for t in data["times"]]
        scores = data.get("voicing_score", data.get("voiced_probability"))
        if (
            scores is None
            or len(scores) != len(times)
            or len(data["pitch"]) != len(times)
        ):
            raise ValueError("pitch/voicing arrays do not match times")
        rows = [
            [(p, s)] if p is not None and s is not None else []
            for p, s in zip(data["pitch"], scores, strict=True)
        ]
    elif spec["format"] == "npz":
        import numpy as np

        with np.load(path, allow_pickle=False) as data:
            times = (data[spec.get("times", "times")] + offset).tolist()
            pitches = data[spec.get("pitches", "pitches")]
            matrix = data[spec["matrix"]]
            if matrix.ndim != 2 or matrix.shape != (len(times), len(pitches)):
                raise ValueError("score matrix axes do not match times/pitches")
            # Keep all bins for aggregation; top-k selection happens after the
            # note window is known, avoiding false zero support for a fourth bin.
            rows = [
                [(float(p), float(s)) for p, s in zip(pitches, row, strict=True)]
                for row in matrix
            ]
    else:
        raise ValueError("unsupported frame format")
    validate_frames(times, rows, spec["score_kind"])
    return {**spec, "times": times, "rows": rows}


def build_evidence(manifest_path):
    manifest_path = Path(manifest_path).resolve()
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("version") != 1:
        raise ValueError("unsupported evidence manifest")
    root = manifest_path.parent
    recording = manifest["recording"]
    source = (root / recording["path"]).resolve(strict=True)
    duration = number(recording["duration_seconds"], "recording duration")
    if duration <= 0:
        raise ValueError("recording duration must be positive")
    notes, frames, boundaries, artifacts, identifiers = [], [], [], [], set()
    for spec in manifest["artifacts"]:
        if spec["id"] in identifiers:
            raise ValueError("duplicate artifact id")
        identifiers.add(spec["id"])
        path = (root / spec["path"]).resolve(strict=True)
        artifacts.append({**spec, "sha256": digest(path)})
        if spec["kind"] == "frames":
            frames.append(load_frames(spec, path))
            continue
        if spec["kind"] == "boundaries":
            boundaries.append(load_boundaries(spec, path))
            continue
        if spec["kind"] != "notes":
            raise ValueError("unsupported artifact kind")
        channels = spec["channels"]
        if not channels or any(
            type(c) is not int or not 1 <= c <= 16 or c == 10 for c in channels
        ):
            raise ValueError("choose explicit pitched channels")
        data = json.loads(path.read_text())
        offset = number(spec.get("source_offset_seconds", 0), "source offset")
        for part_index, part in enumerate(data["parts"]):
            if part["channel"] not in channels:
                continue
            for index, n in enumerate(part.get("notes", [])):
                a = number(n["start_seconds"], "note start") + offset
                b = number(n["end_seconds"], "note end") + offset
                pitch = number(n["pitch"], "note pitch")
                if not a < b or not 0 <= pitch <= 127:
                    raise ValueError("invalid note interval or pitch")
                notes.append(
                    {
                        "artifact_id": spec["id"],
                        "note_id": n.get(
                            "id", f"{part_index}:{part['channel']}:{index}"
                        ),
                        "channel": part["channel"],
                        "role": spec["role"],
                        "pitch": pitch,
                        "start_seconds": a,
                        "end_seconds": b,
                    }
                )
    return {
        "version": 1,
        "timebase": "original recording seconds",
        "source_sha256": digest(source),
        "manifest_sha256": digest(manifest_path),
        "score_semantics": "uncalibrated; agreement is not ground-truth accuracy",
        "artifacts": artifacts,
        "phrases": [
            phrase_packet(p, notes, frames, duration, boundaries=boundaries)
            for p in manifest["phrases"]
        ],
    }
