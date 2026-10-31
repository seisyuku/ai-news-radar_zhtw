"""Bounded security topic/event classification from native source text only.

Topic membership is not an evidence qualification or a featured-score bonus.
No fetching, translation, model calls, or source admission lives here.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


def rx(pattern: str) -> re.Pattern:
    return re.compile(pattern, re.I)


AI = rx(r"(?<![a-z0-9])(?:AI|LLMs?|GPT[-\s]?\d[\w.-]*|ChatGPT|Codex|Claude|Gemini|DeepSeek|Qwen|GLM|Copilot|MCP|OpenAI|Anthropic)(?![a-z0-9])|人工智[能慧]|大[語语]言模型|提示[詞词]?注入|模型.{0,8}(?:越獄|越狱)|AI代理")
ISSUE = rx(r"\b(?:vulnerabilit\w*|hackers?|hacked|compromised|intrusion|cyberattacks?|flaws?|exploits?|breach(?:es)?|malware|ransomware|zero[- ]days?|RCE)\b|\bCVE-\d{4}-\d{4,}\b|駭客|黑客|漏洞|資安事件|资安事件|安全漏洞|資料外洩|資料外泄|数据泄露|憑證外洩|凭证泄露|惡意(?:軟體|套件|程式)|恶意(?:软件|包|程序)")
ATTACK = rx(r"\b(?:prompt injection|privilege escalation|remote code execution|supply.chain attack|data exfiltration|credential (?:theft|exposure)|unauthori[sz]ed access)\b|提示[詞词]?注入|供應鏈攻擊|供应链攻击|權限提升|权限提升|越權|越权|遭駭|遭骇|遭入侵|金鑰外洩|密钥泄露|(?:竊取|窃取).{0,12}(?:資料|数据|憑證|凭证)|(?:繞過|绕过).{0,12}(?:權限|权限|認證|认证)")
ACTION = rx(r"\b(?:attack(?:s|ed|ing)?|target(?:s|ed|ing)?|hack(?:s|ed|ing)?|patch(?:es|ed|ing)?|fix(?:es|ed)?|disclos\w*|discover\w*|reproduc\w*|exploit\w*|compromis\w*|leak(?:s|ed)?|expos\w*|affect\w*|permit\w*|allow\w*|caus\w*|install\w*|steal\w*|exfiltrat\w*)\b|攻擊|攻击|入侵|外洩|泄露|修補|修补|修復|修复|揭露|披露|發現|发现|公布|通報|通报|重現|复现|導致|导致|允許|允许|竊取|窃取|(?:誘使|诱使|利用).{0,20}(?:安裝|安装|執行|执行|攻擊|攻击)")
CYBER = rx(r"\b(?:cybersecurity|cyber.security|security (?:agents?|tools?|products?|research|assessment|testing)|penetration test|red.team)\b|資安|资安|網路安全|网络安全|安全(?:代理|工具|產品|产品)|滲透測試|渗透测试|紅隊|红队|(?:jailbreak|越獄|越狱)")
SUBSTANCE = rx(r"\b(?:releases?|launche[sd]?|introduce[sd]?|announc\w*|compar\w*|evaluat\w*|experiment\w*|measur\w*|tested|tests?|method\w*|results?|benchmark\w*|detect\w*|protect\w*|defen[sc]\w*|mitigat\w*|VulnOps)\b|發布|发布|推出|比較|比较|評估|评估|實驗|实验|測試|测试|方法|結果|结果|偵測|检测|防禦|防御|防護|防护|改善|漏洞管理")
NEGATION = rx(r"\b(?:no (?:confirmed |known )?|not (?:a |an )?|without (?:a |any )?|den(?:ies|ied)\b.{0,45})(?:security |data )?(?:breach|vulnerabilit|attack|exploit)|(?:並未|并未|沒有|没有|未發現|未发现|否認|否认).{0,15}(?:漏洞|外洩|泄露|攻擊|攻击|入侵)")
DISTRACTION = rx(r"\b(?:Halloween|costume|joke|satire|hackathon|teen|child|content moderation)\w*\b|萬聖節|万圣节|裝扮|装扮|玩笑|駭客松|黑客松|駭客馬拉松|黑客马拉松|青少年|兒少|儿少|內容(?:安全|審核)|内容(?:安全|审核)")
TUTORIAL = rx(r"^(?:how to\b|step.by.step\b|如何|怎麼|怎么)|教學|教程|攻略|操作指南")
RESEARCH_DETAIL = rx(r"(?:method|evaluat|experiment|test|方法|實驗|实验|測試|测试|評估|评估).{0,120}(?:results?|detect|protect|defen|結果|结果|偵測|检测|防禦|防御|防護|防护)")
PLATFORM_INCIDENT = rx(r"\b(?:breach|intrusion|hacked|compromised)\b|(?:keys?|credentials?|data).{0,25}(?:exposed|leaked|stolen)|遭.{0,12}(?:入侵|攻擊)|資料外洩|資料外泄|憑證外洩|金鑰外洩|金鑰遭")
BACKGROUND = rx(r"\blast year\b|\bhistorical (?:example|incident)\b|\bfor example\b|去年|歷史案例|历史案例")
MANAGEMENT = rx(r"vulnerability (?:discovery|management)|漏洞(?:管理|發現|发现)")
ASSERTED = rx(r"CVE-\d{4}-\d+|\b(?:disclos(?:es?|ed|ing)|patch(?:es|ed)|exploited|attacked|hacked|breached|allows?|permits?|compromised)\b|(?:已|了).{0,5}(?:修補|修补|攻擊|攻击)|(?:修補|修补|發現|发现)了|披露|揭露|允許|允许|攻擊者|攻击者|(?:駭客|黑客).{0,12}(?:攻擊|攻击)|(?:誘使|诱使|利用).{0,20}(?:安裝|安装|執行|执行|竊取|窃取)")
RELATED = rx(r"延伸閱讀|延伸阅读|相關文章|相关文章|read more|related articles")
SENTENCES = re.compile(r"[。！？!?;；\n]+|(?<!\d)\.(?:\s+|$)")


@dataclass(frozen=True)
class SecurityDecision:
    topic: bool = False
    event: bool = False


def classify(record: dict[str, Any], *, platform_admitted: bool = False) -> SecurityDecision:
    title = RELATED.split(str(record.get("title_original") or record.get("title") or ""), 1)[0][:1600]
    summary = RELATED.split(str(record.get("summary") or ""), 1)[0][:1600]
    # Separate fields/clauses prevent a joke or unrelated lead borrowing an
    # event verb elsewhere. Titles alone can disclose a specific event.
    clauses = [c.strip() for field in (title, summary) for c in SENTENCES.split(field) if c.strip()]
    relevant = []
    events = []
    for clause in clauses:
        if NEGATION.search(clause) or TUTORIAL.search(clause) or BACKGROUND.search(clause):
            continue
        issue, attack = bool(ISSUE.search(clause)), bool(ATTACK.search(clause))
        action = bool(ACTION.search(clause))
        event = ((issue or attack) and action) or bool(platform_admitted and PLATFORM_INCIDENT.search(clause))
        # A CVE is a concrete identifier; a bare generic vulnerability title
        # without action or supporting material does not establish an event.
        event = event or bool(re.search(r"\bCVE-\d{4}-\d{4,}\b", clause, re.I) and issue)
        if MANAGEMENT.search(clause) and not ASSERTED.search(clause):
            event = False
        if DISTRACTION.search(clause) and not (event and ASSERTED.search(clause)):
            continue
        if event:
            events.append(clause)
        if event or ((issue or attack or CYBER.search(clause)) and SUBSTANCE.search(clause)):
            relevant.append(clause)
    if (CYBER.search(title) and not DISTRACTION.search(title)
            and not TUTORIAL.search(title) and not NEGATION.search(title)
            and any(RESEARCH_DETAIL.search(c) and not NEGATION.search(c)
                    and not BACKGROUND.search(c) for c in SENTENCES.split(summary))):
        relevant.append(title)
    context = bool(AI.search(title + "\n" + summary)) or platform_admitted
    return SecurityDecision(topic=bool(relevant) and context, event=bool(events))


def annotate(record: dict[str, Any], *, platform_admitted: bool = False) -> dict[str, Any]:
    return {**record, "security_topic": classify(record, platform_admitted=platform_admitted).topic}
