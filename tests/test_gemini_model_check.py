import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import gemini_model_check as g  # noqa: E402


def test_evaluate_text_ok():
    payload = {"candidates": [{"content": {"parts": [{"text": "OK"}]}}]}
    r = g.evaluate("m", "text", 200, payload)
    assert r["ok"] and "OK" in r["note"]


def test_evaluate_image_without_image_fails():
    payload = {"candidates": [{"content": {"parts": [{"text": "sorry"}]}}]}
    assert not g.evaluate("m", "image", 200, payload)["ok"]


def test_evaluate_image_ok():
    payload = {"candidates": [{"content": {"parts": [{"inlineData": {"data": "x"}}]}}]}
    r = g.evaluate("m", "image", 200, payload)
    assert r["ok"] and r["note"] == "回傳 1 張圖片"


def test_evaluate_http_error():
    r = g.evaluate("m", "text", 404, {"error": {"message": "not found"}})
    assert not r["ok"] and r["note"] == "not found"


def test_compare_added_removed():
    prev = {"date": "2026-11-25", "visible": ["a", "b"], "generate": ["a"]}
    diff = g.compare(prev, ["b", "c"], ["b", "c"])
    assert diff["added"] == ["c"] and diff["removed"] == ["a"]
    assert diff["prev_visible_count"] == 2 and diff["prev_generate_count"] == 1


def test_compare_without_previous():
    diff = g.compare({}, ["a"], ["a"])
    assert diff["added"] == [] and diff["removed"] == []


def test_render_and_comment():
    results = [g.evaluate("m1", "text", 200, {"candidates": [{"content": {"parts": [{"text": "OK"}]}}]}),
               g.evaluate("m2", "image", 500, {})]
    diff = g.compare({"date": "2026-11-25", "visible": ["x"], "generate": ["x"]}, ["y"], ["y"])
    md = g.render_markdown("2026-12-25", results, ["y"], ["y"], diff)
    assert "合計測試 2 個，可用 1 個，失敗 1 個。" in md
    assert "新增可見：`y`" in md and "不再出現：`x`" in md
    comment = g.jira_comment("2026-12-25", results, ["y"], ["y"], diff)
    assert "失敗 1 個：m2" in comment


def test_model_list_size():
    assert len(g.TEXT_MODELS) == 16 and len(g.IMAGE_MODELS) == 7
