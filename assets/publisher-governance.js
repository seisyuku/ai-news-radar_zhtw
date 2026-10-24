(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.AiRadarGovernance = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const POLICY = "publisher-governance-v1";
  const kinds = ["earnings", "market", "security", "pricing", "benchmark", "model_release"];
  const ordered = (x) => Array.isArray(x) ? x.map(ordered) : x && typeof x === "object"
    ? Object.fromEntries(Object.keys(x).sort().map((k) => [k, ordered(x[k])])) : x;
  const same = (a, b) => JSON.stringify(ordered(a)) === JSON.stringify(ordered(b));
  const unique = (xs) => Array.isArray(xs) && new Set(xs).size === xs.length;
  const subset = (xs, ys) => Array.isArray(xs) && xs.every((x) => ys.includes(x));
  const setSame = (a, b) => unique(a) && unique(b) && a.length === b.length && subset(a, b);
  const safeUrl = (s) => { try { const u = new URL(s); return /^https?:$/.test(u.protocol) && !u.username && !u.password && String(s).length <= 2048; } catch { return false; } };
  const permitted = (a, use, revision) => a?.publisher?.schema_version === 1 && a.publisher.status === "identified"
    && a.source_policy?.schema_version === 1 && a.source_policy.policy_id === POLICY
    && a.source_policy.registry_revision === revision
    && ["approved", "limited"].includes(a.source_policy.admission_status) && a.source_policy[`allow_${use}`] === true;
  const supported = (a) => (a?.qualification?.core_evidence || []).filter((e) => e.status === "supported").map((e) => e.kind);
  function allowedKinds(event, a) {
    const required = { security_disclosure: "security", pricing_change: "pricing", model_release: "model_release",
      speed_tier_release: "model_release", platform_availability: "model_release" }[event.identity?.action];
    return supported(a).filter((kind) => !required || required === kind);
  }
  function sameSubject(event, ref) {
    const subject = event.identity?.subject || "";
    if (!/^(?:model|software|product):/.test(subject)) return true;
    const compact = (s) => String(s).normalize("NFKC").toLowerCase().replace(/[^a-z0-9]/g, "");
    return compact(ref.source_material?.title_original || ref.source_material?.title || "").includes(compact(subject.split(":").slice(1).join(":")));
  }

  function validMaterial(a, ref) {
    if (!a || typeof a.id !== "string" || !a.id || a.id.length > 256 || !a.ingress || !a.publisher || !a.source_policy
      || !a.qualification || !["in_scope", "out_of_scope", "unknown"].includes(a.qualification.scope)
      || !Array.isArray(a.qualification.core_evidence) || a.qualification.core_evidence.length > 6) return false;
    const evidenceKinds = [];
    for (const e of a.qualification.core_evidence) {
      if (!kinds.includes(e.kind) || !["supported", "insufficient", "conflict"].includes(e.status)
        || !["official_primary", "technical_primary", "editorial_report", "insufficient"].includes(e.basis)
        || !Array.isArray(e.spans) || e.spans.length > 12 || !Array.isArray(e.urls) || e.urls.length > 24
        || !unique(e.urls) || e.urls.some((u) => !safeUrl(u)) || (e.status === "supported" && !e.spans.length)) return false;
      evidenceKinds.push(e.kind);
      for (const span of e.spans) {
        const text = ref.source_material?.[span.field];
        if (!["title_original", "title", "summary"].includes(span.field) || typeof text !== "string"
          || !Number.isSafeInteger(span.start) || !Number.isSafeInteger(span.end)
          || span.start < 0 || span.end <= span.start || span.end > 100000
          || typeof span.text !== "string" || !span.text || Array.from(span.text).length > 1600
          || Array.from(text).slice(span.start, span.end).join("") !== span.text) return false;
      }
    }
    return unique(evidenceKinds);
  }

  function valid(parent, now = Date.now()) {
    try {
      const g = parent?.publisher_governance, p = parent?.brief_events;
      if (!g || !p || g.record_type !== "publisher_governance_projection" || g.schema_version !== 1
        || g.policy_id !== POLICY || g.status !== "ready" || !/^[0-9a-f]{64}$/.test(g.registry_revision || "")
        || !/^pg1_[0-9a-f]{24}$/.test(g.generation_id || "") || !/^bg1_[0-9a-f]{24}$/.test(p.generation_id || "")
        || !/^[0-9a-f]{64}$/.test(p.state_revision || "") || !["ready", "recovered"].includes(p.status)
        || p.record_type !== "brief_event_projection" || p.history_complete !== false
        || p.matcher_version !== "brief-event-v1" || p.schema_version !== 1
        || !Number.isFinite(Date.parse(g.generated_at)) || Date.parse(g.generated_at) > now + 300000
        || g.generated_at !== parent.generated_at || g.generated_at !== p.generated_at
        || g.brief_generation_id !== p.generation_id || g.brief_state_revision !== p.state_revision
        || !Array.isArray(g.articles) || g.articles.length > 100000 || !Array.isArray(g.events) || g.events.length > 10000
        || !Array.isArray(p.events) || p.events.length > 10000 || !unique(p.selected_event_ids)
        || !g.diagnostics || !Array.isArray(g.diagnostics.errors) || g.diagnostics.errors.length
        || new TextEncoder().encode(JSON.stringify(g)).length > 8388608
        || new TextEncoder().encode(JSON.stringify(p)).length > 8388608) return false;
      const articles = new Map(g.articles.map((a) => [a.id, a]));
      const events = new Map(p.events.map((e) => [e.brief_event_id, e]));
      const decisions = new Map(g.events.map((e) => [e.brief_event_id, e]));
      if (articles.size !== g.articles.length || events.size !== p.events.length || decisions.size !== g.events.length
        || !setSame([...events.keys()], [...decisions.keys()])) return false;
      const refIds = new Set(), eligible = [];
      for (const [eid, event] of events) {
        const d = decisions.get(eid);
        if (!/^be1_[0-9a-f]{24}$/.test(eid) || !/^bp1_[0-9a-f]{24}$/.test(event.active_phase_id || "")
          || d.active_phase_id !== event.active_phase_id || !Array.isArray(event.sources) || !unique(event.member_article_ids)
          || !Array.isArray(event.business_events) || typeof d.featured_eligible !== "boolean"
          || !unique(d.support_article_ids) || !unique(d.qualified_corroboration_keys)
          || !Number.isSafeInteger(d.qualified_source_count) || d.qualified_source_count < 0) return false;
        const refs = new Map(event.sources.map((r) => [r.id, r]));
        if (refs.size !== event.sources.length || !setSame([...refs.keys()], event.member_article_ids) || !refs.has(event.primary_item?.id)) return false;
        for (const [rid, ref] of refs) {
          const a = articles.get(rid), sp = a?.source_policy;
          refIds.add(rid);
          if (!validMaterial(a, ref) || sp.schema_version !== 1 || sp.policy_id !== POLICY || sp.registry_revision !== g.registry_revision
            || !["approved", "limited", "unreviewed", "excluded"].includes(sp.admission_status)
            || !["active_phase", "past_phase", "context_unknown"].includes(ref.role)
            || !/^bp1_[0-9a-f]{24}$/.test(ref.phase_id || "") || !safeUrl(ref.url)
            || ["ingress", "publisher", "source_policy"].some((k) => !same(ref[k], a[k]))
            || (sp.admission_status === "unreviewed" && (sp.source_tier !== "watchlist" || sp.source_tier_rank !== 6 || sp.allow_featured || sp.allow_radar))
            || (sp.admission_status === "excluded" && (sp.allow_general || sp.allow_featured || sp.allow_radar))) return false;
        }
        const keys = new Set();
        for (const rid of d.support_article_ids) {
          const ref = refs.get(rid), a = articles.get(rid);
          if (!ref || !event.member_article_ids.includes(rid) || ref.role !== "active_phase" || ref.phase_id !== event.active_phase_id
            || !permitted(a, "featured", g.registry_revision) || a.qualification.scope !== "in_scope"
            || !allowedKinds(event, a).length || !sameSubject(event, ref)) return false;
          if (ref.corroboration_key) keys.add(ref.corroboration_key);
        }
        if (keys.size !== d.qualified_source_count || !setSame([...keys], d.qualified_corroboration_keys)) return false;
        if (d.featured_eligible) {
          const primary = d.featured_primary_item, rid = d.featured_primary_article_id;
          if (event.eligible !== true || !(Date.parse(event.effective_at) <= Date.parse(g.generated_at)
            && Date.parse(g.generated_at) < Date.parse(event.expires_at)) || !Number.isFinite(Date.parse(event.expires_at))
            || Date.parse(event.expires_at) - Date.parse(event.effective_at) !== 86400000
            || !d.support_article_ids.includes(rid) || primary?.id !== rid || !safeUrl(primary.url)
            || typeof primary.title !== "string" || primary.title.length > 20000
            || ["id", "title", "url", "publisher", "source_policy", "source_material"].some((k) => !same(primary[k], refs.get(rid)[k]))
            || typeof d.featured_score !== "number" || !Number.isFinite(d.featured_score) || d.featured_score < 0 || d.featured_score > 1
            || !unique(d.featured_business_events) || !d.featured_business_events.length
            || !subset(d.featured_business_events, allowedKinds(event, articles.get(rid)))) return false;
          if (d.eligibility_basis === "official_primary") { if (articles.get(rid).source_policy.publisher_kind !== "official") return false; }
          else if (d.eligibility_basis === "multiple_qualified_publishers") { if (keys.size < 2) return false; }
          else if (d.eligibility_basis !== "qualified_score" || d.featured_score < .72) return false;
          if (d.featured_news_summary !== null) {
            if (typeof d.featured_news_summary !== "string" || d.featured_news_summary.length > 2000
              || d.summary_article_id !== rid || event.primary_item.id !== rid || event.news_summary !== d.featured_news_summary) return false;
          } else if (d.summary_article_id !== null) return false;
          eligible.push(eid);
        } else if (["eligibility_basis", "featured_primary_article_id", "featured_primary_item", "featured_score", "featured_news_summary", "summary_article_id"].some((k) => d[k] !== null) || d.featured_business_events?.length !== 0) return false;
      }
      return setSame([...refIds], [...articles.keys()]) && setSame(eligible, g.featured_event_ids)
        && unique(g.daily_selected_event_ids) && g.daily_selected_event_ids.length <= 20
        && subset(g.daily_selected_event_ids, eligible) && same(g.daily_selected_event_ids, p.selected_event_ids);
    } catch { return false; }
  }

  function view(event, d) {
    const refs = event.sources.filter((r) => d.support_article_ids.includes(r.id)), primary = d.featured_primary_item;
    const out = { ...event, primary_item: primary, title: primary.title, url: primary.url, primary_url: primary.url,
      source: primary.source || "", source_name: primary.source_name || "", sources: refs, items: refs, all_sources: event.sources,
      source_count: refs.length, corroboration_count: d.qualified_source_count, duplicate_count: Math.max(1, d.qualified_source_count),
      score: d.featured_score, importance: d.featured_score, importance_score: d.featured_score,
      business_events: d.featured_business_events, publisher_qualified: true,
      governance_publisher_key: primary.corroboration_key || `publisher:${primary.publisher.publisher_id}` };
    Object.keys(out).filter((k) => k.startsWith("news_summary")).forEach((k) => delete out[k]);
    if (d.featured_news_summary) out.news_summary = d.featured_news_summary;
    return out;
  }

  function metaMatches(meta, g) {
    return meta && ["schema_version", "policy_id", "registry_revision", "generated_at", "brief_generation_id", "brief_state_revision", "generation_id", "status"].every((k) => meta[k] === g[k]);
  }

  function validDaily(daily, parent) {
    const g = parent.publisher_governance, p = parent.brief_events;
    if (!metaMatches(daily?.publisher_governance_meta, g) || !Array.isArray(daily.items)
      || daily.total_items !== daily.items.length || !same(daily.items.map((e) => e.brief_event_id), g.daily_selected_event_ids)
      || daily.brief_event_meta?.generation_id !== p.generation_id || daily.brief_event_meta?.generated_at !== p.generated_at
      || !same(daily.brief_event_meta?.selected_event_ids, p.selected_event_ids)
      || daily.selection_diagnostics?.selected_count !== daily.items.length) return false;
    const decisions = new Map(g.events.map((d) => [d.brief_event_id, d]));
    const events = new Map(p.events.map((e) => [e.brief_event_id, e]));
    return daily.items.every((item) => {
      const wanted = view(events.get(item.brief_event_id), decisions.get(item.brief_event_id));
      return ["primary_item", "title", "url", "business_events", "score", "corroboration_count", "news_summary"].every((k) => same(item[k], wanted[k]));
    });
  }

  function resolve(state, now = Date.now()) {
    const parent = state.storiesMerged, incoming = parent?.publisher_governance;
    const signals = [state.latestGovernanceMeta, state.dailyBrief?.publisher_governance_meta, state.llmRadarGovernanceMeta, state.allGovernanceMeta].filter(Boolean);
    const previous = state.publisherGovernanceWatermark;
    const observations = [...signals, ...(incoming ? [incoming] : [])].filter((m) => Number.isFinite(Date.parse(m.generated_at)) && /^[0-9a-f]{64}$/.test(m.registry_revision || ""));
    let watermark = previous;
    for (const m of observations) {
      const time = Date.parse(m.generated_at);
      if (!watermark || time > watermark.time) watermark = { time, revision: m.registry_revision, conflict: false };
      else if (time === watermark.time && m.registry_revision !== watermark.revision) watermark = { ...watermark, conflict: true };
    }
    state.publisherGovernanceWatermark = watermark;
    const reject = () => { state.publisherGovernanceCache = null; return { projection: null, governance: null, cached: false }; };
    const acceptable = (candidate) => {
      const g = candidate.publisher_governance;
      return valid(candidate, now) && (!watermark || (Date.parse(g.generated_at) >= watermark.time && !watermark.conflict && g.registry_revision === watermark.revision))
        && metaMatches(state.latestGovernanceMeta, g) && (!state.generatedAt || state.generatedAt === g.generated_at)
        && (!state.dailyBrief || validDaily(state.dailyBrief, candidate))
        && signals.every((s) => metaMatches(s, g));
    };
    if (incoming?.status === "unavailable" || signals.some((s) => s.status !== "ready") || watermark?.conflict) return reject();
    if (incoming) {
      if (!acceptable(parent)) return reject();
      state.publisherGovernanceCache = JSON.parse(JSON.stringify(parent));
    } else if (parent?.brief_events || parent?.publisher_governance) return reject();
    const candidate = state.publisherGovernanceCache;
    if (!candidate || !acceptable(candidate)) return reject();
    const g = candidate.publisher_governance, p = candidate.brief_events;
    const decisions = new Map(g.events.map((d) => [d.brief_event_id, d]));
    const events = p.events.filter((e) => decisions.get(e.brief_event_id).featured_eligible
      && Date.parse(e.effective_at) <= now && now < Date.parse(e.expires_at)).map((e) => view(e, decisions.get(e.brief_event_id)));
    return { projection: { ...p, events }, governance: g, cached: !incoming };
  }

  function radarEvents(events, meta, state, now = Date.now()) {
    const resolved = resolve(state, now), g = resolved.governance;
    if (!g || !metaMatches(meta, g)) return [];
    return (Array.isArray(events) ? events : []).filter((e) => {
      const when = Date.parse(e.effective_at || e.published_at || e.first_seen_at);
      const tracking = e.source_policy?.scope_id === "llm_stats";
      return permitted(e, "radar", g.registry_revision) && Number.isFinite(when) && when <= now && now < when + 86400000
        && (tracking || (e.qualification?.scope === "in_scope" && supported(e).includes("model_release")));
    });
  }
  return { valid, resolve, view, metaMatches, radarEvents };
});
