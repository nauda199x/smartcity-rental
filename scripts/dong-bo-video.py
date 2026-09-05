#!/usr/bin/env python3
"""Cache public apartment videos as browser-compatible MP4s; never edit data.json."""
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "video-can-ho"
API = "https://script.google.com/macros/s/AKfycbxP2LYjIwPnf9VPofUtKjyIETqo9lGjAmv-AT0txsh0NXcTZhdZLkpHcDDssGQtjEWs/exec?action=inventory"
PREVIEW = re.compile(r"https://drive\.google\.com/file/d/([A-Za-z0-9_-]+)/preview(?:[?#].*)?", re.I)
MAX_INPUT = 400 * 1024 * 1024
MAX_OUTPUT = 30 * 1024 * 1024
MAX_TOTAL = 450 * 1024 * 1024


def video_urls(value):
    values = value if isinstance(value, list) else str(value or "").splitlines()
    return list(dict.fromkeys(s.strip() for s in values if isinstance(s, str) and PREVIEW.fullmatch(s.strip())))


def filename(url):
    drive_id = PREVIEW.fullmatch(url).group(1)
    return hashlib.sha256(("h264-v1:" + drive_id).encode()).hexdigest()[:20] + ".mp4"


def encoding_budget(duration):
    # Leave room for audio and container overhead on longer walkthroughs.
    # A fixed 1.4 Mbps ceiling can exceed 30 MiB for a four-minute video.
    rate = max(160, min(1400, int(MAX_OUTPUT * 0.88 * 8 / duration / 1000) - 96))
    return rate, 720 if rate < 900 else 1280


def probe(path):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)], capture_output=True, text=True, check=True, timeout=30)
    data = json.loads(result.stdout)
    stream = next(s for s in data["streams"] if s.get("codec_type") == "video")
    duration = float(data["format"].get("duration", 0))
    if not duration or not stream.get("width") or not stream.get("height"):
        raise ValueError("Video thiếu thông tin kích thước hoặc thời lượng")
    return {"width": stream["width"], "height": stream["height"], "duration": round(duration, 2), "bytes": path.stat().st_size}


def download(url, target):
    drive_id = PREVIEW.fullmatch(url).group(1)
    direct = "https://drive.usercontent.google.com/download?" + urllib.parse.urlencode({"id": drive_id, "export": "download", "confirm": "t"})
    request = urllib.request.Request(direct, headers={"User-Agent": "SmartCityVideoSync/1.0"})
    with urllib.request.urlopen(request, timeout=90) as response, target.open("wb") as file:
        mime = response.headers.get("Content-Type", "").lower()
        if not (mime.startswith("video/") or "application/octet-stream" in mime):
            raise ValueError("Drive chưa trả file video công khai")
        size = 0
        while chunk := response.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_INPUT:
                raise ValueError("Video vượt giới hạn tải")
            file.write(chunk)


def convert(url, target):
    with tempfile.TemporaryDirectory(prefix="smartcity-video-") as directory:
        original = Path(directory) / "original"
        encoded = Path(directory) / "video.mp4"
        download(url, original)
        rate, edge = encoding_budget(probe(original)["duration"])
        # Fit either orientation, keep the complete picture, and put MP4 metadata
        # first so Safari can start without downloading the complete file.
        subprocess.run([
            "ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(original),
            "-map", "0:v:0", "-map", "0:a:0?", "-sn", "-dn", "-map_metadata", "-1",
            "-vf", f"scale=w='min({edge},iw)':h='min({edge},ih)':force_original_aspect_ratio=decrease:force_divisible_by=2,setsar=1",
            "-c:v", "libx264", "-profile:v", "main", "-pix_fmt", "yuv420p", "-preset", "fast",
            "-crf", "27", "-maxrate", f"{rate}k", "-bufsize", f"{rate * 2}k", "-threads", "2",
            "-c:a", "aac", "-b:a", "96k", "-ac", "2", "-movflags", "+faststart", str(encoded),
        ], check=True, timeout=900)
        info = probe(encoded)
        if info["bytes"] > MAX_OUTPUT:
            raise ValueError("Video tối ưu vượt giới hạn dung lượng")
        total = sum(p.stat().st_size for p in OUT.glob("*.mp4"))
        if total + info["bytes"] > MAX_TOTAL:
            raise ValueError("Kho video đạt giới hạn dung lượng")
        encoded.replace(target)
        return info


def create_poster(video, info):
    """One real frame per clip, also generated for previously cached MP4s."""
    poster = video.with_suffix(".webp")
    if not poster.exists():
        temporary = poster.with_suffix(".tmp.webp")
        try:
            subprocess.run([
                "ffmpeg", "-nostdin", "-v", "error", "-y",
                "-ss", str(min(1, info["duration"] / 3)), "-i", str(video),
                "-frames:v", "1", "-vf", "scale=w='min(800,iw)':h='min(800,ih)':force_original_aspect_ratio=decrease",
                "-c:v", "libwebp", "-quality", "80", "-threads", "2", str(temporary),
            ], check=True, timeout=60)
            if not temporary.exists() or not temporary.stat().st_size:
                raise ValueError("Không tạo được ảnh bìa từ video")
            temporary.replace(poster)
        finally:
            temporary.unlink(missing_ok=True)
    return "/video-can-ho/" + poster.name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, help="Use a saved inventory response for verification")
    parser.add_argument("--limit", type=int, default=0, help="Maximum new videos to encode, 0 = all")
    args = parser.parse_args()
    if args.inventory:
        inventory = json.loads(args.inventory.read_text())
    else:
        with urllib.request.urlopen(API, timeout=120) as response:
            inventory = json.load(response)
    if inventory.get("ok") is not True or not isinstance(inventory.get("items"), list) or not inventory["items"]:
        raise ValueError("Inventory không hợp lệ; giữ nguyên kho video hiện có")
    rows = json.loads((ROOT / "data.json").read_text())
    active = {str(row.get("Mã nội bộ", "")).strip() for row in rows if str(row.get("Hiển thị trên Web", "")).strip().lower() in ("có", "co", "yes", "true", "1")}
    if not active:
        raise ValueError("Không đọc được quỹ căn đang hiển thị; giữ nguyên kho video")
    selected = {str(item.get("id", "")).strip(): video_urls(item.get("videoList")) for item in inventory["items"] if str(item.get("id", "")).strip() in active}
    selected = {code: urls for code, urls in selected.items() if urls}
    OUT.mkdir(exist_ok=True)
    old_path = OUT / "manifest.json"
    old = json.loads(old_path.read_text()) if old_path.exists() else {}
    needed = {filename(url) for urls in selected.values() for url in urls}
    # Remove only our own generated files after both input sources validated.
    for path in OUT.glob("*.mp4"):
        if re.fullmatch(r"[a-f0-9]{20}\.mp4", path.name) and path.name not in needed:
            path.unlink()
    for path in OUT.glob("*.webp"):
        if re.fullmatch(r"[a-f0-9]{20}\.webp", path.name) and path.with_suffix(".mp4").name not in needed:
            path.unlink()
    items, processed, failures = {}, 0, 0
    for code, urls in sorted(selected.items()):
        sources = {}
        for url in urls:
            target = OUT / filename(url)
            try:
                if target.exists():
                    info = probe(target)
                elif not args.limit or processed < args.limit:
                    processed += 1
                    print(f"Tối ưu video {code} ({processed})", flush=True)
                    info = convert(url, target)
                else:
                    continue
                sources[url] = {"src": "/video-can-ho/" + target.name, **info}
                # A poster failure must not discard a playable MP4.
                try:
                    sources[url]["poster"] = create_poster(target, info)
                except (OSError, ValueError, subprocess.SubprocessError) as error:
                    print(f"::warning::Ảnh bìa video {code}: {type(error).__name__}", flush=True)
            except (OSError, ValueError, StopIteration, subprocess.SubprocessError) as error:
                failures += 1
                print(f"::warning::Video {code}: {type(error).__name__}; vẫn có liên kết video gốc", flush=True)
        cover = next((sources[u]["poster"] for u in urls if sources.get(u, {}).get("poster")), "")
        items[code] = {"videos": urls, "sources": sources, "cover": cover}
    manifest = {"version": 1, "items": items}
    if old.get("items") != items or old.get("version") != 1:
        manifest["updatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        temporary = OUT / "manifest.json.tmp"
        temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        temporary.replace(old_path)
    # Refresh existing static pages as well as newly generated apartment URLs.
    for page in ROOT.rglob("*.html"):
        html = page.read_text()
        updated = re.sub(r"/assets/can-ho-detail.js\?v=[\w-]+", "/assets/can-ho-detail.js?v=20260905-3", html)
        updated = re.sub(r"/assets/can-ho-detail-i18n.js\?v=[\w-]+", "/assets/can-ho-detail-i18n.js?v=20260905-3", updated)
        updated = re.sub(r"/dong-bo-can.js\?v=[\w-]+", "/dong-bo-can.js?v=20260905-3", updated)
        if updated != html:
            page.write_text(updated)
    print(f"{len(items)} căn; {sum(len(x['sources']) for x in items.values())} video MP4; {failures} video cần nguồn gốc", flush=True)


if __name__ == "__main__":
    main()
