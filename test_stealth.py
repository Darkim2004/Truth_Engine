import traceback
import sys
try:
    from playwright_stealth import stealth_async
    print("stealth_async OK")
except Exception as e:
    traceback.print_exc()
