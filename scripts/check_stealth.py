def main() -> None:
    try:
        from playwright_stealth import Stealth
    except Exception as exc:
        print(f"playwright-stealth import failed: {exc}")
        raise

    print(f"playwright-stealth is available: {Stealth.__name__}")


if __name__ == "__main__":
    main()
