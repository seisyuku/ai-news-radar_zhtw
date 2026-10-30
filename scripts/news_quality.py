"""Observable funnel and event quality, separate from reader ranking/schema."""
from collections import Counter, defaultdict
import re

try:
    from scripts import article_versions as versions, publisher_governance as governance, publisher_material
except ModuleNotFoundError:
    import article_versions as versions
    import publisher_governance as governance
    import publisher_material


def signals(text):
    """Research leads only: never articles, evidence votes, or automatic approval."""
    parts = re.split(r"[；;\n]", text)
    return [p.strip()[:400] for p in parts if (
        re.search(r"(?:API|訂閱|订阅|subscription).{0,45}(?:credits?|額度|额度|價格|价格)|(?:credits?|額度|额度).{0,35}(?:API|訂閱|订阅)", p, re.I)
        or versions.FINANCE.search(p) and re.search(r"AI|Alphabet|Google|Microsoft|OpenAI|Nvidia|TPU|Azure|Cloud|微軟|谷歌|輝達", p, re.I))][:3]


def material_gaps(row, qualification):
    text = str(row.get("title_original") or row.get("title") or "") + "\n" + str(row.get("summary") or "")
    gaps = list(qualification.get("reason_codes") or [])
    if versions.stale_summary(row) or row.get("summary_quality") == "stale_preview":
        gaps.append("summary_describes_pre_announcement")
    if versions.FINANCE.search(text) and not any(e["kind"] == "earnings" and e["status"] == "supported" for e in qualification.get("core_evidence", [])):
        if not publisher_material.FINANCIAL_VALUE.search(text): gaps.append("financial_metric_value_missing")
        if not governance.PERIOD.search(text): gaps.append("financial_period_missing")
        if versions.PREVIEW.search(text): gaps.append("financial_results_not_yet_asserted")
        if not any(x.startswith("financial_") for x in gaps): gaps.append("financial_value_period_subject_not_linked")
    return sorted(set(gaps))


def build(archive, raw_pool, ai_pool, merged, status, *, now, window_hours=24, fetched_ids=None,
          reader_exclusions=None, project_versions=True):
    # Late import keeps update_news's compatibility entrypoints available.
    try:
        from scripts import update_news as u
    except ModuleNotFoundError:
        import update_news as u
    recent = [r for r in archive if u.is_within_reader_window(r, now, window_hours)]
    projected = {r['id']: r for r in (versions.project(archive) if project_versions else archive)}
    reader_exclusions = reader_exclusions or {}
    raw_ids, ai_ids = {r['id'] for r in raw_pool}, {r['id'] for r in ai_pool}
    public_rows = {r['id']: r for r in [*raw_pool, *ai_pool]}
    overlay = merged.get('publisher_governance') or {}
    events = (merged.get('brief_events') or {}).get('events', [])
    decisions = {d['brief_event_id']: d for d in overlay.get('events', [])}
    annotations = {a['id']: a for a in overlay.get('articles', [])}
    selected = set(overlay.get('daily_selected_event_ids', []))
    membership = defaultdict(list)
    for event in events:
        for rid in [*event['member_article_ids'], *event.get('history_article_ids', [])]: membership[rid].append(event['brief_event_id'])
    rows = []
    for original in recent:
        rid = original['id']; row = projected[rid]
        annotated = u.add_reader_source_policy_fields(row)
        q = annotations.get(rid, {}).get('qualification') or governance.qualify(annotated, governance.source_material(row))
        reasons = list(reader_exclusions.get(rid, []))
        if row.get('source_material_status') == 'superseded_unverified':
            reasons.append('superseded_unverified')
        if (merged.get('brief_events') or {}).get('status') == 'unavailable':
            reasons.append('event_projection_unavailable')
        if row.get('duplicate_of'): reasons.append('superseded_article_version')
        if not annotated['source_policy']['allow_general']: reasons.extend(annotated['source_policy']['reason_codes'])
        # Match production normalization; the English site label must not
        # accidentally count as an AI title signal during an offline audit.
        normalized = dict(row, title=u.to_zh_hant(str(row.get('title') or '')),
                          site_name=u.apply_site_name_alias(str(row.get('site_name') or '')))
        relevance = public_rows.get(rid, {})
        if 'ai_is_related' not in relevance:
            relevance = u.add_ai_relevance_fields(normalized)
        if not relevance.get('ai_is_related'):
            reasons.append('ai_relevance_below_floor')
            reasons.append(relevance.get('ai_relevance_reason') or 'ai_reason_unavailable')
        if q['scope'] == 'out_of_scope': reasons.append('out_of_scope')
        reasons += material_gaps(row, q)
        if rid not in ai_ids and relevance.get('ai_is_related') and annotated['source_policy']['allow_general'] and q['scope'] != 'out_of_scope' and not reasons:
            reasons.append('historical_reader_filter_trace_unavailable')
        rows.append({'article_id': rid, 'url': row.get('url'),
            'fetch_observed': rid in fetched_ids if fetched_ids is not None else None,
            'archived': True, 'first_seen_at': original.get('first_seen_at'), 'last_seen_at': original.get('last_seen_at'),
            'in_window': True, 'in_raw_pool': rid in raw_ids, 'in_ai_pool': rid in ai_ids,
            'superseded_by': row.get('duplicate_of'), 'event_ids': membership[rid],
            'aggregation_status': 'aggregated' if membership[rid] else 'not_in_event_projection',
            'reason_codes': sorted(set(reasons))})
    traces = []
    for e in events:
        eid = e['brief_event_id']; d = decisions.get(eid, {})
        reasons = list(d.get('reason_codes') or [])
        if d.get('featured_eligible') and eid not in selected:
            impact = d.get('supplement_impact') or {}
            reasons.append('supplement_impact_gate' if d.get('selection_class') == 'supplement' and not impact.get('passes') else 'diversity_or_capacity')
        refs = e['sources']; active = [r for r in refs if r.get('role') == 'active_phase']
        article_reasons = {r['article_id']: list(r['reason_codes']) for r in rows if eid in r['event_ids']}
        for ref in refs:
            blockers = article_reasons.setdefault(ref['id'], [])
            if ref.get('role') != 'active_phase': blockers.append('not_current_active_phase')
            if not ref.get('corroboration_key'): blockers.append('publisher_identity_not_countable')
            annotation = annotations.get(ref['id'], {})
            if annotation and not annotation.get('source_policy', {}).get('allow_featured'):
                blockers.append('not_permitted_for_featured')
        traces.append({'event_id': eid, 'article_ids': e['member_article_ids'],
            'eligible': bool(d.get('featured_eligible')), 'selected': eid in selected,
            'selection_class': d.get('selection_class'), 'featured_score': d.get('featured_score'),
            'effective_at': e.get('effective_at'), 'expires_at': e.get('expires_at'),
            'reason_codes': reasons, 'article_reasons': article_reasons,
            'raw_record_count': e.get('raw_record_count', len(refs)), 'article_count': len({versions.article_key(r) or r['id'] for r in active}),
            'independent_publisher_count': len({r['corroboration_key'] for r in active if r.get('corroboration_key')}),
            'qualified_publisher_count': d.get('qualified_source_count', 0), 'supplement_impact': d.get('supplement_impact')})
    groups = Counter(versions.article_key(r) or r['id'] for r in recent)
    current = [projected[r['id']] for r in recent if not projected[r['id']].get('duplicate_of')]
    leads = []
    for row in recent:
        if row['id'] in ai_ids and any(decisions.get(e, {}).get('featured_eligible') for e in membership[row['id']]): continue
        for hint in signals(str(row.get('title') or '') + '\n' + str(row.get('summary') or '')):
            leads.append({'article_id': row['id'], 'signal': hint, 'evidence_status': 'needs_primary_source',
                'search_query': hint, 'publisher_links': row.get('publisher_links', []),
                'reason_codes': next(r['reason_codes'] for r in rows if r['article_id'] == row['id'])})
    event_keys = defaultdict(set)
    for event in events:
        for ref in event['sources']:
            if ref.get('role') == 'active_phase':
                event_keys[versions.article_key(ref) or ref['id']].add(event['brief_event_id'])
    counts = {'fetched_raw_records': status.get('fetched_raw_items'), 'window_raw_records': len(recent),
        'current_records': len(current), 'unique_articles': len({versions.article_key(r) or r['id'] for r in current}),
        'public_raw_pool_articles': len(raw_ids), 'ai_pool_articles': len(ai_ids),
        'events': len(events), 'selected_events': len(selected),
        'same_url_version_groups': sum(v > 1 for v in groups.values()),
        'superseded_records': sum(bool(projected[r['id']].get('duplicate_of')) for r in recent),
        'summary_missing': sum(not r.get('summary') for r in current),
        'summary_stale_preview': sum(versions.stale_summary(r) for r in recent),
        'summary_stale_preview_visible': sum(versions.stale_summary(r) for r in public_rows.values()),
        'summary_placeholder': sum(bool(re.fullmatch(r'(?:read more|click here|continue reading|閱讀全文|閱讀更多|查看全文)[.。… ]*', str(r.get('summary') or ''), re.I)) for r in current),
        'events_single_publisher': sum(e['independent_publisher_count'] == 1 for e in traces),
        'events_without_identified_publisher': sum(e['independent_publisher_count'] == 0 for e in traces),
        'duplicate_event_id_count': len(events) - len({e['brief_event_id'] for e in events}),
        'articles_in_multiple_active_events': sum(len(ids) > 1 for ids in event_keys.values()),
        'high_impact_review_leads': len(leads)}
    sources = []
    for site in status.get('sites', []):
        native = [r for r in archive if r.get('site_id') == site.get('site_id')]
        def latest(field):
            return max((r.get(field) for r in native if u.parse_iso(r.get(field))), key=u.parse_iso, default=None)
        seen = latest('last_seen_at')
        sources.append({'site_id': site.get('site_id'), 'ok': site.get('ok'),
            'item_count': site.get('item_count'), 'error': site.get('error'),
            'latest_published_at': latest('published_at'), 'latest_observed_at': seen,
            'observation_age_seconds': max(0, (now-u.parse_iso(seen)).total_seconds()) if seen else None})
    attempted = [s for s in sources if isinstance(s['ok'], bool)]
    return {'schema_version': 1, 'generated_at': u.iso(now), 'counts': counts,
        'event_generation_status': (merged.get('brief_events') or {}).get('status'),
        'source_health': {'generated_at': status.get('generated_at'), 'scope': 'top_level_source_groups',
            'success_rate': sum(s['ok'] for s in attempted)/len(attempted) if attempted else None, 'sources': sources},
        'articles': rows, 'events': traces, 'review_leads': leads,
        'limitations': ['fetch_observed_null_means_no_fetch_log', 'quality_checks_are_bounded_rules_not_fact_verification',
            'review_leads_are_not_independent_evidence', 'duplicate_event_overlap_is_a_review_signal_not_automatic_merging',
            'source_health_group_success_does_not_imply_every_subfeed_succeeded']}
