from pathlib import Path
from typing import Optional

import fitz
from PIL import Image
from PIL.ExifTags import TAGS

SUSPICIOUS_EDITORS = {"photoshop", "gimp", "canva", "illustrator", "inkscape", "image editor"}


def _empty_metadata(file_path: Path, page_count: int = 1, is_encrypted: bool = False) -> dict:
    return {
        "title": None, "author": None, "creator": None, "producer": None,
        "creation_date": None, "modification_date": None,
        "page_count": page_count, "is_encrypted": is_encrypted,
        "file_size": file_path.stat().st_size,
    }


def extract_metadata(file_path: Path) -> dict:
    if file_path.suffix.lower() == ".pdf":
        doc = fitz.open(str(file_path))
        meta = doc.metadata or {}
        page_count, is_encrypted = doc.page_count, doc.is_encrypted
        doc.close()
        return {
            "title": meta.get("title") or None,
            "author": meta.get("author") or None,
            "creator": meta.get("creator") or None,
            "producer": meta.get("producer") or None,
            "creation_date": meta.get("creationDate") or None,
            "modification_date": meta.get("modDate") or None,
            "page_count": page_count,
            "is_encrypted": is_encrypted,
            "file_size": file_path.stat().st_size,
        }

    try:
        with Image.open(file_path) as img:
            raw = img.getexif()
            exif: dict[str, str] = {}
            for tag_id, value in (raw or {}).items():
                tag = TAGS.get(tag_id, tag_id)
                if isinstance(value, bytes):
                    value = f"<{len(value)} bytes>" if len(value) > 50 else value.decode("utf-8", errors="replace")
                exif[str(tag)] = str(value)
        creator = exif.get("Software") or exif.get("ProcessingSoftware") or exif.get("HostComputer")
        return {
            "title": None,
            "author": exif.get("Artist") or None,
            "creator": creator or None,
            "producer": exif.get("Model") or exif.get("Make") or None,
            "creation_date": exif.get("DateTimeOriginal") or exif.get("DateTime") or None,
            "modification_date": exif.get("DateTime") or None,
            "page_count": 1,
            "is_encrypted": False,
            "file_size": file_path.stat().st_size,
        }
    except Exception:
        return _empty_metadata(file_path)


def check_suspicious_editor(metadata: dict) -> Optional[dict]:
    combined = f"{metadata.get('creator', '') or ''} {metadata.get('producer', '') or ''}".lower()
    for editor in SUSPICIOUS_EDITORS:
        if editor in combined:
            return {"rule": "suspicious_editor", "score": 25, "detail": f"Document processed using suspicious tool: '{editor}'."}
    return None


def check_metadata_mismatch(metadata: dict) -> Optional[dict]:
    c, m = metadata.get("creation_date"), metadata.get("modification_date")
    if c and m and c != m:
        return {"rule": "metadata_mismatch", "score": 20, "detail": "Document creation date and modification date are different."}
    return None


def check_blank_author(metadata: dict) -> Optional[dict]:
    author = metadata.get("author")
    if not author or not author.strip():
        return {"rule": "blank_author", "score": 5, "detail": "Document has no author field. May indicate auto-generation or tampering."}
    return None


def check_encrypted(metadata: dict) -> Optional[dict]:
    if metadata.get("is_encrypted"):
        return {"rule": "encrypted_pdf", "score": 15, "detail": "PDF is encrypted. Content verification is restricted."}
    return None


def run_metadata_analysis(file_path: Path) -> dict:
    metadata = extract_metadata(file_path)
    indicators = [
        r for r in (
            check_suspicious_editor(metadata),
            check_metadata_mismatch(metadata),
            check_blank_author(metadata),
            check_encrypted(metadata),
        ) if r
    ]
    return {"metadata": metadata, "indicators": indicators}