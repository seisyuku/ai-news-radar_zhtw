const assert = require("node:assert/strict");
const test = require("node:test");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const selection = require("../assets/selection.js");

test("section contracts preserve empty fields, hot and unknown section behavior", () => {
  assert.deepEqual([...selection.itemSections({})], ["industry"]);
  assert.equal(selection.itemMatchesSection({}, "industry"), true);
  assert.equal(selection.itemMatchesSection({}, "unknown"), false);
  assert.equal(selection.itemMatchesSection(null, "hot"), true);
  assert.throws(() => selection.itemMatchesSection(null, "models"), TypeError);
  assert.deepEqual([...selection.itemSections({ ai_signals: "not-an-array" })], ["industry"]);
});

test("model versus product terms and multilingual section signals remain distinct", () => {
  assert.equal(selection.itemMatchesSection({ title: "Qwen model weights released" }, "models"), true);
  assert.equal(selection.itemMatchesSection({ title: "Codex CLI update", ai_label: "model_release" }, "models"), false);
  assert.equal(selection.itemMatchesSection({ title: "Codex CLI update", ai_label: "developer_tool" }, "devtools"), true);
  assert.equal(selection.itemMatchesSection({ ai_label: "robotics" }, "products"), true);
  assert.equal(selection.itemMatchesSection({ title_zh: "模型評測研究" }, "research"), true);
  assert.equal(selection.itemMatchesSection({ source: "36氪" }, "community"), true);
  assert.equal(selection.itemMatchesSection({ title: "Company funding IPO" }, "industry"), true);
});

test("classification reads publisher/signals fields and does not mutate inputs", () => {
  const item = { title: "Release", ai_signals: ["arxiv", "MCP"], source: "Example" };
  const before = JSON.stringify(item);
  assert.equal(selection.itemMatchesSection(item, "research"), true);
  assert.equal(selection.itemMatchesSection(item, "devtools"), true);
  selection.itemSections(item).clear();
  assert.equal(selection.itemMatchesSection(item, "research"), true);
  assert.equal(JSON.stringify(item), before);
});

test("classic browser export works without app, DOM, network or state", () => {
  const context = {};
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(__dirname, "../assets/selection.js"), "utf8"), context);
  assert.equal(context.AiRadarSelection.itemMatchesSection({ title: "New model" }, "models"), true);
  assert.deepEqual(Object.keys(context.AiRadarSelection).sort(), ["itemMatchesSection", "itemSections"]);
});
