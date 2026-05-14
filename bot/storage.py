from __future__ import annotations

import uuid

import httpx

from .config import settings
from .db import supabase

BUCKET = "visits"

# Bucket policy allows only these MIME types (see Supabase migration).
_EXT_MAP: dict[str, tuple[str, str]] = {
    "jpg": ("jpg", "image/jpeg"),
    "jpeg": ("jpg", "image/jpeg"),
    "png": ("png", "image/png"),
    "webp": ("webp", "image/webp"),
    "heic": ("heic", "image/heic"),
}


def _resolve_ext(file_path: str) -> tuple[str, str]:
    dot = file_path.rfind(".")
    raw = file_path[dot + 1 :].lower() if dot >= 0 else ""
    return _EXT_MAP.get(raw, ("jpg", "image/jpeg"))


async def upload_telegram_photo(file_id: str, visit_id: str, stage_type: str) -> str:
    """Download a Telegram photo and push it to the `visits` bucket. Returns object path."""
    token = settings.bot_token
    async with httpx.AsyncClient(timeout=30.0) as client:
        info_resp = await client.get(
            f"https://api.telegram.org/bot{token}/getFile",
            params={"file_id": file_id},
        )
        info = info_resp.json()
        if not info.get("ok") or not info.get("result", {}).get("file_path"):
            raise RuntimeError(
                f"Telegram getFile failed: {info.get('description') or info}"
            )
        file_path: str = info["result"]["file_path"]

        file_resp = await client.get(f"https://api.telegram.org/file/bot{token}/{file_path}")
        if file_resp.status_code != 200:
            raise RuntimeError(f"Telegram file download failed: HTTP {file_resp.status_code}")
        body = file_resp.content

    ext, mime = _resolve_ext(file_path)
    path = f"{visit_id}/{stage_type}/{uuid.uuid4()}.{ext}"

    try:
        supabase.storage.from_(BUCKET).upload(
            path=path,
            file=body,
            file_options={"content-type": mime, "upsert": "false"},
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Supabase upload to {BUCKET}/{path} failed: {exc}") from exc

    return path
