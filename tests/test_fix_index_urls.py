import sys
import os
from unittest.mock import MagicMock, patch, mock_open

import fix_index_urls

def test_main_calls_fix_frontmatter():
    with patch("fix_index_urls.fix_frontmatter") as mock_fix:
        fix_index_urls.main()

        assert mock_fix.call_count == len(fix_index_urls.CATEGORIES) * len(fix_index_urls.LANGS)

        for cat in fix_index_urls.CATEGORIES:
            for lang in fix_index_urls.LANGS:
                path = os.path.join(fix_index_urls.CONTENT_DIR, lang, cat, "_index.md")
                mock_fix.assert_any_call(path, lang, cat)

def test_fix_frontmatter_removes_url_and_adds_translation_key():
    content = "---\ntitle: Test\nurl: /forced/url\n---\nBody content"
    mock_fm = {"title": "Test", "url": "/forced/url"}

    with patch("fix_index_urls.yaml.safe_load", return_value=mock_fm), \
         patch("fix_index_urls.yaml.dump") as mock_dump:
        m = mock_open(read_data=content)
        with patch("builtins.open", m):
            fix_index_urls.fix_frontmatter("dummy_path", "es", "fitness")

        assert "url" not in mock_fm
        assert mock_fm["translationKey"] == "section-fitness"
        m().write.assert_any_call("---\n")
        mock_dump.assert_called()
        m().write.assert_any_call("Body content")

def test_fix_frontmatter_translates_en():
    content = "---\ntitle: fitness\n---\nBody"
    mock_fm = {"title": "fitness"}

    with patch("fix_index_urls.yaml.safe_load", return_value=mock_fm), \
         patch("fix_index_urls.yaml.dump"):
        m = mock_open(read_data=content)
        with patch("builtins.open", m):
            fix_index_urls.fix_frontmatter("dummy_path", "en", "fitness")

        assert mock_fm["title"] == "Biohacking & Fitness"
        assert "Sports science" in mock_fm["description"]

def test_fix_frontmatter_file_not_found():
    with patch("builtins.open", side_effect=FileNotFoundError):
        fix_index_urls.fix_frontmatter("non_existent", "es", "fitness")

def test_fix_frontmatter_invalid_yaml():
    content = "---\ninvalid: yaml: :\n---\nBody"
    import yaml
    with patch("fix_index_urls.yaml.safe_load", side_effect=yaml.YAMLError("YAML Error")):
        m = mock_open(read_data=content)
        with patch("builtins.open", m):
            fix_index_urls.fix_frontmatter("invalid_yaml.md", "es", "fitness")

def test_fix_frontmatter_no_frontmatter():
    content = "No frontmatter here"
    m = mock_open(read_data=content)
    with patch("builtins.open", m):
        fix_index_urls.fix_frontmatter("no_fm.md", "es", "fitness")

if __name__ == "__main__":
    test_main_calls_fix_frontmatter()
    test_fix_frontmatter_removes_url_and_adds_translation_key()
    test_fix_frontmatter_translates_en()
    test_fix_frontmatter_file_not_found()
    test_fix_frontmatter_invalid_yaml()
    test_fix_frontmatter_no_frontmatter()
    print("✅ test_fix_index_urls passed")
