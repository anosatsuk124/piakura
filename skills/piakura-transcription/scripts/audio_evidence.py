"""Measure candidate frequencies in explicit audio windows without inferring notes."""

import math
import subprocess
import sys
from array import array
from pathlib import Path

from runtime import digest

SAMPLE_RATE = 44100
FLOOR_POWER = 1e-12


def parse_request(pitches, windows, a4):
    pitches = sorted({float(value) for value in pitches.split(",")})
    windows = [
        tuple(float(value) for value in item.split(":")) for item in windows.split(",")
    ]
    if (
        not pitches
        or len(pitches) > 128
        or any(not math.isfinite(p) or not 0 <= p <= 127 for p in pitches)
    ):
        raise ValueError(
            "provide 1..128 MIDI pitches in 0..127 (fractional pitches allowed)"
        )
    if not math.isfinite(a4) or not 400 <= a4 <= 480:
        raise ValueError("A4 tuning must be 400..480 Hz")
    if not windows or len(windows) > 32:
        raise ValueError("provide 1..32 start:end windows")
    for window in windows:
        if len(window) != 2 or any(not math.isfinite(t) for t in window):
            raise ValueError("each window requires finite start:end seconds")
        start, end = window
        if start < 0 or not 0.05 <= end - start <= 4:
            raise ValueError("each window must start at >=0 and last 0.05..4 seconds")
    if sum(end - start for start, end in windows) > 30:
        raise ValueError("probe at most 30 seconds per request")
    return pitches, windows


def db(power):
    return 10 * math.log10(max(FLOOR_POWER, power))


def measure(channels, pitches, sample_rate=SAMPLE_RATE, a4=440):
    """Hann-windowed sinusoidal peak amplitudes, averaged as channel powers.

    This retains anti-phase stereo content that disappears in a mono average.
    It measures energy at a frequency, not the probability of a played note.
    See references/audio-evidence.md for units and interpretation.
    """
    count = len(channels[0]) if channels else 0
    if count < 3 or any(len(c) != count for c in channels):
        raise ValueError("audio window has insufficient or inconsistent samples")
    if any(not math.isfinite(v) for channel in channels for v in channel):
        raise ValueError("audio contains non-finite samples")
    window = [0.5 - 0.5 * math.cos(2 * math.pi * i / count) for i in range(count)]
    gain = sum(window)
    weighted = []
    for channel in channels:
        mean = sum(channel) / count
        weighted.append([(v - mean) * w for v, w in zip(channel, window)])
    measurements = []
    for pitch in pitches:
        frequency = a4 * 2 ** ((pitch - 69) / 12)
        if not 0 < frequency < sample_rate / 2:
            raise ValueError("candidate frequency must be below Nyquist")
        coefficient = 2 * math.cos(2 * math.pi * frequency / sample_rate)
        power = 0.0
        for channel in weighted:
            previous = earlier = 0.0
            for value in channel:
                current = value + coefficient * previous - earlier
                earlier, previous = previous, current
            power += max(0, previous**2 + earlier**2 - coefficient * previous * earlier)
        power *= 4 / (gain**2 * len(channels))
        measurements.append(
            {
                "midi_pitch": pitch,
                "frequency_hz": frequency,
                "amplitude_dbfs": db(power),
                "below_floor": power <= FLOOR_POWER,
                "cycles_in_window": count * frequency / sample_rate,
            }
        )
    loudest = max(m["amplitude_dbfs"] for m in measurements)
    for item in measurements:
        item["relative_db"] = (
            None if loudest <= -120 else item["amplitude_dbfs"] - loudest
        )
    rms = sum(v * v for channel in channels for v in channel) / (count * len(channels))
    return {
        "samples_per_channel": count,
        "rms_dbfs": db(rms),
        "candidates": measurements,
    }


def probe(source, pitches, windows, a4=440):
    source = Path(source).resolve(strict=True)
    pitches, windows = parse_request(pitches, windows, a4)
    metadata = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=channels",
            "-of",
            "csv=p=0",
            str(source),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    channels = int(metadata.stdout.strip())
    if not 1 <= channels <= 8:
        raise ValueError("probe supports 1..8 audio channels")
    results = []
    for start, end in windows:
        # Output-side seeking decodes and discards until the requested time.
        # Preserve channels instead of downmixing; use known PCM units/endian.
        process = subprocess.run(
            [
                "ffmpeg",
                "-nostdin",
                "-v",
                "error",
                "-i",
                str(source),
                "-ss",
                str(start),
                "-t",
                str(end - start),
                "-map",
                "0:a:0",
                "-vn",
                "-ar",
                str(SAMPLE_RATE),
                "-c:a",
                "pcm_f32le",
                "-f",
                "f32le",
                "pipe:1",
            ],
            check=True,
            capture_output=True,
            timeout=60,
        )
        values = array("f")
        values.frombytes(process.stdout)
        if sys.byteorder != "little":
            values.byteswap()
        if len(values) % channels:
            raise ValueError("decoded PCM has an incomplete audio frame")
        actual_duration = len(values) / (channels * SAMPLE_RATE)
        if abs(actual_duration - (end - start)) > 2 / SAMPLE_RATE:
            raise ValueError(
                "window extends beyond available audio; choose a complete interval"
            )
        result = measure([values[i::channels] for i in range(channels)], pitches, a4=a4)
        result.update(start_seconds=start, end_seconds=start + actual_duration)
        results.append(result)
    return {
        "version": 1,
        "source": str(source),
        "source_sha256": digest(source),
        "sample_rate": SAMPLE_RATE,
        "audio_channels": channels,
        "a4_hz": a4,
        "method": "periodic Hann / Goertzel / mean channel power / DC removed",
        "floor_dbfs": -120,
        "windows": results,
        "interpretation": "Spectral evidence only. Harmonics, leakage and other voices can explain peaks; amplitude is not note confidence.",
    }
