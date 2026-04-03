import sys
import os
sys.path.append('scripts')
from novum_visual import get_image

title = "LEGO Trump War in Iran"
content = "AI generated LEGO style videos mocking the war."
slug = "test-lego-trump"
category = "viral"

print(f"Testing image generation for: {slug}")
res = get_image(title, content, slug, category)
print(f"Result: {res}")

expected_path = os.path.join('static', 'images', f"{slug}.jpg")
if os.path.exists(expected_path):
    print(f"✅ Success! Image exists at {expected_path}")
else:
    print(f"❌ Failure! Image NOT found at {expected_path}")
