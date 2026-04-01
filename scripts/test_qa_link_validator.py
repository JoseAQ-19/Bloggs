"""
test_qa_link_validator.py — Tests para el validador de enlaces.
"""

from qa_link_validator import extract_links, validate_links, _is_internal


def test_extract_links():
    text = """
Según [TechCrunch](https://techcrunch.com/article), la empresa [OpenAI](https://openai.com) 
lanzó su nueva API. Ver más en [NovumWorld](https://novumworld.com/ia/).
"""
    links = extract_links(text)
    assert len(links) == 3
    assert links[0] == ("TechCrunch", "https://techcrunch.com/article")
    assert links[1] == ("OpenAI", "https://openai.com")
    assert links[2] == ("NovumWorld", "https://novumworld.com/ia/")
    print("✅ test_extract_links PASSED")


def test_internal_domain():
    assert _is_internal("https://novumworld.com/ia/test") is True
    assert _is_internal("https://localhost:8080/test") is True
    assert _is_internal("https://techcrunch.com/article") is False
    print("✅ test_internal_domain PASSED")


def test_no_links():
    text = "Este es un texto sin enlaces markdown."
    result = validate_links(text)
    assert result["total"] == 0
    assert len(result["alive"]) == 0
    assert len(result["dead"]) == 0
    print("✅ test_no_links PASSED")


def test_deduplication():
    text = """
[Link 1](https://example.com/page)
[Link 2](https://example.com/page)
[Link 3](https://example.com/other)
"""
    links = extract_links(text)
    assert len(links) == 3  # Extracts all
    # validate_links will deduplicate
    result = validate_links(text)
    assert result["total"] == 2  # Only 2 unique URLs
    print("✅ test_deduplication PASSED")


if __name__ == "__main__":
    test_extract_links()
    test_internal_domain()
    test_no_links()
    test_deduplication()
    print("\n🎉 All qa_link_validator tests PASSED!")
