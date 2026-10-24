"""Final PG05 repair: scoped assertion and complete distribution objects."""
import pytest
from scripts import update_news as u, brief_events as b
from tests.test_publisher_governance import article, NOW
from tests.test_publisher_material_repair import qualification, status

CASES = [('T_parenthetical_denial', 'market', 'OpenAI has not, in fact, acquired Cedar Labs', 'There is no transaction.', 'not_supported'), ('T_dash_denial', 'market', 'OpenAI has not — despite speculation — acquired Cedar Labs', 'There is no transaction.', 'not_supported'), ('T_plain_denial', 'market', 'OpenAI has not acquired Cedar Labs', 'There is no transaction.', 'not_supported'), ('T_assertion_then_question', 'market', 'OpenAI acquired Cedar Labs: what happens next?', 'The transaction closed today.', 'supported'), ('T_signed', 'market', 'OpenAI has signed an agreement to acquire Cedar Labs', 'Regulatory approval is pending.', 'supported'), ('T_plain_assertion', 'market', 'OpenAI acquired Cedar Labs', 'The transaction closed today.', 'supported'), ('M_question', 'model_release', 'Did OpenAI release Photon Nova AI model?', 'No launch has been announced.', 'not_supported'), ('M_conditional', 'model_release', 'If OpenAI releases Photon Nova AI model, developers will get new features', 'This is a hypothetical scenario.', 'not_supported'), ('M_formal_docs', 'model_release', 'OpenAI發布Photon Nova模型正式文件', '這次僅發布既有模型的文件。', 'not_supported'), ('M_quoted_docs', 'model_release', 'OpenAI releases "Photon Nova" AI model documentation', 'Photon Nova is an AI model. Only documentation is new.', 'not_supported'), ('M_possessive_docs', 'model_release', "OpenAI releases Photon Nova AI model's training guide", 'Only the guide for the existing model is new.', 'not_supported'), ('M_series_docs', 'model_release', 'OpenAI releases Photon Nova AI model series documentation', 'Only documentation for the existing model series is new.', 'not_supported'), ('M_actual_model', 'model_release', 'OpenAI releases Photon Nova AI model', 'Photon Nova AI model is now available to developers.', 'supported'), ('M_actual_cjk', 'model_release', 'OpenAI發布Photon Nova模型', 'Photon Nova模型正式開放。', 'supported'), ('M_possessive_weights', 'model_release', "OpenAI releases GPT-6.1 Sol's weights", 'The new open-weight model can be downloaded today.', 'supported'), ('M_plain_weights', 'model_release', 'OpenAI releases GPT-6.1 Sol weights', 'The new open-weight model can be downloaded today.', 'supported'), ('F_own', 'earnings', 'OpenAI reports Q3 earnings', 'Revenue reached $2 billion in Q3.', 'supported'), ('F_foreign', 'earnings', 'OpenAI earnings discussion', "Cedar Labs' Q3 revenue reached $2 billion.", 'not_supported'), ('M_preview', 'model_release', 'OpenAI releases GPT-6.1 Sol preview version', 'GPT-6.1 Sol is now available.', 'supported'), ('M_with_guide', 'model_release', 'OpenAI releases Photon Nova AI model with its developer guide', 'Photon Nova is now available.', 'supported')]

@pytest.mark.parametrize("cid,kind,title,summary,expected", CASES, ids=[x[0] for x in CASES])
def test_third_recheck_material(cid,kind,title,summary,expected):
    actual = status(qualification(title,summary),kind)
    assert actual != "supported" if expected == "not_supported" else actual == expected

@pytest.mark.parametrize("cid,kind,title,summary,expected", CASES, ids=[x[0] for x in CASES])
def test_third_recheck_actual_producer(cid,kind,title,summary,expected):
    row=article(cid,title=title,summary=summary)
    row["business_events"]=u.business_event_score(row)
    row=u.add_ai_relevance_fields(row)
    story=u.build_story_record(cid,[row],NOW,24)
    result=u.build_brief_event_payloads([story],[row],b.StateInput("missing"),NOW,24,
        archive_meta=b.ArchiveMeta("valid",u.iso(NOW)))
    assert result.publisher_governance["status"] == "ready"
    assert len(result.projection["events"]) == 1
    assert bool(result.publisher_governance["featured_event_ids"]) == (expected == "supported")
    radar=u.build_llm_radar_payload([row],NOW,raw_records={cid:row})
    if expected == "not_supported":
        assert not radar["events"]
