"""PG05 repair III: explicit transaction predicates and complete release objects."""
import pytest
from scripts import publisher_governance as g, update_news as u, brief_events as b
from tests.test_publisher_governance import article, NOW
from tests.test_publisher_material_repair import qualification, status

RECHECK_CASES = [('N01_expected',
  'market',
  'OpenAI is expected to acquire Cedar Labs',
  'No agreement has been signed.',
  'not_supported'),
 ('N01_question',
  'market',
  'Will OpenAI acquire Cedar Labs?',
  'The companies have not announced a transaction.',
  'not_supported'),
 ('N01_conditional',
  'market',
  'If OpenAI acquires Cedar Labs, the AI market will change',
  'This is a hypothetical scenario.',
  'not_supported'),
 ('N01_unlikely',
  'market',
  'OpenAI is unlikely to acquire Cedar Labs',
  'The deal remains speculative.',
  'not_supported'),
 ('N01_disagreement',
  'market',
  'OpenAI acquires Cedar Labs',
  'OpenAI completed the acquisition despite disagreement over the price.',
  'supported'),
 ('N01_pending_approval',
  'market',
  'OpenAI signs agreement to acquire Cedar Labs',
  'Closing is subject to regulatory approval.',
  'supported'),
 ('N01_declines',
  'market',
  'OpenAI declines to acquire Cedar Labs',
  'The proposal was rejected.',
  'not_supported'),
 ('N01_cjk_question', 'market', 'OpenAI是否收購Cedar Labs？', '本文探討假設情境，雙方沒有宣布交易。', 'not_supported'),
 ('N02_updated_docs',
  'model_release',
  'OpenAI releases Photon Nova AI model updated documentation',
  'Only documentation for the existing model was updated.',
  'not_supported'),
 ('N02_api_reference',
  'model_release',
  'OpenAI releases Photon Nova AI model API reference',
  'This publication documents the existing API.',
  'not_supported'),
 ('N02_video',
  'model_release',
  'OpenAI releases Photon Nova AI model training tutorial',
  'The existing model is explained in a new tutorial.',
  'not_supported'),
 ('N02_known_updated_docs',
  'model_release',
  'OpenAI releases GPT-6.1 Sol updated documentation',
  'Only documentation for the existing model was updated.',
  'not_supported'),
 ('N02_cjk_manual', 'model_release', 'OpenAI發布Photon Nova模型新版使用手冊', '今天發布的只有使用手冊。', 'not_supported'),
 ('N02_body_with_docs',
  'model_release',
  'OpenAI releases Photon Nova AI model with updated documentation',
  'Photon Nova is now available to developers.',
  'supported'),
 ('N02_document_head',
  'model_release',
  'OpenAI releases updated documentation for Photon Nova AI model',
  'Only documentation for the existing model was updated.',
  'not_supported'),
 ('N02_body_known',
  'model_release',
  'OpenAI releases GPT-6.1 Sol with an API reference',
  'GPT-6.1 Sol is now available to developers.',
  'supported'),
 ('N03_possessive',
  'earnings',
  'OpenAI earnings discussion',
  "Cedar Labs' Q3 revenue reached $2 billion.",
  'not_supported'),
 ('N03_attribution',
  'earnings',
  'OpenAI earnings discussion',
  'According to OpenAI, Cedar Labs reports Q3 revenue of $2 billion.',
  'not_supported'),
 ('N03_reversed',
  'earnings',
  'OpenAI earnings discussion',
  'Q3 revenue at Cedar Labs reached $2 billion.',
  'not_supported'),
 ('N03_reset',
  'earnings',
  'OpenAI earnings discussion',
  'Cedar Labs presented its results. Its Q3 revenue reached $2 billion.',
  'not_supported'),
 ('N03_own_ellipsis',
  'earnings',
  'OpenAI reports quarterly earnings',
  'Revenue reached $2 billion in Q3 2026.',
  'supported'),
 ('N03_own_attributed',
  'earnings',
  'OpenAI reports Q3 earnings',
  'OpenAI revenue reached $2 billion in Q3, CNBC confirmed.',
  'supported'),
 ('N03_own_segment',
  'earnings',
  'OpenAI reports Q3 earnings',
  'Revenue reached $2 billion in Q3, including ChatGPT subscriptions.',
  'supported'),
 ('N03_own_comparison',
  'earnings',
  'OpenAI reports Q3 earnings',
  'OpenAI Q3 revenue reached $2 billion while Cedar Labs revenue reached $1 billion.',
  'supported')]

@pytest.mark.parametrize("case,kind,title,summary,expected", RECHECK_CASES, ids=[x[0] for x in RECHECK_CASES])
def test_second_recheck_cases(case, kind, title, summary, expected):
    actual = status(qualification(title, summary), kind)
    assert (actual != "supported") if expected == "not_supported" else (actual == expected)

@pytest.mark.parametrize("case,kind,title,summary,expected", [x for x in RECHECK_CASES if x[4] == "not_supported"], ids=[x[0] for x in RECHECK_CASES if x[4] == "not_supported"])
def test_negative_material_stays_out_of_actual_featured_and_radar(case, kind, title, summary, expected):
    row = article(case, title=title, summary=summary)
    row["business_events"] = u.business_event_score(row)
    row = u.add_ai_relevance_fields(row)
    assert row["ai_is_related"]
    story = u.build_story_record(case, [row], NOW, 24)
    result = u.build_brief_event_payloads([story], [row], b.StateInput("missing"), NOW, 24,
        archive_meta=b.ArchiveMeta("valid", u.iso(NOW)))
    assert result.publisher_governance["status"] == "ready"
    assert len(result.projection["events"]) == 1
    assert not result.publisher_governance["featured_event_ids"]
    assert not u.build_llm_radar_payload([row], NOW, raw_records={case:row})["events"]

@pytest.mark.parametrize("predicate", [
    "is anticipated to acquire", "expects to acquire", "is discussing acquiring", "refused to acquire",
    "declined to acquire", "has decided against acquiring", "is evaluating whether to acquire",
    "might eventually acquire", "could potentially acquire", "may soon acquire",
    "imagines it acquired", "assumes it will acquire", "allegedly acquired",
    "may have signed a definitive agreement to acquire",
    "could have already signed a definitive agreement to acquire",
    "hypothetically signed an agreement to acquire",
    "是否會收購", "假如收購", "拒絕收購", "放棄收購", "預期將收購",
])
def test_uncommitted_or_declined_transaction_is_not_affirmed(predicate):
    assert status(qualification(f"OpenAI {predicate} Cedar Labs"), "market") != "supported"

@pytest.mark.parametrize("title", [
    "If OpenAI acquired Cedar Labs, its business would change",
    "Suppose OpenAI acquires Cedar Labs",
    "假如OpenAI收購Cedar Labs，市場會如何變化",
    "OpenAI to acquire Cedar Labs?",
    "Has OpenAI acquired Cedar Labs?",
    "OpenAI reviews a proposal to acquire Cedar Labs",
])
def test_transaction_question_and_conditional_are_not_assertions(title):
    assert status(qualification(title), "market") != "supported"

@pytest.mark.parametrize("title,summary", [
    ("OpenAI acquires Cedar Labs", "The company confirmed the deal today."),
    ("OpenAI acquired Cedar Labs", ""),
    ("OpenAI is acquiring Cedar Labs", ""),
    ("OpenAI will acquire Cedar Labs", "OpenAI signed a definitive agreement."),
    ("OpenAI agrees to acquire Cedar Labs", "Approval is pending."),
    ("OpenAI signs a definitive agreement to acquire Cedar Labs", ""),
    ("OpenAI announces its acquisition of Cedar Labs", ""),
    ("OpenAI signed an acquisition agreement with Cedar Labs", ""),
    ("OpenAI收購Cedar Labs", ""),
    ("OpenAI宣布將收購Cedar Labs", ""),
    ("OpenAI已簽署收購Cedar Labs協議", "仍待監管核准。"),
    ("OpenAI completes acquisition of Cedar Labs", ""),
    ("OpenAI has signed a definitive agreement to acquire Cedar Labs", ""),
    ("OpenAI has been acquiring Cedar Labs", "The deal has been announced."),
    ("Acme以63億美元併購Cedar Labs", ""),
    ("Acme與Cedar Labs簽署併購協議", "預計明年完成。"),
    ("Acme宣佈以56.6億美元收購Cedar Labs", ""),
    ("Acme同意被Aspen Cloud以13億美元收購", ""),
    ("Acme已與Cedar Labs達成“反向收購僱傭”交易", "交易將接收Cedar Labs核心團隊。"),
    ("Acme已與音頻初創公司Cedar Labs達成“反向收購僱傭”交易", "交易將接收Cedar Labs核心團隊。"),
])
def test_explicit_transaction_assertions_keep_announced_and_future_closing(title, summary):
    assert status(qualification(title, summary), "market") == "supported"

@pytest.mark.parametrize("name", ["GPT-6.1 Sol", "Photon Nova"])
@pytest.mark.parametrize("artifact", [
    "updated documentation", "API reference", "training tutorial", "revised developer manual",
    "'s updated documentation", "model's revised API reference", "模型新版使用手冊", "模型的新版說明文件",
    "inference code", "release announcement video",
])
def test_model_modifier_with_unfinished_object_cannot_borrow_release_verb(name, artifact):
    assert status(qualification(f"OpenAI releases {name} {artifact}",
        f"{name} is an AI model. Only the accompanying publication is new."), "model_release") != "supported"

@pytest.mark.parametrize("title,summary", [
    ("OpenAI releases Photon Nova AI model with new API documentation", "Photon Nova is now available."),
    ("OpenAI releases Photon Nova AI model and its API reference", "Photon Nova is now available."),
    ("OpenAI releases Photon Nova AI model: a developer tutorial", "Photon Nova is now available."),
    ("OpenAI發布Photon Nova模型，附新版使用手冊", "Photon Nova模型正式開放。"),
    ("OpenAI發布Photon Nova模型及新版使用手冊", "Photon Nova模型正式開放。"),
    ("OpenAI releases GPT-6.1 Sol for developers", "Available now."),
    ("OpenAI releases GPT-6.1 Sol weights", "Developers can download the new model."),
    ("Acme發布Photon Nova模型 準確率超過其他模型", "Photon Nova模型，今日開放。"),
    ("Acme發布Photon Nova模型性能提升20%", "Photon Nova模型正式開放。"),
    ("Acme發布GPT-6.1 Sol語音模型與語音代理SDK", "提供語音模型系列。"),
    ("Acme發布GPT-6.1 Sol預覽版", ""),
    ("Acme發布GPT-6.1 Sol預覽版 支持 4K 輸出", ""),
    ("Acme發布Photon Nova預覽版", "Photon Nova AI model現已開放。"),
])
def test_complete_model_object_can_have_additional_publications_and_qualifiers(title, summary):
    assert status(qualification(title, summary), "model_release") == "supported"


@pytest.mark.parametrize("tail", ["準確率報告", "性能研究論文", "速度測試手冊"])
def test_model_property_noun_is_not_itself_a_following_predicate(tail):
    assert status(qualification("Acme發布Photon Nova模型" + tail,
        "Photon Nova模型的既有數據，只有報告是新的。"), "model_release") != "supported"


@pytest.mark.parametrize("tail", ["語音模型系列新版文件", "預覽版API reference", "preview version updated documentation"])
def test_model_editions_do_not_hide_an_artifact_head(tail):
    assert status(qualification("Acme發布GPT-6.1 Sol" + tail,
        "The existing model has only received new documentation."), "model_release") != "supported"


def test_cjk_letter_of_intent_does_not_assert_a_definitive_acquisition():
    assert status(qualification("Acme計畫併購Cedar Labs",
        "Acme與Cedar Labs簽署併購意向書。"), "market") != "supported"
