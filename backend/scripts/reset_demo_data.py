from pathlib import Path

STORE = Path(__file__).parent.parent / "data" / "fraud_events.json"


def reset():
    if STORE.exists():
        STORE.unlink()
        print(f"Deleted: {STORE}")
    else:
        print("No data file found. Nothing to delete.")


if __name__ == "__main__":
    reset()