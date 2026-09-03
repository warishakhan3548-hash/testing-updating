#!/usr/bin/env python3

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


ROOT = Path("/root/Aarish Kingdom/repo")
TARGET = ROOT / "lib" / "main.dart"

EXPENSE_START = "class ExpenseScreen extends StatefulWidget {"
EXPENSE_END = "class ExpenseDetailScreen extends StatefulWidget {"

PATCH_MARKER = "EXPENSE_LAST_ENTRY_ONLY_V1"

OLD_SUBTITLE = """                    subtitle: group.monthTotal > 0
                        ? 'This month • Last ${_displayDate(group.lastDate)}'
                        : 'No expense this month • Last ${_displayDate(group.lastDate)}',
"""

NEW_SUBTITLE = """                    subtitle:
                        'Last entry: ${_displayDate(group.lastDate)}',
"""


def fail(message: str) -> None:
    print(f"\n❌ ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not TARGET.is_file():
        fail(f"main.dart not found: {TARGET}")

    original = TARGET.read_text(encoding="utf-8")

    start = original.find(EXPENSE_START)
    end = original.find(EXPENSE_END, start)

    if start < 0 or end < 0:
        fail("ExpenseScreen boundaries नहीं मिलीं। कोई code change नहीं किया गया।")

    before = original[:start]
    expense = original[start:end]
    after = original[end:]

    # ---------------------------------------------------------
    # Idempotency
    # ---------------------------------------------------------
    if PATCH_MARKER in expense:
        print("✅ Expense card पहले से fixed है।")
        return

    # ---------------------------------------------------------
    # Replace the ORIGINAL subtitle logic.
    # No wrapper. No duplicate widget. No visual override.
    # ---------------------------------------------------------
    old_count = expense.count(OLD_SUBTITLE)

    if old_count != 1:
        if NEW_SUBTITLE in expense:
            print("✅ Desired Expense subtitle पहले से मौजूद है।")
            return

        fail(
            "Expected Expense subtitle exactly नहीं मिला। "
            f"Found {old_count} matches. Safety के लिए कुछ नहीं बदला।"
        )

    expense = expense.replace(
        OLD_SUBTITLE,
        NEW_SUBTITLE,
        1,
    )

    # Put marker beside the actual changed core logic.
    marker_anchor = NEW_SUBTITLE

    expense = expense.replace(
        marker_anchor,
        f"""                    // {PATCH_MARKER}
{NEW_SUBTITLE}""",
        1,
    )

    patched = before + expense + after

    # ---------------------------------------------------------
    # Verification — old UI text must be gone from ExpenseScreen.
    # ---------------------------------------------------------
    expense_after = patched[
        patched.index(EXPENSE_START):
        patched.index(EXPENSE_END, patched.index(EXPENSE_START))
    ]

    forbidden = (
        "This month • Last ${_displayDate(group.lastDate)}",
        "No expense this month • Last ${_displayDate(group.lastDate)}",
    )

    for token in forbidden:
        if token in expense_after:
            fail(f"Old Expense subtitle अभी भी मौजूद है: {token}")

    # ---------------------------------------------------------
    # Verify desired visual/data path.
    # ---------------------------------------------------------
    required = (
        PATCH_MARKER,
        "'Last entry: ${_displayDate(group.lastDate)}'",
        "title: group.category,",
        "color: semanticRed,",
        "trailing: group.monthTotal > 0",
        "? '-${_money(group.monthTotal)}'",
        ": '—',",
        "ExpenseDetailScreen(",
        "category: group.category,",
    )

    for token in required:
        if token not in expense_after:
            fail(f"Protected Expense logic missing: {token}")

    # ---------------------------------------------------------
    # Protect calculations and top hero.
    # ---------------------------------------------------------
    protected_global = (
        "final List<ExpenseCategorySummary> groups = projection.expenseCategories;",
        "final double total = projection.expenseMonthTotal;",
        "final Color moduleColor = _expenseToneForTotal(total);",
        "label: 'Month Expense',",
        "value: _money(total),",
    )

    for token in protected_global:
        if token not in expense_after:
            fail(f"Expense calculation/UI core unexpectedly changed: {token}")

    # ---------------------------------------------------------
    # Backup + safe write
    # ---------------------------------------------------------
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup = TARGET.with_name(
        f"main.dart.bak_expense_card_{stamp}"
    )

    shutil.copy2(TARGET, backup)

    TARGET.write_text(
        patched,
        encoding="utf-8",
    )

    written = TARGET.read_text(encoding="utf-8")

    if written != patched:
        shutil.copy2(backup, TARGET)
        fail(
            "Post-write verification failed. "
            "Original main.dart automatically restore कर दिया गया।"
        )

    print("")
    print("✅ EXPENSE CARD CORE FIX APPLIED")
    print(f"Target : {TARGET}")
    print(f"Backup : {backup}")
    print("")
    print("अब category card:")
    print("")
    print("  Other")
    print("  Last entry: 3 Sept                 -₹5,610")
    print("")
    print("हटा दिया:")
    print("  • This month")
    print("  • No expense this month")
    print("  • separator bullet")
    print("")
    print("Untouched:")
    print("  • category name")
    print("  • expense amount")
    print("  • red card styling")
    print("  • card 3D/glow")
    print("  • category navigation")
    print("  • expense calculations")
    print("  • Add")
    print("  • Share")
    print("  • database/data logic")
    print("  • Expense detail screen")


if __name__ == "__main__":
    main()
