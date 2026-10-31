// Pure section classification; classic browser script and direct CommonJS API.
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.AiRadarSelection = api;
})(globalThis, function () {
  "use strict";

  function itemHaystack(item) {
    return [
      item.title,
      item.title_zh,
      item.title_en,
      item.title_original,
      item.source,
      item.site_name,
      item.site_id,
      item.ai_label,
      ...(Array.isArray(item.ai_signals) ? item.ai_signals : []),
    ].filter(Boolean).join(" ").toLowerCase();
  }

  function matchesAny(text, patterns) {
    return patterns.some((pattern) => pattern.test(text));
  }

  function itemSections(item) {
    const hay = itemHaystack(item);
    const contentHay = [
      item.title,
      item.title_zh,
      item.title_en,
      item.title_original,
      item.source,
      item.site_name,
      item.site_id,
      ...(Array.isArray(item.ai_signals) ? item.ai_signals : []),
    ].filter(Boolean).join(" ").toLowerCase();
    const sections = new Set();
    const label = item.ai_label || "";
    const hasExplicitModelTerm = matchesAny(contentHay, [
      /gpt[-\s]?\d|claude|gemini|grok|llama|qwen|deepseek|mistral|kimi\s?k\d|glm|gemma|模型|model|weights|权重|權重|多模态|多模態|视频生成|影片生成|diffusion|sora|seedance|llm|大模型/,
    ]);
    const looksLikeToolOrProduct = matchesAny(hay, [
      /skill|copilot|codex|cli|api|sdk|dashboard|workflow|tool|工具|助手|应用|應用|插件|外掛|工作流|支付宝|支付寶|浏览器|瀏覽器|搜索|搜尋/,
    ]);

    if (
      hasExplicitModelTerm ||
      (label === "model_release" && !looksLikeToolOrProduct)
    ) sections.add("models");

    if (
      label === "ai_product_update" ||
      label === "agent_workflow" ||
      label === "robotics" ||
      matchesAny(hay, [
        /app|product|agent|workflow|siri|copilot|chatgpt|perplexity|runway|suno|支付宝|支付寶|产品|產品|应用|應用|智能体|智慧體|机器人|機器人|浏览器|瀏覽器|搜索|搜尋|助手|生成工具|办公|辦公|教育/,
      ])
    ) sections.add("products");

    if (
      label === "developer_tool" ||
      label === "developer_tooling" ||
      label === "infra_compute" ||
      matchesAny(hay, [
        /github|cursor|codex|copilot|openrouter|api|sdk|mcp|cli|framework|inference|推理|开发者|開發者|开源|開源|代码|程式碼|编程|程式設計|算力|芯片|晶片|nvidia|cloud|部署|benchmarking|token/,
      ])
    ) sections.add("devtools");

    if (
      label === "industry_business" ||
      matchesAny(hay, [
        /funding|raised|ipo|acquire|acquisition|lawsuit|regulation|policy|white house|pentagon|nvidia|salesforce|meta|microsoft|融资|融資|收购|收購|上市|监管|監管|政策|裁员|裁員|估值|债券|債券|芯片|晶片|公司|行业|行業|政府|五角大楼|五角大樓|白宫|白宮/,
      ])
    ) sections.add("industry");

    if (
      label === "research_paper" ||
      matchesAny(hay, [
        /paper|arxiv|research|benchmark|eval|dataset|lmsys|rdi|berkeley|huggingface daily papers|论文|論文|研究|基准|基準|评测|評測|数据集|資料集|训练|訓練|k-means|speculative decoding/,
      ])
    ) sections.add("research");

    if (item.security_topic === true) sections.add("security");

    if (!sections.size) sections.add("industry");
    return sections;
  }

  function itemMatchesSection(item, sectionId) {
    return sectionId === "hot" || itemSections(item).has(sectionId);
  }

  return { itemSections, itemMatchesSection };
});
