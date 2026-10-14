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

    def test_legacy_source_figure_crop_requires_paper_locator_and_crop_hash(self):
        path, raw = "assets/source-figures/tirosh2006/figure-01.png", b"reviewed figure crop"
        asset = user_directed_review_figure(path, raw, locator_id="Figure 1", page=3)
        asset["source_bindings"][0]["locators"]["source_sha256"] = "b" * 64
        asset["source_bindings"][0]["crop"] = {"asset_sha256": sha256(raw)}
        asset["provenance_bindings"] = [{"paper_id": "tirosh2006", "doi": "10.1021/cm052401p",
                                         "record_ids": ["tirosh-2006-method-a"]}]
        for repo, target in [("mattersyn-site", path), ("mattersyn", "recipe-atlas/static/" + path)]:
            with self.subTest(repo=repo):
                self.assertIsNone(user_directed_display_error(asset, repo, target))
        for label, mutate in [
            ("wrong directory", lambda a: a["rights"]["user_direction"].update(paper_id="other2006")),
            ("wrong figure", lambda a: a["source_bindings"][0]["locators"].update(id="Figure 2")),
            ("wrong crop", lambda a: a["source_bindings"][0]["crop"].update(asset_sha256="c" * 64)),
            ("missing source", lambda a: a["source_bindings"][0]["locators"].pop("source_sha256")),
            ("missing provenance", lambda a: a.update(provenance_bindings=[])),
        ]:
            with self.subTest(case=label):
                changed = copy.deepcopy(asset)
                mutate(changed)
                self.assertIsNotNone(user_directed_display_error(changed, "mattersyn-site", path))

    def test_legacy_si_table_crop_requires_matching_table_locator(self):
        path, raw = "assets/source-figures/tirosh2006/table-s1.png", b"reviewed SI table crop"
        asset = user_directed_review_figure(path, raw, locator_id="Table S1", page=1)
        asset["source_bindings"][0]["locators"].update(document_role="si", source_sha256="d" * 64)
        asset["source_bindings"][0]["crop"] = {"asset_sha256": sha256(raw)}
        asset["provenance_bindings"] = [{"paper_id": "tirosh2006", "doi": "10.1021/cm052401p",
                                         "record_ids": ["tirosh-2006-method-a"]}]
        self.assertIsNone(user_directed_display_error(asset, "mattersyn-site", path))
        asset["source_bindings"][0]["locators"]["document_role"] = "private_render"
        self.assertIsNotNone(user_directed_display_error(asset, "mattersyn-site", path))

    def test_scoped_main_and_si_figure_crops_require_exact_source_and_render_provenance(self):
        raw = b"reviewed scoped figure crop"
        for path, locator_id, role in [
            ("assets/source-figures/tirosh2006/main-figure-1b-sem.png", "main-figure-1b-sem", "main"),
            ("assets/source-figures/tirosh2006/si-figure-s6.png", "Figure S6", "si"),
        ]:
            with self.subTest(path=path):
                asset = user_directed_review_figure(path, raw, locator_id=locator_id)
                asset["source_bindings"][0]["locators"].update(document_role=role, source_sha256="b" * 64)
                asset["source_bindings"][0]["crop"] = {
                    "asset_sha256": sha256(raw), "render_sha256": "c" * 64,
                    "crop_box": [10, 20, 110, 120],
                }
                asset["provenance_bindings"] = [{"paper_id": "tirosh2006", "doi": "10.1021/cm052401p",
                                                  "record_ids": ["tirosh-2006-method-a"]}]
                for repo, target in (("mattersyn-site", path), ("mattersyn", "recipe-atlas/static/" + path)):
                    self.assertIsNone(user_directed_display_error(asset, repo, target))
                for mutate in (
                    lambda a: a["rights"]["user_direction"].update(paper_id="other2006"),
                    lambda a: a["source_bindings"][0]["locators"].update(id="Figure 2"),
                    lambda a: a["source_bindings"][0]["locators"].update(document_role="main" if role == "si" else "si"),
                    lambda a: a["source_bindings"][0]["locators"].pop("source_sha256"),
                    lambda a: a["source_bindings"][0]["crop"].update(render_sha256="not-a-hash"),
                    lambda a: a["source_bindings"][0]["crop"].update(asset_sha256="d" * 64),
                    lambda a: a.update(provenance_bindings=[]),
                ):
                    changed = copy.deepcopy(asset)
                    mutate(changed)
                    self.assertIsNotNone(user_directed_display_error(changed, "mattersyn-site", path))
                for denied in (path.replace("figure", "page"), path.replace("source-figures", "page-renders")):
                    changed = copy.deepcopy(asset)
                    for delivery in changed["delivery_paths"]:
                        delivery["path"] = delivery["path"].replace(path, denied)
                    self.assertIsNotNone(user_directed_display_error(changed, "mattersyn-site", denied))
                for suffix in ("private", "page", "render", "full"):
                    denied = path.replace(".png", "-" + suffix + ".png")
                    changed = copy.deepcopy(asset)
                    for delivery in changed["delivery_paths"]:
                        delivery["path"] = delivery["path"].replace(path, denied)
                    changed["source_bindings"][0]["locators"]["id"] = Path(denied).stem
                    self.assertEqual(user_directed_display_error(changed, "mattersyn-site", denied),
                                     "user_directed_display_source_path_ineligible")

    def test_fu_unnumbered_si_tem_exception_is_limited_to_one_pinned_crop(self):
        path = "assets/source-figures/fu2009/si-figure-unnumbered-ag-tem.png"
        digest = "0a10f305552758ac9ca26a08d781b2dc6ddd880801abc21ee6ad94d3e90a1793"
        asset = user_directed_review_figure(path, b"synthetic metadata-only test", locator_id="si-figure-unnumbered-ag-tem", page=4)
        asset["asset_hash"] = digest
        asset["rights"]["user_direction"].update(
            asset_hash=digest, paper_id="fu2009-qd-ag-biotin-chemcomm-b816736b", doi="10.1039/b816736b"
        )
        binding = asset["source_bindings"][0]
        binding.update(doi="10.1039/b816736b", url="https://doi.org/10.1039/b816736b")
        binding["locators"].update(
            document_role="si",
            source_sha256="3b015713c56170ab602b9398b220d85abe1bc207c011cd054826861453f21033",
        )
        binding["crop"] = {
            "asset_sha256": digest,
            "render_sha256": "f813589910538969a23f7ab3a21bda304cd325bc01ea5935789dd3eeea589641",
            "crop_box": [340, 440, 1540, 1260],
        }
        asset["provenance_bindings"] = [{
            "paper_id": "fu2009-qd-ag-biotin-chemcomm-b816736b",
            "doi": "10.1039/b816736b",
            "record_ids": ["fu2009-qd-ag-biotin-chemcomm-b816736b-route"],
        }]
        for repo, target in (("mattersyn-site", path), ("mattersyn", "recipe-atlas/static/" + path)):
            self.assertIsNone(user_directed_display_error(asset, repo, target))
        self.assertFalse(asset["rights"]["copyright_permission_verified"])

        mutations = (
            lambda a: a["rights"]["user_direction"].update(paper_id="other2009"),
            lambda a: a["rights"]["user_direction"].update(doi="10.1000/other"),
            lambda a: a.update(asset_hash="a" * 64),
            lambda a: a["source_bindings"][0]["locators"].update(document_role="main"),
            lambda a: a["source_bindings"][0]["locators"].update(page=3),
            lambda a: a["source_bindings"][0]["locators"].update(id="Figure S4"),
            lambda a: a["source_bindings"][0]["locators"].update(source_sha256="a" * 64),
            lambda a: a["source_bindings"][0]["crop"].update(render_sha256="a" * 64),
            lambda a: a["source_bindings"][0]["crop"].update(crop_box=[340, 440, 1541, 1260]),
            lambda a: a["source_bindings"][0]["crop"].update(asset_sha256="a" * 64),
            lambda a: a.update(provenance_bindings=[]),
            lambda a: a["rights"].update(copyright_permission_verified=True),
        )
        for mutate in mutations:
            changed = copy.deepcopy(asset)
            mutate(changed)
            self.assertIsNotNone(user_directed_display_error(changed, "mattersyn-site", path))
        for denied in (
            "assets/source-figures/fu2009/si-figure-unnumbered-other.png",
            "assets/source-figures/other2009/si-figure-unnumbered-ag-tem.png",
            "assets/page-renders/fu2009/si-figure-unnumbered-ag-tem.png",
        ):
            changed = copy.deepcopy(asset)
            for delivery in changed["delivery_paths"]:
                delivery["path"] = delivery["path"].replace(path, denied)
            self.assertIsNotNone(user_directed_display_error(changed, "mattersyn-site", denied))

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


class ScopedNamedCropTests(unittest.TestCase):
    def test_main_scheme_and_table_require_exact_scoped_pins(self):
        cases = [
            ("assets/source-figures/routzahn2014/main-scheme-1.png", "routzahn2014-single-nc-exchange-nl4044289", "10.1021/nl4044289"),
            ("assets/source-figures/ko2010/main-table-1.png", "ko2010-ag2te-pbte-artificial-atoms-nl100571m", "10.1021/nl100571m"),
        ]
        for path, paper_id, doi in cases:
            with self.subTest(path=path):
                raw = b"synthetic exact reviewed crop"
                asset = user_directed_review_figure(path, raw, locator_id=Path(path).stem, page=2)
                asset["rights"]["user_direction"].update(paper_id=paper_id, doi=doi)
                binding = asset["source_bindings"][0]
                binding.update(doi=doi, url="https://doi.org/" + doi)
                binding["locators"].update(document_role="main", source_sha256="b" * 64)
                binding["crop"] = {"asset_sha256": sha256(raw), "render_sha256": "c" * 64,
                                   "crop_box": [10, 20, 110, 120]}
                asset["provenance_bindings"] = [{"paper_id": paper_id, "doi": doi, "record_ids": [paper_id + "-route"]}]
                for repo, target in (("mattersyn-site", path), ("mattersyn", "recipe-atlas/static/" + path)):
                    self.assertIsNone(user_directed_display_error(asset, repo, target))
                for mutate in (
                    lambda a: a["source_bindings"][0]["locators"].update(document_role="si"),
                    lambda a: a["source_bindings"][0]["locators"].update(id="main-figure-1"),
                    lambda a: a["source_bindings"][0]["locators"].pop("source_sha256"),
                    lambda a: a["source_bindings"][0]["crop"].update(render_sha256="bad"),
                    lambda a: a["source_bindings"][0]["crop"].update(asset_sha256="d" * 64),
                    lambda a: a.update(provenance_bindings=[]),
                    lambda a: a["rights"]["user_direction"].update(doi="10.1021/wrong"),
                ):
                    changed = copy.deepcopy(asset)
                    mutate(changed)
                    self.assertIsNotNone(user_directed_display_error(changed, "mattersyn-site", path))
                for denied in (
                    path.replace("main-", "si-"), path.replace("source-figures", "page-renders"),
                    path.replace("-1.png", "-1-private.png"), path.replace("-1.png", "-1-page.png"),
                    path.replace("-1.png", "-1-render.png"), path.replace("-1.png", "-1-full.png"),
                ):
                    changed = copy.deepcopy(asset)
                    for delivery in changed["delivery_paths"]:
                        delivery["path"] = delivery["path"].replace(path, denied)
                    changed["source_bindings"][0]["locators"]["id"] = Path(denied).stem
                    reason = user_directed_display_error(changed, "mattersyn-site", denied)
                    self.assertIsNotNone(reason)
                    if "source-figures" in denied:
                        self.assertEqual(reason, "user_directed_display_source_path_ineligible")



# BEGIN same-invocation opaque-image sanitation regressions; invented inputs only.
import os
import sys
from unittest.mock import patch
import public_release_guard as g
HERE = Path(__file__).resolve().parent

def opaque_config(path='assets/a.png', raw=b'PNG synthetic opaque fixture'):
    asset = {'asset_hash': g.sha256(raw), 'classification': 'authored_diagram', 'source_bindings': [],
             'delivery_paths': [{'repo': 'mattersyn-site', 'path': path, 'bytes': len(raw)}],
             'rights': {'status': 'not_source_derived', 'attribution': 'Invented test fixture'}}
    config = make_config(registry_assets=[asset])
    config['path_rules'][0]['content_class'] = 'site_asset'
    config['exact_blob_approval_classes'] = []
    return config, asset, allow_entry(path, raw, content_class='site_asset')


def within(function):
    return g._opaque_image_invocation(function)()


def entrypoint(source, config):
    raw = b'<p>Invented test entrypoint</p>'
    (source / 'index.html').write_bytes(raw)
    rule = copy.deepcopy(config['path_rules'][0])
    config['path_rules'][0]['path_glob'] = 'assets/*'
    rule.update(path_glob='index.html', content_class='site_code', rule_id='invented-entrypoint')
    config['path_rules'].append(rule)
    return allow_entry('index.html', raw, content_class='site_code')


class OpaqueMemoTests(unittest.TestCase):
    def setUp(self):
        g.sanitation_memo_state(clear=True, enabled=True)

    def tearDown(self):
        g.sanitation_memo_state(clear=True, enabled=True)

    def test_opaque_cache_disabled_outside_single_invocation(self):
        config, _, _ = opaque_config()
        for _ in range(2): g._sanitize_content('assets/a.png', b'fixture', config, 'mattersyn-site')
        self.assertEqual(g.sanitation_memo_state()['entries'], 0)
        self.assertEqual(g.sanitation_memo_state()['hits'], 0)

    def test_one_scope_reuses_exact_opaque_bytes_and_discards_entries(self):
        config, _, _ = opaque_config()
        def run():
            expected = g._sanitize_content_uncached('assets/a.png', b'fixture', config, 'mattersyn-site')
            self.assertEqual(expected, g._sanitize_content('assets/a.png', b'fixture', config, 'mattersyn-site'))
            self.assertEqual(expected, g._sanitize_content('assets/a.png', b'fixture', config, 'mattersyn-site'))
            state = g.sanitation_memo_state()
            self.assertEqual((state['entries'], state['misses'], state['hits'], state['retained_output_bytes']), (1, 1, 1, 0))
        within(run)
        self.assertEqual(g.sanitation_memo_state()['entries'], 0)

    def test_distinct_invocations_do_not_share_opaque_results(self):
        config, _, _ = opaque_config()
        for _ in range(2): within(lambda: g._sanitize_content('a.png', b'fixture', config, 'mattersyn-site'))
        state = g.sanitation_memo_state()
        self.assertEqual((state['entries'], state['hits'], state['misses']), (0, 0, 2))

    def test_copied_context_after_export_lifetime_cannot_admit_or_reuse(self):
        from contextvars import copy_context
        saved = []
        def run():
            saved.append(copy_context())
            g._sanitize_content('a.png', b'fixture')
        within(run)
        before = g.sanitation_memo_state()
        for _ in range(2): saved[0].run(g._sanitize_content, 'a.png', b'fixture')
        self.assertEqual(g.sanitation_memo_state(), before)
        self.assertEqual(g.sanitation_memo_state()['entries'], 0)
        self.assertEqual(g._OPAQUE_SANITATION_ACTIVE, set())

    def test_exception_clears_scope_and_only_its_entries(self):
        g._sanitize_content('a.json', b'{}')
        def run():
            g._sanitize_content('a.png', b'fixture')
            raise RuntimeError('invented failure')
        with self.assertRaisesRegex(RuntimeError, 'invented failure'): within(run)
        self.assertIsNone(g._OPAQUE_SANITATION_SCOPE.get())
        self.assertEqual(g.sanitation_memo_state()['entries'], 1)

    def test_owner_exit_before_copied_context_store_leaves_no_dead_entry(self):
        from contextvars import copy_context
        import inspect
        import threading
        paused, resume = threading.Event(), threading.Event()
        errors, workers = [], []
        lines, first_line = inspect.getsourcelines(g._sanitize_content)
        target = first_line + next(i for i, line in enumerate(lines) if 'value = (unchanged, retained' in line)
        code = g._sanitize_content.__code__
        def trace(frame, event, arg):
            if frame.f_code is code and event == 'line' and frame.f_lineno == target:
                paused.set()
                if not resume.wait(5): raise RuntimeError('invented race timeout')
                sys.settrace(None)
            return trace
        def consume(context):
            try:
                sys.settrace(trace)
                context.run(g._sanitize_content, 'a.png', b'fixture')
            except BaseException as error: errors.append(repr(error))
            finally: sys.settrace(None)
        def owner():
            worker = threading.Thread(target=consume, args=(copy_context(),))
            workers.append(worker); worker.start()
            self.assertTrue(paused.wait(5))
        try:
            within(owner)
            self.assertEqual(g._OPAQUE_SANITATION_ACTIVE, set())
        finally:
            resume.set()
            for worker in workers: worker.join(5)
        self.assertTrue(all(not worker.is_alive() for worker in workers))
        self.assertEqual(errors, [])
        self.assertEqual(g.sanitation_memo_state()['entries'], 0)

    def test_nested_scope_keeps_outer_entry_until_outer_exit(self):
        def outer():
            g._sanitize_content('a.png', b'fixture')
            within(lambda: g._sanitize_content('a.png', b'fixture'))
            self.assertEqual(g.sanitation_memo_state()['entries'], 1)
            g._sanitize_content('a.png', b'fixture')
            self.assertEqual(g.sanitation_memo_state()['hits'], 1)
        within(outer)
        self.assertEqual(g.sanitation_memo_state()['entries'], 0)

    def test_byte_path_repo_code_and_policy_pins_separate_keys(self):
        config, _, _ = opaque_config()
        def run():
            for path, raw, repo in [('a.png', b'aaa', 'mattersyn-site'), ('a.png', b'bbb', 'mattersyn-site'),
                                   ('b.png', b'aaa', 'mattersyn-site'), ('a.png', b'aaa', 'mattersyn')]:
                g._sanitize_content(path, raw, config, repo)
            config['policy_sha256'] = '1' * 64
            g._sanitize_content('a.png', b'aaa', config, 'mattersyn-site')
            config['asset_rights_registry_sha256'] = '2' * 64
            g._sanitize_content('a.png', b'aaa', config, 'mattersyn-site')
            with patch.object(g, '_SANITATION_GUARD_VERSION', 'different code'):
                g._sanitize_content('a.png', b'aaa', config, 'mattersyn-site')
            self.assertEqual(g.sanitation_memo_state()['misses'], 7)
        within(run)

    def test_pdf_disguise_and_every_secret_predicate_match_uncached(self):
        samples = [b' \n%PDF-1.7 synthetic', b'-----BEGIN ' + b'PRIVATE KEY-----',
                   b'ghp_' + b'A' * 40, b'sk-' + b'B' * 40, b'AKIA' + b'C' * 16,
                   b'xoxb-' + b'D' * 25]
        def run():
            for i, raw in enumerate(samples):
                path = str(i) + '.png'
                expected = g._sanitize_content_uncached(path, raw)
                self.assertIsNone(expected[0])
                self.assertEqual(expected, g._sanitize_content(path, raw))
                self.assertEqual(expected, g._sanitize_content(path, raw))
        within(run)

    def test_ordered_secret_patterns_flags_and_in_place_changes_invalidate(self):
        raw = b'UPPER fixture'; config, _, _ = opaque_config()
        patterns = {'one': re.compile(b'lower'), 'two': re.compile(b'other')}
        with patch.object(g, '_SECRET_PATTERNS', patterns):
            def run():
                first = g._sanitize_content('a.png', raw, config)
                self.assertIsNotNone(first[0])
                patterns['one'] = re.compile(b'upper', re.I)
                second = g._sanitize_content('a.png', raw, config)
                self.assertEqual(second[1], 'credential_pattern_one')
                patterns['two'] = re.compile(b'upper', re.I)
                g._SECRET_PATTERNS = dict(reversed(list(patterns.items())))
                third = g._sanitize_content('a.png', raw, config)
                self.assertEqual(third[1], 'credential_pattern_two')
                self.assertEqual(g.sanitation_memo_state()['misses'], 3)
            within(run)

    def test_changed_suffix_sets_or_text_filename_bypass_opaque_cache(self):
        def run():
            g._sanitize_content('a.png', b'normal')
            with patch.object(g, 'IMAGE_SUFFIXES', set()):
                self.assertEqual(g._sanitize_content('a.png', b'normal')[1], 'unclassified_binary_content')
            with patch.object(g, 'TEXT_SUFFIXES', g.TEXT_SUFFIXES | {'.png'}):
                self.assertEqual(g._sanitize_content('a.png', b'\xff')[1], 'invalid_text_encoding')
            with patch.object(g, 'TEXT_FILENAMES', g.TEXT_FILENAMES | {'a.png'}):
                self.assertEqual(g._sanitize_content('a.png', b'\xff')[1], 'invalid_text_encoding')
            self.assertEqual(g.sanitation_memo_state()['entries'], 1)
        within(run)

    def test_raced_hit_pattern_change_cannot_reuse_old_safe_result(self):
        from collections import OrderedDict
        patterns = {'initial': re.compile(b'not-present')}
        class RacedCache(OrderedDict):
            armed = False
            def get(self, key, default=None):
                if self.armed:
                    self.armed = False
                    patterns['sentinel'] = re.compile(b'SENTINEL')
                return super().get(key, default)
        cache = RacedCache()
        with patch.object(g, '_SECRET_PATTERNS', patterns), patch.object(g, '_SANITATION_MEMO', cache):
            def run():
                self.assertEqual(g._sanitize_content('a.png', b'SENTINEL')[1], 'unchanged')
                cache.armed = True
                self.assertEqual(g._sanitize_content('a.png', b'SENTINEL')[1], 'credential_pattern_sentinel')
            within(run)

    def test_raced_miss_pattern_change_is_not_stored_under_old_context(self):
        patterns = {'initial': re.compile(b'not-present')}
        original = g._sanitize_content_uncached
        def changed(path, raw, config, repo):
            patterns['sentinel'] = re.compile(b'SENTINEL')
            return original(path, raw, config, repo)
        with patch.object(g, '_SECRET_PATTERNS', patterns), patch.object(g, '_sanitize_content_uncached', side_effect=changed):
            def run():
                self.assertEqual(g._sanitize_content('a.png', b'SENTINEL')[1], 'credential_pattern_sentinel')
                self.assertEqual(g.sanitation_memo_state()['entries'], 0)
            within(run)

    def test_svg_and_structure_still_uncached(self):
        def run():
            for path in ('a.svg', 'a.cif', 'a.sdf', 'a.xyz'):
                for _ in range(2): g._sanitize_content(path, b'invented fixture')
            self.assertEqual(g.sanitation_memo_state()['entries'], 0)
        within(run)

    def test_mutated_stats_do_not_change_cached_result_and_limits_hold(self):
        def run():
            with patch.object(g, '_SANITATION_MEMO_MAX_ENTRIES', 2):
                for i in range(3): g._sanitize_content(str(i) + '.png', b'fixture')
                result = g._sanitize_content('2.png', b'fixture')
                result[2]['source_text_fields_removed'] = 100
                self.assertEqual(g._sanitize_content('2.png', b'fixture')[2]['source_text_fields_removed'], 0)
                self.assertEqual(g.sanitation_memo_state()['entries'], 2)
                self.assertEqual(g.sanitation_memo_state()['retained_output_bytes'], 0)
        within(run)

    def test_rule_review_identity_and_rights_gates_remain_live(self):
        path, raw = 'assets/a.png', b'PNG synthetic opaque fixture'
        config, asset, entry = opaque_config(path, raw)
        def run():
            self.assertEqual(g.validate_allowlist_entry(path, raw, entry, config, 'mattersyn-site'), (raw, None))
            self.assertEqual(g.validate_allowlist_entry(path, raw, entry, config, 'mattersyn-site'), (raw, None))
            self.assertEqual(g.sanitation_memo_state()['hits'], 1)
            asset['rights']['status'] = 'withheld'
            self.assertEqual(g.validate_allowlist_entry(path, raw, entry, config, 'mattersyn-site')[1], 'asset_rights_withheld')
            asset['rights']['status'] = 'not_source_derived'
            entry['reviewer'] = ''
            self.assertEqual(g.validate_allowlist_entry(path, raw, entry, config, 'mattersyn-site')[1], 'release_entry_review_incomplete')
            entry['reviewer'] = 'synthetic-test-reviewer'
            entry['sha256'] = 'f' * 64
            self.assertEqual(g.validate_allowlist_entry(path, raw, entry, config, 'mattersyn-site')[1], 'source_file_hash_or_size_mismatch')
            entry['sha256'] = g.sha256(raw)
            config['path_rules'][0]['decision'] = 'omit'
            self.assertIsNotNone(g.validate_allowlist_entry(path, raw, entry, config, 'mattersyn-site')[1])
        within(run)

    def test_source_crop_provenance_is_checked_after_cache_hit(self):
        path, raw = 'assets/figures/example/figure-2.png', b'synthetic source figure'
        asset = user_directed_figure(path, raw)
        config = make_config(registry_assets=[asset]); config['exact_blob_approval_classes'] = []
        config['path_rules'][0]['content_class'] = 'site_asset'
        def run():
            self.assertEqual(g.history_project('mattersyn-site', path, raw, config)['action'], 'allow')
            self.assertEqual(g.history_project('mattersyn-site', path, raw, config)['action'], 'allow')
            asset['source_bindings'] = []
            self.assertEqual(g.history_project('mattersyn-site', path, raw, config)['action'], 'omit')
        within(run)

    def test_full_export_receipts_and_files_equal_disabled_cache(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            top = Path(td); source = top / 'source'; source.mkdir()
            path, raw = 'assets/a.png', b'PNG synthetic opaque fixture'
            config, _, entry = opaque_config(path, raw)
            (source / 'assets').mkdir(); (source / path).write_bytes(raw)
            allow = make_allowlist([entry, entrypoint(source, config)]); allow['asset_rights_registry_sha256'] = config['asset_rights_registry_sha256']
            al = top / 'allowlist.json'; al.write_text(json.dumps(allow), encoding='utf-8')
            g.sanitation_memo_state(enabled=False)
            cold = g.export_public_release(source, top / 'cold', al, config, 'mattersyn-site', top / 'cold-manifest.json', top / 'cold-report.json')
            g.sanitation_memo_state(clear=True, enabled=True)
            warm = g.export_public_release(source, top / 'warm', al, config, 'mattersyn-site', top / 'warm-manifest.json', top / 'warm-report.json')
            self.assertEqual(cold, warm)
            self.assertEqual((top / 'cold-manifest.json').read_bytes(), (top / 'warm-manifest.json').read_bytes())
            self.assertEqual((top / 'cold-report.json').read_bytes(), (top / 'warm-report.json').read_bytes())
            self.assertEqual((top / 'cold' / path).read_bytes(), (top / 'warm' / path).read_bytes())
            self.assertEqual((g.sanitation_memo_state()['hits'], g.sanitation_memo_state()['misses']), (1, 1))
            self.assertEqual(g.sanitation_memo_state()['entries'], 0)

    def test_export_stage_rereads_same_size_mutated_bytes(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            top = Path(td); source = top / 'source'; source.mkdir()
            path, raw = 'assets/a.png', b'PNG synthetic opaque fixture'
            config, _, entry = opaque_config(path, raw)
            (source / 'assets').mkdir(); (source / path).write_bytes(raw)
            allow = make_allowlist([entry, entrypoint(source, config)]); allow['asset_rights_registry_sha256'] = config['asset_rights_registry_sha256']
            al = top / 'allowlist.json'; al.write_text(json.dumps(allow), encoding='utf-8')
            actual = g.validate_stage
            def tamper(root, *args):
                target = Path(root) / path; stat = target.stat()
                target.write_bytes(b'Z' + raw[1:]); os.utime(target, ns=(stat.st_atime_ns, stat.st_mtime_ns))
                return actual(root, *args)
            with patch.object(g, 'validate_stage', side_effect=tamper):
                _, report = g.export_public_release(source, top / 'out', al, config, 'mattersyn-site', top / 'manifest.json', top / 'report.json')
            self.assertEqual(report['status'], 'failed')
            self.assertEqual(report['failures'][0]['reason_code'], 'staged_sha256_mismatch')
            self.assertEqual(g.sanitation_memo_state()['entries'], 0)

# END same-invocation opaque-image sanitation regressions.

if __name__ == "__main__":
    unittest.main()


# BEGIN exact opaque-image credential-prefix equivalence tests; invented bytes only.
class OpaqueCredentialPrefixTests(unittest.TestCase):
    def setUp(self):
        g.sanitation_memo_state(clear=True, enabled=True)

    def tearDown(self):
        g.sanitation_memo_state(clear=True, enabled=True)

    def baseline(self, path, raw, config=None):
        # Mutated/unknown helper must take the exact old regex path.
        with patch.object(g, '_secret_literal_prefix_absent', None):
            return g._sanitize_content_uncached(path, raw, config)

    def compare(self, raw, path='assets/invented.png', config=None):
        expected = self.baseline(path, raw, config)
        actual = g._sanitize_content_uncached(path, raw, config)
        self.assertEqual(actual, expected)
        return actual

    def samples(self):
        samples = []
        for letter in b'pousr':
            samples.append(('github_token', b'gh' + bytes([letter]) + b'_' + b'A' * 40))
        samples.append(('github_token', b'github_pat_' + b'A' * 60))
        for optional in (b'', b'proj-', b'svcacct-'):
            samples.append(('openai_key_shape', b'sk-' + optional + b'B' * 40))
        for prefix in (b'AKIA', b'ASIA'):
            samples.append(('aws_key_shape', prefix + b'C' * 16))
        for kind in (b'', b'RSA ', b'EC ', b'OPENSSH ', b'DSA '):
            samples.append(('private_key_header', b'-----BEGIN ' + kind + b'PRIVATE KEY-----'))
        for letter in b'baprs':
            samples.append(('slack_token_shape', b'xox' + bytes([letter]) + b'-' + b'D' * 25))
        return samples

    def test_every_pattern_branch_positive_and_binary_boundaries(self):
        for name, payload in self.samples():
            for prefix in (b'', b'\x00\xff ', b'PNG\r\n'):
                with self.subTest(name=name, prefix=prefix):
                    result = self.compare(prefix + payload + b'\x00')
                    self.assertIsNone(result[0])
                    self.assertEqual(result[1], 'credential_pattern_' + name)

    def test_case_near_misses_NUL_and_binary_negatives_match(self):
        samples = [b'', bytes(range(256)) * 8, b'\x00\xffGHP_' + b'A' * 40,
                   b'SK-' + b'B' * 40, b'akia' + b'C' * 16,
                   b'XOXB-' + b'D' * 25, b's\x00k-' + b'B' * 40,
                   b'ghp_' + b'A' * 29, b'github_pat_' + b'A' * 49,
                   b'-----begin PRIVATE KEY-----', b'wordsk-' + b'B' * 40]
        for raw in samples:
            with self.subTest(raw_bytes=len(raw)):
                self.compare(raw)

    def test_known_absence_is_only_a_necessary_condition(self):
        for name, pattern in g._SECRET_PATTERNS.items():
            if name == 'private_key_header':
                self.assertFalse(g._secret_literal_prefix_absent(name, pattern, b'clean'))
            else:
                self.assertTrue(g._secret_literal_prefix_absent(name, pattern, b'\x00invented clean\xff'))
        for name, raw in self.samples():
            self.assertFalse(g._secret_literal_prefix_absent(name, g._SECRET_PATTERNS[name], raw))
        # A present prefix does not approve a payload or replace regex matching.
        self.compare(b'gh, github_pat_, sk-, AKIA, ASIA, xox')

    def test_all_patterns_keep_original_first_failure_order(self):
        raw = b' '.join(payload for _, payload in reversed(self.samples()))
        self.assertEqual(self.compare(raw)[1], 'credential_pattern_github_token')
        with patch.object(g, '_SECRET_PATTERNS', dict(reversed(list(g._SECRET_PATTERNS.items())))):
            self.assertEqual(self.compare(raw)[1], 'credential_pattern_slack_token_shape')

    def test_unknown_expression_or_ignorecase_flags_fall_back(self):
        for pattern, raw in ((re.compile(b'INVENTED', re.I), b'invented'),
                             (re.compile(g._SECRET_PATTERNS['openai_key_shape'].pattern, re.I), b'SK-' + b'B' * 40)):
            patterns = dict(g._SECRET_PATTERNS)
            patterns['openai_key_shape'] = pattern
            with patch.object(g, '_SECRET_PATTERNS', patterns):
                self.assertFalse(g._secret_literal_prefix_absent('openai_key_shape', pattern, raw))
                self.assertEqual(self.compare(raw)[1], 'credential_pattern_openai_key_shape')

    def test_equal_recompiled_pattern_identity_falls_back(self):
        original = g._SECRET_PATTERNS['github_token']
        re.purge()
        other = re.compile(original.pattern, original.flags)
        self.assertIsNot(other, original)
        patterns = dict(g._SECRET_PATTERNS); patterns['github_token'] = other
        with patch.object(g, '_SECRET_PATTERNS', patterns):
            self.assertFalse(g._secret_literal_prefix_absent('github_token', other, b'clean'))
            self.compare(b'ghp_' + b'A' * 40)

    def test_helper_identity_code_and_defaults_mutations_fall_back(self):
        raw = b'ghp_' + b'A' * 40
        expected = self.baseline('x.png', raw)
        original = g._secret_literal_prefix_absent
        with patch.object(g, '_secret_literal_prefix_absent', lambda *args: True):
            self.assertEqual(g._sanitize_content_uncached('x.png', raw), expected)
        saved_code = original.__code__
        try:
            original.__code__ = (lambda *args: True).__code__
            self.assertEqual(g._sanitize_content_uncached('x.png', raw), expected)
        finally:
            original.__code__ = saved_code
        saved_defaults = original.__defaults__
        try:
            original.__defaults__ = ((),)
            self.assertEqual(g._sanitize_content_uncached('x.png', raw), expected)
        finally:
            original.__defaults__ = saved_defaults

    def test_unknown_matcher_and_key_types_preserve_search_and_error_order(self):
        calls = []
        class Matcher:
            def search(self, raw):
                calls.append(raw)
                return False
        class UnusualName(str):
            __hash__ = str.__hash__
            def __eq__(self, other):
                raise AssertionError('Unknown key comparison must not run')
        patterns = {UnusualName('github_token'): Matcher()}
        with patch.object(g, '_SECRET_PATTERNS', patterns):
            result = g._sanitize_content_uncached('x.png', b'invented')
            self.assertIsNotNone(result[0]); self.assertEqual(calls, [b'invented'])
        class Broken:
            def search(self, raw):
                raise RuntimeError('invented matcher error')
        with patch.object(g, '_SECRET_PATTERNS', {'unknown': Broken()}):
            with self.assertRaisesRegex(RuntimeError, 'invented matcher error'):
                g._sanitize_content_uncached('x.png', b'invented')
            self.assertEqual(g._sanitize_content_uncached('x.png', b'%PDF-1.7')[1],
                             'original_source_document_or_archive')

    def test_nonimages_and_text_svg_and_unusual_types_keep_old_path(self):
        for path, raw in [('x.txt', b'invented'), ('x.svg', b'<svg/>'), ('x.json', b'{}'),
                          ('x.bin', b'\x00invented'), ('x.png', bytearray(b'invented'))]:
            with self.subTest(path=path): self.compare(raw, path)
        raw = b'ghp_' + b'A' * 40
        for key, replacement in (('_is_image', lambda path: False),
                                 ('TEXT_SUFFIXES', set(g.TEXT_SUFFIXES) | {'.png'}),
                                 ('TEXT_FILENAMES', set(g.TEXT_FILENAMES) | {'x.png'})):
            with patch.object(g, key, replacement): self.compare(raw, 'x.png')

    def test_R4_context_pattern_and_live_mutation_invalidation_still_hold(self):
        raw = b'invented binary'; config, _, _ = opaque_config('x.png', raw)
        def run():
            self.assertIsNotNone(g._sanitize_content('x.png', raw, config)[0])
            self.assertIsNotNone(g._sanitize_content('x.png', raw, config)[0])
            changed = dict(g._SECRET_PATTERNS); changed['new'] = re.compile(b'invented')
            with patch.object(g, '_SECRET_PATTERNS', changed):
                self.assertEqual(g._sanitize_content('x.png', raw, config)[1], 'credential_pattern_new')
            config['policy_sha256'] = '1' * 64
            self.assertIsNotNone(g._sanitize_content('x.png', raw, config)[0])
        within(run)
        self.assertEqual(g.sanitation_memo_state()['entries'], 0)

    def test_deterministic_invented_binary_fuzz_equivalence(self):
        import random
        rng = random.Random(372914)
        positives = [raw for _, raw in self.samples()]
        for index in range(160):
            raw = bytes(rng.randrange(256) for _ in range(rng.randrange(0, 2048)))
            if index % 3 == 0:
                at = rng.randrange(len(raw) + 1)
                raw = raw[:at] + b'\x00' + positives[index % len(positives)] + b'\x00' + raw[at:]
            self.compare(raw)
# END exact opaque-image credential-prefix equivalence tests.


class OpaqueCredentialInLoopMutationTests(unittest.TestCase):
    def test_earlier_unknown_search_mutations_cannot_disable_later_credential_search(self):
        raw = b'ghp_' + b'A' * 40  # Invented fixture only.
        for mutation in ('code', 'defaults', 'identity'):
            with self.subTest(mutation=mutation):
                original = g._secret_literal_prefix_absent
                old_code, old_defaults = original.__code__, original.__defaults__
                github = g._SECRET_PATTERNS['github_token']
                calls = []
                class Matcher:
                    def search(self, payload):
                        calls.append(payload)
                        if mutation == 'code':
                            original.__code__ = (lambda *args: True).__code__
                        elif mutation == 'defaults':
                            # Keep a known pattern but lie about its necessary prefix.
                            original.__defaults__ = ((('github_token', github, github.pattern,
                                github.flags, (b'never-in-invented-payload',)),),)
                        else:
                            g._secret_literal_prefix_absent = lambda *args: True
                        return False
                try:
                    with patch.object(g, '_SECRET_PATTERNS', {'unknown_before': Matcher(), 'github_token': github}):
                        result = g._sanitize_content_uncached('invented.png', raw)
                    self.assertEqual(result, (None, 'credential_pattern_github_token', {}))
                    self.assertEqual(calls, [raw])
                finally:
                    original.__code__, original.__defaults__ = old_code, old_defaults
                    g._secret_literal_prefix_absent = original
