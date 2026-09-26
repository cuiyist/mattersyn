from __future__ import annotations

import copy
import json
import re
import tempfile
import unittest
from pathlib import Path

from public_release_guard import (
    ALLOWLIST_SCHEMA,
    POLICY_SCHEMA,
    RIGHTS_SCHEMA,
    BoundaryError,
    _sanitize_content,
    export_public_release,
    history_exclude_path,
    history_project,
    load_config,
    sha256,
    validate_allowlist_entry,
    validate_stage,
    user_directed_display_error,
)


def make_config(*, registry_assets=None, approvals=None):
    registry = {
        "schema_version": RIGHTS_SCHEMA,
        "snapshots": [],
        "assets": registry_assets or [],
    }
    registry_bytes = (json.dumps(registry, ensure_ascii=False, indent=2) + "\n").encode()
    return {
        "approval_status": "approved",
        "approved_by": "synthetic-test-reviewer",
        "policy_sha256": "0" * 64,
        "asset_rights_registry_sha256": sha256(registry_bytes),
        "allowed_content_classes": [
            "authored_code", "authored_docs", "memory", "skill", "audited_facts",
            "citation_metadata", "audit_summary", "site_code", "site_data", "site_asset", "structure_data",
        ],
        "path_rules": [{
            "rule_id": "synthetic-reviewed-all-paths",
            "repo": "mattersyn-site",
            "path_glob": "*",
            "decision": "allow",
            "content_class": "site_data",
            "review_status": "approved",
            "reviewer": "synthetic-test-reviewer",
            "requires_source_refs": False,
        }],
        "blob_approvals": approvals or [],
        "exact_blob_approval_classes": ["site_data"],
        "asset_rights_registry": registry,
    }


def allow_entry(path: str, raw: bytes, *, content_class="site_data", refs=None, digest=None):
    return {
        "repo": "mattersyn-site",
        "path": path,
        "sha256": digest if digest is not None else sha256(raw),
        "bytes": len(raw),
        "decision": "allow",
        "review_status": "approved",
        "reviewer": "synthetic-test-reviewer",
        "reviewed_at": "2026-09-24T00:00:00Z",
        "content_class": content_class,
        "source_refs": refs or [],
    }


def blob_approval(path: str, raw: bytes, content_class="site_data"):
    return {
        "repo": "mattersyn-site",
        "path": path,
        "sha256": sha256(raw),
        "decision": "allow",
        "review_status": "approved",
        "reviewer": "synthetic-test-reviewer",
        "reviewed_at": "2026-09-24T00:00:00Z",
        "content_class": content_class,
    }


def synthetic_windows_path(*parts: str) -> str:
    return chr(67) + chr(58) + chr(92) + chr(92).join(parts)


def synthetic_cod_uri(cod_id: str) -> str:
    prefix = "file:" + "//" + "/" + "/".join([
        "home", "coder", "svn-repositories", "_RELOADED_COD", "cod-reloaded", "cif",
    ])
    groups = [cod_id[-7:-6], cod_id[-6:-4], cod_id[-4:-2], cod_id]
    return prefix + "/" + "/".join(groups) + ".cif"


def make_allowlist(files):
    return {
        "schema_version": ALLOWLIST_SCHEMA,
        "repo": "mattersyn-site",
        "release_id": "synthetic-test-release",
        "source_commit": "a" * 40,
        "policy_sha256": "0" * 64,
        "asset_rights_registry_sha256": None,
        "files": files,
    }


def user_directed_figure(path, raw):
    return {
        "asset_hash": sha256(raw),
        "classification": "source_figure",
        "source_bindings": [{"doi": "10.1000/example", "url": "https://doi.org/10.1000/example"}],
        "delivery_paths": [
            {"repo": "mattersyn-site", "path": path, "bytes": len(raw)},
            {"repo": "mattersyn", "path": "recipe-atlas/static/" + path, "bytes": len(raw)},
        ],
        "rights": {
            "status": "user_directed_display", "attribution": "Source: DOI 10.1000/example, Figure 2",
            "copyright_permission_verified": False, "license_id": None, "license_evidence": [],
            "user_direction": {
                "record_id": "synthetic-explicit-user-direction", "recorded_at": "2026-09-24T12:00:00Z",
                "scope": "restore_previously_delivered_source_figures", "asset_hash": sha256(raw),
                "previous_delivery": [{"repo": "mattersyn-site", "path": path,
                                       "commit": "a" * 40, "asset_hash": sha256(raw)}],
            },
        },
    }


def user_directed_review_figure(path, raw, *, locator_id="figure-1", page=3):
    digest = sha256(raw)
    return {
        "asset_hash": digest,
        "classification": "source_figure",
        "source_bindings": [{
            "doi": "10.1021/cm052401p",
            "url": "https://doi.org/10.1021/cm052401p",
            "locators": {"document_role": "main", "page": page, "id": locator_id},
        }],
        "delivery_paths": [
            {"repo": "mattersyn-site", "path": path, "bytes": len(raw)},
            {"repo": "mattersyn", "path": "recipe-atlas/static/" + path, "bytes": len(raw)},
        ],
        "rights": {
            "status": "user_directed_display",
            "attribution": "Tirosh et al., DOI 10.1021/cm052401p, Figure 1",
            "copyright_permission_verified": False,
            "license_id": None,
            "license_evidence": [],
            "user_direction": {
                "record_id": "explicit-user-direction-to-retain-reviewed-source-figures",
                "recorded_at": "2026-09-24T12:00:00Z",
                "scope": "display_source_figures_for_reviewed_papers",
                "paper_id": "tirosh2006",
                "doi": "10.1021/cm052401p",
                "asset_hash": digest,
                "previous_delivery": [],
            },
        },
    }


class BoundaryGuardTests(unittest.TestCase):
    def test_exact_user_directed_figure_passes_without_claiming_copyright_clearance(self):
        path, raw = "assets/figures/example/figure-2.png", b"synthetic figure bytes"
        asset = user_directed_figure(path, raw)
        before = copy.deepcopy(asset)
        for repo, target in [("mattersyn-site", path), ("mattersyn", "recipe-atlas/static/" + path)]:
            with self.subTest(repo=repo):
                cfg = make_config(registry_assets=[asset])
                cfg["path_rules"][0].update(repo=repo, content_class="site_asset")
                entry = allow_entry(target, raw, content_class="site_asset")
                entry["repo"] = repo
                projected, reason = validate_allowlist_entry(target, raw, entry, cfg, repo)
                self.assertIsNone(reason)
                self.assertEqual(projected, raw)
                self.assertIsNone(history_exclude_path(repo, target, cfg))
                self.assertEqual(history_project(repo, target, raw, cfg)["action"], "allow")
        self.assertEqual(asset, before)
        self.assertFalse(asset["rights"]["copyright_permission_verified"])
        self.assertIsNone(asset["rights"]["license_id"])

    def test_user_direction_metadata_is_required_and_exact(self):
        path, raw = "assets/figures/example/figure-2.png", b"synthetic figure bytes"
        base = user_directed_figure(path, raw)
        mutations = [
            ("unknown", lambda x: x.update(classification="unknown")),
            ("working crop", lambda x: x.update(classification="private_working_crop")),
            ("authored", lambda x: x.update(classification="authored_diagram")),
            ("attribution", lambda x: x["rights"].update(attribution=" ")),
            ("source", lambda x: x.update(source_bindings=[])),
            ("local source URL", lambda x: x.update(source_bindings=[{"url": "file:" + "///synthetic"}])),
            ("permission missing", lambda x: x["rights"].pop("copyright_permission_verified")),
            ("permission claimed", lambda x: x["rights"].update(copyright_permission_verified=True)),
            ("instruction", lambda x: x["rights"].pop("user_direction")),
            ("record id", lambda x: x["rights"]["user_direction"].update(record_id="")),
            ("scope", lambda x: x["rights"]["user_direction"].update(scope="all_images")),
            ("time", lambda x: x["rights"]["user_direction"].update(recorded_at="2026-09-24")),
            ("directive hash", lambda x: x["rights"]["user_direction"].update(asset_hash="f" * 64)),
            ("prior delivery missing", lambda x: x["rights"]["user_direction"].update(previous_delivery=[])),
            ("prior path", lambda x: x["rights"]["user_direction"]["previous_delivery"][0].update(path="assets/other.png")),
            ("prior hash", lambda x: x["rights"]["user_direction"]["previous_delivery"][0].update(asset_hash="f" * 64)),
            ("prior commit", lambda x: x["rights"]["user_direction"]["previous_delivery"][0].update(commit="HEAD")),
            ("prior repo", lambda x: x["rights"]["user_direction"]["previous_delivery"][0].update(repo="mattersyn")),
            ("prior duplicate", lambda x: x["rights"]["user_direction"]["previous_delivery"].append(copy.deepcopy(x["rights"]["user_direction"]["previous_delivery"][0]))),
            ("delivery duplicate", lambda x: x["delivery_paths"].append(copy.deepcopy(x["delivery_paths"][0]))),
        ]
        for label, mutate in mutations:
            with self.subTest(case=label):
                asset = copy.deepcopy(base); mutate(asset)
                self.assertIsNotNone(user_directed_display_error(asset, "mattersyn-site", path))

    def test_user_direction_cannot_bypass_raw_document_or_private_path_rules(self):
        paths = ["private/figure.png", "assets/private-working/figure.png", "assets/page-renders/figure.png",
                 "assets/main-page3.png", "assets/figure.pdf", "assets/figure.txt", "assets/.cache/figure.png"]
        for path in paths:
            with self.subTest(path=path):
                asset = user_directed_figure(path, b"synthetic")
                self.assertEqual(user_directed_display_error(asset, "mattersyn-site", path),
                                 "user_directed_display_path_ineligible")
        path = "assets/figures/example/cropped-panel.png"
        asset = user_directed_figure(path, b"synthetic")
        asset["classification"] = "source_page_crop"
        self.assertIsNone(user_directed_display_error(asset, "mattersyn-site", path))

    def test_cited_figure_for_reviewed_paper_can_be_displayed_without_prior_delivery(self):
        path, raw = "assets/paper-reviews/tirosh2006/figure-1.png", b"reviewed source figure"
        asset = user_directed_review_figure(path, raw)
        for repo, target in [("mattersyn-site", path), ("mattersyn", "recipe-atlas/static/" + path)]:
            with self.subTest(repo=repo):
                self.assertIsNone(user_directed_display_error(asset, repo, target))

    def test_cited_scheme_for_reviewed_paper_preserves_exact_bytes_and_rights(self):
        path, raw = "assets/paper-reviews/tirosh2006/scheme-1.png", b"synthetic reviewed reaction scheme"
        asset = user_directed_review_figure(path, raw, locator_id="scheme-1", page=2)
        asset["rights"]["attribution"] = "Synthetic cited source, DOI 10.1021/cm052401p, Scheme 1, page 2"
        before = copy.deepcopy(asset)
        for repo, target in [("mattersyn-site", path), ("mattersyn", "recipe-atlas/static/" + path)]:
            with self.subTest(repo=repo):
                self.assertIsNone(user_directed_display_error(asset, repo, target))
                config = make_config(registry_assets=[asset])
                config["path_rules"][0].update(repo=repo, content_class="site_asset")
                entry = allow_entry(target, raw, content_class="site_asset")
                entry["repo"] = repo
                projected, reason = validate_allowlist_entry(target, raw, entry, config, repo)
                self.assertIsNone(reason)
                self.assertEqual(projected, raw)
        self.assertEqual(asset, before)
        self.assertFalse(asset["rights"]["copyright_permission_verified"])
        self.assertIsNone(asset["rights"]["license_id"])

    def test_scheme_requires_matching_paper_doi_and_scheme_locator(self):
        path, raw = "assets/paper-reviews/tirosh2006/scheme-1.png", b"synthetic reviewed reaction scheme"
        base = user_directed_review_figure(path, raw, locator_id="scheme-1", page=2)
        mutations = [
            ("different scheme id", lambda x: x["source_bindings"][0]["locators"].update(id="scheme-2")),
            ("figure id instead of scheme", lambda x: x["source_bindings"][0]["locators"].update(id="figure-1")),
            ("different paper", lambda x: x["rights"]["user_direction"].update(paper_id="other-paper")),
            ("different source DOI", lambda x: x["source_bindings"][0].update(doi="10.1000/different")),
            ("missing page", lambda x: x["source_bindings"][0]["locators"].pop("page")),
        ]
        for label, mutate in mutations:
            with self.subTest(case=label):
                asset = copy.deepcopy(base)
                mutate(asset)
                self.assertEqual(user_directed_display_error(asset, "mattersyn-site", path),
                                 "user_directed_display_source_binding_missing")

    def test_new_source_figure_scope_requires_exact_paper_path_and_locator(self):
        raw = b"reviewed source figure"
        cases = [
            ("assets/paper-reviews/other-paper/figure-1.png", "figure-1", 3),
            ("assets/paper-reviews/tirosh2006/figure-1.png", "figure-2", 3),
            ("assets/paper-reviews/tirosh2006/table-1.png", "table-1", None),
            ("assets/source-renders/tirosh2006/figure-1.png", "figure-1", 3),
        ]
        for path, locator_id, page in cases:
            with self.subTest(path=path, locator=locator_id, page=page):
                asset = user_directed_review_figure(path, raw, locator_id=locator_id, page=page)
                if page is None:
                    asset["source_bindings"][0]["locators"].pop("page")
                self.assertIsNotNone(user_directed_display_error(asset, "mattersyn-site", path))

    def test_user_direction_still_requires_exact_image_bytes(self):
        path, raw = "assets/figures/example/figure-2.png", b"synthetic figure bytes"
        asset = user_directed_figure(path, raw)
        cfg = make_config(registry_assets=[asset])
        cfg["path_rules"][0]["content_class"] = "site_asset"
        changed = raw + b"changed"
        self.assertEqual(validate_allowlist_entry(path, changed, allow_entry(path, changed, content_class="site_asset"),
                                                 cfg, "mattersyn-site")[1], "asset_rights_record_missing_or_ambiguous")

    def test_legacy_corpus_and_tracked_private_paths_stay_denied(self):
        cfg = make_config()
        paths = [
            "research-assets/incoming-paper-monitor/corpus-screening/20260919/documents.jsonl",
            "project/data/raw-cache/page-3.json",
            "recipe-atlas/.cache/generated-preview.json",
            "recipe-atlas/private/audit.json",
        ]
        for path in paths:
            with self.subTest(path=path):
                self.assertIsNotNone(history_exclude_path("mattersyn-site", path, cfg))
                result = history_project("mattersyn-site", path, b"{}", cfg)
                self.assertEqual(result["action"], "omit")
                self.assertNotIn("content", result)

    def test_history_needs_exact_reviewer_approval_for_blob_hash(self):
        path = "data/material.json"
        raw = b'{"formula":"CoNi2S4","yield_percent":14}\n'
        cfg = make_config()
        no_approval = history_project("mattersyn-site", path, raw, cfg)
        self.assertEqual(no_approval["reason"], "historical_blob_not_exact_hash_approved")
        cfg["blob_approvals"] = [blob_approval(path, raw)]
        approved = history_project("mattersyn-site", path, raw, cfg)
        self.assertEqual(approved["action"], "allow")
        self.assertEqual(approved["content"], raw)
        self.assertEqual(approved["content_class"], "site_data")

    def test_schema_aware_sanitizer_preserves_authored_text_and_science(self):
        authored = "Academic explanation of the reaction mechanism. " * 30
        obj = {
            "record_id": "synthetic-01",
            "description": {"text": authored, "text_origin": "authored"},
            "measurements": {"absorbance": 0.73, "temperature_C": 220},
        }
        raw = (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode()
        projected, why, stats = _sanitize_content("records/record.json", raw)
        self.assertEqual(projected, raw)
        self.assertEqual(why, "unchanged")
        self.assertEqual(stats["source_text_fields_removed"], 0)

    def test_machine_extracted_text_and_windows_path_are_removed_without_report_text(self):
        payload = {
            "source_path": synthetic_windows_path("Users", "SyntheticUser", "Desktop", "private", "paper.pdf"),
            "citation_id": "doi:10.1234/example",
            "evidence": [
                {"text": "PUBLISHER RAW FULL TEXT phrase", "text_origin": "machine extracted", "page": 2},
                {"text": "Authored summary of the reported phase", "text_origin": "authored", "phase": "spinel"},
            ],
            "note": "Temporary file at " + synthetic_windows_path("Users", "SyntheticUser", "Desktop", "cache", "x.txt"),
        }
        raw = (json.dumps(payload) + "\n").encode()
        projected, why, stats = _sanitize_content("records/record.json", raw)
        text = projected.decode()
        self.assertNotIn("PUBLISHER RAW FULL TEXT phrase", text)
        self.assertNotIn(synthetic_windows_path("Users", "SyntheticUser"), text)
        self.assertIn("Authored summary of the reported phase", text)
        self.assertIn('"phase": "spinel"', text)
        self.assertEqual(why, "projected_json")
        self.assertGreater(stats["source_text_fields_removed"], 0)
        self.assertGreater(stats["local_path_fields_removed"], 0)
        self.assertGreater(stats["local_path_strings_redacted"], 0)

    def test_path_regex_runtime_assembly_is_exact_and_sources_self_project_unchanged(self):
        import public_release_guard as guard

        backslash = chr(92)
        slash = chr(47)
        separator = "[" + backslash * 2 + slash + "]+"
        windows_segment = "[^" + backslash * 2 + slash + r"\s\"'<>|,;]+"
        posix_segment = "[^" + slash + r"\s\"'<>|,;]+"
        expected_windows = (
            r"(?<![A-Za-z0-9])(?:[A-Za-z]:" + separator + ")"
            + "(?:" + windows_segment + separator + ")*"
            + windows_segment
        )
        expected_profile = (
            r"(?i)(?<![A-Za-z0-9])(?:[A-Z]:" + separator
            + r"(?:Users|Documents and Settings)" + separator + r"(?!<)"
            + windows_segment + "(?:" + separator + windows_segment + ")*"
            + "|" + slash + r"(?:Users|home)" + slash + posix_segment
            + "(?:" + slash + posix_segment + ")*)"
        )
        self.assertEqual(guard._WINDOWS_PATH_RE.pattern, expected_windows)
        self.assertEqual(guard._WINDOWS_PATH_RE.flags, re.compile(expected_windows).flags)
        self.assertEqual(guard._PROFILE_PATH_RE.pattern, expected_profile)
        self.assertEqual(guard._PROFILE_PATH_RE.flags, re.compile(expected_profile, re.IGNORECASE).flags)
        win_sample = synthetic_windows_path("Users", "SyntheticUser", "private", "paper.pdf")
        posix_sample = slash + slash.join(("home", "synthetic-user", "private", "paper.pdf"))
        self.assertTrue(guard._WINDOWS_PATH_RE.search(win_sample))
        self.assertTrue(guard._PROFILE_PATH_RE.search(win_sample))
        self.assertTrue(guard._PROFILE_PATH_RE.search(posix_sample))

        boundary = Path(__file__).resolve().parent.parent
        for source in (boundary / "public_release_guard.py", Path(__file__).resolve()):
            raw = source.read_bytes()
            projected, reason, _ = _sanitize_content("tools/mattersyn-release/source.py", raw)
            self.assertEqual(projected, raw, source.name)
            self.assertEqual(reason, "unchanged", source.name)

    def test_escaped_profile_paths_in_code_and_data_are_removed_without_decoding_code(self):
        for repetitions in (1, 2, 4, 8):
            separator = chr(92) * repetitions
            value = "C:" + separator + separator.join(("Users", "SyntheticUser", "project", "input.json"))
            for extension, text in (
                (".mjs", "const fixture = " + json.dumps(value) + ";"),
                (".py", "fixture = " + repr(value)),
                (".md", value),
            ):
                with self.subTest(repetitions=repetitions, extension=extension):
                    raw = text.encode()
                    cleaned, reason, stats = _sanitize_content("synthetic" + extension, raw)
                    self.assertNotEqual(cleaned, raw)
                    self.assertNotIn(b"SyntheticUser", cleaned)
                    self.assertIn(b"[local path redacted]", cleaned)
                    self.assertEqual(reason, "sanitized_local_paths")
                    self.assertGreater(stats["local_path_strings_redacted"], 0)

    def test_escaped_paths_in_nested_json_values_and_keys_are_checked(self):
        for repetitions in (1, 2, 4, 8):
            separator = chr(92) * repetitions
            value = "C:" + separator + separator.join(("Users", "SyntheticUser", "project", "input.json"))
            for depth in (0, 1, 2):
                obj = {"note": value, "measurement": {"value": 3.2, "unit": "nm", "raw_text": "3.2 nm"}}
                for _ in range(depth):
                    obj = {"payload": json.dumps(obj)}
                raw = json.dumps(obj).encode()
                with self.subTest(repetitions=repetitions, depth=depth):
                    cleaned, reason, stats = _sanitize_content("synthetic.json", raw)
                    self.assertNotEqual(cleaned, raw)
                    self.assertNotIn(b"SyntheticUser", cleaned)
                    result = json.loads(cleaned)
                    for _ in range(depth):
                        result = json.loads(result["payload"])
                    self.assertEqual(result["measurement"], {"value": 3.2, "unit": "nm", "raw_text": "3.2 nm"})
                    self.assertEqual(result["note"], "[local path redacted]")
                    self.assertGreater(stats["local_path_strings_redacted"], 0)
            raw = json.dumps({value: {"value": 3.2, "unit": "nm"}}).encode()
            cleaned, reason, _ = _sanitize_content("synthetic.json", raw)
            self.assertIsNone(cleaned)
            self.assertEqual(reason, "local_path_in_json_key")

    def test_escaped_detection_preserves_portable_code_and_scientific_lexemes(self):
        separator = chr(92) * 2
        code = ("const example = " + json.dumps("C:" + separator + "example" + separator + "file") + ";\n"
                + "const pattern = " + repr(separator + "s+") + ";\n"
                + "const fixture = new URL('./bindings-proposal.json', import.meta.url);\n").encode()
        self.assertEqual(_sanitize_content("synthetic.mjs", code)[0], code)
        data = {"source_url": "https://doi.org/10.1000/example",
                "measurement": {"value": 3.2, "unit": "nm", "raw_text": "3.2 nm"}}
        raw = json.dumps(data).encode()
        self.assertEqual(_sanitize_content("synthetic.json", raw)[0], raw)

    def test_legacy_source_hash_and_page_located_snippet_text_is_removed(self):
        obj = {
            "features": {"snippets": [{
                "text": "Publisher paragraph that was copied into an old screening record.",
                "source_sha256": "b" * 64,
                "page": 7,
            }]},
            "claim": "authored, concise phase summary",
            "phase": "rocksalt",
        }
        raw = (json.dumps(obj) + "\n").encode()
        projected, _, stats = _sanitize_content("data/record.json", raw)
        text = projected.decode()
        self.assertNotIn("Publisher paragraph that was copied", text)
        self.assertIn("source_sha256", text)
        self.assertIn('"page": 7', text)
        self.assertIn("authored, concise phase summary", text)
        self.assertGreater(stats["source_text_fields_removed"], 0)

    def test_nested_raw_origin_inherits_but_explicit_authored_child_is_preserved(self):
        obj = {
            "text_origin": "machine_extracted",
            "sections": [
                {"text": "NESTED RAW PAPER TEXT", "page": 3},
                {"text": "Authored contextual note", "text_origin": "authored"},
            ],
        }
        projected, _, _ = _sanitize_content("data/record.json", (json.dumps(obj) + "\n").encode())
        result = projected.decode()
        self.assertNotIn("NESTED RAW PAPER TEXT", result)
        self.assertIn("Authored contextual note", result)

    def test_json_object_key_that_is_local_absolute_path_is_removed(self):
        obj = {
            synthetic_windows_path("Users", "Synthetic", "source.pdf"): {"page": 1},
            "citation_id": "doi:10.1234/example",
        }
        projected, reason, stats = _sanitize_content("data/record.json", (json.dumps(obj) + "\n").encode())
        self.assertIsNone(projected)
        self.assertEqual(reason, "local_path_in_json_key")
        self.assertGreater(stats["local_path_key_detected"], 0)

    def test_legacy_private_first_page_preview_field_is_stripped(self):
        obj = {
            "record_id": "synthetic-record",
            "firstPagePreviewPrivate": "PRIVATE PREVIEW TEXT",
            "phase": "spinel",
        }
        projected, why, stats = _sanitize_content("data/record.json", (json.dumps(obj) + "\n").encode())
        result = projected.decode()
        self.assertNotIn("PRIVATE PREVIEW TEXT", result)
        self.assertIn('"phase": "spinel"', result)
        self.assertEqual(why, "projected_json")
        self.assertEqual(stats["source_text_fields_removed"], 1)

    def test_duplicate_json_keys_fail_closed_instead_of_silently_colliding(self):
        raw = b'{"phase":"spinel","phase":"rocksalt"}\n'
        projected, reason, _ = _sanitize_content("data/record.json", raw)
        self.assertIsNone(projected)
        self.assertEqual(reason, "invalid_structured_payload")

    def test_structured_quantity_raw_text_and_empty_lexemes_are_preserved(self):
        obj = {
            "measurements": [
                {"raw_text": "4mL"},
                {"raw_text": "180°C"},
                {"raw_text": ""},
                {
                "parameter": "precursor_volume",
                "numeric_value": 4,
                "unit": "mL",
                "raw_text": "4mL",
                }, {
                "parameter": "reported_temperature",
                "numeric_value": None,
                "unit": "",
                "raw_text": "",
                },
            ],
            "cells": [{
                "cell_id": "S7",
                "raw_text": "180°C",
                "numeric_value": 180,
                "unit": "°C",
                "unit_status": "explicit",
                "evidence": {"page": 3},
            }],
        }
        raw = (json.dumps(obj, ensure_ascii=False) + "\n").encode()
        projected, why, stats = _sanitize_content("data/measurements.json", raw)
        self.assertEqual(projected, raw)
        self.assertEqual(why, "unchanged")
        self.assertEqual(stats["source_text_fields_removed"], 0)

    def test_measurement_container_name_alone_does_not_exempt_arbitrary_raw_prose(self):
        obj = {"measurements": [{"raw_text": "A long publisher sentence about the reported synthetic result."}]}
        projected, _, stats = _sanitize_content("data/measurements.json", (json.dumps(obj) + "\n").encode())
        result = projected.decode()
        self.assertNotIn("A long publisher sentence", result)
        self.assertGreater(stats["source_text_fields_removed"], 0)

    def test_structured_measurement_wrapper_cannot_exempt_long_source_paragraphs(self):
        paragraph = "Synthetic source paragraph with reported conditions and observations. " * 8
        for record in [
            {"raw_text": paragraph, "evidence": {"page": 2}},
            {"raw_text": paragraph, "value": 1, "unit": "nm", "evidence": {"page": 2}},
            {"raw_text": "x" * 65, "cell_id": "S2", "numeric_value": 1, "unit": "nm", "evidence": {"page": 2}},
        ]:
            obj = {"measurements": [record]}
            projected, _, stats = _sanitize_content("data/measurements.json", (json.dumps(obj) + "\n").encode())
            self.assertNotIn("raw_text", projected.decode())
            self.assertGreater(stats["source_text_fields_removed"], 0)

    def test_embedded_json_measurement_tables_are_inspected_and_preserved_byte_for_byte(self):
        table = {
            "rows": [
                {"cell_id": "T1", "raw_text": "2.63 nm", "numeric_value": 2.63, "unit": "nm", "evidence": {"page": 4}},
                {"cell_id": "T2", "raw_text": "1.40 nm", "numeric_value": 1.4, "unit": "nm", "evidence": {"page": 4}},
            ]
        }
        encoded_table = json.dumps(table, ensure_ascii=False, separators=(",", ":"))
        obj = {"measurements": [{"parameter": "lattice_fit", "value": {"value": encoded_table}}]}
        raw = (json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
        projected, reason, stats = _sanitize_content("data/measurement-fit.json", raw)
        self.assertEqual(projected, raw)
        self.assertEqual(reason, "unchanged")
        self.assertEqual(stats["source_text_fields_removed"], 0)

    def test_embedded_json_source_text_and_local_paths_are_checked_recursively(self):
        private = "PRIVATE SOURCE PARAGRAPH " * 5
        encoded_source = json.dumps({
            "text_origin": "machine_extracted",
            "sections": [{"text": private}],
        }, separators=(",", ":"))
        obj = {"measurements": [{"value": {"value": encoded_source}}]}
        projected, reason, stats = _sanitize_content(
            "data/embedded-source.json", (json.dumps(obj, separators=(",", ":")) + "\n").encode()
        )
        self.assertIsNotNone(projected)
        cleaned_outer = json.loads(projected)
        cleaned_inner = json.loads(cleaned_outer["measurements"][0]["value"]["value"])
        self.assertNotIn("text", cleaned_inner["sections"][0])
        self.assertGreater(stats["source_text_fields_removed"], 0)
        self.assertEqual(reason, "projected_json")

        local_path = synthetic_windows_path("Users", "SyntheticUser", "private", "paper.pdf")
        encoded_path_value = json.dumps({"payload": local_path}, separators=(",", ":"))
        encoded_path_key = json.dumps({local_path: "private"}, separators=(",", ":"))
        path_obj = {"measurements": [{"value": {"value": encoded_path_value}}]}
        path_raw = (json.dumps(path_obj, separators=(",", ":")) + "\n").encode()
        path_projected, path_reason, path_stats = _sanitize_content("data/embedded-path.json", path_raw)
        self.assertIsNotNone(path_projected)
        self.assertNotIn(local_path.encode(), path_projected)
        self.assertIn(b"[local path redacted]", path_projected)
        self.assertGreater(path_stats["local_path_strings_redacted"], 0)

        path_key_obj = {"measurements": [{"value": {"value": encoded_path_key}}]}
        path_key_raw = (json.dumps(path_key_obj, separators=(",", ":")) + "\n").encode()
        key_projected, key_reason, key_stats = _sanitize_content("data/embedded-path.json", path_key_raw)
        self.assertIsNone(key_projected)
        self.assertEqual(key_reason, "local_path_in_json_key")
        self.assertGreater(key_stats["local_path_key_detected"], 0)

    def test_current_and_historical_json_schemas_preserve_raw_text_declarations_only(self):
        schemas = [
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {"raw_text": {"type": "string"}},
                "required": ["raw_text"],
            },
            {
                "type": "object",
                "properties": {"raw_text": {"type": "string", "maxLength": 64}},
                "required": [],
            },
        ]
        for schema in schemas:
            raw = (json.dumps(schema, separators=(",", ":")) + "\n").encode()
            projected, reason, stats = _sanitize_content("data/record.schema.json", raw)
            self.assertEqual(projected, raw)
            self.assertEqual(reason, "unchanged")
            self.assertEqual(stats["source_text_fields_removed"], 0)
        data = {"raw_text": {"type": "string"}}
        projected, _, stats = _sanitize_content("data/record.json", (json.dumps(data) + "\n").encode())
        self.assertNotIn('"raw_text"', projected.decode())
        self.assertEqual(stats["source_text_fields_removed"], 1)

    def test_structure_and_repository_markers_are_safe_text_or_empty_marker(self):
        for name, content in [
            (".gitattributes", b"recipe-atlas/data/records/*.json -text\n"),
            ("reference.cif", b"data_reference\n_cell_length_a 3.5\n"),
            ("ligand.sdf", b"synthetic sdf record\n$$$$\n"),
            ("coordinates.xyz", b"2\nreference-only\nCd 0 0 0\nSe 0 0 2.6\n"),
            (".gitignore", b"_build/\n.cache/\n"),
            (".nojekyll", b""),
        ]:
            with self.subTest(name=name):
                projected, _, _ = _sanitize_content(name, content)
                self.assertEqual(projected, content)
        invalid, reason, _ = _sanitize_content("reference.cif", b"data_x\n\x00bad\n")
        self.assertIsNone(invalid)
        self.assertEqual(reason, "invalid_structure_text_control_bytes")
        private_path = synthetic_windows_path("Users", "SyntheticUser", "private", "local.cif")
        private, reason, _ = _sanitize_content("reference.cif", ("data_x\n_note " + private_path + "\n").encode())
        self.assertIsNone(private)
        self.assertEqual(reason, "local_path_in_structure_data")

    def test_cod_archive_comment_exception_requires_exact_hash_path_and_citation(self):
        cod_id = "9016056"
        path = "assets/crystal-references/9016056.cif"
        raw = (
            "data_COD\n"
            "#$URL: " + synthetic_cod_uri(cod_id) + " $\n"
            "_cell_length_a 3.5\n"
        ).encode()
        exception = {
            "repo": "mattersyn-site",
            "path": path,
            "sha256": sha256(raw),
            "bytes": len(raw),
            "cod_id": cod_id,
            "pattern_id": "cod_archive_annotation_v1",
            "review_status": "approved",
            "reviewer": "synthetic-test-reviewer",
            "source_refs": [{"citation_id": "COD-9016056", "url": "https://www.crystallography.net/cod/9016056.html"}],
        }
        cfg = make_config()
        cfg["structure_path_exceptions"] = [exception]
        projected, reason, _ = _sanitize_content(path, raw, cfg, "mattersyn-site")
        self.assertEqual(projected, raw)
        self.assertEqual(reason, "approved_cod_archive_annotation_preserved")
        wrong_hash, reason, _ = _sanitize_content(path, raw + b"# changed\n", cfg, "mattersyn-site")
        self.assertIsNone(wrong_hash)
        self.assertEqual(reason, "local_path_in_structure_data")
        other_private_path = raw + ("# local " + synthetic_windows_path("Users", "SyntheticUser", "secret.cif") + "\n").encode()
        blocked, reason, _ = _sanitize_content(path, other_private_path, cfg, "mattersyn-site")
        self.assertIsNone(blocked)
        self.assertEqual(reason, "local_path_in_structure_data")
        no_source_ref = dict(exception, source_refs=[])
        cfg["structure_path_exceptions"] = [no_source_ref]
        blocked, reason, _ = _sanitize_content(path, raw, cfg, "mattersyn-site")
        self.assertIsNone(blocked)
        self.assertEqual(reason, "local_path_in_structure_data")

    def test_structure_data_requires_source_and_license_metadata_and_keeps_exact_bytes(self):
        path = "assets/structures/reference.cif"
        raw = b"data_reference\n_cell_length_a 3.5\n"
        cfg = make_config()
        cfg["path_rules"] = [dict(cfg["path_rules"][0], content_class="structure_data", requires_source_refs=True)]
        entry = allow_entry(path, raw, content_class="structure_data", refs=[{
            "citation_id": "mp-1234",
            "url": "https://materialsproject.org/materials/mp-1234",
            "license_id": "CC-BY-4.0",
            "format": "CIF",
        }])
        projected, reason = validate_allowlist_entry(path, raw, entry, cfg, "mattersyn-site")
        self.assertIsNone(reason)
        self.assertEqual(projected, raw)
        missing_provenance = allow_entry(path, raw, content_class="structure_data")
        self.assertEqual(
            validate_allowlist_entry(path, raw, missing_provenance, cfg, "mattersyn-site")[1],
            "source_references_required",
        )

    def test_release_receipt_source_refs_are_structured_citation_metadata(self):
        raw = b'{"claim":"phase assignment"}\n'
        safe = allow_entry("records/record.json", raw, refs=[{
            "doi": "10.1234/example", "page": "p. 4", "figure": "Fig. 2b",
        }])
        self.assertIsNone(validate_allowlist_entry("records/record.json", raw, safe, make_config(), "mattersyn-site")[1])
        unsafe = allow_entry("records/record.json", raw, refs=[{"citation_id": synthetic_windows_path("Users", "SyntheticUser", "secret.pdf")}])
        self.assertEqual(
            validate_allowlist_entry("records/record.json", raw, unsafe, make_config(), "mattersyn-site")[1],
            "local_path_in_source_reference",
        )
        prose = allow_entry("records/record.json", raw, refs=[{"quote": "long publisher excerpt"}])
        self.assertEqual(
            validate_allowlist_entry("records/record.json", raw, prose, make_config(), "mattersyn-site")[1],
            "source_reference_field_not_allowlisted",
        )

    def test_policy_must_pin_exact_asset_registry_hash(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry = {"schema_version": RIGHTS_SCHEMA, "snapshots": [], "assets": []}
            registry_path = root / "registry.json"
            registry_bytes = (json.dumps(registry, indent=2) + "\n").encode()
            registry_path.write_bytes(registry_bytes)
            policy = {
                "schema_version": POLICY_SCHEMA,
                "approval_status": "approved",
                "approved_by": "synthetic-test-reviewer",
                "asset_rights_registry_sha256": sha256(registry_bytes),
                "path_rules": [],
                "blob_approvals": [],
                "exact_blob_approval_classes": [],
            }
            policy_path = root / "policy.json"
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            cfg = load_config(policy_path, registry_path)
            self.assertEqual(cfg["asset_rights_registry_sha256"], sha256(registry_bytes))
            policy["asset_rights_registry_sha256"] = "f" * 64
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            with self.assertRaisesRegex(BoundaryError, "asset_registry_hash_not_pinned_by_policy"):
                load_config(policy_path, registry_path)

    def test_unresolved_and_wrong_hash_images_fail_closed(self):
        path = "assets/figures/figure-1.png"
        raw = b"synthetic image bytes"
        entry = allow_entry(path, raw, content_class="site_data")
        withheld = {
            "asset_hash": sha256(raw),
            "classification": "source_figure",
            "delivery_paths": [{"repo": "mattersyn-site", "path": path, "bytes": len(raw)}],
            "rights": {"status": "withheld", "reason": "synthetic unresolved rights"},
        }
        cfg = make_config(registry_assets=[withheld])
        self.assertEqual(validate_allowlist_entry(path, raw, entry, cfg, "mattersyn-site")[1], "asset_rights_withheld")
        wrong = dict(withheld, asset_hash="f" * 64)
        cfg = make_config(registry_assets=[wrong])
        self.assertEqual(validate_allowlist_entry(path, raw, entry, cfg, "mattersyn-site")[1], "asset_rights_record_missing_or_ambiguous")
        self.assertEqual(
            validate_allowlist_entry(path, raw, entry, make_config(), "mattersyn-site")[1],
            "asset_rights_record_missing_or_ambiguous",
        )

    def test_explicitly_authored_image_can_pass_with_exact_hash_and_attribution(self):
        path = "assets/chemistry/ligand.svg"
        raw = b"<svg xmlns='http://www.w3.org/2000/svg'><text>authored</text></svg>\n"
        rights_record = {
            "asset_hash": sha256(raw),
            "classification": "authored_molecule",
            "delivery_paths": [{"repo": "mattersyn-site", "path": path, "bytes": len(raw)}],
            "rights": {"status": "not_source_derived", "attribution": "MatterSyn authored structure diagram"},
        }
        cfg = make_config(registry_assets=[rights_record])
        rule = dict(cfg["path_rules"][0], path_glob="*")
        rule["content_class"] = "site_asset"
        cfg["path_rules"] = [rule]
        entry = allow_entry(path, raw, content_class="site_asset")
        projected, reason = validate_allowlist_entry(path, raw, entry, cfg, "mattersyn-site")
        self.assertIsNone(reason)
        self.assertEqual(projected, raw)

    def test_stage_rejects_hash_mismatch_unlisted_files_and_git_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "stage"
            root.mkdir()
            file = root / "index.html"
            file.write_text('{"value": 1}\n', encoding="utf-8")
            raw = file.read_bytes()
            allowlist = Path(td) / "allowlist.json"
            cfg = make_config()
            al = make_allowlist([allow_entry("index.html", raw, digest="a" * 64)])
            al["asset_rights_registry_sha256"] = cfg["asset_rights_registry_sha256"]
            allowlist.write_text(json.dumps(al), encoding="utf-8")
            _, report = validate_stage(root, allowlist, cfg, "mattersyn-site")
            self.assertEqual(report["status"], "failed")
            self.assertIn("staged_sha256_mismatch", {x["reason_code"] for x in report["failures"]})
            (root / "unexpected.txt").write_text("unreviewed", encoding="utf-8")
            _, report = validate_stage(root, allowlist, cfg, "mattersyn-site")
            self.assertIn("staged_file_not_allowlisted", {x["reason_code"] for x in report["failures"]})
            git = root / ".git"
            git.mkdir()
            (git / "config").write_text("synthetic", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "git_metadata_in_release_stage"):
                validate_stage(root, allowlist, cfg, "mattersyn-site")

    def test_export_refuses_same_or_overlapping_source_destination_without_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source"
            source.mkdir()
            (source / "authored.md").write_text("Original authored prose.\n", encoding="utf-8")
            allowlist = Path(td) / "allowlist.json"
            raw = (source / "authored.md").read_bytes()
            cfg = make_config()
            al = make_allowlist([allow_entry("authored.md", raw, content_class="site_data")])
            al["asset_rights_registry_sha256"] = cfg["asset_rights_registry_sha256"]
            allowlist.write_text(json.dumps(al), encoding="utf-8")
            before = (source / "authored.md").read_bytes()
            with self.assertRaisesRegex(ValueError, "source_and_destination_must_be_disjoint"):
                export_public_release(source, source, allowlist, cfg, "mattersyn-site", Path(td) / "m.json", Path(td) / "r.json")
            with self.assertRaisesRegex(ValueError, "source_and_destination_must_be_disjoint"):
                export_public_release(source, source / "child", allowlist, cfg, "mattersyn-site", Path(td) / "m.json", Path(td) / "r.json")
            with self.assertRaisesRegex(ValueError, "receipts_must_be_outside_source"):
                export_public_release(source, Path(td) / "stage", allowlist, cfg, "mattersyn-site", source / "manifest.json", Path(td) / "report.json")
            self.assertEqual((source / "authored.md").read_bytes(), before)
            self.assertFalse((source / "child").exists())
            self.assertFalse((source / "manifest.json").exists())

    def test_export_sanitizes_into_a_new_tree_and_emits_hash_bound_receipts(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            source.mkdir()
            page = source / "index.html"
            original = ("<p>Authored description. " + synthetic_windows_path("Users", "SyntheticUser", "Desktop", "private.txt") + "</p>\n").encode()
            page.write_bytes(original)
            cfg = make_config()
            allowlist = base / "allowlist.json"
            al = make_allowlist([allow_entry("index.html", original)])
            al["asset_rights_registry_sha256"] = cfg["asset_rights_registry_sha256"]
            allowlist.write_text(json.dumps(al), encoding="utf-8")
            output = base / "public-stage"
            receipts = base / "receipts"
            manifest_path = receipts / "manifest.json"
            report_path = receipts / "report.json"
            manifest, report = export_public_release(
                source, output, allowlist, cfg, "mattersyn-site", manifest_path, report_path,
            )
            self.assertEqual(report["status"], "passed")
            self.assertEqual(manifest["status"], "passed")
            self.assertNotIn(synthetic_windows_path("Users", "SyntheticUser").encode(), (output / "index.html").read_bytes())
            self.assertIn(b"Authored description.", (output / "index.html").read_bytes())
            self.assertEqual(page.read_bytes(), original)
            self.assertTrue(manifest_path.is_file())
            self.assertTrue(report_path.is_file())


if __name__ == "__main__":
    unittest.main()
