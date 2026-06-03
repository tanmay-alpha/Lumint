import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

from research.dataset_manifest import DatasetManifest, DatasetType

# Re-use regexes from anonymization for checking leaks
EMAIL_REGEX = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')
PHONE_REGEX = re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|\b\d{10}\b')
UPI_ID_REGEX = re.compile(r'\b[a-zA-Z0-9.\-_]+@[a-zA-Z0-9]+\b')
UTR_REGEX = re.compile(r'\b\d{12}\b')
USER_PATH_REGEX = re.compile(r'(?:[cC]:\\Users\\|/home/|/Users/)([^/\\]+)', re.IGNORECASE)

class DatasetValidationIssue(BaseModel):
    severity: Literal["info", "warning", "error"]
    code: str
    detail: str
    record_id: Optional[str] = None

def check_label_distribution(manifest: DatasetManifest) -> List[DatasetValidationIssue]:
    """
    Checks if there's extreme class imbalance or missing classes.
    """
    issues = []
    total = len(manifest.records)
    if total == 0:
        issues.append(DatasetValidationIssue(
            severity="error",
            code="EMPTY_MANIFEST",
            detail="The manifest contains no records."
        ))
        return issues
        
    counts = {"CLEAN": 0, "SUSPICIOUS": 0, "HIGH": 0}
    for r in manifest.records:
        counts[r.label] = counts.get(r.label, 0) + 1
        
    for label, count in counts.items():
        pct = (count / total) * 100
        if count == 0 and label in {"CLEAN", "HIGH"}:
            issues.append(DatasetValidationIssue(
                severity="warning",
                code="MISSING_CLASS",
                detail=f"Label class '{label}' has 0 records. This makes benchmarking difficult."
            ))
        elif pct > 95.0:
            issues.append(DatasetValidationIssue(
                severity="warning",
                code="EXTREME_IMBALANCE",
                detail=f"Label class '{label}' constitutes {pct:.1f}% of the dataset."
            ))
            
    return issues

def check_missing_files(manifest: DatasetManifest, base_dir: Optional[Path] = None) -> List[DatasetValidationIssue]:
    """
    Checks if files specified as path_or_value exist locally (for file-based datasets).
    """
    issues = []
    for r in manifest.records:
        # Only check document or screenshot paths, URLs are not local files
        if r.dataset_type in {DatasetType.DOCUMENT, DatasetType.UPI_SCREENSHOT}:
            val_path = Path(r.path_or_value)
            if base_dir and not val_path.is_absolute():
                val_path = base_dir / val_path
                
            if not val_path.exists():
                issues.append(DatasetValidationIssue(
                    severity="warning",
                    code="MISSING_FILE",
                    detail=f"Local file does not exist: {r.path_or_value}",
                    record_id=r.id
                ))
    return issues

def check_duplicate_records(manifest: DatasetManifest) -> List[DatasetValidationIssue]:
    """
    Checks for duplicate record IDs or duplicate content paths/values.
    """
    issues = []
    seen_ids = set()
    dup_ids = set()
    
    seen_vals = {}
    
    for r in manifest.records:
        # Check IDs
        if r.id in seen_ids:
            dup_ids.add(r.id)
            issues.append(DatasetValidationIssue(
                severity="error",
                code="DUPLICATE_ID",
                detail=f"Duplicate record ID found: {r.id}",
                record_id=r.id
            ))
        seen_ids.add(r.id)
        
        # Check values
        if r.path_or_value in seen_vals:
            original_id = seen_vals[r.path_or_value]
            issues.append(DatasetValidationIssue(
                severity="warning",
                code="DUPLICATE_VALUE",
                detail=f"Value/Path is identical to record '{original_id}': {r.path_or_value}",
                record_id=r.id
            ))
        else:
            seen_vals[r.path_or_value] = r.id
            
    return issues

def _scan_text_for_leaks(text: str, record_id: str, field_name: str) -> List[DatasetValidationIssue]:
    issues = []
    if not text:
        return issues
        
    # Check emails
    if EMAIL_REGEX.search(text):
        issues.append(DatasetValidationIssue(
            severity="warning",
            code="LEAK_EMAIL",
            detail=f"Potential email address leak in {field_name}",
            record_id=record_id
        ))
        
    # Check phone
    if PHONE_REGEX.search(text):
        # Ensure we don't flag simple small integers
        # Phone numbers are typically longer strings
        issues.append(DatasetValidationIssue(
            severity="warning",
            code="LEAK_PHONE",
            detail=f"Potential phone number leak in {field_name}",
            record_id=record_id
        ))
        
    # Check UPI ID
    # Since UPI regex matches user@bank, we must filter out things that were already flagged as email
    # by checking if it ends with standard domain extensions (.com, .org) or bank names.
    # To keep it simple, if we find matches, check if it's an email first.
    upi_matches = UPI_ID_REGEX.findall(text)
    for match in upi_matches:
        # if the match is an email address, skip flagging as UPI ID
        if not EMAIL_REGEX.search(match):
            issues.append(DatasetValidationIssue(
                severity="warning",
                code="LEAK_UPI_ID",
                detail=f"Potential UPI ID leak in {field_name}",
                record_id=record_id
            ))
            break
            
    # Check 12-digit UTR
    if UTR_REGEX.search(text):
        issues.append(DatasetValidationIssue(
            severity="warning",
            code="LEAK_UTR",
            detail=f"Potential 12-digit UTR transaction number leak in {field_name}",
            record_id=record_id
        ))
        
    # Check absolute paths containing username
    match_user = USER_PATH_REGEX.search(text)
    if match_user:
        # Flag username leaks
        username = match_user.group(1)
        # Avoid flagging system names like 'Default' or 'Public'
        if username.lower() not in {"default", "public", "administrator", "all users", "system32"}:
            issues.append(DatasetValidationIssue(
                severity="warning",
                code="LEAK_USERNAME",
                detail=f"Absolute path contains username '{username}' in {field_name}",
                record_id=record_id
            ))
            
    # Check raw query string in URLs
    if text.startswith(("http://", "https://")) and "?" in text:
        issues.append(DatasetValidationIssue(
            severity="info",
            code="URL_QUERY_PARAMS",
            detail="URL contains raw query parameters. Ensure no session tokens or API keys are exposed.",
            record_id=record_id
        ))
        
    return issues

def _scan_metadata_recursive(meta: Any, record_id: str, prefix: str) -> List[DatasetValidationIssue]:
    issues = []
    if isinstance(meta, dict):
        for k, v in meta.items():
            issues.extend(_scan_metadata_recursive(v, record_id, f"{prefix}.{k}"))
    elif isinstance(meta, list):
        for idx, item in enumerate(meta):
            issues.extend(_scan_metadata_recursive(item, record_id, f"{prefix}[{idx}]"))
    elif isinstance(meta, str):
        issues.extend(_scan_text_for_leaks(meta, record_id, prefix))
    return issues

def check_private_data_leakage(manifest: DatasetManifest) -> List[DatasetValidationIssue]:
    """
    Scans path_or_value and metadata for sensitive information leaks (email, phone, UPI, UTR, username).
    """
    issues = []
    for r in manifest.records:
        # Scan value
        issues.extend(_scan_text_for_leaks(r.path_or_value, r.id, "path_or_value"))
        # Scan metadata
        issues.extend(_scan_metadata_recursive(r.metadata, r.id, "metadata"))
    return issues

def validate_manifest_for_experiment(manifest: DatasetManifest) -> List[Dict[str, Any]]:
    """
    Runs all validator functions on the manifest and returns a list of dictionaries.
    """
    issues = []
    issues.extend(check_duplicate_records(manifest))
    issues.extend(check_label_distribution(manifest))
    issues.extend(check_missing_files(manifest))
    issues.extend(check_private_data_leakage(manifest))
    return [issue.model_dump() for issue in issues]

def summarize_validation(issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregates validation issues into severity counts and determining overall validity.
    """
    summary = {
        "valid": True,
        "error_count": 0,
        "warning_count": 0,
        "info_count": 0,
        "codes": set()
    }
    for issue in issues:
        severity = issue.get("severity")
        code = issue.get("code")
        if code:
            summary["codes"].add(code)
            
        if severity == "error":
            summary["error_count"] += 1
            summary["valid"] = False
        elif severity == "warning":
            summary["warning_count"] += 1
        elif severity == "info":
            summary["info_count"] += 1
            
    summary["codes"] = list(summary["codes"])
    return summary
