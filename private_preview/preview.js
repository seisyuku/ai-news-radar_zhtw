"use strict";

const token = document.querySelector('meta[name="preview-token"]').content;
const byId = (id) => document.getElementById(id);
let status = null;
let snapshot = null;
let original = null;
let busy = false;

function message(text, error = false) {
  const target = byId("message");
  target.textContent = text;
  target.classList.toggle("error", error);
}

function conflict(text) {
  byId("conflict-text").textContent = text;
  byId("conflict").hidden = false;
  message("偵測到版本衝突。畫面上的修改尚未套用，請先重新讀取。", true);
}

function clearConflict() { byId("conflict").hidden = true; }

async function api(path, options = {}) {
  const response = await fetch(path, {
    cache: "no-store",
    ...options,
    headers: { "X-Preview-Token": token, ...(options.headers || {}) },
  });
  if (!response.ok) {
    let body = {};
    try { body = await response.json(); } catch (_) { /* fixed generic error below */ }
    const error = new Error(body.error || "service_unavailable");
    error.code = body.error || "service_unavailable";
    error.currentRevision = body.current_revision;
    throw error;
  }
  return response;
}

async function json(path, options = {}) { return (await api(path, options)).json(); }
function baseUrl(base) { return encodeURIComponent(base); }
function requestId() { return crypto.randomUUID(); }
function post(path, payload) {
  return json(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
}

function setBusy(value) {
  busy = value;
  for (const id of ["save", "readback", "export", "restore", "choose-base", "base-choice"]) {
    byId(id).disabled = value;
  }
  byId("stories").querySelectorAll("button, input, textarea").forEach((control) => { control.disabled = value; });
}

function showStatus() {
  const shortBase = (value) => value ? `${value.slice(0, 12)}…` : "尚未選擇";
  byId("issue-date").textContent = status.issue_date + "（臺北 06:00 截止）";
  byId("delivery-status").textContent = status.meets_daily_target ? "合成準時交付" : "合成審閱／未達準時";
  byId("selected-base").textContent = shortBase(status.selected_base);
  byId("working-base").textContent = shortBase(snapshot?.base_identity);
  byId("selected-base-full").textContent = status.selected_base || "尚未選擇";
  byId("working-base-full").textContent = snapshot?.base_identity || "尚未載入";
  byId("revision").textContent = snapshot ? `${snapshot.revision}（最新 ${snapshot.current_revision}）` : "尚未載入";
  const choice = byId("base-choice");
  const current = snapshot?.base_identity || status.selected_base;
  choice.replaceChildren();
  for (const row of status.bases) {
    const option = document.createElement("option");
    option.value = row.base_identity;
    option.textContent = `${row.base_identity.slice(0, 12)}… · ${row.quality} · r${row.revision}${row.base_identity === status.selected_base ? "（已選用）" : ""}`;
    choice.append(option);
  }
  if (current) choice.value = current;
  byId("restore-revision").max = String(snapshot?.current_revision || 0);
}

function addButton(parent, text, action, label) {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = text;
  button.setAttribute("aria-label", label);
  button.addEventListener("click", action);
  parent.append(button);
  return button;
}

function renderStories() {
  const list = byId("stories");
  list.replaceChildren();
  snapshot.stories.forEach((story, index) => {
    const item = document.createElement("li");
    item.className = "story" + (story.included ? "" : " excluded");
    item.dataset.storyId = story.story_id;
    const heading = document.createElement("h3");
    heading.textContent = `第 ${index + 1} 則：${story.title}`;
    item.append(heading);
    const id = document.createElement("p");
    id.className = "story-id";
    id.textContent = `題號 ${index + 1} → story ID：${story.story_id}`;
    item.append(id);
    const controls = document.createElement("div");
    controls.className = "story-controls";
    const keep = addButton(controls, story.included ? "保留中 · 點擊排除" : "已排除 · 點擊保留", () => {
      item.dataset.included = item.dataset.included === "true" ? "false" : "true";
      const included = item.dataset.included === "true";
      item.classList.toggle("excluded", !included);
      keep.textContent = included ? "保留中 · 點擊排除" : "已排除 · 點擊保留";
      keep.setAttribute("aria-pressed", String(included));
    }, `第 ${index + 1} 則保留或排除`);
    keep.setAttribute("aria-pressed", String(story.included));
    item.dataset.included = String(story.included);
    addButton(controls, "上移", () => { if (item.previousElementSibling) list.insertBefore(item, item.previousElementSibling); renumber(); }, `第 ${index + 1} 則上移`);
    addButton(controls, "下移", () => { if (item.nextElementSibling) list.insertBefore(item.nextElementSibling, item); renumber(); }, `第 ${index + 1} 則下移`);
    item.append(controls);
    const titleLabel = document.createElement("label");
    const title = document.createElement("input");
    title.type = "text";
    title.maxLength = 4096;
    title.value = story.title;
    title.id = `title-${index}`;
    title.className = "title-field";
    titleLabel.htmlFor = title.id;
    titleLabel.textContent = `第 ${index + 1} 則標題（可聽寫）`;
    item.append(titleLabel, title);
    addButton(item, "標題恢復原稿", () => {
      title.value = original.stories.find((row) => row.story_id === story.story_id).title;
      title.dataset.reset = "true";
    }, `第 ${index + 1} 則標題恢復原稿`);
    title.addEventListener("input", () => {
      delete title.dataset.reset;
      heading.textContent = `第 ${[...list.children].indexOf(item) + 1} 則：${title.value}`;
    });
    const summaryLabel = document.createElement("label");
    const summary = document.createElement("textarea");
    summary.maxLength = 32768;
    summary.value = story.summary;
    summary.id = `summary-${index}`;
    summary.className = "summary-field";
    summaryLabel.htmlFor = summary.id;
    summaryLabel.textContent = `第 ${index + 1} 則摘要（可聽寫）`;
    item.append(summaryLabel, summary);
    addButton(item, "摘要恢復原稿", () => {
      summary.value = original.stories.find((row) => row.story_id === story.story_id).summary;
      summary.dataset.reset = "true";
    }, `第 ${index + 1} 則摘要恢復原稿`);
    summary.addEventListener("input", () => { delete summary.dataset.reset; });
    const sourceHeading = document.createElement("p");
    sourceHeading.textContent = "來源：";
    item.append(sourceHeading);
    const sources = document.createElement("ul");
    sources.className = "source-list";
    for (const source of story.sources) {
      const li = document.createElement("li");
      li.textContent = `${source.source || source.site_id || "來源"} · ${source.url || ""}`;
      sources.append(li);
    }
    item.append(sources);
    list.append(item);
  });
  if (busy) list.querySelectorAll("button, input, textarea").forEach((control) => { control.disabled = true; });
}

function renumber() {
  [...byId("stories").children].forEach((item, index) => {
    const id = item.dataset.storyId;
    item.querySelector(".story-id").textContent = `題號 ${index + 1} → story ID：${id}`;
    item.querySelector("h3").textContent = `第 ${index + 1} 則：${item.querySelector(".title-field").value}`;
    item.querySelector(".title-field").labels[0].textContent = `第 ${index + 1} 則標題（可聽寫）`;
    item.querySelector(".summary-field").labels[0].textContent = `第 ${index + 1} 則摘要（可聽寫）`;
    const buttons = item.querySelectorAll("button");
    ["保留或排除", "上移", "下移", "標題恢復原稿", "摘要恢復原稿"].forEach((action, offset) => {
      buttons[offset].setAttribute("aria-label", `第 ${index + 1} 則${action}`);
    });
  });
}

async function load(base) {
  const [latest, initial] = await Promise.all([
    json(`/api/review?base=${baseUrl(base)}`),
    json(`/api/revision?base=${baseUrl(base)}&revision=0`),
  ]);
  snapshot = latest;
  original = initial;
  status = await json("/api/status");
  showStatus();
  renderStories();
  clearConflict();
  message(`已讀取第 ${snapshot.revision} 版，共 ${snapshot.stories.length} 則；請核對題號與 story ID。`);
}

function collectPatch() {
  const entries = [...byId("stories").children];
  const order = entries.map((item) => item.dataset.storyId);
  const updates = {};
  for (const item of entries) {
    const id = item.dataset.storyId;
    const current = snapshot.stories.find((story) => story.story_id === id);
    const fields = {};
    const included = item.dataset.included === "true";
    if (included !== current.included) fields.included = included;
    const title = item.querySelector(".title-field");
    const summary = item.querySelector(".summary-field");
    if (title.dataset.reset === "true") fields.title_override = null;
    else if (title.value !== current.title) fields.title_override = title.value;
    if (summary.dataset.reset === "true") fields.summary_override = null;
    else if (summary.value !== current.summary) fields.summary_override = summary.value;
    if (Object.keys(fields).length) updates[id] = fields;
  }
  const initialOrder = snapshot.content.ordered_story_ids;
  return { ordered_story_ids: order.some((id, index) => id !== initialOrder[index]) ? order : null, updates };
}

function hasUnsavedChanges() {
  if (!snapshot) return false;
  const patch = collectPatch();
  return patch.ordered_story_ids !== null || Object.keys(patch.updates).length > 0;
}

function canDiscardChanges() {
  return !hasUnsavedChanges() || window.confirm("目前有尚未儲存的修改。要放棄並讀取其他內容嗎？");
}

async function verifiedEdit(payload) {
  if (busy || !snapshot) return;
  setBusy(true);
  try {
    const result = await post("/api/edit", payload);
    const exact = await json(`/api/revision?base=${baseUrl(payload.base_identity)}&revision=${result.applied_revision}`);
    if (exact.content_sha256 !== result.content_sha256 || exact.revision !== result.applied_revision) {
      throw new Error("readback_mismatch");
    }
    await load(payload.base_identity);
    if (snapshot.revision === result.applied_revision) {
      message(`已儲存並讀回核對第 ${result.applied_revision} 版（${result.result_code}）。`);
    } else {
      message(`第 ${result.applied_revision} 版已讀回核對；目前已有更新的第 ${snapshot.revision} 版。`, true);
    }
  } catch (error) { handleError(error); }
  finally { setBusy(false); }
}

function handleError(error) {
  if (error.code === "revision_conflict") {
    conflict(`這份校稿使用舊版本。伺服器目前版本：${error.currentRevision ?? "請重新讀取"}。`);
  } else {
    message(`操作未完成：${error.code || error.message || "service_unavailable"}。請重新讀取確認。`, true);
  }
}

byId("save").addEventListener("click", () => {
  if (!snapshot) return;
  verifiedEdit({ schema_version: 1, request_id: requestId(), issue_date: snapshot.issue_date,
    base_identity: snapshot.base_identity, expected_revision: snapshot.revision,
    operation: "patch", ...collectPatch() });
});
byId("restore").addEventListener("click", () => {
  if (!snapshot) return;
  if (!canDiscardChanges()) return;
  const value = byId("restore-revision").value;
  if (!/^\d+$/.test(value) || Number(value) > snapshot.current_revision) {
    message("請輸入 0 到目前版本的整數。", true);
    return;
  }
  verifiedEdit({ schema_version: 1, request_id: requestId(), issue_date: snapshot.issue_date,
    base_identity: snapshot.base_identity, expected_revision: snapshot.revision,
    operation: "restore", restore_revision: Number(value) });
});
byId("readback").addEventListener("click", async () => {
  if (!snapshot || busy) return;
  if (!canDiscardChanges()) return;
  setBusy(true);
  try { await load(snapshot.base_identity); } catch (error) { handleError(error); }
  finally { setBusy(false); }
});
byId("reload-conflict").addEventListener("click", () => byId("readback").click());
byId("base-choice").addEventListener("change", async (event) => {
  if (busy) return;
  if (!canDiscardChanges()) { event.target.value = snapshot.base_identity; return; }
  setBusy(true);
  try { await load(event.target.value); } catch (error) { handleError(error); }
  finally { setBusy(false); }
});
byId("choose-base").addEventListener("click", async () => {
  if (busy || !status) return;
  const base = byId("base-choice").value;
  setBusy(true);
  try {
    const result = await post("/api/select", { schema_version: 1, request_id: requestId(),
      issue_date: status.issue_date, base_identity: base, expected_control_version: status.control_version });
    status = await json("/api/status");
    if (status.selected_base !== result.selected_base) throw new Error("readback_mismatch");
    await load(base);
    message("已選用原稿，並讀回核對目前選版。");
  } catch (error) {
    if (error.code === "revision_conflict") conflict("原稿選版狀態已改變，請重新讀取後再選。 ");
    else handleError(error);
  } finally { setBusy(false); }
});
byId("export").addEventListener("click", async () => {
  if (!snapshot || busy) return;
  setBusy(true);
  try {
    const response = await api(`/api/export?base=${baseUrl(snapshot.base_identity)}&revision=${snapshot.revision}`);
    const body = await response.blob();
    const url = URL.createObjectURL(body);
    const link = document.createElement("a");
    link.href = url;
    link.download = `digest-${snapshot.issue_date}-${snapshot.base_identity.slice(0, 12)}-r${snapshot.revision}.review.json`;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    message(`已匯出第 ${snapshot.revision} 版。`);
  } catch (error) { handleError(error); }
  finally { setBusy(false); }
});

(async () => {
  try {
    status = await json("/api/status");
    if (!status.selected_base) throw new Error("no_selected_base");
    await load(status.selected_base);
  } catch (error) { handleError(error); }
})();
