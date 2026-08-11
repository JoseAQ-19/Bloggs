import os
import sys
import pytest
import frontmatter
from PIL import Image

# Ensure paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from novum_visual import generate_unique_visual_prompt
from fix_duplicate_images import (
    scan_for_duplicates,
    remediate_duplicate_images,
    extract_category,
    sync_featured_image_in_body,
)


def test_generate_unique_visual_prompt(monkeypatch):
    monkeypatch.setattr(
        "llm_router.LLMRouter.route_call",
        lambda prompt, system_prompt, fallback_func, model_type="parsing", temperature=0.7: "A vivid photographic shot of Bitcoin crypto trading chart with golden glow"
    )
    title = "Bitcoin Spikes to New Heights"
    content = "The market is bullish as crypto traders celebrate."
    category = "crypto"

    prompt = generate_unique_visual_prompt(title, content, category)
    assert isinstance(prompt, str)
    assert len(prompt) > 20
    assert "Bitcoin" in prompt or "crypto" in prompt.lower() or "trading" in prompt.lower()


def test_extract_category():
    post = frontmatter.Post("Content", categories=["crypto"])
    assert extract_category("/some/path", post) == "crypto"
    
    post_empty = frontmatter.Post("Content")
    assert extract_category("content/es/fitness/post-slug.md", post_empty) == "fitness"


def test_sync_featured_image_in_body_replaces_first_image():
    post = frontmatter.Post(
        "![Old image](/images/defaults/default-ia.jpg)\n\nBody",
        title="Article",
    )

    sync_featured_image_in_body(post, "/images/article.webp")

    assert post.content.startswith("![Old image](/images/article.webp)")
    assert "/images/defaults/default-ia.jpg" not in post.content


def test_sync_featured_image_in_body_injects_missing_image():
    post = frontmatter.Post("Body", title="Article")

    sync_featured_image_in_body(post, "featured.webp")

    assert post.content.startswith("![Article](featured.webp)")


def test_scan_for_duplicates_and_dry_run(tmp_path):
    posts_dir = tmp_path / "content" / "posts"
    posts_dir.mkdir(parents=True)

    # Article 1 (Duplicate Image A)
    post1_path = posts_dir / "post-1.md"
    post1 = frontmatter.Post("Contenido del post 1", title="Post 1", slug="post-1", featured_image="/images/defaults/default-ia.jpg")
    with open(post1_path, "wb") as f:
        frontmatter.dump(post1, f)

    # Article 2 (Duplicate Image A)
    post2_path = posts_dir / "post-2.md"
    post2 = frontmatter.Post("Contenido del post 2", title="Post 2", slug="post-2", featured_image="/images/defaults/default-ia.jpg")
    with open(post2_path, "wb") as f:
        frontmatter.dump(post2, f)

    # Article 3 (Unique Image B)
    post3_path = posts_dir / "post-3.md"
    post3 = frontmatter.Post("Contenido del post 3", title="Post 3", slug="post-3", featured_image="/images/unique-3.webp")
    with open(post3_path, "wb") as f:
        frontmatter.dump(post3, f)

    # Scan
    groups, total_scanned = scan_for_duplicates(str(posts_dir))
    assert total_scanned == 3
    assert len(groups) == 1
    assert "/images/defaults/default-ia.jpg" in groups
    assert len(groups["/images/defaults/default-ia.jpg"]) == 2

    # Dry Run
    remediate_duplicate_images(groups, dry_run=True)

    # Check post 1 frontmatter unchanged after dry run
    reloaded_post1 = frontmatter.load(post1_path)
    assert reloaded_post1.get("featured_image") == "/images/defaults/default-ia.jpg"


def test_remediate_duplicate_images_live(tmp_path, monkeypatch):
    # Mock LLM visual prompt generation to bypass network timeouts in unit tests
    monkeypatch.setattr(
        "fix_duplicate_images.generate_unique_visual_prompt",
        lambda title, content, category, slug="": f"Mock visual prompt for {title}"
    )
    monkeypatch.setattr(
        "novum_visual.generate_unique_visual_prompt",
        lambda title, content, category, slug="": f"Mock visual prompt for {title}"
    )

    posts_dir = tmp_path / "content" / "posts"
    posts_dir.mkdir(parents=True)

    # Create Leaf Bundle 1 (Duplicate Image)
    bundle1 = posts_dir / "leaf-bundle-1"
    bundle1.mkdir()
    post1_path = bundle1 / "index.md"
    post1 = frontmatter.Post("Leaf Bundle Content 1", title="Leaf 1", slug="leaf-bundle-1", image="/images/defaults/default-ia.jpg")
    with open(post1_path, "wb") as f:
        frontmatter.dump(post1, f)

    # Create Leaf Bundle 2 (Duplicate Image)
    bundle2 = posts_dir / "leaf-bundle-2"
    bundle2.mkdir()
    post2_path = bundle2 / "index.md"
    post2 = frontmatter.Post("Leaf Bundle Content 2", title="Leaf 2", slug="leaf-bundle-2", image="/images/defaults/default-ia.jpg")
    with open(post2_path, "wb") as f:
        frontmatter.dump(post2, f)

    # Scan & Remediate Live
    groups, total_scanned = scan_for_duplicates(str(posts_dir))
    assert len(groups) == 1

    remediate_duplicate_images(groups, dry_run=False)

    # Verify post 1 updated
    reloaded_post1 = frontmatter.load(post1_path)
    assert reloaded_post1.get("image") == "featured.webp"
    assert (bundle1 / "featured.webp").exists()
    assert (bundle1 / "featured.webp").stat().st_size / 1024 < 150

    # Verify post 2 updated
    reloaded_post2 = frontmatter.load(post2_path)
    assert reloaded_post2.get("image") == "featured.webp"
    assert (bundle2 / "featured.webp").exists()
    assert (bundle2 / "featured.webp").stat().st_size / 1024 < 150


def test_scan_detects_same_bytes_under_different_names(tmp_path):
    """Regresión: placeholders copiados con nombres únicos por slug deben detectarse por hash."""
    img = Image.new("RGB", (64, 64), color=(10, 20, 30))

    bundle1 = tmp_path / "content" / "es" / "crypto" / "post-a"
    bundle1.mkdir(parents=True)
    img.save(bundle1 / "cover-a.webp", "WEBP")
    post1 = frontmatter.Post("Cuerpo A", title="Post A", slug="post-a", featured_image="cover-a.webp")
    with open(bundle1 / "index.md", "wb") as f:
        frontmatter.dump(post1, f)

    bundle2 = tmp_path / "content" / "es" / "crypto" / "post-b"
    bundle2.mkdir(parents=True)
    img.save(bundle2 / "cover-b.webp", "WEBP")
    post2 = frontmatter.Post("Cuerpo B", title="Post B", slug="post-b", featured_image="cover-b.webp")
    with open(bundle2 / "index.md", "wb") as f:
        frontmatter.dump(post2, f)

    groups, total = scan_for_duplicates(str(tmp_path / "content"))
    assert total == 2
    assert len(groups) == 1
    group_posts = next(iter(groups.values()))
    assert {p["slug"] for p in group_posts} == {"post-a", "post-b"}


def test_scan_respects_categories_filter(tmp_path):
    posts_dir = tmp_path / "content" / "es"
    for cat in ("crypto", "fitness"):
        d = posts_dir / cat
        d.mkdir(parents=True)
        post = frontmatter.Post("Cuerpo", title=f"P-{cat}", slug=f"p-{cat}", featured_image=f"/images/{cat}-x.webp")
        with open(d / f"p-{cat}.md", "wb") as f:
            frontmatter.dump(post, f)

    _, total = scan_for_duplicates(str(posts_dir), categories=["crypto"])
    assert total == 1
