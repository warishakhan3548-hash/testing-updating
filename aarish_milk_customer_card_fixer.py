#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime
import shutil
import sys

TARGET = Path("/root/Aarish Kingdom/repo/lib/main.dart")

MILK_START = "class MilkScreen extends StatefulWidget {"
MILK_END = "class _TransactionPairButton extends StatelessWidget {"

OLD_PROFILE = """                  final Map<String, dynamic> profile = _map(database[name]);
"""

OLD_SUBTITLE = """                    subtitle:
                        '${totals.netKg >= 0 ? 'Given' : 'Taken'} ${totals.netKg.abs().toStringAsFixed(2)} KG • ${profile['rate'] ?? LedgerMath.defaultMilkRate}/KG',
"""

NEW_SUBTITLE = """                    subtitle:
                        '${totals.netKg.abs().toStringAsFixed(2)} KG',
"""

PATCH_MARKER = "MILK_CUSTOMER_TOTAL_KG_ONLY_V1"


def fail(message: str) -> None:
    print(f"\n❌ ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not TARGET.is_file():
        fail(f"main.dart नहीं मिला: {TARGET}")

    original = TARGET.read_text(encoding="utf-8")

    if MILK_START not in original or MILK_END not in original:
        fail("MilkScreen boundaries नहीं मिलीं। कोई change नहीं किया गया।")

    start = original.index(MILK_START)
    end = original.index(MILK_END, start)

    before = original[:start]
    milk = original[start:end]
    after = original[end:]

    changed = False

    # ---------------------------------------------------------
    # 1. Replace old Milk customer subtitle.
    # ---------------------------------------------------------
    if OLD_SUBTITLE in milk:
        if milk.count(OLD_SUBTITLE) != 1:
            fail(
                "Milk customer subtitle एक से ज्यादा जगह मिला। "
                "Safety के लिए patch रोक दिया गया।"
            )

        milk = milk.replace(OLD_SUBTITLE, NEW_SUBTITLE, 1)
        changed = True

    elif NEW_SUBTITLE not in milk:
        fail(
            "Expected Milk subtitle नहीं मिला। "
            "Source शायद बदल चुका है; कोई unsafe change नहीं किया गया।"
        )

    # ---------------------------------------------------------
    # 2. Remove profile variable because rate is no longer shown.
    #    Leaving it behind would create an unused-local warning.
    # ---------------------------------------------------------
    if OLD_PROFILE in milk:
        if milk.count(OLD_PROFILE) != 1:
            fail(
                "Expected profile declaration unique नहीं है। "
                "Safety के लिए patch रोक दिया गया।"
            )

        milk = milk.replace(OLD_PROFILE, "", 1)
        changed = True

    patched = before + milk + after

    # ---------------------------------------------------------
    # Surgical verification
    # ---------------------------------------------------------

    milk_after = patched[
        patched.index(MILK_START):
        patched.index(MILK_END, patched.index(MILK_START))
    ]

    forbidden = (
        "? 'Given' : 'Taken'",
        "profile['rate'] ?? LedgerMath.defaultMilkRate",
        "KG •",
    )

    for token in forbidden:
        if token in milk_after:
            fail(f"पुराना Milk-card text अभी भी मौजूद है: {token}")

    required = (
        "final MilkTotals totals =",
        "projection.milkTotalsByProfile[name]!",
        "final Color color = _tone(totals.netAmount);",
        "'${totals.netKg.abs().toStringAsFixed(2)} KG'",
        "trailing: _signedMoney(totals.netAmount),",
        "MilkDetailScreen(sync: widget.sync, customerName: name)",
    )

    for token in required:
        if token not in milk_after:
            fail(f"Protected Milk logic गायब हो गया: {token}")

    # The obsolete profile declaration must be gone.
    if "final Map<String, dynamic> profile = _map(database[name]);" in milk_after:
        fail("Unused profile variable अभी भी मौजूद है।")

    if not changed:
        print("✅ पहले से fixed है — कोई source change जरूरी नहीं।")
        return

    # ---------------------------------------------------------
    # Backup + atomic-style safe write
    # ---------------------------------------------------------
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_name(
        f"main.dart.bak_milk_customer_card_{stamp}"
    )

    shutil.copy2(TARGET, backup)
    TARGET.write_text(patched, encoding="utf-8")

    written = TARGET.read_text(encoding="utf-8")

    if written != patched:
        shutil.copy2(backup, TARGET)
        fail("Write verification fail हुई। Original backup restore कर दिया।")

    print("")
    print("✅ MILK CUSTOMER CARD FIX APPLIED")
    print(f"Target : {TARGET}")
    print(f"Backup : {backup}")
    print("")
    print("अब Milk cards ऐसे होंगे:")
    print("")
    print("  Imran")
    print("  37.00 KG                         -₹2,960")
    print("")
    print("  Wahid")
    print("  3.00 KG                            -₹240")
    print("")
    print("  Djdj")
    print("  8.00 KG                            +₹704")
    print("")
    print("हटा दिया गया:")
    print("  • Given")
    print("  • Taken")
    print("  • Rate")
    print("  • /KG")
    print("")
    print("Untouched:")
    print("  • Amount")
    print("  • Green/Red card color")
    print("  • Total KG calculation")
    print("  • Customer navigation")
    print("  • Milk database/data logic")


if __name__ == "__main__":
    main()
