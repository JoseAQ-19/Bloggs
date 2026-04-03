import sys
import os
sys.path.append('scripts')
from content_engine_pro import main_upgrade_engine

article = 'content/en/viral/how-ai-lego-style-videos-are-mocking-trumps-war-in-iran-en.md'
print(f"Testing upgrade on: {article}")
main_upgrade_engine(article)
