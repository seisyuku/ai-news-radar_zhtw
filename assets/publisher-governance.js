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
  const compareIds = (a, b) => {
    const left = Array.from(a), right = Array.from(b);
    for (let i = 0; i < Math.min(left.length, right.length); i++) {
      const delta = left[i].codePointAt(0) - right[i].codePointAt(0);
      if (delta) return delta;
    }
    return left.length - right.length;
  };
  const safeUrl = (s) => { try { const u = new URL(s); return /^https?:$/.test(u.protocol) && !u.username && !u.password && String(s).length <= 2048; } catch { return false; } };
  const permitted = (a, use, revision) => a?.publisher?.schema_version === 1 && a.publisher.status === "identified"
    && a.source_policy?.schema_version === 1 && a.source_policy.policy_id === POLICY
    && a.source_policy.registry_revision === revision
    && ["approved", "limited"].includes(a.source_policy.admission_status) && a.source_policy[`allow_${use}`] === true;
  const supported = (a) => (a?.qualification?.core_evidence || []).filter((e) => e.status === "supported").map((e) => e.kind);
  function allowedKinds(event, a) {
    if (a?.qualification?.core_evidence?.some((e) => e.status === "conflict")) return [];
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
      if (!validSpans(e, ref)) return false;
      evidenceKinds.push(e.kind);
    }
    const s = a.supplement_evidence;
    if (!unique(evidenceKinds) || !s || ![null, "industry_news", "capability_disclosure"].includes(s.kind)
      || !unique(s.qualifiers) || !subset(s.qualifiers, ["provider_claim", "unreleased"])
      || !validSpans(s, ref) || !Array.isArray(ref.source_links) || ref.source_links.length > 24
      || ref.source_links.some((u) => !safeUrl(u)) || typeof ref.source_site_name !== "string") return false;
    if (s.kind === null) return !s.spans.length && !s.urls.length && !s.qualifiers.length;
    if (a.qualification.scope !== "in_scope" || !s.spans.length || a.qualification.core_evidence.some((e) => e.status === "conflict")) return false;
    const field = ref.source_material.title_original ? "title_original" : "title";
    const bounded = (text) => Array.from(String(text || "").split(/延伸閱讀|延伸阅读|相關文章|相关文章|read more|related articles/i)[0]).slice(0, 1600).join("");
    const title = bounded(ref.source_material[field]), summary = bounded(ref.source_material.summary);
    const spans = [[field, title], ["summary", summary]].filter(([, text]) => text)
      .map(([field, text]) => ({ field, start: 0, end: Array.from(text).length, text }));
    if (!same(s.spans, spans)) return false;
    if (s.kind === "industry_news" && (s.qualifiers.length || a.qualification.core_evidence.length)) return false;
    if (s.kind === "capability_disclosure") {
      const native = `${title}\n${summary}`;
      const unreleased = /\bunreleased\b|\bunpublished\b|not (?:yet )?(?:released|available)|未(?:發[布佈表]|发布|公開|公开)|尚未(?:發[布佈表]|发布|公開|公开)/i.test(native);
      if (!same(s.qualifiers, unreleased ? ["provider_claim", "unreleased"] : ["provider_claim"])) return false;
    }
    return true;
  }

  function validSpans(e, ref) {
    if (!Array.isArray(e.spans) || e.spans.length > 12 || !unique(e.urls) || e.urls.length > 24
      || e.urls.some((u) => !safeUrl(u) || ![ref.url, ...ref.source_links].includes(u))) return false;
    return e.spans.every((span) => {
      const text = ref.source_material?.[span.field];
      return ["title_original", "title", "summary"].includes(span.field) && typeof text === "string"
        && Number.isSafeInteger(span.start) && Number.isSafeInteger(span.end) && span.start >= 0
        && span.end > span.start && span.end <= 100000 && typeof span.text === "string"
        && Array.from(span.text).length <= 1600
        && Array.from(text).slice(span.start, span.end).join("") === span.text;
    });
  }

  function existingKey(ref) {
    if (ref.publisher?.status !== "identified") return false;
    const pid = ref.publisher.publisher_id;
    return ref.corroboration_key === (["aibase", "kr36", "juya"].includes(pid) ? "cn_aggregator" : `publisher:${pid}`);
  }

  function impactScore(native, basis) {
    const bounded = (s) => Array.from(String(s || "").split(/延伸閱讀|延伸阅读|相關文章|相关文章|read more|related articles/i)[0]).slice(0, 1600).join("");
    const title = bounded(native?.title_original || native?.title), summary = bounded(native?.summary);
    if (!title) return { i: 0, p: 0, e: 0, c: 0, total: 0, passes: false };
    const text = `${title}\n${summary}`;
    const dollars = (s) => {
      const values = [...s.matchAll(/(?:US\s*)?\$\s*(\d+(?:\.\d+)?)\s*(billion|bn|million|m)\b/gi)]
        .map((m) => Number(m[1]) * (/^(?:billion|bn)$/i.test(m[2]) ? 1e9 : 1e6));
      for (const m of s.matchAll(/(\d+(?:\.\d+)?)\s*(億|万|萬)\s*(?:美[元金]|USD)/gi))
        values.push(Number(m[1]) * (m[2] === "億" ? 1e8 : 1e4));
      return Math.max(0, ...values);
    };
    const capital = /acquir|acquisition|merger|收購|收购|併購|并购/i.test(title);
    const finance = /\b(?:funding|financing|investment|invests?|offering|stock sale|raises?|raised|secures?|secured)\b|融資|募資|投資|股票發行/i.test(title) || capital;
    const amount = finance ? dollars(text) : 0;
    const savings = /\b(?:annual cost savings|realized savings|saved in operating costs)\b|年度節省成本|已節省成本/i.test(text)
      && /\b(?:deploy\w*|contract|refinery|factory|enterprise rollout)\b|部署|合約|煉油廠/i.test(text) ? dollars(text) : 0;
    const supplyHarm = /supply.chain|發布鏈|供應鏈|official release|官方發布/i.test(text)
      && /(?<![A-Za-z0-9])(?:PyPI|container|registry|published package|malicious version)(?![A-Za-z0-9])|惡意版本|發布渠道/i.test(text)
      && /\b(?:attack|compromis\w*|malicious|stolen|breach|hacked|exfiltrat\w*)\b|入侵|惡意|竊取|外洩/i.test(text);
    const monitoredGap = /\b(?:unmonitored|monitoring gap|unobserved traffic)\b|監控缺口|未受監控/i.test(text)
      && /\d+(?:\.\d+)?\s*%/.test(summary);
    const unitCost = ([...summary.matchAll(/\$\s*\d+(?:\.\d+)?/g)].length
      + [...summary.matchAll(/\b\d+(?:\.\d+)?\s+cents?\b/gi)].length >= 2)
      && /\b(?:instead of|versus|vs\.?|compared (?:with|to))\b|對比|相較於/i.test(summary)
      && /\b(?:per|an?|one)\s+(?:hour|video|token|request|image|task)\b|每(?:小時|次|張|百萬)|一小時/i.test(text)
      && /\b(?:quality|accuracy|performance|scor\w*|error|benchmark)\b|品質|準確|效能|評測/i.test(text);
    const deployment = /\b(?:deploy\w*|contract|refinery|factory|enterprise rollout)\b|部署|合約|煉油廠/i.test(title);
    const content = /\b(?:clip|trailer|video generated|film|Odyssey)\b|影片片段|電影預告/i.test(title);
    const product = /\b(?:launch\w*|releas\w*|introduc\w*|unveil\w*|open.sourc\w*|redesign|update|integration|platform|tool)\b|推出|發布|開源|改版|更新|平台|工具/i.test(title) && !content;
    let i = supplyHarm || amount >= 1e9 ? 40 : amount >= 1e8 || savings >= 1e8 || monitoredGap ? 30
      : deployment || unitCost || (finance && amount > 0) ? 15 : product ? 5 : 0;
    if (/revenue|earnings|operating costs?|market share|營收|营收|營運成本|市佔|市占/i.test(text) && (/\d+(?:\.\d+)?\s*%/.test(text) || dollars(text) > 0)) i = Math.max(30, i);
    if (basis === "supported_core") i = Math.max(15, i);
    const p = basis === "supported_core" || supplyHarm || (finance && amount > 0) || product || deployment ? 20 : unitCost ? 10 : 0;
    const titleWords = new Set((title.toLowerCase().match(/[a-z0-9]+/g) || []));
    const newWords = new Set((summary.toLowerCase().match(/[a-z0-9]+/g) || []).filter((w) => w.length > 3 && !titleWords.has(w)));
    const cjkDetail = /[\u3400-\u9fff]/.test(summary) && Array.from(summary).length >= Array.from(title).length + 20 && !summary.includes(title);
    const detail = /\b(?:because|after|using|uses?|found|affect\w*|caus\w*|result\w*|includ\w*|add\w*|built?|deplo\w*|test\w*|quality|sav\w*|customer\w*|closed|expand\w*|leaked|entered|scor\w*)\b|引入|功能|發現|发现|影響|影响|造成|結果|结果|採用|采用|測試|测试|節省|节省|外洩|外泄|憑證|凭证|渠道/i.test(summary);
    const e = (newWords.size >= 5 || cjkDetail) && detail && !content ? 20 : 10;
    const c = content ? 0 : /\b(?:refinery|oil|bank|hospital|factory|manufacturer)\b|煉油廠|銀行|醫院|製造/i.test(title) && deployment || capital && /(?:AI|OpenAI|Anthropic)[ -]backed|(?:AI|人工智慧).{0,6}(?:支持|支援|投資)/i.test(title) && !/\b(?:model|LLM|inference)\b|模型|推理/i.test(title) ? 10
      : basis === "capability_disclosure" || /(?<![A-Za-z])(?:AI|LLM|GPT|Claude|Copilot|LiteLLM|OpenAI|Anthropic|Nvidia|Meta|Qwen)(?![A-Za-z])|\bmodel\b|人工智慧|模型|機器學習/i.test(text) ? 20 : 0;
    if (c < 20) i = Math.min(15, i);
    const total = i + p + e + c;
    return { i, p, e, c, total, passes: total >= 70 && (i >= 30 || p === 20) };
  }

  // Same bounded default selection as the producer. Filtering is deliberately
  // left to the reader; the overlay retains all candidates.
  function rank(impact, selectionClass, effective, now = Date.now()) {
    const age = Math.max(0, (now - Date.parse(effective)) / 3600000);
    const value = (impact.total + (selectionClass === "core" ? 3 : 0)) * 2 ** -Math.sqrt(age / 48) / 103;
    return Math.round(value * 10000) / 10000;
  }

  function selectIds(decisions, limit = 20, target = 5) {
    const selected = [], counts = new Map();
    const rest = decisions.filter(d => d.featured_eligible && d.supplement_impact.passes);
    const key = d => d.featured_primary_item.corroboration_key || `publisher:${d.featured_primary_item.publisher.publisher_id}`;
    while (rest.length && selected.length < Math.min(limit, target)) {
      rest.sort((a,b) => (-a.featured_score + .03 * (counts.get(key(a)) || 0))
        - (-b.featured_score + .03 * (counts.get(key(b)) || 0)) || compareIds(a.brief_event_id,b.brief_event_id));
      const d=rest.shift(); selected.push(d.brief_event_id); counts.set(key(d),(counts.get(key(d)) || 0)+1);
    }
    return selected;
  }

  function valid(parent, now = Date.now()) {
    try {
      const g = parent?.publisher_governance, p = parent?.brief_events;
      if (!g || !p || g.record_type !== "publisher_governance_projection" || g.schema_version !== 2
        || g.selection_policy !== "impact-v2" || g.default_visible_limit !== 5
        || g.policy_id !== POLICY || g.status !== "ready" || !/^[0-9a-f]{64}$/.test(g.registry_revision || "")
        || !/^pg2_[0-9a-f]{24}$/.test(g.generation_id || "") || !/^bg1_[0-9a-f]{24}$/.test(p.generation_id || "")
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
            || !Number.isSafeInteger(sp.source_tier_rank) || sp.source_tier_rank < 0 || sp.source_tier_rank > 9
            || ["allow_general", "allow_featured", "allow_radar"].some((k) => typeof sp[k] !== "boolean")
            || !["active_phase", "past_phase", "context_unknown"].includes(ref.role)
            || !/^bp1_[0-9a-f]{24}$/.test(ref.phase_id || "") || !safeUrl(ref.url)
            || ["ingress", "publisher", "source_policy"].some((k) => !same(ref[k], a[k]))
            || (sp.admission_status === "unreviewed" && (sp.source_tier !== "watchlist" || sp.source_tier_rank !== 6 || sp.allow_featured || sp.allow_radar))
            || (sp.admission_status === "excluded" && (sp.allow_general || sp.allow_featured || sp.allow_radar))) return false;
        }
        const core = [], supplements = [];
        const inWindow = event.eligible === true && Date.parse(event.effective_at) <= Date.parse(g.generated_at)
          && Date.parse(g.generated_at) < Date.parse(event.expires_at);
        for (const [rid, ref] of refs) {
          const a = articles.get(rid);
          if (!inWindow || ref.role !== "active_phase" || ref.phase_id !== event.active_phase_id || !existingKey(ref)
            || !permitted(a, "featured", g.registry_revision)) continue;
          if (a.qualification.scope === "in_scope" && allowedKinds(event, a).length && sameSubject(event, ref)) core.push(rid);
          else if (event.identity?.action === "article" && a.supplement_evidence.kind) supplements.push(rid);
        }
        const expectedSupport = core.length ? core : supplements;
        if (!setSame(d.support_article_ids, expectedSupport) || d.featured_eligible !== Boolean(expectedSupport.length)
          || !Array.isArray(d.support_scores) || !unique(d.support_scores.map((s) => s.article_id))
          || !setSame(d.support_scores.map((s) => s.article_id), expectedSupport)
          || d.support_scores.some((s) => typeof s.score !== "number" || !Number.isFinite(s.score) || s.score < 0 || s.score > 1)) return false;
        const keys = new Set();
        for (const rid of d.support_article_ids) {
          const ref = refs.get(rid), a = articles.get(rid);
          if (!ref || !event.member_article_ids.includes(rid) || ref.role !== "active_phase" || ref.phase_id !== event.active_phase_id
            || !permitted(a, "featured", g.registry_revision) || a.qualification.scope !== "in_scope"
            || (core.length && (!allowedKinds(event, a).length || !sameSubject(event, ref)))) return false;
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
            || !same(primary, { ...refs.get(rid), business_events: d.featured_business_events })
            || typeof d.featured_score !== "number" || !Number.isFinite(d.featured_score) || d.featured_score < 0 || d.featured_score > 1
            || !unique(d.featured_business_events) || !unique(d.disclosure_flags)) return false;
          const scores = new Map(d.support_scores.map((s) => [s.article_id, s.score]));
          const ranked = [...expectedSupport].sort((a, b) => scores.get(b) - scores.get(a)
            || articles.get(a).source_policy.source_tier_rank - articles.get(b).source_policy.source_tier_rank || compareIds(a, b));
          const s = articles.get(rid).supplement_evidence;
          const impact = d.supplement_impact;
          if (!same(impact, impactScore(primary.source_material, d.eligibility_basis))) return false;
          for (const id of expectedSupport) {
            const basis = core.length ? "supported_core" : articles.get(id).supplement_evidence.kind;
            const expectedScore = rank(impactScore(refs.get(id).source_material, basis), d.selection_class, event.effective_at, Date.parse(g.generated_at));
            if (scores.get(id) !== expectedScore) return false;
          }
          if (ranked[0] !== rid || d.featured_score !== scores.get(rid)
            || d.selection_class !== (core.length ? "core" : "supplement")
            || d.eligibility_basis !== (core.length ? "supported_core" : s.kind)
            || !same(d.featured_business_events, core.length ? allowedKinds(event, articles.get(rid)) : [])
            || !same(d.disclosure_flags, core.length ? [] : s.qualifiers)
            || !same(primary.business_events, d.featured_business_events)) return false;
          if (d.featured_news_summary !== null) {
            if (typeof d.featured_news_summary !== "string" || d.featured_news_summary.length > 2000
              || d.summary_article_id !== rid || event.primary_item.id !== rid || event.news_summary !== d.featured_news_summary) return false;
          } else if (d.summary_article_id !== null) return false;
          eligible.push(eid);
        } else if (["selection_class", "eligibility_basis", "featured_primary_article_id", "featured_primary_item", "featured_score", "featured_news_summary", "summary_article_id", "supplement_impact"].some((k) => d[k] !== null) || d.featured_business_events?.length !== 0 || d.disclosure_flags?.length !== 0) return false;
      }
      return setSame([...refIds], [...articles.keys()]) && setSame(eligible, g.featured_event_ids)
        && unique(g.daily_selected_event_ids) && g.daily_selected_event_ids.length <= 20
        && subset(g.daily_selected_event_ids, eligible) && same(g.daily_selected_event_ids, p.selected_event_ids)
        && same(g.daily_selected_event_ids, selectIds(g.events));
    } catch { return false; }
  }

  function view(event, d) {
    const refs = event.sources.filter((r) => d.support_article_ids.includes(r.id)), primary = d.featured_primary_item;
    const out = { ...event, primary_item: primary, title: primary.title, url: primary.url, primary_url: primary.url,
      source: primary.source || "", source_name: primary.source_name || "", sources: refs, items: refs, all_sources: event.sources,
      source_count: refs.length, corroboration_count: d.qualified_source_count, duplicate_count: Math.max(1, d.qualified_source_count),
      score: d.featured_score, importance: d.featured_score, importance_score: d.featured_score,
      business_events: d.featured_business_events, publisher_qualified: true,
      selection_class: d.selection_class, signal_label: d.selection_class === "core" ? "核心事件" : "產業動態",
      disclosure_flags: d.disclosure_flags, supplement_impact: d.supplement_impact,
      governance_publisher_key: primary.corroboration_key || `publisher:${primary.publisher.publisher_id}` };
    Object.keys(out).filter((k) => k.startsWith("news_summary")).forEach((k) => delete out[k]);
    const bonus = d.selection_class === "core" ? 3 : 0;
    out.importance_breakdown = {impact:d.supplement_impact.total, core_bonus:bonus,
      freshness:d.supplement_impact.total + bonus ? Math.round(d.featured_score * 103 / (d.supplement_impact.total + bonus) * 10000) / 10000 : 0};
    if (d.featured_news_summary) out.news_summary = d.featured_news_summary;
    return out;
  }

  function metaMatches(meta, g) {
    return meta && ["schema_version", "selection_policy", "default_visible_limit", "policy_id", "registry_revision", "generated_at", "brief_generation_id", "brief_state_revision", "generation_id", "status"].every((k) => meta[k] === g[k]);
  }

  function validDaily(daily, parent) {
    const g = parent.publisher_governance, p = parent.brief_events;
    if (!metaMatches(daily?.publisher_governance_meta, g) || !Array.isArray(daily.items)
      || daily.total_items !== daily.items.length || !same(daily.items.map((e) => e.brief_event_id), g.daily_selected_event_ids)
      || daily.brief_event_meta?.generation_id !== p.generation_id || daily.brief_event_meta?.generated_at !== p.generated_at
      || !same(daily.brief_event_meta?.selected_event_ids, p.selected_event_ids)
      || daily.selection_diagnostics?.selected_count !== daily.items.length
      || daily.selection_diagnostics?.score_gate !== null
      || daily.selection_diagnostics?.selection_policy !== g.selection_policy
      || daily.selection_diagnostics?.default_visible_limit !== 5
      || daily.selection_diagnostics?.core_count !== g.events.filter((d) => d.featured_eligible && d.supplement_impact.passes && d.selection_class === "core").length
      || daily.selection_diagnostics?.supplement_candidate_count !== g.events.filter((d) => d.featured_eligible && d.selection_class === "supplement").length) return false;
    const decisions = new Map(g.events.map((d) => [d.brief_event_id, d]));
    const events = new Map(p.events.map((e) => [e.brief_event_id, e]));
    return daily.items.every((item) => {
      const wanted = view(events.get(item.brief_event_id), decisions.get(item.brief_event_id));
      return ["primary_item", "title", "url", "business_events", "score", "corroboration_count", "news_summary", "selection_class", "signal_label", "disclosure_flags", "supplement_impact"].every((k) => same(item[k], wanted[k]));
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
      && decisions.get(e.brief_event_id).supplement_impact.passes
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
  return { valid, resolve, view, metaMatches, radarEvents, rank, impactScore };
});
