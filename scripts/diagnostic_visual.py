import sys
import os
import traceback
sys.path.append('scripts')
from novum_visual import get_image

# Force logging to console for debug
import novum_visual
# novum_visual.VERBOSE = True # if it had it

title = "LEGO Trump War in Iran"
content = "AI generated LEGO style videos mocking the war."
slug = "test-lego-trump"
category = "viral"

print(f"--- STARTING SAVE PATH TEST ---")
print(f"Current Directory: {os.getcwd()}")
print(f"Slug: {slug}")

try:
    res_path = get_image(title, content, slug, category)
    print(f"get_image returned: {res_path}")

    # Check existence
    # res_path is like /images/test-lego-trump.jpg
    expected_local = os.path.join(os.getcwd(), 'static', res_path.lstrip('/'))
    print(f"Expected local path: {expected_local}")
    
    if os.path.exists(expected_local):
        print(f"✅ SUCCESS! Image exists.")
        print(f"Size: {os.path.getsize(expected_local)} bytes")
    else:
        print(f"❌ FAILURE! Image NOT FOUND at {expected_local}")
        # Let's see if static/images exists
        static_dir = os.path.join(os.getcwd(), 'static', 'images')
        print(f"Static images dir exists? {os.path.exists(static_dir)}")
        if os.path.exists(static_dir):
            print(f"Contents of {static_dir}:")
            print(os.listdir(static_dir)[:5]) # First 5 files
except Exception as e:
    print(f"🚨 CRASH! {e}")
    traceback.print_exc()
