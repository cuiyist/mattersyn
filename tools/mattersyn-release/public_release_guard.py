"""Fail-closed public release boundary and reusable offline history policy.

This module is a proposal overlay. It does not mutate a Git repository, call a
network service, or publish a site. Release inputs are exact-path, exact-hash
allowlisted; history callers can apply the same path/class/image rules to every
blob in every ref. Reports intentionally omit source text, credentials, and
absolute source paths.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit


POLICY_SCHEMA = "mattersyn-public-projection-policy/1"
ALLOWLIST_SCHEMA = "mattersyn-public-release-allowlist/1"
RIGHTS_SCHEMA = "mattersyn-public-asset-rights/1"
MANIFEST_SCHEMA = "mattersyn-public-release-manifest/1"
REPORT_SCHEMA = "mattersyn-public-boundary-report/1"
REPOSITORIES = {"mattersyn", "mattersyn-site"}

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif", ".tif", ".tiff", ".bmp", ".svg"}
SOURCE_DOCUMENT_SUFFIXES = {
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".zip", ".rar", ".7z",
    ".xls", ".xlsx", ".odt", ".rtf",
}
TEXT_SUFFIXES = {
    ".json", ".jsonl", ".ndjson", ".yaml", ".yml", ".toml", ".md",
    ".txt", ".csv", ".tsv", ".html", ".htm", ".css", ".js", ".mjs",
    ".cjs", ".py", ".sh", ".xml", ".svg", ".ini", ".rst",
    ".cif", ".sdf", ".xyz",
}
TEXT_FILENAMES = {".gitattributes", ".gitignore", ".nojekyll"}
CODE_SUFFIXES = {".py", ".js", ".mjs", ".cjs", ".css", ".sh"}

_DENIED_COMPONENTS = {
    ".git", ".cache", ".sites-runtime", ".venv", "venv", "node_modules",
    "private", "cache", "caches", "raw-cache", "text-cache",
    "downloaded_papers", "downloaded-papers", "source-render",
    "source-renders", "audit-pages", "page-renders", "first-page-text",
    "fulltext", "full-text", "raw-text", "extracted-text",
    "evidence-candidates", "corpus-screening",
}
_DENIED_PATH_PREFIXES = (
    "research-assets/incoming-paper-monitor/corpus-screening/",
    "research-assets/corpus-20260917/private/",
)
_DENIED_SCREENING_RE = re.compile(
    r"(?:^|/)research-assets/incoming-paper-monitor/deadline-[^/]+/.*(?:^|/)screen(?:/|$)",
    re.IGNORECASE,
)
_PAGE_RENDER_NAME_RE = re.compile(
    r"^(?:(?:main|si|page)[-_]?(?:page[-_]?)?\d+|contact[-_]?(?:sheet|pages)[-_]?\d*)\.(?:png|jpe?g|webp|tiff?)$",
    re.IGNORECASE,
)
_PATH_SLASH = chr(47)
_PATH_BACKSLASH = chr(92)
_PATH_SEPARATOR_CLASS = "[" + 2 * _PATH_BACKSLASH + _PATH_SLASH + "]"
_WINDOWS_PATH_SEGMENT = "[^" + 2 * _PATH_BACKSLASH + _PATH_SLASH + r"\s\"'<>|,;]+"
_POSIX_PATH_SEGMENT = "[^" + _PATH_SLASH + r"\s\"'<>|,;]+"
_WINDOWS_PATH_PATTERN = (
    r"(?<![A-Za-z0-9])(?:[A-Za-z]:" + _PATH_SEPARATOR_CLASS + ")"
    + "(?:" + _WINDOWS_PATH_SEGMENT + _PATH_SEPARATOR_CLASS + ")*"
    + _WINDOWS_PATH_SEGMENT
)
_PROFILE_PATH_PATTERN = (
    r"(?i)(?<![A-Za-z0-9])(?:[A-Z]:" + _PATH_SEPARATOR_CLASS
    + r"(?:Users|Documents and Settings)" + _PATH_SEPARATOR_CLASS + r"(?!<)"
    + _WINDOWS_PATH_SEGMENT + "(?:" + _PATH_SEPARATOR_CLASS + _WINDOWS_PATH_SEGMENT + ")*"
    + "|" + _PATH_SLASH + r"(?:Users|home)" + _PATH_SLASH + _POSIX_PATH_SEGMENT
    + "(?:" + _PATH_SLASH + _POSIX_PATH_SEGMENT + ")*)"
)
_WINDOWS_PATH_RE = re.compile(_WINDOWS_PATH_PATTERN)
_PROFILE_PATH_RE = re.compile(_PROFILE_PATH_PATTERN)
_POSIX_LOCAL_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9:])/(?:Users|home|mnt|tmp|private|Volumes)/[^\s\"'<>|,;]+"
)
_UNC_PATH_RE = re.compile(r"(?<!\\)\\\\[^\\\s]+\\[^\\\s]+(?:\\[^\\\s]+)*")
_FILE_URI_RE = re.compile(r"(?i)\bfile://(?:localhost)?/?[^\s\"'<>|,;]+")
_COD_ARCHIVE_URI_PREFIX = "file://" + "/" + "home" + "/" + "coder/svn-repositories/_RELOADED_COD/cod-reloaded/cif/"
_COD_ARCHIVE_URI_RE = re.compile(
    r"(?i)^" + re.escape(_COD_ARCHIVE_URI_PREFIX) + r"(?:[0-9]+/)+[0-9]+\.cif$"
)
_SECRET_PATTERNS = {
    "github_token": re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})"),
    "openai_key_shape": re.compile(rb"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{35,}"),
    "aws_key_shape": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "private_key_header": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "slack_token_shape": re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{20,}"),
}

_PRIVATE_TEXT_KEYS = {
    "rawsource", "rawsourcetext", "fulltext", "fulldocumenttext",
    "documentbody", "publishertext", "sourceexcerpt", "verbatimexcerpt",
    "verbatimtext", "ocrtext", "pdftext", "pagetext", "extractedpagetext",
    "sourcetextwindow", "sourcewindowtext", "privatefulltext", "firstpagepreviewprivate",
}
_LOCAL_PATH_KEYS = {
    "sourcepath", "localpath", "filepath", "absolutepath", "inputpath",
    "archivepath", "pdfpath", "documentpath", "originalpath", "cachepath",
}
_TEXT_MEMBER_KEYS = {"text", "snippet", "excerpt", "body", "content", "raw_text", "rawtext"}
_RAW_TEXT_ORIGINS = {
    "publisher_text", "source_excerpt", "verbatim_source", "machine_extracted",
    "pdf_extraction", "ocr", "page_text", "raw_source", "full_text",
    "copied_from_source", "source_window",
}
_NON_SOURCE_DERIVED_CLASSES = {
    "authored_molecule", "authored_apparatus", "generated_artwork", "authored_diagram",
    "authored_icon", "vendor_asset",
}


class BoundaryError(ValueError):
    """Safe boundary error. Messages must never include source content."""


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def normalize_repo(repo: str) -> str:
    if repo not in REPOSITORIES:
        raise BoundaryError("repository_not_allowlisted")
    return repo


def normalize_path(path: str) -> str:
    if not isinstance(path, str) or not path or "\x00" in path:
        raise BoundaryError("invalid_relative_path")
    if "\\" in path:
        raise BoundaryError("path_must_use_posix_separators")
    p = PurePosixPath(path)
    if p.is_absolute() or any(part in {"", ".", ".."} for part in path.split("/")):
        raise BoundaryError("path_traversal_or_absolute_path")
    if re.match(r"^[A-Za-z]:", path):
        raise BoundaryError("path_traversal_or_absolute_path")
    return path


def _parts(path: str) -> list[str]:
    return [x.casefold() for x in PurePosixPath(path).parts]


def _path_block_reason(path: str) -> str | None:
    low = path.casefold()
    parts = _parts(path)
    if any(p in _DENIED_COMPONENTS or p.startswith("private-") for p in parts):
        return "private_or_cache_path"
    if any(low.startswith(prefix) for prefix in _DENIED_PATH_PREFIXES):
        return "private_or_cache_path"
    if _DENIED_SCREENING_RE.search(low):
        return "raw_screening_workspace"
    name = PurePosixPath(low).name
    suffix = PurePosixPath(name).suffix
    if name.endswith((".tmp", ".temp", ".swp", ".bak")):
        return "temporary_file"
    if suffix in SOURCE_DOCUMENT_SUFFIXES:
        return "original_source_document_or_archive"
    if suffix in IMAGE_SUFFIXES and _PAGE_RENDER_NAME_RE.match(name):
        return "source_page_render"
    if "pages" in parts and suffix in IMAGE_SUFFIXES:
        if _PAGE_RENDER_NAME_RE.match(name) or "source-render" in parts or "audit-pages" in parts:
            return "source_page_render"
    if name in {"source-cues.jsonl", "documents.jsonl"} and "research-assets" in parts:
        if any(x in parts for x in {"incoming-paper-monitor", "corpus-screening", "cache"}):
            return "raw_screening_workspace"
    return None


def _enabled_rule_matches(repo: str, path: str, config: dict[str, Any]) -> list[dict[str, Any]]:
    rules = config.get("path_rules", [])
    if not isinstance(rules, list):
        return []
    matches = []
    for rule in rules:
        if not isinstance(rule, dict) or not rule.get("enabled", True):
            continue
        rule_repo = rule.get("repo", "*")
        glob = rule.get("path_glob")
        if rule_repo not in {repo, "*"} or not isinstance(glob, str):
            continue
        if fnmatch.fnmatchcase(path, glob):
            matches.append(rule)
    return matches


def _approved_rule(repo: str, path: str, config: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    matches = _enabled_rule_matches(repo, path, config)
    if not matches:
        return None, "path_not_allowlisted"
    denies = [r for r in matches if r.get("decision") == "omit"]
    if denies:
        reason = str(denies[0].get("reason_code") or "reviewed_path_exclusion")
        return None, reason
    allows = [r for r in matches if r.get("decision") == "allow"]
    if not allows:
        return None, "path_not_allowlisted"
    signatures = {(r.get("content_class"), r.get("rule_id")) for r in allows}
    classes = {r.get("content_class") for r in allows}
    if len(classes) != 1:
        return None, "conflicting_path_rules"
    # Overlapping rules with the same class are safe only if every rule is reviewed.
    for r in allows:
        if r.get("review_status") != "approved" or not str(r.get("reviewer", "")).strip():
            return None, "path_rule_review_incomplete"
        if not str(r.get("rule_id", "")).strip():
            return None, "path_rule_missing_id"
    # Stable first rule; all same-class rules are retained under the reviewed policy.
    return allows[0], None


def _is_image(path: str) -> bool:
    return PurePosixPath(path).suffix.casefold() in IMAGE_SUFFIXES


def _registry_assets(registry: dict[str, Any]) -> list[dict[str, Any]]:
    if registry.get("schema_version") != RIGHTS_SCHEMA or not isinstance(registry.get("assets"), list):
        raise BoundaryError("asset_rights_registry_schema_invalid")
    return registry["assets"]


def _build_asset_indexes(registry: dict[str, Any]) -> tuple[dict[tuple[str, str], list[dict[str, Any]]], dict[tuple[str, str, str], list[dict[str, Any]]]]:
    by_delivery: dict[tuple[str, str], list[dict[str, Any]]] = {}
    by_hash_delivery: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for asset in _registry_assets(registry):
        if not isinstance(asset, dict) or not isinstance(asset.get("asset_hash"), str):
            continue
        digest = asset["asset_hash"].lower()
        for delivery in asset.get("delivery_paths", []):
            if not isinstance(delivery, dict):
                continue
            key = (delivery.get("repo"), delivery.get("path"))
            if key[0] not in REPOSITORIES or not isinstance(key[1], str):
                continue
            by_delivery.setdefault(key, []).append(asset)
            by_hash_delivery.setdefault((digest, key[0], key[1]), []).append(asset)
    return by_delivery, by_hash_delivery


def _indexes(config: dict[str, Any]) -> tuple[dict[tuple[str, str], list[dict[str, Any]]], dict[tuple[str, str, str], list[dict[str, Any]]]]:
    cached = config.get("asset_registry_indexes")
    if isinstance(cached, tuple) and len(cached) == 2:
        return cached
    registry = config.get("asset_rights_registry")
    if not isinstance(registry, dict):
        return {}, {}
    cached = _build_asset_indexes(registry)
    config["asset_registry_indexes"] = cached
    return cached


def user_directed_display_error(asset: dict[str, Any], repo: str, path: str) -> str | None:
    """Validate an exact restoration instruction, never copyright permission.

    The recorded prior delivery is an evidence pin supplied by the release
    reviewer; this offline guard does not independently query Git history.
    Unknown graphics and private/full-document paths remain ineligible.
    """
    try:
        normalize_repo(repo)
        normalize_path(path)
    except BoundaryError:
        return "user_directed_display_path_invalid"
    if _path_block_reason(path) or not _is_image(path):
        return "user_directed_display_path_ineligible"
    if asset.get("classification") not in {"source_figure", "source_page_crop"}:
        return "user_directed_display_classification_ineligible"
    digest = asset.get("asset_hash")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        return "user_directed_display_asset_hash_invalid"
    rights = asset.get("rights", {})
    if not isinstance(rights, dict) or rights.get("status") != "user_directed_display":
        return "user_directed_display_status_invalid"
    if rights.get("copyright_permission_verified") is not False:
        return "user_directed_display_permission_qualification_missing"
    if not isinstance(rights.get("attribution"), str) or not rights["attribution"].strip():
        return "user_directed_display_attribution_missing"
    bindings = asset.get("source_bindings")
    source_identified = False
    for binding in bindings if isinstance(bindings, list) else []:
        if not isinstance(binding, dict):
            continue
        doi, url = binding.get("doi"), binding.get("url")
        if isinstance(doi, str) and re.fullmatch(r"10\.\d{4,9}/\S+", doi):
            source_identified = True
        if isinstance(url, str) and not re.search(r"\s", url):
            try:
                parsed = urlsplit(url)
                if parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password:
                    source_identified = True
            except ValueError:
                pass
    if not source_identified:
        return "user_directed_display_source_binding_missing"
    direction = rights.get("user_direction")
    if not isinstance(direction, dict):
        return "user_directed_display_instruction_missing"
    if not isinstance(direction.get("record_id"), str) or not direction["record_id"].strip():
        return "user_directed_display_instruction_missing"
    if direction.get("scope") != "restore_previously_delivered_source_figures":
        return "user_directed_display_scope_invalid"
    if direction.get("asset_hash") != digest:
        return "user_directed_display_instruction_hash_mismatch"
    try:
        timestamp = datetime.fromisoformat(direction.get("recorded_at", "").replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            return "user_directed_display_instruction_time_invalid"
    except (TypeError, ValueError, AttributeError):
        return "user_directed_display_instruction_time_invalid"
    deliveries = asset.get("delivery_paths", [])
    if not isinstance(deliveries, list) or len([
        item for item in deliveries if isinstance(item, dict) and item.get("repo") == repo and item.get("path") == path
    ]) != 1:
        return "user_directed_display_delivery_missing_or_ambiguous"
    site_path = path
    if repo == "mattersyn":
        prefix = "recipe-atlas/static/"
        if not path.startswith(prefix):
            return "user_directed_display_source_path_ineligible"
        site_path = path[len(prefix):]
    prior = direction.get("previous_delivery")
    if not isinstance(prior, list) or not prior:
        return "user_directed_display_previous_delivery_missing"
    matches = []
    for delivery in prior:
        if not isinstance(delivery, dict):
            return "user_directed_display_previous_delivery_invalid"
        try:
            prior_path = normalize_path(delivery.get("path"))
        except BoundaryError:
            return "user_directed_display_previous_delivery_invalid"
        if (delivery.get("repo") != "mattersyn-site" or _path_block_reason(prior_path)
                or not _is_image(prior_path) or delivery.get("asset_hash") != digest
                or not isinstance(delivery.get("commit"), str)
                or not re.fullmatch(r"[0-9a-f]{40}", delivery["commit"])):
            return "user_directed_display_previous_delivery_invalid"
        if prior_path == site_path:
            matches.append(delivery)
    if len(matches) != 1:
        return "user_directed_display_previous_path_missing_or_ambiguous"
    return None


def _rights_result(path: str, raw: bytes, repo: str, registry: dict[str, Any], index=None) -> str | None:
    digest = sha256(raw)
    if index is None:
        index = _build_asset_indexes(registry)[1]
    matches = index.get((digest, repo, path), [])
    if len(matches) != 1:
        return "asset_rights_record_missing_or_ambiguous"
    asset = matches[0]
    classification = asset.get("classification")
    rights = asset.get("rights")
    if not isinstance(rights, dict):
        return "asset_rights_record_incomplete"
    status = rights.get("status")
    if status == "withheld":
        return "asset_rights_withheld"
    if status == "cleared":
        if not rights.get("license_id") or not rights.get("license_evidence") or not rights.get("attribution"):
            return "asset_rights_evidence_incomplete"
        if classification in {"unknown", None}:
            return "asset_classification_unknown"
    elif status == "user_directed_display":
        reason = user_directed_display_error(asset, repo, path)
        if reason:
            return reason
    elif status == "not_source_derived":
        if classification not in _NON_SOURCE_DERIVED_CLASSES:
            return "asset_not_source_derived_status_not_qualified"
        if not rights.get("attribution"):
            return "asset_authorship_attribution_missing"
        if classification == "vendor_asset" and (not rights.get("license_id") or not rights.get("license_evidence")):
            return "vendor_asset_license_evidence_incomplete"
    else:
        return "asset_rights_status_not_approved"
    for delivery in asset.get("delivery_paths", []):
        if delivery.get("repo") == repo and delivery.get("path") == path:
            if delivery.get("bytes") is not None and delivery["bytes"] != len(raw):
                return "asset_delivery_size_mismatch"
            blob_oid = delivery.get("git_blob")
            if blob_oid:
                git_blob_sha1 = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
                if blob_oid.lower() != git_blob_sha1:
                    return "asset_git_blob_mismatch"
    return None


def history_exclude_path(kind: str, path: str, config: dict[str, Any]) -> str | None:
    """Cheap path-only omission check suitable for every historical tree.

    `None` means the caller may read the blob and call `history_project`; it does
    not mean the blob is approved. This avoids decompressing known private caches.
    """
    try:
        repo = normalize_repo(kind)
        rel = normalize_path(path)
    except BoundaryError as exc:
        return str(exc)
    denied = _path_block_reason(rel)
    if denied:
        return denied
    rule, reason = _approved_rule(repo, rel, config)
    if reason:
        return reason
    if _is_image(rel):
        registry = config.get("asset_rights_registry")
        if not isinstance(registry, dict):
            return "asset_rights_registry_missing"
        # Path presence is only a prefilter; history_project validates the hash.
        records = _indexes(config)[0].get((repo, rel), [])
        if not records:
            return "asset_rights_record_missing"
        if all(not isinstance(a.get("rights"), dict) or a["rights"].get("status") == "withheld" for a in records):
            return "asset_rights_withheld"
    return None


def _normalize_origin(value: Any) -> str:
    if isinstance(value, str):
        return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")
    if isinstance(value, dict):
        for key in ("origin", "type", "source_type", "method", "classification"):
            if key in value:
                return _normalize_origin(value[key])
    return ""


_AUTHORED_TEXT_ORIGINS = {
    "authored", "human_authored", "reviewer_authored", "paraphrased_summary",
    "curated_summary", "model_generated_summary",
}


def _object_source_text_state(obj: dict[str, Any]) -> bool | None:
    for key in ("text_origin", "content_origin", "text_provenance", "content_provenance", "provenance"):
        if key in obj:
            origin = _normalize_origin(obj[key])
            if origin in _RAW_TEXT_ORIGINS:
                return True
            if origin in _AUTHORED_TEXT_ORIGINS:
                return False
    # Some legacy snippet records carry a source-file hash and page locator but
    # no explicit origin field. Treat only the text in that evidence object as
    # source-derived; keep the page/hash locator and surrounding authored facts.
    normalized = {re.sub(r"[^a-z0-9]+", "", str(key).casefold()) for key in obj}
    has_text = bool(normalized & {"text", "snippet", "excerpt", "body", "content"})
    has_source_hash = bool(normalized & {"sourcehash", "sourcefilehash", "sourcepdfhash", "sourcesha256", "sourcefilehashsha256"})
    has_page_locator = bool(normalized & {"page", "pdfpage", "pagenumber", "printedpage", "printedpagenumber"})
    if has_text and has_source_hash and has_page_locator:
        return True
    return None


def _redact_path_string(value: str, *, strict: bool) -> tuple[str, int]:
    patterns = [_FILE_URI_RE, _UNC_PATH_RE, _WINDOWS_PATH_RE if strict else _PROFILE_PATH_RE]
    if strict:
        patterns.append(_POSIX_LOCAL_PATH_RE)
    count = 0
    result = value
    for pattern in patterns:
        result, n = pattern.subn("[local path redacted]", result)
        count += n
    return result, count


def _looks_local_path(value: str) -> bool:
    _clean, count = _redact_path_string(value, strict=True)
    return count > 0


_MEASUREMENT_CUE_KEYS = {
    "cellid", "numericvalue", "normalizedvalue", "value", "unit", "units", "unitstatus",
    "quantity", "quantityvalue", "parameter", "measurementname", "evidence", "transcriptionstatus",
}
_MEASUREMENT_LEXEME_RE = re.compile(
    r"^\s*[~≈<>≤≥]?\s*[+-]?\d+(?:[.,]\d+)?(?:\s*(?:[-–—]\s*\d+(?:[.,]\d+)?)?)"
    r"(?:\s*(?:±\s*\d+(?:[.,]\d+)?))?\s*(?:[%°µμA-Za-z/·^0-9-]+)?"
    r"(?:\s*(?:for|at|under)\s*[~≈<>≤≥]?\s*[+-]?\d+(?:[.,]\d+)?"
    r"\s*(?:[%°µμA-Za-z/·^0-9-]+)?)?\s*$",
    re.IGNORECASE,
)
_MAX_STRUCTURED_CELL_LEXEME_CHARS = 64
_MAX_EMBEDDED_JSON_DEPTH = 4
_MAX_EMBEDDED_JSON_BYTES = 8 * 1024 * 1024


class _UnsafeEmbeddedJson(ValueError):
    """A JSON-looking embedded payload could not be checked within bounds."""


def _is_structured_measurement_object(obj: dict[str, Any]) -> bool:
    normalized = {re.sub(r"[^a-z0-9]+", "", str(key).casefold()) for key in obj}
    cues = normalized & _MEASUREMENT_CUE_KEYS
    return "rawtext" in normalized and bool(cues) and (len(cues) >= 2 or bool(cues & {"numericvalue", "normalizedvalue", "cellid", "unitstatus", "evidence"}))


def _is_measurement_lexeme(value: Any) -> bool:
    return isinstance(value, str) and bool(_MEASUREMENT_LEXEME_RE.fullmatch(value))


_SCHEMA_PROPERTY_KEYS = {
    "type", "description", "title", "format", "minLength", "maxLength",
    "pattern", "readOnly", "writeOnly", "deprecated",
}


def _is_record_json_schema(path: str, value: Any) -> bool:
    """Recognize declarative JSON Schema files without treating data as schema."""
    if not PurePosixPath(path).name.casefold().endswith(".schema.json") or not isinstance(value, dict):
        return False
    return (
        value.get("type") == "object"
        and isinstance(value.get("properties"), dict)
        and isinstance(value.get("required"), list)
    )


def _is_schema_property_definition(value: Any) -> bool:
    if not isinstance(value, dict) or not value or not set(value).issubset(_SCHEMA_PROPERTY_KEYS):
        return False
    schema_type = value.get("type")
    return isinstance(schema_type, str) or (
        isinstance(schema_type, list) and all(isinstance(item, str) for item in schema_type)
    )


def _is_bounded_structured_cell_lexeme(value: Any) -> bool:
    """Keep only the short cell spelling used by the current reviewed schema.

    The current MatterSyn structured corpus has a maximum raw cell spelling of
    64 characters. This bound prevents a measurement-shaped wrapper from being
    used to smuggle a paragraph into the public projection.
    """
    return isinstance(value, str) and len(value) <= _MAX_STRUCTURED_CELL_LEXEME_CHARS and "\n" not in value and "\r" not in value


def _walk_json(value: Any, stats: dict[str, int], *, strict_paths: bool,
               inherited_source_text_origin: bool = False, inherited_measurement_context: bool = False,
               declarative_schema: bool = False, schema_property_map: bool = False,
               embedded_json_depth: int = 0) -> Any:
    if isinstance(value, dict):
        local_state = _object_source_text_state(value)
        source_text_origin = inherited_source_text_origin if local_state is None else local_state
        structured_measurement = _is_structured_measurement_object(value)
        measurement_context = inherited_measurement_context or structured_measurement
        out = {}
        for key, item in value.items():
            if isinstance(key, str) and _looks_local_path(key):
                stats["local_path_key_detected"] += 1
                continue
            normalized_key = re.sub(r"[^a-z0-9]+", "", str(key).casefold())
            if normalized_key in _PRIVATE_TEXT_KEYS:
                stats["source_text_fields_removed"] += 1
                continue
            if normalized_key in _LOCAL_PATH_KEYS:
                stats["local_path_fields_removed"] += 1
                continue
            if source_text_origin and normalized_key in {re.sub(r"[^a-z0-9]+", "", x) for x in _TEXT_MEMBER_KEYS}:
                stats["source_text_fields_removed"] += 1
                continue
            schema_field_definition = (
                declarative_schema and schema_property_map and normalized_key == "rawtext"
                and _is_schema_property_definition(item)
            )
            if normalized_key == "rawtext" and item not in ("", None) and not (
                schema_field_definition
                or
                (structured_measurement and _is_bounded_structured_cell_lexeme(item))
                or (inherited_measurement_context and _is_measurement_lexeme(item))
            ):
                stats["source_text_fields_removed"] += 1
                continue
            out[key] = _walk_json(
                item, stats, strict_paths=strict_paths,
                inherited_source_text_origin=source_text_origin,
                inherited_measurement_context=measurement_context or normalized_key in {"measurement", "measurements", "measurementvalue", "quantitativemeasurement", "quantitativemeasurements"},
                declarative_schema=declarative_schema,
                schema_property_map=declarative_schema and normalized_key in {"properties", "patternproperties"},
                embedded_json_depth=embedded_json_depth,
            )
        return out
    if isinstance(value, list):
        return [
            _walk_json(item, stats, strict_paths=strict_paths,
                       inherited_source_text_origin=inherited_source_text_origin,
                       inherited_measurement_context=inherited_measurement_context,
                       declarative_schema=declarative_schema,
                       schema_property_map=schema_property_map,
                       embedded_json_depth=embedded_json_depth)
        for item in value
        ]
    if isinstance(value, str):
        candidate = value.strip()
        looks_like_embedded_json = (
            len(candidate) >= 2
            and ((candidate.startswith("{") and candidate.endswith("}"))
                 or (candidate.startswith("[") and candidate.endswith("]")))
        )
        if looks_like_embedded_json:
            if embedded_json_depth >= _MAX_EMBEDDED_JSON_DEPTH or len(value.encode("utf-8")) > _MAX_EMBEDDED_JSON_BYTES:
                raise _UnsafeEmbeddedJson("embedded_json_limit_exceeded")
            try:
                embedded = json.loads(candidate, object_pairs_hook=_unique_json_object)
            except _DuplicateJsonKey as exc:
                raise _UnsafeEmbeddedJson("duplicate_embedded_json_key") from exc
            except (json.JSONDecodeError, UnicodeError):
                embedded = None
            if isinstance(embedded, (dict, list)):
                before = dict(stats)
                cleaned = _walk_json(
                    embedded, stats, strict_paths=strict_paths,
                    inherited_source_text_origin=inherited_source_text_origin,
                    inherited_measurement_context=inherited_measurement_context,
                    declarative_schema=False, schema_property_map=False,
                    embedded_json_depth=embedded_json_depth + 1,
                )
                if cleaned == embedded and stats == before:
                    return value
                # Keep embedded valid JSON machine-readable after applying the
                # same source-text and path rules as top-level JSON objects.
                return json.dumps(cleaned, ensure_ascii=False, separators=(",", ":"))
        new, count = _redact_path_string(value, strict=strict_paths)
        stats["local_path_strings_redacted"] += count
        return new
    return value


class _DuplicateJsonKey(ValueError):
    pass


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out = {}
    for key, value in pairs:
        if key in out:
            raise _DuplicateJsonKey("duplicate_json_key")
        out[key] = value
    return out


def _sanitize_content(path: str, raw: bytes, config: dict[str, Any] | None = None, repo: str | None = None) -> tuple[bytes | None, str, dict[str, int]]:
    ext = PurePosixPath(path).suffix.casefold()
    if raw.lstrip().startswith(b"%PDF-"):
        return None, "original_source_document_or_archive", {}
    for secret_name, pattern in _SECRET_PATTERNS.items():
        if pattern.search(raw):
            return None, "credential_pattern_" + secret_name, {}
    stats = {
        "source_text_fields_removed": 0,
        "local_path_fields_removed": 0,
        "local_path_key_detected": 0,
        "local_path_strings_redacted": 0,
    }
    if ext in {".json", ".jsonl", ".ndjson"}:
        try:
            text = raw.decode("utf-8-sig")
            if ext in {".jsonl", ".ndjson"}:
                rows = [json.loads(line, object_pairs_hook=_unique_json_object) for line in text.splitlines() if line.strip()]
                cleaned = [_walk_json(row, stats, strict_paths=True) for row in rows]
                output = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in cleaned)
            else:
                obj = json.loads(text, object_pairs_hook=_unique_json_object)
                cleaned = _walk_json(obj, stats, strict_paths=True,
                                     declarative_schema=_is_record_json_schema(path, obj))
                output = json.dumps(cleaned, ensure_ascii=False, indent=2) + "\n"
            encoded = output.encode("utf-8")
            if stats["local_path_key_detected"]:
                return None, "local_path_in_json_key", stats
            return (raw if stats["source_text_fields_removed"] == 0 and stats["local_path_fields_removed"] == 0 and stats["local_path_strings_redacted"] == 0 else encoded), "projected_json" if any(stats.values()) else "unchanged", stats
        except (UnicodeError, ValueError, RecursionError):
            return None, "invalid_structured_payload", stats
    name = PurePosixPath(path).name.casefold()
    if name == ".nojekyll" and raw == b"":
        return raw, "unchanged", stats
    if ext in TEXT_SUFFIXES or name in TEXT_FILENAMES:
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeError:
            return None, "invalid_text_encoding", stats
        if ext in {".cif", ".sdf", ".xyz"} and any(ord(char) < 32 and char not in "\t\r\n" for char in text):
            return None, "invalid_structure_text_control_bytes", stats
        if ext in {".cif", ".sdf", ".xyz"}:
            _unchanged, path_count = _redact_path_string(text, strict=True)
            if path_count:
                if config is not None and repo is not None and _cod_structure_annotation_is_approved(path, raw, config, repo):
                    return raw, "approved_cod_archive_annotation_preserved", stats
                return None, "local_path_in_structure_data", stats
            return raw, "unchanged", stats
        # General local absolute paths are scrubbed from prose and data. Source
        # code receives the narrower profile-path scrub to preserve examples of
        # ordinary drive/path syntax while removing user-specific locations.
        clean, count = _redact_path_string(text, strict=ext not in CODE_SUFFIXES)
        stats["local_path_strings_redacted"] += count
        return (raw if count == 0 else clean.encode("utf-8")), "sanitized_local_paths" if count else "unchanged", stats
    # Opaque binaries have no safe text/provenance interpretation unless they
    # are images with an explicit rights record. Fonts/vendor binaries need an
    # explicit extension and rights rule in a later policy revision.
    if not _is_image(path):
        return None, "unclassified_binary_content", stats
    return raw, "unchanged", stats


def history_project(kind: str, path: str, raw: bytes, config: dict[str, Any]) -> dict[str, Any]:
    """Project one historical blob under reviewed rules, without Git I/O.

    Return the agreed history-engine interface. `allow` content is either the
    exact original bytes or a deterministic sanitized representation. A path
    omission and a content omission carry reason codes only, never prose.
    """
    try:
        repo = normalize_repo(kind)
        rel = normalize_path(path)
    except BoundaryError as exc:
        return {"action": "omit", "reason": str(exc), "content_class": None}
    reason = history_exclude_path(repo, rel, config)
    if reason:
        return {"action": "omit", "reason": reason, "content_class": None}
    rule, reason = _approved_rule(repo, rel, config)
    if reason or rule is None:
        return {"action": "omit", "reason": reason or "path_not_allowlisted", "content_class": None}
    content_class = str(rule.get("content_class"))
    if content_class not in set(config.get("allowed_content_classes", [])):
        return {"action": "omit", "reason": "content_class_not_approved", "content_class": None}
    if not isinstance(raw, bytes):
        return {"action": "omit", "reason": "blob_bytes_invalid", "content_class": None}
    if content_class in set(config.get("exact_blob_approval_classes", [])):
        approval_error = _history_blob_approval(repo, rel, raw, config, content_class)
        if approval_error:
            return {"action": "omit", "reason": approval_error, "content_class": None}
    if _is_image(rel):
        registry = config.get("asset_rights_registry")
        if not isinstance(registry, dict):
            return {"action": "omit", "reason": "asset_rights_registry_missing", "content_class": None}
        rights_error = _rights_result(rel, raw, repo, registry, _indexes(config)[1])
        if rights_error:
            return {"action": "omit", "reason": rights_error, "content_class": None}
    content, reason, _stats = _sanitize_content(rel, raw, config, repo)
    if content is None:
        return {"action": "omit", "reason": reason, "content_class": None}
    reason = "public_content_sanitized" if content != raw else "approved_class_and_asset_rights"
    return {"action": "allow", "reason": reason, "content": content, "content_class": content_class}


def load_json(path: str | Path, schema: str | None = None) -> dict[str, Any]:
    try:
        obj = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        raise BoundaryError("policy_or_manifest_unreadable") from None
    if not isinstance(obj, dict):
        raise BoundaryError("policy_or_manifest_schema_invalid")
    if schema and obj.get("schema_version") != schema:
        raise BoundaryError("policy_or_manifest_schema_invalid")
    return obj


def load_config(policy_path: str | Path, registry_path: str | Path) -> dict[str, Any]:
    policy = load_json(policy_path, POLICY_SCHEMA)
    registry = load_json(registry_path, RIGHTS_SCHEMA)
    if policy.get("approval_status") != "approved" or not str(policy.get("approved_by", "")).strip():
        raise BoundaryError("projection_policy_review_incomplete")
    if not isinstance(policy.get("path_rules"), list):
        raise BoundaryError("projection_policy_rules_missing")
    config = dict(policy)
    config["asset_rights_registry"] = registry
    config["policy_sha256"] = sha256(Path(policy_path).read_bytes())
    config["asset_rights_registry_sha256"] = sha256(Path(registry_path).read_bytes())
    if policy.get("asset_rights_registry_sha256") != config["asset_rights_registry_sha256"]:
        raise BoundaryError("asset_registry_hash_not_pinned_by_policy")
    if not isinstance(config.get("blob_approvals", []), list):
        raise BoundaryError("history_blob_approval_manifest_invalid")
    if not isinstance(config.get("exact_blob_approval_classes", []), list):
        raise BoundaryError("history_blob_approval_classes_invalid")
    if not isinstance(config.get("structure_path_exceptions", []), list):
        raise BoundaryError("structure_path_exception_manifest_invalid")
    _registry_assets(registry)
    config["asset_registry_indexes"] = _build_asset_indexes(registry)
    return config


def _read_allowlist(path: str | Path) -> dict[str, Any]:
    data = load_json(path, ALLOWLIST_SCHEMA)
    if not isinstance(data.get("files"), list):
        raise BoundaryError("release_allowlist_files_missing")
    return data


def _validate_release_bindings(allowlist: dict[str, Any], config: dict[str, Any], repo: str) -> None:
    if allowlist.get("repo") != repo:
        raise BoundaryError("release_repo_binding_mismatch")
    if allowlist.get("policy_sha256") != config.get("policy_sha256"):
        raise BoundaryError("release_policy_hash_mismatch")
    if allowlist.get("asset_rights_registry_sha256") != config.get("asset_rights_registry_sha256"):
        raise BoundaryError("release_asset_registry_hash_mismatch")
    if not isinstance(allowlist.get("release_id"), str) or not allowlist["release_id"].strip():
        raise BoundaryError("release_id_missing")
    if not isinstance(allowlist.get("source_commit"), str) or not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", allowlist["source_commit"]):
        raise BoundaryError("source_commit_missing_or_invalid")
    if not isinstance(allowlist.get("files"), list) or not allowlist["files"]:
        raise BoundaryError("release_allowlist_empty")
    if repo == "mattersyn-site" and not any(isinstance(item, dict) and item.get("path") == "index.html" for item in allowlist["files"]):
        raise BoundaryError("site_entrypoint_missing")


def _safe_file(root: Path, rel: str) -> Path:
    rel = normalize_path(rel)
    cursor = root
    for component in PurePosixPath(rel).parts:
        cursor = cursor / component
        if cursor.is_symlink():
            raise BoundaryError("symlink_not_allowed")
    try:
        resolved_root = root.resolve(strict=True)
        resolved = cursor.resolve(strict=True)
    except (OSError, RuntimeError):
        raise BoundaryError("release_file_missing") from None
    if resolved_root != resolved and resolved_root not in resolved.parents:
        raise BoundaryError("resolved_path_escapes_root")
    if not resolved.is_file():
        raise BoundaryError("release_file_missing")
    return resolved


def _resolved_future_path(value: str | Path) -> Path:
    """Resolve existing symlinked ancestors even when the final path is new."""
    try:
        return Path(value).absolute().resolve(strict=False)
    except (OSError, RuntimeError):
        raise BoundaryError("filesystem_path_unresolvable") from None


def _is_within(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def _allowlist_entry_map(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out = {}
    for entry in data["files"]:
        if not isinstance(entry, dict):
            raise BoundaryError("release_allowlist_entry_invalid")
        path = normalize_path(entry.get("path"))
        if path in out:
            raise BoundaryError("release_allowlist_duplicate_path")
        out[path] = entry
    return out


def _validate_review_fields(entry: dict[str, Any], *, repo: str, rule: dict[str, Any]) -> str | None:
    if entry.get("repo", repo) != repo:
        return "release_repo_binding_mismatch"
    if entry.get("decision") != "allow":
        return "release_entry_not_allowed"
    if entry.get("review_status") != "approved" or not str(entry.get("reviewer", "")).strip() or not entry.get("reviewed_at"):
        return "release_entry_review_incomplete"
    if entry.get("content_class") != rule.get("content_class"):
        return "release_content_class_mismatch"
    expected_class = str(entry.get("content_class", ""))
    if rule.get("requires_source_refs") and not entry.get("source_refs"):
        return "source_references_required"
    if expected_class == "structure_data" and not entry.get("source_refs"):
        return "structure_data_provenance_required"
    if expected_class not in {"authored_code", "authored_docs", "memory", "skill", "audited_facts", "citation_metadata", "audit_summary", "site_code", "site_data", "site_asset", "structure_data"}:
        return "content_class_not_approved"
    refs_error = _validate_source_refs(entry.get("source_refs", []))
    if refs_error:
        return refs_error
    return None


_SOURCE_REF_KEYS = {
    "citation_id", "doi", "url", "page", "figure", "table", "section", "locator",
    "license_id", "license_url", "database_id", "format",
}


def _validate_source_refs(value: Any) -> str | None:
    """Keep public provenance structured and prevent prose/local paths in receipts."""
    if not isinstance(value, list):
        return "source_references_schema_invalid"
    for ref in value:
        if not isinstance(ref, dict) or not ref:
            return "source_references_schema_invalid"
        if set(ref) - _SOURCE_REF_KEYS:
            return "source_reference_field_not_allowlisted"
        for key, item in ref.items():
            if key == "reference_only" and isinstance(item, bool):
                continue
            if not isinstance(item, (str, int)) or isinstance(item, bool):
                return "source_reference_value_invalid"
            value_text = str(item)
            if len(value_text) > 240:
                return "source_reference_value_too_long"
            if _FILE_URI_RE.search(value_text) or _UNC_PATH_RE.search(value_text) or _WINDOWS_PATH_RE.search(value_text) or _POSIX_LOCAL_PATH_RE.search(value_text):
                return "local_path_in_source_reference"
            if key in {"doi", "url"} and not value_text.strip():
                return "source_reference_value_invalid"
    return None


def _cod_structure_annotation_is_approved(path: str, raw: bytes, config: dict[str, Any], repo: str) -> bool:
    """Allow only the exact pre-reviewed COD exporter comment in bound CIF hashes."""
    exceptions = config.get("structure_path_exceptions", [])
    if not isinstance(exceptions, list):
        return False
    digest = sha256(raw)
    records = [
        item for item in exceptions
        if isinstance(item, dict)
        and item.get("repo") == repo
        and item.get("path") == path
        and str(item.get("sha256", "")).lower() == digest
        and item.get("bytes") == len(raw)
        and item.get("pattern_id") == "cod_archive_annotation_v1"
        and item.get("review_status") == "approved"
        and str(item.get("reviewer", "")).strip()
        and item.get("cod_id") is not None
    ]
    if len(records) != 1:
        return False
    record = records[0]
    cod_id = str(record.get("cod_id"))
    if not re.fullmatch(r"[0-9]+", cod_id):
        return False
    refs = record.get("source_refs")
    if _validate_source_refs(refs):
        return False
    expected_sources = {
        f"https://www.crystallography.net/cod/{cod_id}.html",
        f"https://www.crystallography.net/cod/{cod_id}.cif",
    }
    if not any(isinstance(ref, dict) and ref.get("url") in expected_sources for ref in refs):
        return False
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeError:
        return False
    file_uris = _FILE_URI_RE.findall(text)
    if len(file_uris) != 1 or not _COD_ARCHIVE_URI_RE.fullmatch(file_uris[0]):
        return False
    if PurePosixPath(file_uris[0]).name != f"{cod_id}.cif":
        return False
    posix_paths = _POSIX_LOCAL_PATH_RE.findall(text)
    expected_posix = file_uris[0].removeprefix("file://")
    if posix_paths != [expected_posix]:
        return False
    if _WINDOWS_PATH_RE.search(text) or _UNC_PATH_RE.search(text):
        return False
    if text.count("#$URL:") != 1:
        return False
    return True


def _history_blob_approval(repo: str, path: str, raw: bytes, config: dict[str, Any], content_class: str) -> str | None:
    """Require exact-hash reviewer approval for each retained historical blob."""
    digest = sha256(raw)
    approvals = config.get("blob_approvals", [])
    if not isinstance(approvals, list):
        return "history_blob_approval_manifest_invalid"
    records = [
        record for record in approvals
        if isinstance(record, dict)
        and record.get("repo") == repo
        and record.get("path") == path
        and str(record.get("sha256", "")).lower() == digest
    ]
    if len(records) != 1:
        return "historical_blob_not_exact_hash_approved"
    record = records[0]
    if record.get("decision") != "allow":
        return "historical_blob_not_approved"
    if record.get("content_class") != content_class:
        return "historical_blob_class_mismatch"
    if record.get("review_status") != "approved" or not str(record.get("reviewer", "")).strip() or not record.get("reviewed_at"):
        return "historical_blob_review_incomplete"
    return None


def validate_stage(root: str | Path, allowlist_path: str | Path, config: dict[str, Any], repo: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate a materialized public stage; no files are changed."""
    root = Path(root).resolve(strict=True)
    repo = normalize_repo(repo)
    allowlist = _read_allowlist(allowlist_path)
    _validate_release_bindings(allowlist, config, repo)
    expected = _allowlist_entry_map(allowlist)
    actual = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise BoundaryError("symlink_not_allowed")
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            if ".git" in PurePosixPath(rel).parts:
                raise BoundaryError("git_metadata_in_release_stage")
            actual[rel] = path
    missing = sorted(set(expected) - set(actual))
    unlisted = sorted(set(actual) - set(expected))
    failures: list[dict[str, str]] = []
    for rel in missing:
        failures.append({"path": rel, "reason_code": "allowlisted_file_missing"})
    for rel in unlisted:
        failures.append({"path": rel, "reason_code": "staged_file_not_allowlisted"})
    manifest_files = []
    for rel, entry in sorted(expected.items()):
        if rel not in actual:
            continue
        block = _path_block_reason(rel)
        if block:
            failures.append({"path": rel, "reason_code": block})
            continue
        rule, rule_error = _approved_rule(repo, rel, config)
        if rule_error or not rule:
            failures.append({"path": rel, "reason_code": rule_error or "path_not_allowlisted"})
            continue
        review_error = _validate_review_fields(entry, repo=repo, rule=rule)
        if review_error:
            failures.append({"path": rel, "reason_code": review_error})
            continue
        try:
            file_path = _safe_file(root, rel)
            raw = file_path.read_bytes()
        except BoundaryError as exc:
            failures.append({"path": rel, "reason_code": str(exc)})
            continue
        digest = sha256(raw)
        if entry.get("sha256", "").lower() != digest:
            failures.append({"path": rel, "reason_code": "staged_sha256_mismatch"})
            continue
        if entry.get("bytes") != len(raw):
            failures.append({"path": rel, "reason_code": "staged_size_mismatch"})
            continue
        if _is_image(rel):
            rights_error = _rights_result(rel, raw, repo, config.get("asset_rights_registry", {}), _indexes(config)[1])
            if rights_error:
                failures.append({"path": rel, "reason_code": rights_error})
                continue
        sanitized, projection_reason, _stats = _sanitize_content(rel, raw, config, repo)
        if sanitized is None:
            failures.append({"path": rel, "reason_code": projection_reason})
            continue
        if sanitized != raw:
            failures.append({"path": rel, "reason_code": "staged_content_requires_sanitization"})
            continue
        manifest_files.append({
            "path": rel,
            "sha256": digest,
            "bytes": len(raw),
            "content_class": entry["content_class"],
            "source_refs": entry.get("source_refs", []),
        })
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "repo": repo,
        "release_id": allowlist.get("release_id"),
        "source_commit": allowlist.get("source_commit"),
        "policy_sha256": config.get("policy_sha256"),
        "asset_rights_registry_sha256": config.get("asset_rights_registry_sha256"),
        "files": manifest_files,
        "file_count": len(manifest_files),
        "snapshot_sha256": sha256(json.dumps(manifest_files, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()),
    }
    report = {
        "schema_version": REPORT_SCHEMA,
        "repo": repo,
        "status": "passed" if not failures else "failed",
        "checked_files": len(expected),
        "passed_files": len(manifest_files),
        "failure_count": len(failures),
        "failures": failures,
        "notice": "Diagnostics contain paths and reason codes only; private source text is never included.",
    }
    return manifest, report


def export_public_release(source_root: str | Path, destination: str | Path, allowlist_path: str | Path,
                          config: dict[str, Any], repo: str, manifest_path: str | Path,
                          report_path: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Copy only allowlisted files to a new, disjoint directory and scrub paths.

    The destination must not exist. Output manifests/reports must be outside the
    destination so the public tree has no self-referential hash or diagnostic.
    """
    source = Path(source_root).resolve(strict=True)
    destination = _resolved_future_path(destination)
    manifest_path = _resolved_future_path(manifest_path)
    report_path = _resolved_future_path(report_path)
    repo = normalize_repo(repo)
    if source == destination or source in destination.parents or destination in source.parents:
        raise BoundaryError("source_and_destination_must_be_disjoint")
    if destination.exists():
        raise BoundaryError("destination_must_not_exist")
    if _is_within(manifest_path, destination):
        raise BoundaryError("manifest_must_be_outside_destination")
    if _is_within(report_path, destination):
        raise BoundaryError("report_must_be_outside_destination")
    if _is_within(manifest_path, source) or _is_within(report_path, source):
        raise BoundaryError("receipts_must_be_outside_source")
    if manifest_path == report_path:
        raise BoundaryError("receipt_paths_must_be_distinct")
    if manifest_path.exists() or report_path.exists():
        raise BoundaryError("receipts_must_not_overwrite_existing_files")
    allowlist = _read_allowlist(allowlist_path)
    _validate_release_bindings(allowlist, config, repo)
    entries = _allowlist_entry_map(allowlist)
    prepared: list[tuple[str, dict[str, Any], bytes, bytes, str]] = []
    for rel, entry in sorted(entries.items()):
        block = _path_block_reason(rel)
        if block:
            raise BoundaryError(block)
        rule, error = _approved_rule(repo, rel, config)
        if error or not rule:
            raise BoundaryError(error or "path_not_allowlisted")
        review_error = _validate_review_fields(entry, repo=repo, rule=rule)
        if review_error:
            raise BoundaryError(review_error)
        file_path = _safe_file(source, rel)
        raw = file_path.read_bytes()
        if entry.get("sha256", "").lower() != sha256(raw) or entry.get("bytes") != len(raw):
            raise BoundaryError("source_file_hash_or_size_mismatch")
        if _is_image(rel):
            rights_error = _rights_result(rel, raw, repo, config.get("asset_rights_registry", {}), _indexes(config)[1])
            if rights_error:
                raise BoundaryError(rights_error)
        projected, reason, _stats = _sanitize_content(rel, raw, config, repo)
        if projected is None:
            raise BoundaryError(reason)
        prepared.append((rel, entry, raw, projected, reason))
    destination.mkdir(parents=True, exist_ok=False)
    release_files = []
    failures = []
    for rel, entry, raw, projected, reason in prepared:
        target = destination.joinpath(*PurePosixPath(rel).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(projected)
        release_files.append({
            "path": rel,
            "source_sha256": sha256(raw),
            "sha256": sha256(projected),
            "bytes": len(projected),
            "content_class": entry["content_class"],
            "source_refs": entry.get("source_refs", []),
            "projection_reason": reason,
        })
    release_manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "repo": repo,
        "release_id": allowlist.get("release_id"),
        "source_commit": allowlist.get("source_commit"),
        "policy_sha256": config.get("policy_sha256"),
        "asset_rights_registry_sha256": config.get("asset_rights_registry_sha256"),
        "files": release_files,
        "file_count": len(release_files),
        "snapshot_sha256": sha256(json.dumps(release_files, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()),
    }
    # Re-validate the projected directory against its just-produced exact manifest.
    stage_allowlist = {
        "schema_version": ALLOWLIST_SCHEMA,
        "repo": repo,
        "release_id": allowlist.get("release_id"),
        "source_commit": allowlist.get("source_commit"),
        "policy_sha256": config.get("policy_sha256"),
        "asset_rights_registry_sha256": config.get("asset_rights_registry_sha256"),
        "files": [
            {"path": f["path"], "sha256": f["sha256"], "bytes": f["bytes"],
             "content_class": f["content_class"], "decision": "allow", "review_status": "approved",
             "reviewer": "projection-policy", "reviewed_at": "2026-09-24T00:00:00Z", "source_refs": f["source_refs"]}
            for f in release_files
        ],
    }
    # Reuse the in-memory manifest so no private inputs are echoed in errors.
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", prefix="mattersyn-allowlist-", suffix=".json", delete=False) as temp_file:
        allow_tmp = Path(temp_file.name)
        temp_file.write(json.dumps(stage_allowlist))
    try:
        verified_manifest, report = validate_stage(destination, allow_tmp, config, repo)
    finally:
        try:
            allow_tmp.unlink()
        except OSError:
            pass
    if report["status"] != "passed":
        failures = report["failures"]
        release_manifest["status"] = "failed"
    else:
        release_manifest["status"] = "passed"
        # Validate_stage binds the exact deployed output snapshot.
        release_manifest["snapshot_sha256"] = verified_manifest["snapshot_sha256"]
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("x", encoding="utf-8") as manifest_file:
        manifest_file.write(json.dumps(release_manifest, ensure_ascii=False, indent=2) + "\n")
    export_report = {
        "schema_version": REPORT_SCHEMA,
        "repo": repo,
        "status": report["status"],
        "checked_files": len(entries),
        "passed_files": report["passed_files"],
        "failure_count": len(failures),
        "failures": failures,
        "transformation_count": sum(f["projection_reason"] != "unchanged" for f in release_files),
        "omitted_source_files": "Not copied; only explicit allowlist paths were read and emitted.",
    }
    with report_path.open("x", encoding="utf-8") as report_file:
        report_file.write(json.dumps(export_report, ensure_ascii=False, indent=2) + "\n")
    return release_manifest, export_report


def validate_allowlist_entry(path: str, raw: bytes, entry: dict[str, Any], config: dict[str, Any], repo: str) -> tuple[str | None, str | None]:
    """Shared precise-input check used by standalone gate and export code."""
    try:
        rel = normalize_path(path)
        repo = normalize_repo(repo)
    except BoundaryError as exc:
        return None, str(exc)
    reason = _path_block_reason(rel)
    if reason:
        return None, reason
    rule, reason = _approved_rule(repo, rel, config)
    if reason or not rule:
        return None, reason or "path_not_allowlisted"
    reason = _validate_review_fields(entry, repo=repo, rule=rule)
    if reason:
        return None, reason
    if entry.get("sha256", "").lower() != sha256(raw) or entry.get("bytes") != len(raw):
        return None, "source_file_hash_or_size_mismatch"
    if _is_image(rel):
        rights_error = _rights_result(rel, raw, repo, config.get("asset_rights_registry", {}), _indexes(config)[1])
        if rights_error:
            return None, rights_error
    output, reason, _stats = _sanitize_content(rel, raw, config, repo)
    if output is None:
        return None, reason
    return output, None
