from tests.js_bridge import extract_declarations, run_js


DECLARATIONS = extract_declarations(
    "itemHasModelRelease",
    "mergeWeeklyModelItems",
)


def _run(body: str) -> dict:
    return run_js(f"{DECLARATIONS}\n{body}")


def test_weekly_releases_are_added_only_to_models_section():
    result = _run(
        """
        const base = [{id: 'today', title: 'Today'}];
        const weekly = [{id: 'qwen', title: 'Qwen3.8'}, {id: 'grok', title: 'Grok 4.6'}];
        console.log(JSON.stringify({
          models: mergeWeeklyModelItems(base, weekly, 'models').map((item) => item.id),
          hot: mergeWeeklyModelItems(base, weekly, 'hot').map((item) => item.id),
        }));
        """
    )
    assert result["models"] == ["today", "qwen", "grok"]
    assert result["hot"] == ["today"]


def test_weekly_release_deduplicates_an_item_already_in_24h_pool():
    result = _run(
        """
        const qwen = {id: 'qwen', title: 'Qwen3.8', business_events: ['model_release']};
        const merged = mergeWeeklyModelItems([qwen], [qwen], 'models');
        console.log(JSON.stringify({length: merged.length, isRelease: itemHasModelRelease(merged[0])}));
        """
    )
    assert result == {"length": 1, "isRelease": True}
