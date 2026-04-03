import sys
import os
sys.path.append('scripts')
from llm_router import LLMRouter

print("Testing LLMRouter...")
try:
    res = LLMRouter.route_call("Say hello", "You are a helpful assistant", lambda p, s: "fallback", model_type="flash")
    print(f"Result: {res}")
except Exception as e:
    print(f"Error: {e}")
