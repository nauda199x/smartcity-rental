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
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "video-can-ho"
API = "https://script.google.com/macros/s/AKfycbxP2LYjIwPnf9VPofUtKjyIETqo9lGjAmv-AT0txsh0NXcTZhdZLkpHcDDssGQtjEWs/exec?action=inventory"
DRIVE_ID = re.compile(r"^[A-Za-z0-9_-]{10,}$")
DRIVE_FILE_PATH = re.compile(r"/file/d/([A-Za-z0-9_-]{10,})(?:/|$)", re.I)
VIDEO_EXT = re.compile(r"\.(?:mp4|mov|m4v|webm)(?:[?#\"'].*)?$", re.I)
MAX_INPUT = 400 * 1024 * 1024
MAX_OUTPUT = 30 * 1024 * 1024
MAX_TOTAL = 450 * 1024 * 1024


def extract_drive_id(value):
    """Return a Drive file id from known public Drive URL shapes or a raw id."""
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    if DRIVE_ID.fullmatch(text):
        return text
    try:
        parsed = urllib.parse.urlparse(text)
    except ValueError:
        return ""
    host = (parsed.hostname or "").lower()
    if host not in {"drive.google.com", "docs.google.com", "drive.usercontent.google.com"}:
        return ""
    match = DRIVE_FILE_PATH.search(parsed.path)
    if match:
        return match.group(1)
    query = urllib.parse.parse_qs(parsed.query)
    for key in ("id", "file_id", "fileId"):
        candidate = (query.get(key) or [""])[0].strip()
        if DRIVE_ID.fullmatch(candidate):
            return candidate
    return ""


def canonical_drive_url(drive_id):
    return f"https://drive.google.com/file/d/{drive_id}/preview"


def direct_drive_url(drive_id):
    return "https://drive.usercontent.google.com/download?" + urllib.parse.urlencode(
        {"id": drive_id, "export": "download", "confirm": "t"}
    )


def video_urls(value):
    """Normalize known Drive video values to canonical preview URLs."""
    values = value if isinstance(value, list) else str(value or "").splitlines()
    urls = []
    for entry in values:
        raw = entry
        mime = ""
        name = ""
        if isinstance(entry, dict):
            mime = str(entry.get("mimeType") or entry.get("mime") or "").strip().lower()
            name = str(entry.get("name") or entry.get("fileName") or "").strip()
            raw = (
                entry.get("fileId") or entry.get("id") or entry.get("url")
                or entry.get("previewUrl") or entry.get("webViewLink") or ""
            )
            if mime and not mime.startswith("video/") and not VIDEO_EXT.search(name):
                continue
        elif not isinstance(entry, str):
            continue
        drive_id = extract_drive_id(raw)
        if not drive_id:
            continue
        url = canonical_drive_url(drive_id)
        if url not in urls:
            urls.append(url)
    return urls


def remote_is_video(drive_id):
    """Probe response metadata so a video-only thumbnail can be recovered safely."""
    request = urllib.request.Request(
        direct_drive_url(drive_id),
        headers={"User-Agent": "SmartCityVideoSync/1.4", "Range": "bytes=0-0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            mime = response.headers.get("Content-Type", "").lower()
            disposition = response.headers.get("Content-Disposition", "")
            return mime.startswith("video/") or (
                "application/octet-stream" in mime and bool(VIDEO_EXT.search(disposition))
            )
    except (OSError, ValueError):
        return False


def filename(url):
    drive_id = extract_drive_id(url)
    if not drive_id:
        raise ValueError("Không nhận diện được Drive file id")
    return hashlib.sha256(("h264-v1:" + drive_id).encode()).hexdigest()[:20] + ".mp4"


def encoding_budget(duration):
    rate = max(160, min(1400, int(MAX_OUTPUT * 0.88 * 8 / duration / 1000) - 96))
    return rate, 720 if rate < 900 else 1280


def probe(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True, text=True, check=True, timeout=30,
    )
    data = json.loads(result.stdout)
    stream = next(s for s in data["streams"] if s.get("codec_type") == "video")
    duration = float(data["format"].get("duration", 0))
    if not duration or not stream.get("width") or not stream.get("height"):
        raise ValueError("Video thiếu thông tin kích thước hoặc thời lượng")
    return {
        "width": stream["width"], "height": stream["height"],
        "duration": round(duration, 2), "bytes": path.stat().st_size,
    }


def download(url, target):
    drive_id = extract_drive_id(url)
    if not drive_id:
        raise ValueError("Không nhận diện được Drive file id")
    request = urllib.request.Request(
        direct_drive_url(drive_id), headers={"User-Agent": "SmartCityVideoSync/1.4"}
    )
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
                "-frames:v", "1",
                "-vf", "scale=w='min(800,iw)':h='min(800,ih)':force_original_aspect_ratio=decrease",
                "-c:v", "libwebp", "-quality", "80", "-threads", "2", str(temporary),
            ], check=True, timeout=60)
            if not temporary.exists() or not temporary.stat().st_size:
                raise ValueError("Không tạo được ảnh bìa từ video")
            temporary.replace(poster)
        finally:
            temporary.unlink(missing_ok=True)
    return "/video-can-ho/" + poster.name


def valid_inventory(value):
    return (
        isinstance(value, dict)
        and value.get("ok") is True
        and isinstance(value.get("items"), list)
        and bool(value["items"])
    )


def load_inventory(path):
    """Strict for test fixtures; fault-tolerant for the live Apps Script endpoint."""
    if path:
        value = json.loads(path.read_text())
        if not valid_inventory(value):
            raise ValueError("Inventory không hợp lệ; giữ nguyên kho video hiện có")
        return value, True
    try:
        request = urllib.request.Request(API, headers={"User-Agent": "SmartCityVideoSync/1.4"})
        with urllib.request.urlopen(request, timeout=15) as response:
            value = json.load(response)
        if not valid_inventory(value):
            raise ValueError("inventory payload invalid")
        return value, True
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(
            f"::warning::Inventory API không dùng được ({type(error).__name__}); "
            "giữ video hiện có và dùng fallback an toàn từ data.json.",
            flush=True,
        )
        return None, False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, help="Use a saved inventory response for verification")
    parser.add_argument("--limit", type=int, default=0, help="Maximum new videos to encode, 0 = all")
    args = parser.parse_args()

    OUT.mkdir(exist_ok=True)
    old_path = OUT / "manifest.json"
    try:
        old = json.loads(old_path.read_text()) if old_path.exists() else {}
    except (OSError, ValueError):
        old = {}
    old_items = old.get("items") if old.get("version") == 1 and isinstance(old.get("items"), dict) else {}

    inventory, inventory_ok = load_inventory(args.inventory)
    rows = json.loads((ROOT / "data.json").read_text())
    active_rows = {
        str(row.get("Mã nội bộ", "")).strip(): row
        for row in rows
        if str(row.get("Mã nội bộ", "")).strip()
        and str(row.get("Hiển thị trên Web", "")).strip().lower() in ("có", "co", "yes", "true", "1")
    }
    active = set(active_rows)
    if not active:
        raise ValueError("Không đọc được quỹ căn đang hiển thị; giữ nguyên kho video")

    selected = {}
    rejected = []
    if inventory_ok:
        for item in inventory["items"]:
            code = str(item.get("id", "")).strip()
            if not code or code not in active:
                continue
            raw_videos = item.get("videoList")
            urls = video_urls(raw_videos)
            if urls:
                selected[code] = urls
            elif raw_videos:
                rejected.append(code)
    else:
        # A temporary Apps Script outage must never erase already published media.
        for code, item in old_items.items():
            if code not in active or not isinstance(item, dict):
                continue
            urls = video_urls(item.get("videos"))
            if urls:
                selected[code] = urls
        print(f"Giữ lại {len(selected)} căn video từ manifest gần nhất.", flush=True)

    if rejected:
        sample = ", ".join(rejected[:20])
        more = f" +{len(rejected) - 20} căn" if len(rejected) > 20 else ""
        print(f"::warning::Có videoList nhưng không nhận diện được Drive file id: {sample}{more}", flush=True)

    # Recover rows where the upstream sheet used an MP4 thumbnail as "Ảnh đại diện"
    # while leaving Danh sách ảnh/Video empty. Probe candidates concurrently so a
    # temporary Drive slowdown cannot turn this safety fallback into a long serial job.
    candidates = {}
    for code, row in active_rows.items():
        row_urls = video_urls(row.get("Video"))
        if row_urls:
            selected[code] = row_urls
            continue
        if code in selected or str(row.get("Danh sách ảnh", "")).strip():
            continue
        cover_id = extract_drive_id(row.get("Ảnh đại diện"))
        if cover_id:
            candidates[code] = cover_id

    recovered = []
    if candidates:
        with ThreadPoolExecutor(max_workers=min(12, len(candidates))) as pool:
            futures = {pool.submit(remote_is_video, drive_id): (code, drive_id) for code, drive_id in candidates.items()}
            for future in as_completed(futures):
                code, drive_id = futures[future]
                try:
                    is_video = future.result()
                except Exception:
                    is_video = False
                if is_video:
                    selected[code] = [canonical_drive_url(drive_id)]
                    recovered.append(code)
    if recovered:
        recovered.sort()
        print("Khôi phục video-only từ ảnh đại diện: " + ", ".join(recovered), flush=True)

    if not inventory_ok and not selected:
        raise ValueError("Inventory đang lỗi và không có manifest/fallback video an toàn; giữ nguyên kho video")

    needed = {filename(url) for urls in selected.values() for url in urls}
    # Prune only with an authoritative inventory. During an outage stale cache is
    # harmless; deleting a still-live video is not.
    if inventory_ok:
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
    if old_items != items or old.get("version") != 1:
        manifest["updatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        temporary = OUT / "manifest.json.tmp"
        temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        temporary.replace(old_path)

    for page in ROOT.rglob("*.html"):
        html = page.read_text()
        updated = re.sub(r"/assets/can-ho-detail.js\?v=[\w-]+", "/assets/can-ho-detail.js?v=20260905-3", html)
        updated = re.sub(r"/assets/can-ho-detail-i18n.js\?v=[\w-]+", "/assets/can-ho-detail-i18n.js?v=20260905-3", updated)
        updated = re.sub(r"/dong-bo-can.js\?v=[\w-]+", "/dong-bo-can.js?v=20260905-3", updated)
        if updated != html:
            page.write_text(updated)

    mode = "inventory" if inventory_ok else "fallback"
    print(
        f"{len(items)} căn; {sum(len(x['sources']) for x in items.values())} video MP4; "
        f"{failures} video cần nguồn gốc; chế độ {mode}",
        flush=True,
    )


if __name__ == "__main__":
    main()
