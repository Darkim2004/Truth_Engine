import asyncio
import json
import logging
from pipeline import run_pipeline

logging.basicConfig(filename="py_debug.log", level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

async def test():
    with open("input_example.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    print("Running pipeline...")
    output = await run_pipeline(data)
    with open("raw_output.json", "w", encoding="utf-8") as f:
        f.write(output.model_dump_json(indent=2))
    print("Done")

if __name__ == "__main__":
    asyncio.run(test())
