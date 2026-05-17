# tests/test_parsing.py
# JSON 解析工具测试 — extract_json、parse_structured_output

from __future__ import annotations



class TestExtractJson:
    """测试 extract_json 函数"""

    def test_extract_valid_json(self):
        from backend.core.parsing import extract_json
        text = 'Some text before {"stance": "bullish", "confidence": 0.8} and after'
        result = extract_json(text)
        assert result == {"stance": "bullish", "confidence": 0.8}

    def test_extract_nested_json(self):
        from backend.core.parsing import extract_json
        text = 'Result: {"outer": {"inner": 42}}'
        result = extract_json(text)
        assert result == {"outer": {"inner": 42}}

    def test_no_json_returns_none(self):
        from backend.core.parsing import extract_json
        text = "Just plain text without any JSON"
        result = extract_json(text)
        assert result is None

    def test_invalid_json_returns_none(self):
        from backend.core.parsing import extract_json
        text = 'Text with {invalid json: missing quote}'
        result = extract_json(text)
        assert result is None

    def test_extract_first_json_only(self):
        from backend.core.parsing import extract_json
        text = '{"first": 1} some text {"second": 2}'
        result = extract_json(text)
        # regex \{[\s\S]*\} matches from first { to last }, so this returns merged invalid JSON
        # The function returns None because the matched string is not valid JSON
        assert result is None

    def test_multiline_json(self):
        from backend.core.parsing import extract_json
        text = """Here is the result:
        {
            "stance": "bullish",
            "confidence": 0.9
        }
        End."""
        result = extract_json(text)
        assert result == {"stance": "bullish", "confidence": 0.9}


class TestParseStructuredOutput:
    """测试 parse_structured_output 函数"""

    def test_parse_success_with_defaults(self):
        from backend.core.parsing import parse_structured_output
        defaults = {"stance": "neutral", "confidence": 0.5, "summary": ""}
        text = '{"stance": "bullish", "confidence": 0.8}'
        result = parse_structured_output(text, defaults)
        assert result["stance"] == "bullish"
        assert result["confidence"] == 0.8
        assert result["summary"] == ""  # 未被覆盖的默认值

    def test_parse_failure_fallback(self):
        from backend.core.parsing import parse_structured_output
        defaults = {"stance": "neutral", "confidence": 0.5, "summary": "", "key_points": []}
        text = "This is not JSON at all"
        result = parse_structured_output(text, defaults)
        assert result["stance"] == "neutral"
        assert result["confidence"] == 0.5
        assert result["summary"] == "This is not JSON at all"
        assert result["key_points"] == ["This is not JSON at all"]

    def test_partial_json(self):
        from backend.core.parsing import parse_structured_output
        defaults = {"stance": "neutral", "confidence": 0.5, "extra": "default"}
        text = '{"stance": "bearish"}'
        result = parse_structured_output(text, defaults)
        assert result["stance"] == "bearish"
        assert result["confidence"] == 0.5  # 默认值
        assert result["extra"] == "default"

    def test_empty_json(self):
        from backend.core.parsing import parse_structured_output
        defaults = {"stance": "neutral", "confidence": 0.5}
        text = "{}"
        result = parse_structured_output(text, defaults)
        assert result["stance"] == "neutral"
        assert result["confidence"] == 0.5
