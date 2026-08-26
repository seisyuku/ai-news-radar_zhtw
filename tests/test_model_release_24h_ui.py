from tests.js_bridge import extract_declarations, run_js


DECLARATIONS = extract_declarations(
    "itemHasModelRelease",
    "mergeModelReleaseItems",
)


def _run(body: str) -> dict:
    return run_js(f"{DECLARATIONS}\n{body}")


def test_24_hour_releases_are_added_only_to_models_section():
    result = _run(
        """
        const base = [{id: 'today', title: 'Today'}];
        const releases = [{id: 'qwen', title: 'Qwen3.8'}, {id: 'grok', title: 'Grok 4.6'}];
        console.log(JSON.stringify({
          models: mergeModelReleaseItems(base, releases, 'models').map((item) => item.id),
          hot: mergeModelReleaseItems(base, releases, 'hot').map((item) => item.id),
        }));
        """
    )
    assert result["models"] == ["today", "qwen", "grok"]
    assert result["hot"] == ["today"]


def test_24_hour_release_deduplicates_an_item_already_in_24h_pool():
    result = _run(
        """
        const qwen = {id: 'qwen', title: 'Qwen3.8', business_events: ['model_release']};
        const merged = mergeModelReleaseItems([qwen], [qwen], 'models');
        console.log(JSON.stringify({length: merged.length, isRelease: itemHasModelRelease(merged[0])}));
        """
    )
    assert result == {"length": 1, "isRelease": True}
