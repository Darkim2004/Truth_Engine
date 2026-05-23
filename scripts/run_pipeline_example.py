import asyncio
import json
import logging
from pathlib import Path

from config import EXAMPLE_INPUT_PATH, RUNTIME_LOG_DIR, RUNTIME_OUTPUT_DIR
from pipeline import run_pipeline


async def main() -> None:
    RUNTIME_LOG_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        filename=RUNTIME_LOG_DIR / "pipeline_debug.log",
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    with Path(EXAMPLE_INPUT_PATH).open("r", encoding="utf-8") as f:
        data = json.load(f)

    print("Running pipeline...")
    output = await run_pipeline(data)

    output_path = RUNTIME_OUTPUT_DIR / "raw_output.json"
    output_path.write_text(output.model_dump_json(indent=2), encoding="utf-8")
    print(f"Done. Output written to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
