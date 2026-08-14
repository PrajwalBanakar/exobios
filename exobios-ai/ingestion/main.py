# Unused `uv init` scaffolding — the real entry point is scripts/main.py,
# run via `uv run python -m scripts.main` (see README.md). Left in place so
# `uv run` still has a default script target, but nothing imports this.
def main():
    raise SystemExit("Not the real entry point — run `uv run python -m scripts.main` instead.")


if __name__ == "__main__":
    main()
