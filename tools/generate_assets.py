#!/usr/bin/env python3
"""Generate lightweight game assets for GitHub Pages deployment.

Uses only the Python standard library. The Seoul skyline is downloaded from
Wikimedia Commons (CC0); a tiny fallback JPEG is used if the download fails.
"""
from __future__ import annotations

import base64
import math
import random
import struct
import urllib.request
import wave
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "assets" / "audio"
IMAGES = ROOT / "assets" / "images"
ICONS = ROOT / "assets" / "icons"
for directory in (AUDIO, IMAGES, ICONS):
    directory.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 22050


def clamp16(value: float) -> int:
    return max(-32767, min(32767, int(value * 32767)))


def write_wav(name: str, duration: float, sample_fn) -> None:
    total = int(SAMPLE_RATE * duration)
    frames = bytearray()
    for i in range(total):
        t = i / SAMPLE_RATE
        frames += struct.pack("<h", clamp16(sample_fn(t, i, total)))
    with wave.open(str(AUDIO / name), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(frames)


def generate_audio() -> None:
    rng = random.Random(2607)

    last = 0.0
    def crowd(t, _i, _n):
        nonlocal last
        noise = rng.uniform(-1, 1)
        last = last * 0.94 + noise * 0.06
        chant = math.sin(2 * math.pi * 1.35 * t) * 0.035
        swell = 0.55 + 0.25 * math.sin(2 * math.pi * 0.09 * t)
        return (last * 0.22 + chant) * swell
    write_wav("stadium-crowd.wav", 10.0, crowd)

    def kick(t, _i, _n):
        env = math.exp(-24 * t)
        return env * (0.7 * math.sin(2 * math.pi * (118 - 45 * t) * t) + rng.uniform(-0.22, 0.22))
    write_wav("kick.wav", 0.24, kick)

    def whistle(t, _i, _n):
        env = min(1, t * 30) * max(0, 1 - t / 0.72)
        vibrato = 120 * math.sin(2 * math.pi * 7 * t)
        return env * 0.35 * math.sin(2 * math.pi * (1850 + vibrato) * t)
    write_wav("whistle.wav", 0.72, whistle)

    def goal(t, _i, _n):
        env = max(0, 1 - t / 1.8)
        chord = sum(math.sin(2 * math.pi * f * t) for f in (262, 330, 392, 523)) / 4
        cheer = rng.uniform(-1, 1) * (0.12 + 0.16 * math.sin(math.pi * min(1, t / 0.5)))
        return env * (0.48 * chord + cheer)
    write_wav("goal.wav", 1.8, goal)

    def special(t, _i, _n):
        env = max(0, 1 - t / 0.9)
        freq = 180 + 920 * (t / 0.9) ** 1.5
        return env * 0.42 * (math.sin(2 * math.pi * freq * t) + 0.25 * math.sin(2 * math.pi * freq * 2 * t))
    write_wav("special.wav", 0.9, special)

    def pickup(t, _i, _n):
        env = max(0, 1 - t / 0.42)
        freq = 620 + 680 * (t / 0.42)
        return env * 0.38 * math.sin(2 * math.pi * freq * t)
    write_wav("pickup.wav", 0.42, pickup)


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def write_icon(size: int) -> None:
    pixels = bytearray()
    cx = cy = size / 2
    ball_r = size * 0.23
    for y in range(size):
        pixels.append(0)
        for x in range(size):
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy)
            mix = (x + y) / (2 * size)
            r = int(5 + 7 * mix)
            g = int(18 + 31 * mix)
            b = int(28 + 38 * mix)
            edge = min(x, y, size - 1 - x, size - 1 - y)
            if size * 0.045 < edge < size * 0.08:
                r, g, b = 33, 214, 232
            if d <= ball_r:
                r, g, b = 246, 251, 255
                if d < ball_r * 0.34:
                    r, g, b = 23, 33, 42
                for angle in [i * 2 * math.pi / 5 - math.pi / 2 for i in range(5)]:
                    px = cx + math.cos(angle) * ball_r * 0.72
                    py = cy + math.sin(angle) * ball_r * 0.72
                    if math.hypot(x - px, y - py) < ball_r * 0.13:
                        r, g, b = 23, 33, 42
                        break
            if size * 0.2 < x < size * 0.8 and size * 0.79 < y < size * 0.9:
                r, g, b = 139, 255, 186
            pixels.extend((r, g, b, 255))
    raw = bytes(pixels)
    png = b"\x89PNG\r\n\x1a\n"
    png += png_chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
    png += png_chunk(b"IDAT", zlib.compress(raw, 9))
    png += png_chunk(b"IEND", b"")
    (ICONS / f"icon-{size}.png").write_bytes(png)


def download_skyline() -> None:
    destination = IMAGES / "seoul-skyline.jpg"
    url = "https://commons.wikimedia.org/wiki/Special:Redirect/file/Seoul%20Skyline%20Night%202018.jpg?width=1200"
    request = urllib.request.Request(url, headers={"User-Agent": "Jangsoccer-GitHub-Pages/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            data = response.read()
        if len(data) < 10000 or not data.startswith(b"\xff\xd8"):
            raise RuntimeError("unexpected image response")
        destination.write_bytes(data)
        print(f"Downloaded skyline image: {len(data):,} bytes")
    except Exception as exc:
        fallback = base64.b64decode(
            "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////"
            "2wBDAf//////////////////////////////////////////////////////////////////////////////////////"
            "wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAX/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAF//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABBQJ//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAwEBPwF//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAgEBPwF//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQAGPwJ//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPyF//9oADAMBAAIAAwAAABAf/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAwEBPxB//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAgEBPxB//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxB//9k="
        )
        destination.write_bytes(fallback)
        print(f"Skyline download failed ({exc}); wrote fallback image")


def main() -> None:
    generate_audio()
    write_icon(192)
    write_icon(512)
    download_skyline()
    print("Generated game assets")


if __name__ == "__main__":
    main()
