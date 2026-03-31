from __future__ import annotations

import getpass
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
VENV_DIR = ROOT / ".venv"


def step(message: str) -> None:
    print(f"[START] {message}")


def run_command(cmd: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd or ROOT, check=True)


def read_env_value(name: str) -> str:
    if not ENV_FILE.exists():
        return ""

    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(f"{name}="):
            return line.split("=", 1)[1].strip()
    return ""


def set_env_value(name: str, value: str) -> None:
    lines: list[str] = []
    found = False

    if ENV_FILE.exists():
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()

    for idx, raw_line in enumerate(lines):
        stripped = raw_line.strip()
        if stripped.startswith(f"{name}="):
            lines[idx] = f"{name}={value}"
            found = True
            break

    if not found:
        lines.append(f"{name}={value}")

    ENV_FILE.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def prompt_groq_api_key() -> str:
    while True:
        value = getpass.getpass("Insert your Groq API key (gsk_...): ").strip()
        if value:
            return value
        print("The API key cannot be empty. Please try again.")


def ensure_api_key() -> None:
    step("Groq API key setup")

    existing = read_env_value("GROQ_API_KEY")
    if not existing:
        key = prompt_groq_api_key()
        set_env_value("GROQ_API_KEY", key)
        print("Saved GROQ_API_KEY in .env")
        return

    answer = input("A GROQ_API_KEY already exists in .env. Overwrite it? (y/N): ").strip().lower()
    if answer in {"y", "yes"}:
        key = prompt_groq_api_key()
        set_env_value("GROQ_API_KEY", key)
        print("Updated GROQ_API_KEY in .env")
    else:
        print("Keeping current GROQ_API_KEY from .env")


def venv_python_path() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def ensure_venv() -> Path:
    step("Virtual environment check")
    python_in_venv = venv_python_path()

    if not python_in_venv.exists():
        print("Creating .venv...")
        run_command([sys.executable, "-m", "venv", str(VENV_DIR)])
    else:
        print(".venv already present")

    if not python_in_venv.exists():
        raise RuntimeError("Virtual environment was not created correctly.")

    return python_in_venv


def run_python_check(python_exe: Path, code: str, *args: str) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(code)
        temp_script = Path(tmp.name)

    try:
        return subprocess.run(
            [str(python_exe), str(temp_script), *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        try:
            temp_script.unlink(missing_ok=True)
        except Exception:
            pass


def requirements_satisfied(python_exe: Path, requirements_path: Path) -> bool:
    check_code = textwrap.dedent(
        """
        import importlib.metadata as md
        import sys
        from pathlib import Path

        try:
            from packaging.requirements import Requirement
        except Exception:
            sys.exit(1)

        path = Path(sys.argv[1])
        lines = path.read_text(encoding="utf-8").splitlines()

        for raw in lines:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "#" in line:
                line = line.split("#", 1)[0].strip()
                if not line:
                    continue

            try:
                req = Requirement(line)
            except Exception:
                sys.exit(1)

            try:
                version = md.version(req.name)
            except md.PackageNotFoundError:
                sys.exit(1)

            if req.specifier and version not in req.specifier:
                sys.exit(1)

        sys.exit(0)
        """
    )

    result = run_python_check(python_exe, check_code, str(requirements_path))
    return result.returncode == 0


def playwright_chromium_ready(python_exe: Path) -> bool:
    check_code = textwrap.dedent(
        """
        import os
        import sys

        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            sys.exit(1)

        try:
            p = sync_playwright().start()
            chromium_path = p.chromium.executable_path
            p.stop()
        except Exception:
            sys.exit(1)

        if chromium_path and os.path.exists(chromium_path):
            sys.exit(0)

        sys.exit(1)
        """
    )

    result = run_python_check(python_exe, check_code)
    return result.returncode == 0


def ensure_dependencies(python_exe: Path) -> None:
    step("Upgrading pip")
    run_command([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"])

    requirements_path = ROOT / "requirements.txt"
    if not requirements_path.exists():
        raise FileNotFoundError(f"requirements.txt not found at: {requirements_path}")

    step("Checking dependencies from requirements.txt")
    if requirements_satisfied(python_exe, requirements_path):
        print("All requirements already satisfied. Skipping install.")
    else:
        print("Missing or incompatible packages detected. Installing requirements...")
        run_command([str(python_exe), "-m", "pip", "install", "-r", str(requirements_path)])


def ensure_playwright(python_exe: Path) -> None:
    step("Checking Playwright Chromium")
    if playwright_chromium_ready(python_exe):
        print("Playwright Chromium already installed. Skipping install.")
    else:
        print("Playwright Chromium missing. Installing...")
        run_command([str(python_exe), "-m", "playwright", "install", "chromium"])


def start_app(python_exe: Path) -> None:
    step("Starting app.py on http://127.0.0.1:5001")
    run_command([str(python_exe), "app.py"])


def main() -> int:
    if sys.version_info < (3, 11):
        print("Python 3.11+ is required to run this startup script.")
        return 1

    try:
        ensure_api_key()
        python_exe = ensure_venv()
        ensure_dependencies(python_exe)
        ensure_playwright(python_exe)
        start_app(python_exe)
        return 0
    except KeyboardInterrupt:
        print("\nStartup interrupted by user.")
        return 130
    except subprocess.CalledProcessError as exc:
        print(f"\nStartup failed while running: {' '.join(exc.cmd)}")
        return exc.returncode or 1
    except Exception as exc:
        print(f"\nStartup failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
