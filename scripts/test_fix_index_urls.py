import sys
from unittest.mock import MagicMock, patch, mock_open
import os

# Mock yaml before importing the module that uses it
mock_yaml = MagicMock()
# Mock YAMLError to be an exception class
class MockYAMLError(Exception):
    pass
mock_yaml.YAMLError = MockYAMLError
sys.modules["yaml"] = mock_yaml

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

    mock_yaml.safe_load.return_value = mock_fm
    mock_yaml.safe_load.side_effect = None
    # We want to see what yaml.dump is called with

    m = mock_open(read_data=content)
    with patch("builtins.open", m):
        fix_index_urls.fix_frontmatter("dummy_path", "es", "fitness")

    # Check if url was deleted
    assert "url" not in mock_fm
    # Check if translationKey was added
    assert mock_fm["translationKey"] == "section-fitness"

    # Verify file was written back
    # fix_frontmatter writes: ---\n, then yaml.dump, then ---\n, then body
    m().write.assert_any_call("---\n")
    mock_yaml.dump.assert_called()
    # Verify body was written
    m().write.assert_any_call("Body content")

def test_fix_frontmatter_translates_en():
    content = "---\ntitle: fitness\n---\nBody"
    mock_fm = {"title": "fitness"}
    mock_yaml.safe_load.return_value = mock_fm
    mock_yaml.safe_load.side_effect = None

    m = mock_open(read_data=content)
    with patch("builtins.open", m):
        fix_index_urls.fix_frontmatter("dummy_path", "en", "fitness")

    assert mock_fm["title"] == "Biohacking & Fitness"
    assert "Sports science" in mock_fm["description"]

def test_fix_frontmatter_file_not_found():
    with patch("builtins.open", side_effect=FileNotFoundError):
        # Should not raise exception, just print warning
        fix_index_urls.fix_frontmatter("non_existent", "es", "fitness")

def test_fix_frontmatter_invalid_yaml():
    content = "---\ninvalid: yaml: :\n---\nBody"
    mock_yaml.safe_load.side_effect = MockYAMLError("YAML Error")

    m = mock_open(read_data=content)
    with patch("builtins.open", m):
        # Should not raise exception, just print error
        fix_index_urls.fix_frontmatter("invalid_yaml.md", "es", "fitness")

def test_fix_frontmatter_no_frontmatter():
    content = "No frontmatter here"
    m = mock_open(read_data=content)
    with patch("builtins.open", m):
        # Should not raise exception
        fix_index_urls.fix_frontmatter("no_fm.md", "es", "fitness")
