"""Read generated video covers for all static apartment/card generators."""
import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def video_manifest():
    try:
        value = json.loads((ROOT / "video-can-ho/manifest.json").read_text())
        return value["items"] if value.get("version") == 1 and isinstance(value.get("items"), dict) else {}
    except (OSError, ValueError):
        return {}


def media_video(can):
    return video_manifest().get(str(can.get("Mã nội bộ", "")).strip(), {})


def bia_video(can):
    cover = media_video(can).get("cover", "")
    if (re.fullmatch(r"/video-can-ho/[a-f0-9]{20}\.webp", cover)
            and (ROOT / cover.lstrip("/")).is_file()):
        return cover
    return ""
