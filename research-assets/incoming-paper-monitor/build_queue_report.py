"""Render a private static work-queue snapshot without scanning or changing state."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from html import escape
import json
import os
from pathlib import Path
import time
from urllib.parse import quote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import monitor

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent
DEFAULT_BIBLIOGRAPHY = PROJECT / "research-assets/corpus-20260917/public-bibliographic-manifest.json"
DEFAULT_BASELINE = PROJECT / "recipe-atlas/data/inventory-summary.json"
DEFAULT_RELEASE = HERE / "latest-publication.json"
STAGE_NAMES = {"read": "Source reading", "extract": "Data extraction", "audit": "Scientific audit", "integrate": "Website integration", "publish": "Publication"}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def human_time(value):
    if not value:
        return "Not recorded"
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    try:
        return stamp.astimezone(ZoneInfo("America/Chicago")).strftime("%b %d, %Y · %I:%M:%S %p %Z")
    except ZoneInfoNotFoundError:
        return stamp.astimezone(timezone.utc).strftime("%b %d, %Y · %H:%M:%S UTC")


def title_index(bibliography):
    result = {}
    for paper in bibliography.get("papers", []):
        doi = monitor.normalized_doi(paper.get("doi", ""))
        title = paper.get("title")
        if doi and isinstance(title, str) and title.strip():
            result[doi] = {"title": title.strip(), "year": paper.get("year"),
                           "origin": paper.get("titleMetadata", {}).get("origin", "local_bibliographic_metadata"),
                           "confidence": paper.get("titleMetadata", {}).get("confidence", "not_recorded")}
    return result


def group_snapshot(ledger, key, titles, now, rankings=None):
    group = ledger["groups"][key]
    files = [ledger["files"][name] for name in group["files"]]
    candidates = group.get("doi_candidates", [])
    title_match = next((titles[doi] for doi in candidates if doi in titles), None)
    checkpoint = group["review"].get("checkpoint", {})
    title = checkpoint.get("title") or (title_match or {}).get("title")
    mains = sum(item["role"] == "main" for item in files)
    si = sum(item["role"] == "si" for item in files)
    source_stable = monitor.eligible(ledger, key, now)
    priority = monitor.priority_state(ledger, key, rankings=rankings)
    default_ready = monitor.claimable(ledger, key, now, rankings=rankings)
    stable_without_main = monitor.eligible(ledger, key, now, require_main=False)
    readiness = "Ready from stored observations" if default_ready else (
        "Main missing; explicit scoped review required" if not mains and stable_without_main else
        "Priority screening pending or stale" if source_stable and not priority["eligible_for_selection"] else "Stability or completeness hold")
    hashes = {item.get("sha256") for item in files if item.get("sha256")}
    return {"group_id": key, "queue_order": group["queue_order"], "doi_candidates": candidates,
            "title": title, "title_is_candidate_metadata": not bool(checkpoint.get("title")),
            "title_metadata": title_match, "sources": sorted({item.get("source_id", "incoming") for item in files}),
            "file_copies": len(files), "main_candidates": mains, "si_candidates": si,
            "other_role_candidates": len(files)-mains-si, "confirmed_unique_content_hashes": len(hashes),
            "unhashed_copies": sum(not item.get("sha256") for item in files),
            "ambiguous_role_copies": sum(bool(item.get("role_ambiguous")) for item in files),
            "generation": group["generation"], "needs_recheck": group["needs_recheck"],
            "review_status": group["review"]["status"], "readiness": readiness, "default_ready": default_ready,
            "source_stable": source_stable, "priority": priority,
            "milestones": group["review"].get("milestones", {}), "checkpoint": checkpoint,
            "review_updated_at": group["review"].get("updated_at"),
            "files": [{"key": name, "path": str(monitor.file_path(ledger, name)),
                       "role_candidate": ledger["files"][name]["role"], "sha256": ledger["files"][name].get("sha256")}
                      for name in group["files"]]}


def evidence_closed(group):
    if group.get("alias_of") or group["needs_recheck"] or group["review"]["status"] not in monitor.TERMINAL_STATUSES:
        return False
    if group.get("fingerprint", {}).get("generation") != group["generation"]:
        return False
    stages = group["review"].get("milestones", {})
    return all(stages.get(stage, {}).get("status") in {"complete", "not_applicable"}
               and stages[stage].get("generation") == group["generation"] and stages[stage].get("evidence")
               for stage in monitor.MILESTONES)


def build_snapshot(ledger, titles, baseline, release, now=None, ledger_sha256=None):
    now = time.time_ns() if now is None else now
    pending = monitor.queued(ledger)
    rankings = monitor.priority_index(ledger)
    claims = monitor.active_claims(ledger)
    active_keys = {claim["group_id"] for claim in claims}
    waiting = [key for key in pending if key not in active_keys]
    active_papers = [group_snapshot(ledger, claim["group_id"], titles, now, rankings) for claim in claims]
    active = active_papers[0] if active_papers else None
    groups = [group for group in ledger["groups"].values() if not group.get("alias_of")]
    summary = monitor.summary(ledger, now)
    counts = baseline.get("summary", {})
    no_main = [key for key in pending if not any(ledger["files"][name]["role"] == "main" for name in ledger["groups"][key]["files"])]
    return {"report_schema": "mattersyn-private-queue-snapshot/2", "generated_at": monitor.iso(now),
            "static_snapshot": True, "network_used": False, "source_files_scanned": False, "ledger_changed": False,
            "ledger_sha256": ledger_sha256, "ledger_last_scan_at": ledger.get("last_scan_at"),
            "counts": {**summary, "active_review_claims": len(active_papers), "waiting_review_scopes": len(waiting),
                       "evidence_closed_new_queue_scopes": sum(evidence_closed(group) for group in groups),
                       "screened_no_recipe_scopes": sum(evidence_closed(group) and group["review"]["status"] == "no_synthesis_recipe" for group in groups),
                       "fully_curated_queue_scopes": sum(evidence_closed(group) and group["review"]["status"] == "complete" for group in groups),
                       "historical_terminal_scopes_requiring_recheck": sum(group["review"]["status"] in monitor.TERMINAL_STATUSES and not evidence_closed(group) for group in groups),
                       "pending_main_missing_scopes": len(no_main),
                       "default_ready_pending_scopes": sum(monitor.claimable(ledger, key, now, rankings=rankings) for key in pending)},
            "active": active, "active_papers": active_papers, "batch": ledger.get("current_batch"),
            "selection_policy": {k: v for k, v in ledger.get("selection_policy", {"mode": "arrival_order"}).items() if k != "rankings"},
            "next_12_waiting": [group_snapshot(ledger, key, titles, now, rankings) for key in waiting[:12]],
            "main_missing_examples": [group_snapshot(ledger, key, titles, now, rankings) for key in no_main[:4]],
            "published_baseline": {"source": str(DEFAULT_BASELINE), "inventory_version": baseline.get("inventory_version"),
                "release_status": release.get("status"), "version": release.get("public_live_version"),
                "published_at": release.get("published_at"), "public_url": release.get("public_url"),
                "material_hubs": counts.get("public_material_hubs"), "synthesis_route_variants": counts.get("synthesis_route_variant_records"),
                "canonical_records": counts.get("canonical_records"), "benchmark_rows": counts.get("published_benchmark_rows"),
                "formal_full_main_and_si_reviews": counts.get("formal_full_main_and_matched_si_reviews")},
            "interpretation": ["This is a static, private ledger snapshot; it does not scan folders or run a reviewer.",
                "Resume the fixed batch of up to five papers before claiming another. Each paper has separate review and audit evidence; batch membership is not live worker telemetry.",
                "No-recipe screening exclusions are separate from full scientific curation. Stable filenames and source hashes preserve main/SI provenance; changed evidence reopens a scope.",
                "Several individually validated papers may share a public deployment; pending members retain their own incomplete milestones.",
                "Evidence-priority scores are automated screening candidates, not verified recipes or sample-coordinate pairs. Source changes invalidate scheduling scores; original arrival order is retained for ties and provenance.",
                "Readiness uses saved file observations, not a new filesystem check. A new scan is required before acting on changed sources.",
                "Titles and DOI links are candidates from existing local metadata unless recorded in the active review checkpoint.",
                "Review scopes, document copies and DOI candidates are not verified unique-paper, synthesized-material or recipe totals.",
                "Past publication is separate from this queue's evidence-gated completion. Existing papers require completeness re-audit.",
                "Main-missing scopes are held for explicit limited-scope review, not discarded or counted as fully read papers."],
            "regenerate_command": "python -X utf8 build_queue_report.py"}


def fmt(value):
    return f"{value:,}" if isinstance(value, int) else "Not recorded" if value is None else str(value)


def e(value):
    return escape(str(value), quote=True)


def local_link(path, output_dir):
    try:
        return quote(os.path.relpath(Path(path), output_dir).replace(os.sep, "/"), safe="/:._-")
    except ValueError:
        return Path(path).as_uri()


def render_html(data, output_dir):
    counts, active, baseline = data["counts"], data["active"], data["published_baseline"]
    priority_mode = data.get("selection_policy", {}).get("mode", "arrival_order")
    priority_label = "Synthesis and structure evidence (automated candidates)" if priority_mode == "evidence_richness" else "Original arrival order"
    card_values = [("Active batch papers", counts["active_review_claims"], "Separate claims; up to five per batch"),
                   ("Waiting scopes", counts["waiting_review_scopes"], "Candidates awaiting end-to-end review"),
                   ("Scopes with final dispositions", counts["evidence_closed_new_queue_scopes"], f'{counts["fully_curated_queue_scopes"]} fully curated; {counts["screened_no_recipe_scopes"]} no-recipe screening skips; other exclusions tracked separately'),
                   ("Document copies", counts["present_files"], "Both source folders · duplicates retained")]
    cards = "".join(f'<article class="metric"><span>{e(label)}</span><strong>{fmt(value)}</strong><small>{e(note)}</small></article>' for label, value, note in card_values)
    stages = ""
    active_sections = []
    for active in data.get("active_papers", [active] if active else []):
        stages = ""
        cp = active["checkpoint"]
        for name in monitor.MILESTONES:
            record = active["milestones"].get(name, {"status": "pending"})
            status = record.get("status", "pending")
            valid = record.get("generation") == active["generation"]
            suffix = " · prior generation" if status != "pending" and not valid else ""
            links = "".join(f'<li><a href="{local_link(ref, output_dir)}">{e(Path(ref).name)}</a></li>' for ref in record.get("evidence", []))
            evidence = f'<details><summary>Evidence ({len(record.get("evidence", []))})</summary><ul>{links}</ul></details>' if links else '<small>No completion evidence recorded.</small>'
            stages += f'<article class="stage"><span class="badge {e(status)}">{e(status.replace("_", " ")+suffix)}</span><h3>{e(STAGE_NAMES[name])}</h3><p>{e(record.get("note", "No checkpoint recorded for this stage."))}</p>{evidence}</article>'
        counters = [("Main pages reviewed", len(cp.get("main_pages_text_reviewed", []))),
                    ("Private typed drafts", cp.get("private_typed_draft_records")),
                    ("Figure / table crops", (cp.get("original_figures", 0) + cp.get("original_tables", 0))),
                    ("Public canonical imports", cp.get("canonical_records_created"))]
        counter_html = "".join(f'<div><strong>{fmt(value)}</strong><span>{e(label)}</span></div>' for label, value in counters)
        work_rows = "".join(f'<article><div><strong>{e(item.get("label", "Unnamed checkpoint task"))}</strong><span class="badge {e(item.get("status", "pending"))}">{e(item.get("status", "pending").replace("_", " "))}</span></div><p>{e(item.get("scope", "Scope not recorded."))}</p></article>' for item in cp.get("current_work_items", []) if isinstance(item, dict))
        work_html = f'<section class="checkpoint-work"><span class="eyebrow">WORK ITEMS AS OF THE SAVED CHECKPOINT</span><p class="work-note">Checkpoint {e(human_time(active["review_updated_at"]))} · these are recorded tasks, not live worker status.</p><div class="worklist">{work_rows}</div></section>' if work_rows else ""
        active_body = f'<div class="paper-heading"><div><span class="eyebrow">CURRENT PAPER · QUEUE #{active["queue_order"]}</span><h2>{e(active["title"] or "Title not recorded")}</h2><p class="doi">{e(" · ".join(active["doi_candidates"]) or active["group_id"])}</p></div><span class="badge in_progress">In progress</span></div><div class="scope-note"><strong>Source scope</strong><p>{e(cp.get("si_status", "SI scope has not been recorded."))}</p><small>{active["file_copies"]} source copies · {active["confirmed_unique_content_hashes"]} confirmed unique contents · checkpoint {e(human_time(active["review_updated_at"]))}</small></div><div class="active-counters">{counter_html}</div><div class="stages">{stages}</div>{work_html}<div class="next-action"><span class="eyebrow">CURRENT NEXT ACTION</span><p>{e(cp.get("next_action", "See saved review checkpoint."))}</p></div>'
        active_sections.append('<section class="panel">' + active_body + '</section>')
    active_body = ''.join(active_sections) or '<section class="panel"><p>No active paper is claimed in the saved ledger.</p></section>'
    rows = ""
    for position, group in enumerate(data["next_12_waiting"], 1):
        dois = " · ".join(f'<a href="https://doi.org/{quote(doi, safe="/")}">{e(doi)}</a>' for doi in group["doi_candidates"]) or e(group["group_id"])
        title = group["title"] or "Title not available in the local index"
        title_meta = group.get("title_metadata") or {}
        origin = (f'Raw heading candidate · {title_meta.get("confidence", "unknown")} confidence' if title_meta.get("origin") == "first_page_heading_heuristic" else "Unverified bibliographic candidate") if group["title"] else "No title inferred"
        sources = " + ".join("Incoming" if source == "incoming" else "Legacy" for source in group["sources"])
        flags = f'{group["main_candidates"]} main · {group["si_candidates"]} SI candidates'
        if group["ambiguous_role_copies"]:
            flags += f' · {group["ambiguous_role_copies"]} ambiguous'
        raw_detail = f'<details class="raw-title"><summary>Exact raw metadata</summary><p>{e(title)}</p></details>' if group["title"] else ""
        score = group.get("priority", {}).get("score")
        if score is not None:
            raw_detail += f'<small>Screening priority: {e(score)} · candidate evidence, not a scientific quality rating</small>'
        rows += f'<tr><td class="position">{position:02d}<small>#{group["queue_order"]}</small></td><td><strong class="candidate-title" title="{e(title)}">{e(title)}</strong><div class="doi">{dois}</div><small>{e(origin)}</small>{raw_detail}</td><td>{e(sources)}<small>{e(flags)}</small></td><td><span class="readiness {"ready" if group["default_ready"] else "hold"}">{e(group["readiness"])}</span><small>{group["file_copies"]} file copies · {e(group["review_status"])}</small></td></tr>'
    root_rows = "".join(f'<tr><td><strong>{"Incoming folder" if alias == "incoming" else "Legacy backfill"}</strong><small>{e(path)}</small></td><td class="number">{fmt(counts["source_document_copies"][alias])}</td></tr>' for alias, path in counts["source_paths"].items())
    policy = "".join(f'<li>{e(note)}</li>' for note in data["interpretation"][1:])
    old_public = f'<a href="{e(baseline["public_url"])}">Open existing public site ↗</a>' if baseline.get("public_url") else "No publication URL recorded."
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>MatterSyn · Curation work queue</title>
<style>
:root{{--ink:#16332f;--muted:#587069;--line:#d7e2dc;--paper:#f5f8f4;--white:#fff;--green:#126a52;--pale:#e7f4eb;--amber:#8a560a;--amber-bg:#fff3dc;--blue:#265d87;--blue-bg:#e9f1f7}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:17px/1.55 "Segoe UI",Arial,sans-serif}}a{{color:var(--green);text-underline-offset:3px}}.wrap{{max-width:1420px;margin:auto;padding:36px 46px 64px}}header{{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;margin-bottom:28px}}.brand{{font-weight:750;letter-spacing:.09em;font-size:17px}}.eyebrow{{font-size:12px;letter-spacing:.11em;font-weight:750;color:var(--muted)}}h1{{font-size:42px;line-height:1.15;letter-spacing:-.04em;margin:14px 0 10px}}h2{{font-size:27px;line-height:1.3;letter-spacing:-.025em;margin:9px 0}}h3{{font-size:18px;margin:13px 0 10px}}p{{margin:8px 0 14px}}header p{{max-width:820px;color:var(--muted)}}.stamp{{text-align:right;font-size:13px;flex:0 0 270px;padding-top:4px}}.stamp strong{{display:block;margin:9px 0}}.badge{{display:inline-block;padding:5px 10px;font-size:12px;line-height:1.4;font-weight:750;border-radius:7px;background:#edf0ed;color:var(--muted);text-transform:capitalize;white-space:nowrap}}.badge.complete{{background:var(--pale);color:var(--green)}}.badge.partial,.badge.prior{{background:var(--amber-bg);color:var(--amber)}}.badge.in_progress{{background:var(--blue-bg);color:var(--blue)}}.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:26px 0}}.metric{{border:1px solid var(--line);border-radius:15px;background:var(--white);padding:20px 22px}}.metric>span{{font-size:14px;font-weight:650;color:var(--muted)}}.metric strong{{display:block;font-size:39px;line-height:1.2;margin:8px 0 12px;letter-spacing:-.04em}}small{{display:block;font-size:12px;color:var(--muted);line-height:1.5}}.panel{{border:1px solid var(--line);border-radius:18px;background:var(--white);padding:29px;margin:25px 0}}.paper-heading{{display:flex;justify-content:space-between;align-items:flex-start;gap:20px}}.paper-heading h2{{max-width:960px}}.doi{{font-size:14px;color:var(--muted);margin-top:6px;overflow-wrap:anywhere}}.scope-note{{margin:23px 0;padding:17px 20px;background:#fff9ee;border:1px solid #eadfc6;border-left:4px solid #cda45c;border-radius:9px}}.scope-note p{{margin:5px 0}}.active-counters{{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;padding:2px 0 25px}}.active-counters strong{{font-size:28px;display:block;line-height:1.3}}.active-counters span{{font-size:13px;color:var(--muted)}}.stages{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));border-top:1px solid var(--line);padding-top:22px;gap:20px}}.stage{{min-width:0}}.stage p{{font-size:13px;line-height:1.6;color:var(--muted)}}details{{font-size:12px;overflow-wrap:anywhere}}summary{{cursor:pointer;font-weight:650}}details ul{{padding-left:16px}}.next-action{{margin-top:24px;background:#f0f6f2;border-radius:10px;padding:17px 20px}}.next-action p{{font-size:15px;margin:7px 0}}.section-title{{display:flex;justify-content:space-between;align-items:baseline;gap:20px}}.section-title p{{font-size:13px;color:var(--muted)}}.table-wrap{{overflow:auto}}table{{width:100%;border-collapse:collapse;font-size:14px}}th{{text-align:left;font-size:11px;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);font-weight:750;padding:14px 10px;border-bottom:2px solid var(--line)}}td{{padding:17px 10px;border-bottom:1px solid #e6ece7;vertical-align:top}}tr:last-child td{{border-bottom:0}}td strong{{font-weight:650;line-height:1.45;display:block}}td small{{margin-top:7px}}.position{{width:68px;font-size:20px;color:var(--green);font-weight:650}}.position small{{font-weight:400;font-size:11px}}.readiness{{font-size:12px;font-weight:650;display:block;max-width:170px}}.readiness.ready{{color:var(--green)}}.readiness.hold{{color:var(--amber)}}.two-cols{{display:grid;grid-template-columns:1.12fr 1fr;gap:24px}}.two-cols .panel{{margin-top:0;margin-bottom:0}}.number{{text-align:right;font-variant-numeric:tabular-nums;font-size:22px}}.hash-counts{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:23px 0}}.hash-counts b{{font-size:23px;display:block}}.hash-counts span{{font-size:13px;color:var(--muted)}}.notice{{font-size:13px;color:var(--muted);padding:15px 0;border-top:1px solid var(--line)}}.baseline-counts{{display:flex;gap:26px;flex-wrap:wrap;margin:22px 0}}.baseline-counts strong{{font-size:29px;display:block}}.baseline-counts span{{font-size:13px;color:var(--muted)}}.notes{{font-size:14px;color:var(--muted);padding-left:22px}}.notes li{{margin:9px 0}}code{{display:block;padding:14px 16px;background:#edf2ed;border-radius:8px;overflow:auto;font:12px/1.6 Consolas,monospace;margin-top:10px}}footer{{margin-top:30px;font-size:12px;color:var(--muted);display:flex;justify-content:space-between;gap:20px}}.links a{{margin-right:16px}}@media(max-width:1100px){{.wrap{{padding:25px}}.stages{{grid-template-columns:repeat(3,1fr)}}.stamp{{flex-basis:220px}}}}@media(max-width:760px){{.wrap{{padding:20px 15px}}header,.paper-heading{{display:block}}.stamp{{text-align:left;margin-top:20px}}h1{{font-size:33px}}h2{{font-size:23px}}.metrics,.active-counters,.two-cols{{grid-template-columns:1fr 1fr}}.stages{{grid-template-columns:1fr}}.panel{{padding:20px}}.two-cols{{display:block}}.two-cols .panel{{margin-bottom:24px}}.stage{{border-bottom:1px solid var(--line);padding-bottom:15px}}.section-title{{display:block}}footer{{display:block}}}}
.candidate-title{{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}.raw-title{{margin-top:7px;color:var(--muted)}}.raw-title p{{font-size:13px}}.checkpoint-work{{margin-top:27px;padding-top:22px;border-top:1px solid var(--line)}}.work-note{{font-size:12px;color:var(--muted)}}.worklist{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}}.worklist article{{padding:15px 17px;border:1px solid var(--line);border-radius:10px}}.worklist article>div{{display:flex;gap:15px;justify-content:space-between;align-items:flex-start}}.worklist strong{{font-size:14px}}.worklist p{{font-size:13px;color:var(--muted);margin:10px 0 0}}@media(max-width:760px){{.worklist{{grid-template-columns:1fr}}}}
</style></head><body><main class="wrap">
<header><div><div class="brand">MATTERSYN</div><h1>Curation work queue</h1><p>Batches contain up to five independently reviewed papers, each with its own audit. Ready contributions may be published together. Detailed-review order follows the saved selection policy; original arrival order remains recorded.</p></div><aside class="stamp"><span class="badge">Private · Static snapshot</span><strong>{e(human_time(data['generated_at']))}</strong><span>Last folder scan<br>{e(human_time(data['ledger_last_scan_at']))}</span></aside></header>
<section class="metrics">{cards}</section><p class="notice"><strong>Selection policy:</strong> {e(priority_label)}. Saved claims below retain their own review and audit evidence.</p>{active_body}
<section class="panel"><div class="section-title"><h2>Next 12 waiting scopes</h2><p>Candidate priority · resume the current batch first</p></div><p class="notice">These are queued review candidates, not twelve papers being processed simultaneously. All active batch members and duplicate main-file aliases are excluded. Titles come from existing local metadata and do not establish useful synthesis content.</p><div class="table-wrap"><table><thead><tr><th>Next / order</th><th>Paper candidate</th><th>Source / scope</th><th>Saved readiness</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<div class="two-cols"><section class="panel"><span class="eyebrow">COVERAGE &amp; RECONCILIATION</span><h2>Both collections are tracked</h2><table><tbody>{root_rows}</tbody></table><div class="hash-counts"><div><b>{fmt(counts['known_unique_document_hashes'])}</b><span>Known unique document hashes</span></div><div><b>{fmt(counts['confirmed_duplicate_document_copies'])}</b><span>Confirmed duplicate copies</span></div><div><b>{fmt(counts['document_copies_not_yet_hashed'])}</b><span>Copies without ledger fingerprints</span></div><div><b>{fmt(counts['normalized_doi_candidates'])}</b><span>Candidate DOI clusters</span></div></div><p class="notice"><strong>{fmt(counts['pending_main_missing_scopes'])}</strong> pending scopes lack a main candidate; <strong>{fmt(counts['ambiguous_role_document_copies'])}</strong> document copies have ambiguous role flags. They need explicit source-scope review. Unknown unique-paper, material, and recipe totals remain unknown. These fingerprint counts describe the queue ledger; the separate corpus screening report records its own verified source hashes.</p></section>
<section class="panel"><span class="eyebrow">PREVIOUSLY PUBLISHED · SEPARATE BASELINE</span><h2>Existing public atlas</h2><p>Public version {e(baseline.get('version'))} · {e(human_time(baseline.get('published_at')))}</p><div class="baseline-counts"><div><strong>{fmt(baseline['material_hubs'])}</strong><span>Material hubs</span></div><div><strong>{fmt(baseline['synthesis_route_variants'])}</strong><span>Synthesis routes / variants</span></div><div><strong>{fmt(baseline['canonical_records'])}</strong><span>Canonical records</span></div></div><p>{fmt(baseline['benchmark_rows'])} of these records are separate numeric benchmark rows. {fmt(baseline['formal_full_main_and_si_reviews'])} sources have formal full supplied-main and matched-SI review ledgers.</p><p class="notice">Published totals include earlier contributions and completed queue work. Consult each source’s five milestones; publication alone does not waive any outstanding completeness review.</p><p>{old_public}</p><small>Local inventory: {e(baseline.get('inventory_version'))}. The report did not query or change the live website.</small></section></div>
<section class="panel"><h2>How to read and refresh this snapshot</h2><ul class="notes">{policy}</ul><p>This report does not refresh itself. Regenerate it from the private monitor folder:</p><code>{e(data['regenerate_command'])}</code><p class="links"><a href="queue-status.md">Readable Markdown</a><a href="queue-status.json">Structured snapshot</a><a href="README.md">Queue workflow</a></p></section>
<footer><span>Private review workspace · no raw papers uploaded by this report</span><span>Ledger snapshot SHA256: {e((data.get('ledger_sha256') or '')[:16])}…</span></footer>
</main></body></html>'''


def render_markdown(data):
    c, active, baseline = data["counts"], data["active"], data["published_baseline"]
    lines = ["# MatterSyn curation work queue", "", f"**Private static snapshot — {human_time(data['generated_at'])}.**",
             f"Last folder scan: {human_time(data['ledger_last_scan_at'])}. No new folder scan or ledger mutation was performed.", "",
             f"- Active review claims: **{c['active_review_claims']}**", f"- Selection policy: **{data.get('selection_policy', {}).get('mode', 'arrival_order')}**", f"- Waiting review scopes: **{fmt(c['waiting_review_scopes'])}**",
             f"- Scopes with evidenced final dispositions: **{c['evidence_closed_new_queue_scopes']}**",
             f"- Fully curated queue scopes: **{c['fully_curated_queue_scopes']}**; no-recipe screening skips: **{c['screened_no_recipe_scopes']}** (other audited exclusions tracked separately)",
             f"- Document copies: **{fmt(c['present_files'])}**", ""]
    for active in data.get("active_papers", [active] if active else []):
        lines += ["## Current paper", "", f"**{active['title'] or active['group_id']}**", "", ", ".join(active["doi_candidates"]), "",
                  f"SI scope: {active['checkpoint'].get('si_status', 'Not recorded')}", "",
                  f"{active['file_copies']} source copies; {active['confirmed_unique_content_hashes']} confirmed unique contents. Current file generation {active['generation']}.", ""]
        for stage in monitor.MILESTONES:
            record = active["milestones"].get(stage, {})
            lines += [f"- **{STAGE_NAMES[stage]} — {record.get('status', 'pending')}**: {record.get('note', 'No milestone note recorded.')}"]
        lines += ["", "Next action: " + active["checkpoint"].get("next_action", "See checkpoint."), ""]
        work = active["checkpoint"].get("current_work_items", [])
        if work:
            lines += ["### Work items as of the saved checkpoint", "", "These are recorded tasks, not live worker status.", ""]
            lines += [f"- **{item.get('label', 'Unnamed task')} — {item.get('status', 'pending')}**: {item.get('scope', 'Scope not recorded.')}" for item in work if isinstance(item, dict)]
            lines.append("")
    lines += ["## Next 12 waiting scopes", "", "Titles, DOI associations and automated evidence scores are candidate metadata. Selection follows the active policy; original queue order is retained. All active batch papers are excluded.", "",
              "| Next | Queue order | DOI / group | Local candidate title | Copies (main / SI candidates) | Saved readiness |", "|---:|---:|---|---|---|---|"]
    for position, group in enumerate(data["next_12_waiting"], 1):
        title = (group["title"] or "Not available in local index").replace("|", "\\|")
        doi = ", ".join(group["doi_candidates"]) or group["group_id"]
        lines.append(f"| {position} | {group['queue_order']} | {doi} | {title} | {group['file_copies']} ({group['main_candidates']} / {group['si_candidates']}) | {group['readiness']} |")
    lines += ["", "## Coverage and limits", ""]
    for source, value in c["source_document_copies"].items():
        lines.append(f"- {source.capitalize()}: {fmt(value)} document copies.")
    lines += [f"- Queue-ledger unique hashes: {fmt(c['known_unique_document_hashes'])}; confirmed duplicate copies: {fmt(c['confirmed_duplicate_document_copies'])}; copies without ledger fingerprints: {fmt(c['document_copies_not_yet_hashed'])}.",
              f"- Pending scopes without a main candidate: {fmt(c['pending_main_missing_scopes'])}; ambiguous-role document copies: {fmt(c['ambiguous_role_document_copies'])}.",
              "- Verified unique-paper, synthesized-material and recipe totals remain unknown.", "", "## Existing published baseline", "",
              f"Version {baseline.get('version')}: {fmt(baseline['material_hubs'])} material hubs, {fmt(baseline['synthesis_route_variants'])} synthesis routes/variants, {fmt(baseline['canonical_records'])} canonical records including {fmt(baseline['benchmark_rows'])} numeric benchmark rows.",
              "Published totals and completed queue counts are separate measures; prior publication does not waive outstanding review.", "", "## Regenerate", "",
              "Run in the incoming-paper-monitor directory:", "", "```powershell", data["regenerate_command"], "```", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=HERE / "ledger.json")
    parser.add_argument("--bibliography", type=Path, default=DEFAULT_BIBLIOGRAPHY)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--release", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--output-dir", type=Path, default=HERE)
    args = parser.parse_args()
    raw = args.ledger.read_bytes()
    ledger = json.loads(raw)
    data = build_snapshot(ledger, title_index(read_json(args.bibliography)), read_json(args.baseline), read_json(args.release), ledger_sha256=hashlib.sha256(raw).hexdigest())
    active_keys = {claim["group_id"] for claim in monitor.active_claims(ledger)}
    expected = [key for key in monitor.queued(ledger) if key not in active_keys][:12]
    assert [group["group_id"] for group in data["next_12_waiting"]] == expected
    assert sum(data["counts"]["source_document_copies"].values()) == data["counts"]["present_files"]
    assert not any(ledger["groups"][key].get("alias_of") for key in expected)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "queue-status.json").write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (args.output_dir / "queue-status.md").write_text(render_markdown(data), encoding="utf-8")
    (args.output_dir / "queue-status.html").write_text(render_html(data, args.output_dir), encoding="utf-8")
    print(json.dumps({"html": str(args.output_dir / "queue-status.html"), "active": [paper["group_id"] for paper in data["active_papers"]],
                      "waiting_scopes": data["counts"]["waiting_review_scopes"], "new_evidence_closed_scopes": data["counts"]["evidence_closed_new_queue_scopes"],
                      "next_orders": [group["queue_order"] for group in data["next_12_waiting"]],
                      "static_snapshot": True, "ledger_unchanged_during_render": args.ledger.read_bytes() == raw}, indent=2))


if __name__ == "__main__":
    main()
