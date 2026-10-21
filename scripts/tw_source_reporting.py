"""Isolated daily email ledger, seven-calendar-day evidence bundle and stop gate.

All remote writes remain Actions upload steps. The only provider contact is the
explicit notify entry point after durable remote intent and report verification.
"""
from __future__ import annotations

import csv
from datetime import date, timedelta
import io
import json

try:
    from . import tw_source_actions as actions, tw_source_observation as core, tw_source_email as email
except ImportError:
    import tw_source_actions as actions
    import tw_source_observation as core
    import tw_source_email as email

KINDS = {"daily_report", "final", "mail_intent", "mail_receipt"}
PURPOSES = {"daily-final", "final-correction-1"}
STATUSES = {"provider_accepted", "definite_nonacceptance", "delivery_unknown"}


def dates(plan):
    start = date.fromisoformat(plan["start_date"])
    return [(start + timedelta(days=i)).isoformat() for i in range(7)]


def fingerprint(files):
    return core.digest({name: actions.sha(content) for name, content in files.items() if name != "manifest.json"})


def name(plan, kind, day=None, purpose="daily-final", attempt_no=None):
    prefix = f"twso-{plan['experiment_id']}-"
    actions.require(kind in KINDS and purpose in PURPOSES, "invalid_report_kind")
    if kind == "final":
        return prefix + "final"
    actions.require(day in dates(plan), "report_date_outside_experiment")
    key = "daily" if purpose == "daily-final" else "final-correction"
    if kind == "daily_report":
        return f"{prefix}{day}-{key}-report"
    actions.require(type(attempt_no) is int and 1 <= attempt_no <= 3, "invalid_delivery_attempt")
    return f"{prefix}{day}-{key}-mail-{attempt_no}-{'intent' if kind == 'mail_intent' else 'receipt'}"


def metadata(plan, run_id, kind, day=None, purpose="daily-final", attempt_no=None):
    return {"experiment_id": plan["experiment_id"], "kind": kind, "date": day, "purpose": purpose,
            "attempt_no": attempt_no, "code_sha": plan["code_sha"], "plan_hash": core.digest(plan),
            "run_id": run_id, "run_attempt": 1}


def validate_notification(plan):
    config = plan["notification"]
    actions.require(config.get("channel") == "email" and type(config.get("enabled")) is bool
                    and config.get("provider") in {None, "smtp"}
                    and config.get("settings_secret_name") == "TW_SOURCE_EMAIL_SETTINGS"
                    and config.get("resend_on_unknown_delivery") is False
                    and config.get("max_delivery_attempts") == 3
                    and config.get("retry_only_on_definite_nonacceptance") is True,
                    "invalid_notification_policy")
    actions.require(config.get("send_success") is True and config.get("send_failure") is True,
                    "both_success_failure_reports_required")
    actions.require(not config["enabled"] or config["provider"] == "smtp", "smtp_provider_required")


def read_ledger(api, plan, now, current_run_id=None):
    """Restore verified report and mail artifacts, never trust an absent receipt."""
    result = {}
    prefix = f"twso-{plan['experiment_id']}-"
    summaries = api.report_runs(plan["start_date"], now.astimezone(core.TAIPEI).date().isoformat())
    actions.require(len({r["id"] for r in summaries}) == len(summaries), "duplicate_report_run")
    current = api.run(current_run_id) if current_run_id else None
    for summary in summaries:
        run = api.run(summary["id"])
        if current and (core.timestamp(run["created_at"]), run["id"]) > (core.timestamp(current["created_at"]), current_run_id):
            continue
        actions.verify_run(api, run, plan, "report")
        relevant = [a for a in api.artifacts(run["id"]) if a["name"].startswith(prefix)]
        run_kinds = set()
        for artifact in relevant:
            files, manifest = actions.unpack(api.archive(artifact), artifact, final=artifact["name"] == name(plan, "final"))
            kind = manifest.get("kind")
            actions.require(kind in KINDS, "unknown_report_artifact")
            expected = metadata(plan, run["id"], kind, manifest.get("date"), manifest.get("purpose"), manifest.get("attempt_no"))
            actions.require(all(manifest.get(k) == value for k, value in expected.items())
                            and artifact.get("workflow_run", {}).get("id") == run["id"], "report_manifest_scope_mismatch")
            expected_name = name(plan, kind, manifest["date"], manifest["purpose"], manifest["attempt_no"])
            actions.require(artifact["name"] == expected_name and expected_name not in result, "duplicate_or_wrong_report_artifact")
            if kind == "daily_report":
                actions.require(set(files) == {"daily.json", "message.json", "REPORT.md"}, "invalid_daily_report_files")
            elif kind in {"mail_intent", "mail_receipt"}:
                actions.require(set(files) == {"intent.json" if kind == "mail_intent" else "receipt.json"}, "invalid_mail_files")
            else:
                verify_final(plan, files)
            result[expected_name] = {"kind": kind, "manifest": manifest, "files": files,
                                     "hash": fingerprint(files), "artifact_id": artifact["id"], "run_id": run["id"],
                                     "run_created_at": run["created_at"]}
            run_kinds.add(kind)
        if run["id"] != current_run_id:
            jobs = api.jobs(run["id"])
            actions.require(bool(jobs), "missing_report_jobs")
            for entry in jobs:
                for step in entry.get("steps", []):
                    if step.get("name") == "Persist notification intent" and step.get("conclusion") == "success":
                        actions.require("mail_intent" in run_kinds, "notification_intent_missing")
                    if step.get("name") == "Send daily report" and step.get("conclusion") not in {None, "skipped"}:
                        actions.require("mail_intent" in run_kinds, "notification_intent_missing")
    # Pairing and scope validation happen even when deciding not to send today.
    mail_attempts(plan, result)
    return result


def mail_attempts(plan, ledger):
    grouped = {}
    for record in ledger.values():
        if record["kind"] != "mail_intent":
            continue
        manifest = record["manifest"]
        intent = json.loads(record["files"]["intent.json"])
        day, purpose, number = manifest["date"], manifest["purpose"], manifest["attempt_no"]
        key = f"{plan['experiment_id']}:{day}:{purpose}"
        actions.require(intent.get("key") == key and intent.get("attempt_no") == number
                        and intent.get("day") == day and intent.get("purpose") == purpose,
                        "notification_scope_mismatch")
        actions.require(core.timestamp(intent["created_at"]) >= core.timestamp(record["run_created_at"]),
                        "intent_predates_run")
        message = intent["message"]
        actions.require(set(message) == {"subject", "body"} and all(isinstance(v, str) for v in message.values())
                        and "\n" not in message["subject"] and "\r" not in message["subject"]
                        and intent.get("payload_hash") == core.digest(message), "mail_payload_hash_mismatch")
        covered = intent["covered_dates"]
        actions.require(isinstance(covered, list) and bool(covered) and len(covered) == len(set(covered))
                        and day in covered and all(d in dates(plan) and d <= day for d in covered), "invalid_covered_dates")
        ref = intent["report_ref"]
        target = ledger.get(ref["name"])
        actions.require(target and target["kind"] == "daily_report" and target["hash"] == ref["hash"]
                        and json.loads(target["files"]["message.json"]) == message, "mail_report_mismatch")
        card = json.loads(target["files"]["daily.json"])
        actions.require(card.get("final_ref") == intent.get("final_ref") and card.get("covered_dates") == covered,
                        "mail_report_scope_mismatch")
        if intent.get("final_ref"):
            final = ledger.get(name(plan, "final"))
            actions.require(day == dates(plan)[-1] and final and intent["final_ref"] == {
                "name": name(plan, "final"), "hash": final["hash"]}, "final_mail_binding_mismatch")
        receipt_name = name(plan, "mail_receipt", day, purpose, number)
        receipt_record = ledger.get(receipt_name)
        receipt = json.loads(receipt_record["files"]["receipt.json"]) if receipt_record else None
        if receipt:
            actions.require(receipt_record["run_id"] == record["run_id"], "receipt_run_mismatch")
            actions.require(core.timestamp(intent["created_at"]) <= core.timestamp(receipt["attempt_started_at"])
                            <= core.timestamp(receipt["recorded_at"]), "invalid_receipt_chronology")
            for field in ("key", "attempt_no", "payload_hash", "report_ref", "final_ref", "covered_dates"):
                actions.require(receipt.get(field) == intent.get(field), "receipt_payload_mismatch")
            actions.require(receipt.get("status") in STATUSES and type(receipt.get("retryable")) is bool,
                            "invalid_delivery_receipt")
            actions.require(receipt["status"] == "definite_nonacceptance" or not receipt["retryable"], "invalid_receipt_retry")
            actions.require(receipt["status"] != "provider_accepted" or receipt.get("smtp_code") == 250
                            and receipt.get("phase") == "data", "acceptance_not_proven")
        grouped.setdefault(key, []).append({"intent": intent, "receipt": receipt, "record": record})
    for key, attempts in grouped.items():
        attempts.sort(key=lambda row: row["intent"]["attempt_no"])
        actions.require([a["intent"]["attempt_no"] for a in attempts] == list(range(1, len(attempts) + 1)), "delivery_attempt_gap")
        for previous, subsequent in zip(attempts, attempts[1:]):
            receipt = previous["receipt"]
            actions.require(receipt and receipt["status"] == "definite_nonacceptance" and receipt["retryable"],
                            "retry_after_unknown_or_accepted")
            actions.require(previous["intent"]["payload_hash"] == subsequent["intent"]["payload_hash"], "retry_payload_changed")
    for record in ledger.values():
        if record["kind"] == "mail_receipt":
            m = record["manifest"]
            actions.require(name(plan, "mail_intent", m["date"], m["purpose"], m["attempt_no"]) in ledger, "orphan_mail_receipt")
    return grouped


def csv_bytes(rows, fields):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    # Titles/URLs originate outside the repo; keep exported CSV safe to open in
    # a spreadsheet without turning publisher text into formulas.
    writer.writerows({key: "'" + value if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r")) else value
                     for key, value in row.items()} for row in rows)
    return output.getvalue().encode("utf-8-sig")


def final_files(plan, rows, evidence):
    """Freeze seven dates, 35 source rows and a deduplicated manual-review list."""
    try:
        from . import evaluate_tw_source_admission as shadow
    except ImportError:
        import evaluate_tw_source_admission as shadow
    by_day = {row["date"]: row for row in rows}
    actions.require(set(by_day) == set(dates(plan)), "final_requires_seven_dates")
    source_rows, events, files, baseline_union = [], {}, {}, set()
    for day in dates(plan):
        row = by_day[day]
        attempts = {attempt["slot"]: attempt for attempt in row["attempts"]}
        comparison_baseline = None
        for slot in core.SLOTS:
            comparison_baseline = attempts.get(slot, {}).get("baseline_at") or comparison_baseline
        for sid in core.SOURCES:
            outcome = row["source_summary"].get(sid, {})
            origin = attempts.get(outcome.get("origin_slot"), {})
            source_rows.append({"date": day, "source_id": sid, "status": outcome.get("status", row["status"]),
                                "item_count": outcome.get("item_count", ""), "retrieved_at": outcome.get("retrieved_at", ""),
                                "origin_slot": outcome.get("origin_slot", ""), "daily_status": row["status"],
                                "comparison_baseline_at": comparison_baseline or "",
                                "source_slot_baseline_at": origin.get("baseline_at") or "",
                                "origin_run_id": origin.get("origin_run_id", ""),
                                "origin_artifact_id": origin.get("origin_artifact_id", "")})
        for slot, slot_files in evidence.get(day, {}).items():
            for filename, content in slot_files.items():
                files[f"{day}-{slot}-{filename}"] = content
            if "baseline.json" in slot_files:
                baseline = json.loads(slot_files["baseline.json"])
                baseline_union.update(shadow.canonical_url(item.get("url")) for item in baseline.get("items", []))
            if "capture.json" not in slot_files:
                continue
            capture = json.loads(slot_files["capture.json"])
            report = json.loads(slot_files["report.json"]) if "report.json" in slot_files else None
            comparisons = {(source["source_id"], article["canonical_url"]): article.get("comparison", "unknown")
                           for source in report["sources"] for article in source["articles"]} if report else {}
            for source in capture["sources"]:
                for article in source["articles"]:
                    if shadow.filter_article(article, shadow.timestamp(capture["generated_at"]), 7) != "candidate_requires_review":
                        continue
                    key = (source["source_id"], article["canonical_url"])
                    entry = events.setdefault(key, {"source_id": key[0], "canonical_url": key[1], "title": article["title"],
                                                    "first_seen": day, "last_seen": day, "days_seen": set(), "comparisons": {}})
                    entry["last_seen"] = day
                    entry["days_seen"].add(day)
                    entry["comparisons"][day] = comparisons.get(key, "baseline_unavailable")
    event_rows = [{"source_id": entry["source_id"], "canonical_url": entry["canonical_url"], "title": entry["title"],
                   "first_seen": entry["first_seen"], "last_seen": entry["last_seen"], "days_seen": len(entry["days_seen"]),
                   "daily_comparisons": json.dumps(entry["comparisons"], ensure_ascii=False, sort_keys=True),
                   "retrospective_url_seen": entry["canonical_url"] in baseline_union, "manual_decision": ""}
                  for _, entry in sorted(events.items())]
    files.update({"SOURCE_DAILY.csv": csv_bytes(source_rows, list(source_rows[0])),
                  "EVENT_REVIEW.csv": csv_bytes(event_rows, ["source_id", "canonical_url", "title", "first_seen", "last_seen",
                      "days_seen", "daily_comparisons", "retrospective_url_seen", "manual_decision"]),
                  "observations.json": actions.encoded({"experiment_id": plan["experiment_id"], "start_date": dates(plan)[0],
                      "end_date": dates(plan)[-1], "days": rows, "novel_events_confirmed": None, "new_evidence_confirmed": None,
                      "candidate_source_urls": len(events)})})
    complete = sum(row["status"] == "complete" for row in rows)
    files["FINAL_REPORT.md"] = (f"# 台灣來源七日觀察結案\n\n{dates(plan)[0]}～{dates(plan)[-1]}：{complete}/7 日完整。\n\n"
        f"五站逐日紀錄 35 列，跨日按來源＋URL 去重後 {len(events)} 筆待人工核對候選。\n"
        "新增事件、新證據及誤收率尚未經人工裁決；候選數不能當新增事件數。\n\n"
        "SOURCE_DAILY.csv 含缺測與限制；EVENT_REVIEW.csv 保留每日比較與回看 URL 可見性。\n"
        "回看 baseline 聯集只表示事後 URL 可見，不代表當日已覆蓋或同一事件。\n"
        "observations.json 保留原始時點、slot、來源 run/artifact ID 與未完成原因。\n"
        "最後是否准入來源、如何收錄與排序，均由使用者決策；不自動修改正式系統。\n").encode()
    files["checksums.json"] = actions.encoded({filename: actions.sha(content) for filename, content in files.items()})
    actions.require(sum(map(len, files.values())) <= actions.MAX_FINAL_EXPANDED, "final_bundle_too_large")
    return files


def verify_final(plan, files):
    actions.require({"FINAL_REPORT.md", "SOURCE_DAILY.csv", "EVENT_REVIEW.csv", "observations.json", "checksums.json"} <= set(files), "final_package_incomplete")
    expected = json.loads(files["checksums.json"])
    actions.require(expected == {k: actions.sha(v) for k, v in files.items() if k != "checksums.json"}, "final_checksum_mismatch")
    observation = json.loads(files["observations.json"])
    actions.require(observation.get("experiment_id") == plan["experiment_id"]
                    and [row["date"] for row in observation["days"]] == dates(plan)
                    and observation.get("start_date") == dates(plan)[0] and observation.get("end_date") == dates(plan)[-1]
                    and observation.get("novel_events_confirmed") is None
                    and observation.get("new_evidence_confirmed") is None, "final_date_scope_mismatch")
    daily = list(csv.DictReader(io.StringIO(files["SOURCE_DAILY.csv"].decode("utf-8-sig"))))
    actions.require(len(daily) == 35 and {(row["date"], row["source_id"]) for row in daily}
                    == {(d, sid) for d in dates(plan) for sid in core.SOURCES}, "final_source_matrix_incomplete")


def message(plan, row, covered_rows, run_id, final_ref, now):
    number = dates(plan).index(row["date"]) + 1
    status = {"complete": "成功", "missing": "缺測", "unmet": "未達標", "unavailable": "證據無法驗證"}.get(row["status"], "未達標")
    recovered = any(a["slot"] == "recovery" and a["state"] == "finished" for a in row["attempts"])
    if row["status"] == "complete" and recovered:
        status = "補試成功"
    subject = f"[TW來源觀察][D{number}/7][{status}{'／七日結案' if final_ref else ''}] {row['date']}"
    if row["date"] < now.astimezone(core.TAIPEI).date().isoformat() or len(covered_rows) > 1:
        subject = subject.replace("[TW來源觀察]", "[TW來源觀察][延遲補報]", 1)
    lines = [subject, "", f"觀察狀態：{row['status']}；通知接受與實際收件是不同狀態。", ""]
    lines += [f"候選篇數：{row.get('candidate_articles') if row.get('candidate_articles') is not None else '未知'}；待人工核對篇數：{row.get('pending_review_articles') if row.get('pending_review_articles') is not None else '未知'}。"]
    if recovered and not any(a["slot"] == "primary" for a in row["attempts"]):
        lines.append("主觸發缺失；本日由補試首次採樣，時間按實際取得記錄。")
    for attempt in row["attempts"]:
        lines.append(f"{attempt['slot']}：{attempt['state']}，開始 {attempt['started_at']}，結束 {attempt.get('finished_at', '未確認')}，baseline {attempt.get('baseline_at') or '不可用'}")
    for sid in core.SOURCES:
        source = row["source_summary"].get(sid, {})
        lines.append(f"{sid}：{source.get('status', row['status'])}，篇數 {source.get('item_count', '未知')}，取得 {source.get('retrieved_at', '未確認')}")
    lines += ["", "本封涵蓋日期（延遲補報會明列原日期，不回補採樣）："]
    lines += [f"{r['date']}：{r['status']}" for r in covered_rows]
    lines += ["", "候選不等於新增事件；人工裁決尚未完成。已知抓取限制請見報告，沒有繞過登入、robots 或付費牆。",
              f"測試報告與 artifacts：https://github.com/{core.REPOSITORY}/actions/runs/{run_id}"]
    if final_ref:
        lines += [f"結案包：{final_ref['name']}；SHA-256：{final_ref['hash']}", "七日資料完整／缺測一併保留；正式 Radar 未受觀察影響，來源准入由你裁決。"]
    return {"subject": subject, "body": "\n".join(lines) + "\n"}


def prepare(api, plan, context, output, now, rows, evidence):
    validate_notification(plan)
    if not plan["notification"]["enabled"]:
        return {"mail_due": "false", "stop": "false", "notification_status": "disabled"}
    # Pre-start workflow completions are valid wake-ups, but no ledger date
    # range exists yet. Do not mistake that absence for unavailable evidence.
    if now.astimezone(core.TAIPEI).date().isoformat() < dates(plan)[0]:
        actions.require(not rows, "pre_experiment_rows_unexpected")
        return {"mail_due": "false", "stop": "false", "notification_status": "before_experiment"}
    actions.require(bool(rows), "in_experiment_rows_missing")
    ledger = read_ledger(api, plan, now, context["run_id"])
    grouped = mail_attempts(plan, ledger)
    target = rows[-1]
    day = target["date"]
    terminal = (target["status"] == "complete" or target["deadline_exceeded"] or
                any(a["slot"] == "recovery" and a["state"] == "finished" for a in target["attempts"]))
    if not terminal:
        return {"mail_due": "false", "stop": "false", "notification_status": "pending_recovery"}
    final_ready = day == dates(plan)[-1] and target["collection_state"] != "in_progress"
    result = {"mail_due": "false", "stop": "false", "final_bundle_ready": "false"}
    final_ref = None
    if final_ready:
        final = ledger.get(name(plan, "final"))
        if final:
            final_ref = {"name": name(plan, "final"), "hash": final["hash"]}
        else:
            files = final_files(plan, rows, evidence)
            verify_final(plan, files)
            final_ref = {"name": name(plan, "final"), "hash": fingerprint(files)}
            actions.write_files(output / "final", actions.seal(files, metadata(plan, context["run_id"], "final")))
            result.update(final_bundle_ready="true", final_artifact_name=final_ref["name"], final_bundle_path=str(output / "final"))
    purpose = "daily-final"
    key = f"{plan['experiment_id']}:{day}:{purpose}"
    attempts = grouped.get(key, [])
    if final_ref and attempts and attempts[-1]["receipt"] and attempts[-1]["receipt"]["status"] == "provider_accepted" and not attempts[-1]["intent"].get("final_ref"):
        purpose = "final-correction-1"
        key = f"{plan['experiment_id']}:{day}:{purpose}"
        attempts = grouped.get(key, [])
    if attempts:
        last = attempts[-1]
        receipt = last["receipt"]
        if not receipt or receipt["status"] == "delivery_unknown":
            return result | {"notification_status": "delivery_unknown"}
        if receipt["status"] == "provider_accepted":
            return result | {"notification_status": "already_accepted"}
        if not receipt["retryable"] or len(attempts) >= 3:
            return result | {"notification_status": "notification_failed"}
    done, uncertain = set(), set()
    for items in grouped.values():
        last = items[-1]
        receipt = last["receipt"]
        if receipt and receipt["status"] == "provider_accepted":
            done.update(last["intent"]["covered_dates"])
        elif not receipt or receipt["status"] == "delivery_unknown":
            uncertain.update(last["intent"]["covered_dates"])
    if day in done and purpose == "daily-final":
        return result | {"notification_status": "already_covered"}
    report_name = name(plan, "daily_report", day, purpose)
    existing = ledger.get(report_name)
    if existing:
        report_files = existing["files"]
        card = json.loads(report_files["daily.json"])
        payload = json.loads(report_files["message.json"])
        covered = card["covered_dates"]
        final_ref = card["final_ref"]
    else:
        covered = [row["date"] for row in rows if row["date"] not in done | uncertain]
        if purpose == "final-correction-1":
            covered = [day]
        actions.require(day in covered, "current_day_delivery_unknown")
        payload = message(plan, target, [row for row in rows if row["date"] in covered], context["run_id"], final_ref, now)
        if purpose == "final-correction-1":
            payload["subject"] = payload["subject"].replace("[TW來源觀察]", "[TW來源觀察][結案更正1]", 1)
        card = {"date": day, "covered_dates": covered, "final_ref": final_ref, "daily": target}
        report_files = {"daily.json": actions.encoded(card), "message.json": actions.encoded(payload), "REPORT.md": payload["body"].encode()}
        actions.write_files(output / "daily-report", actions.seal(report_files, metadata(plan, context["run_id"], "daily_report", day, purpose)))
        result.update(report_bundle_ready="true", report_artifact_name=report_name, report_bundle_path=str(output / "daily-report"))
    number = len(attempts) + 1
    intent = {"key": key, "purpose": purpose, "day": day, "attempt_no": number, "covered_dates": covered,
              "message": payload, "payload_hash": core.digest(payload), "report_ref": {"name": report_name, "hash": fingerprint(report_files)},
              "final_ref": final_ref, "created_at": now.isoformat()}
    actions.write_files(output / "mail-intent", actions.seal({"intent.json": actions.encoded(intent)},
                        metadata(plan, context["run_id"], "mail_intent", day, purpose, number)))
    (output / "notification-state.json").write_bytes(actions.encoded({"plan": plan, "context": context, "intent": intent}))
    result.update(mail_due="true", mail_intent_artifact_name=name(plan, "mail_intent", day, purpose, number),
                  mail_intent_path=str(output / "mail-intent"), mail_receipt_artifact_name=name(plan, "mail_receipt", day, purpose, number),
                  mail_receipt_path=str(output / "mail-receipt"), notification_status="notification_pending")
    return result


def notify(api, plan, context, output, now, raw_settings, sender=email.send, clock=None):
    validate_notification(plan)
    actions.require(plan["notification"]["enabled"], "notification_disabled")
    state = json.loads((output / "notification-state.json").read_bytes())
    actions.require(state["plan"] == plan and state["context"] == context, "notification_context_changed")
    intent = state["intent"]
    ledger = read_ledger(api, plan, now, context["run_id"])
    intent_name = name(plan, "mail_intent", intent["day"], intent["purpose"], intent["attempt_no"])
    record = ledger.get(intent_name)
    actions.require(record and record["run_id"] == context["run_id"]
                    and record["files"]["intent.json"] == actions.encoded(intent), "persisted_notification_intent_required")
    attempts = mail_attempts(plan, ledger)[intent["key"]]
    actions.require(attempts[-1]["intent"] == intent and attempts[-1]["receipt"] is None, "notification_already_attempted")
    claim = {"mode": "prepare_attempt", "claim_required": True, "plan_hash": core.digest(plan),
             "intent_key": {"key": intent["key"], "attempt_no": intent["attempt_no"]}}
    actions.require(core.LocalIntentStore(output / "send-guard").claim(claim), "notification_already_started")
    response = sender({**intent["message"], "payload_hash": intent["payload_hash"]}, raw_settings)
    actions.require(response.get("status") in STATUSES and type(response.get("retryable")) is bool, "invalid_provider_result")
    # Only these fields are allowed into a public receipt. No provider text/IDs,
    # settings, sender/recipient, credentials or exception messages are retained.
    fields = ("status", "retryable", "phase", "smtp_code", "error_type")
    receipt = {k: intent[k] for k in ("key", "attempt_no", "payload_hash", "report_ref", "final_ref", "covered_dates")}
    receipt.update({k: response.get(k) for k in fields})
    receipt["attempt_started_at"] = now.isoformat()
    receipt["recorded_at"] = (clock() if clock else now).isoformat()
    actions.write_files(output / "mail-receipt", actions.seal({"receipt.json": actions.encoded(receipt)},
                        metadata(plan, context["run_id"], "mail_receipt", intent["day"], intent["purpose"], intent["attempt_no"])))
    return {"mode": "notified", "notification_status": receipt["status"],
            "final_report_accepted": "true" if receipt["status"] == "provider_accepted" and intent["final_ref"] else "false"}


def audit_stop(api, plan, context, now):
    """No mutation: produce the stop authorization only from persisted evidence."""
    actions.require(plan.get("auto_disable_requires_final_artifact_and_mail_receipt") is True
                    and plan.get("self_disable_workflows") == ["tw-source-observation.yml", "tw-source-report.yml"], "invalid_stop_targets")
    if now.astimezone(core.TAIPEI).date().isoformat() < dates(plan)[-1]:
        return {"mode": "audited", "stop": "false", "reason": "before_final_day"}
    ledger = read_ledger(api, plan, now, context["run_id"])
    final = ledger.get(name(plan, "final"))
    if not final:
        return {"mode": "audited", "stop": "false", "reason": "final_package_missing"}
    verify_final(plan, final["files"])
    for attempts in mail_attempts(plan, ledger).values():
        latest = attempts[-1]
        if latest["receipt"] and latest["receipt"]["status"] == "provider_accepted" and latest["intent"]["final_ref"] == {
                "name": name(plan, "final"), "hash": final["hash"]}:
            return {"mode": "audited", "stop": "true", "reason": "final_package_and_final_mail_verified"}
    return {"mode": "audited", "stop": "false", "reason": "final_mail_receipt_missing_or_not_accepted"}
