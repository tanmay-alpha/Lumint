from pathlib import Path
from typing import Optional
import fitz  # PyMuPDF
from PIL import Image
from PIL.ExifTags import TAGS


SUSPICIOUS_EDITORS = [
    "photoshop", "gimp", "canva", "illustrator", "inkscape", "image editor"
]


def extract_metadata(file_path: Path) -> dict:
    if file_path.suffix.lower() in [".pdf"]:
        doc = fitz.open(str(file_path))
        meta = doc.metadata or {}
        page_count = doc.page_count
        is_encrypted = doc.is_encrypted
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
    else:
        # Image
        try:
            with Image.open(file_path) as img:
                exif_data = img.getexif()
                exif = {}
                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        # Filter out very long byte strings like MakerNote
                        if isinstance(value, bytes):
                            if len(value) > 50:
                                value = f"<{len(value)} bytes>"
                            else:
                                try:
                                    value = value.decode("utf-8", errors="replace")
                                except:
                                    value = repr(value)
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
            return {
                "title": None,
                "author": None,
                "creator": None,
                "producer": None,
                "creation_date": None,
                "modification_date": None,
                "page_count": 1,
                "is_encrypted": False,
                "file_size": file_path.stat().st_size,
            }


def check_suspicious_editor(metadata: dict) -> Optional[dict]:
    creator = (metadata.get("creator") or "").lower()
    producer = (metadata.get("producer") or "").lower()
    combined = creator + " " + producer

    for editor in SUSPICIOUS_EDITORS:
        if editor in combined:
            return {
                "rule": "suspicious_editor",
                "score": 25,
                "detail": f"Document created or processed using suspicious tool: '{editor}'.",
            }
    return None


def check_metadata_mismatch(metadata: dict) -> Optional[dict]:
    creation = metadata.get("creation_date")
    modification = metadata.get("modification_date")

    if creation and modification and creation != modification:
        return {
            "rule": "metadata_mismatch",
            "score": 20,
            "detail": "Document creation date and modification date are different.",
        }
    return None


def check_blank_author(metadata: dict) -> Optional[dict]:
    author = metadata.get("author")
    if not author or author.strip() == "":
        return {
            "rule": "blank_author",
            "score": 5,
            "detail": "Document has no author field. May indicate auto-generation or tampering.",
        }
    return None


def check_encrypted(metadata: dict) -> Optional[dict]:
    if metadata.get("is_encrypted"):
        return {
            "rule": "encrypted_pdf",
            "score": 15,
            "detail": "PDF is encrypted. Content verification is restricted.",
        }
    return None


def run_metadata_analysis(file_path: Path) -> dict:
    metadata = extract_metadata(file_path)

    indicators = []
    for check_fn in [
        check_suspicious_editor,
        check_metadata_mismatch,
        check_blank_author,
        check_encrypted,
    ]:
        result = check_fn(metadata)
        if result:
            indicators.append(result)

    return {
        "metadata": metadata,
        "indicators": indicators,
    }