import asyncio
import json
import traceback
from pipeline import run_pipeline

async def main():
    with open("input.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    print("Running with input:", data)
    try:
        res = await run_pipeline(data)
        print("Success:", res)
    except Exception as e:
        traceback.print_exc()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except Exception as e:
        print("Crash in run_until_complete:", e)
        traceback.print_exc()
    finally:
        try:
            loop.close()
        except OSError as e:
            if e.errno == 22:
                print("Caught [Errno 22] in loop.close()")
            else:
                raise
