#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime
import shutil
import sys

TARGET = Path("/root/Aarish Kingdom/repo/lib/main.dart")

OLD = """                      subtitle:
                          '$label • Milk ${_signedMoney(item.milk)} • Credit ${_signedMoney(item.credit)}',"""

NEW = """                      subtitle: label,"""

ALREADY = "                      subtitle: label,"


def fail(message: str) -> None:
    print(f"\nERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not TARGET.is_file():
        fail(f"main.dart not found: {TARGET}")

    source = TARGET.read_text(encoding="utf-8")

    old_count = source.count(OLD)

    if old_count == 0:
        # Idempotent: don't damage an already-fixed source.
        if ALREADY in source:
            print("Already fixed — Party Ledger subtitle is status-only.")
            return

        fail(
            "Expected Party Ledger subtitle block was not found. "
            "Nothing was changed."
        )

    if old_count != 1:
        fail(
            f"Expected exactly 1 Party Ledger subtitle block, found {old_count}. "
            "Nothing was changed."
        )

    patched = source.replace(OLD, NEW, 1)

    # Surgical verification.
    if (
        "'$label • Milk ${_signedMoney(item.milk)} • "
        "Credit ${_signedMoney(item.credit)}'"
        in patched
    ):
        fail("Old Milk/Credit subtitle still exists.")

    if "subtitle: label," not in patched:
        fail("New status-only subtitle was not installed.")

    # Do not touch Party Ledger calculations or card identity.
    protected = (
        "final Color color = _tone(item.net);",
        "? 'TO RECEIVE'",
        ": 'TO PAY';",
        "title: item.name,",
        "trailing: _signedMoney(item.net),",
    )

    for token in protected:
        if token not in patched:
            fail(f"Protected Party Ledger logic missing: {token}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_name(
        f"main.dart.bak_party_subtitle_{timestamp}"
    )

    shutil.copy2(TARGET, backup)
    TARGET.write_text(patched, encoding="utf-8")

    if TARGET.read_text(encoding="utf-8") != patched:
        shutil.copy2(backup, TARGET)
        fail("Write verification failed. Backup restored.")

    print("")
    print("PARTY LEDGER SUBTITLE FIX APPLIED ✅")
    print(f"Backup: {backup}")
    print("")
    print("Now cards will show:")
    print("  Aarish")
    print("  TO RECEIVE")
    print("")
    print("  Sameer")
    print("  TO PAY")
    print("")
    print("Removed from card subtitle:")
    print("  Milk ₹...")
    print("  Credit ₹...")
    print("")
    print("Net amount, colors, avatar, data and calculations are untouched.")


if __name__ == "__main__":
    main()
