#!/usr/bin/env python3

from __future__ import annotations

import re
import shutil
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path("/root/Aarish Kingdom/repo")
TARGET = ROOT / "lib" / "main.dart"

LIST_CLASS = "class _ListCard extends StatelessWidget {"
CREDIT_CLASS = "class CreditScreen extends StatefulWidget {"
CREDIT_DETAIL_CLASS = "class CreditDetailScreen extends StatefulWidget {"

PATCH_MARKER = "CREDIT_LIST_STATUS_COLUMN_V2"


def fail(message: str) -> None:
    print(f"\n❌ ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def class_region(source: str, marker: str) -> tuple[int, int, str]:
    start = source.find(marker)
    if start < 0:
        fail(f"Class not found: {marker}")

    match = re.search(r"\nclass\s+", source[start + len(marker):])
    if match is None:
        end = len(source)
    else:
        end = start + len(marker) + match.start() + 1

    return start, end, source[start:end]


def replace_exact_once(
    source: str,
    old: str,
    new: str,
    label: str,
) -> str:
    count = source.count(old)

    if count != 1:
        fail(
            f"{label}: expected exactly 1 match, found {count}. "
            "Nothing unsafe was changed."
        )

    return source.replace(old, new, 1)


def upgrade_list_card(source: str) -> str:
    start, end, block = class_region(source, LIST_CLASS)

    # ---------------------------------------------------------
    # 1. Add optional trailingLabel to the ORIGINAL shared card.
    # ---------------------------------------------------------
    if "this.trailingLabel," not in block:
        block = replace_exact_once(
            block,
            """    this.trailing,
    this.onDelete,
""",
            """    this.trailing,
    this.trailingLabel,
    this.onDelete,
""",
            "_ListCard constructor",
        )

    if "final String? trailingLabel;" not in block:
        block = replace_exact_once(
            block,
            """  final String? trailing;
  final VoidCallback? onDelete;
""",
            f"""  final String? trailing;
  final String? trailingLabel;
  // {PATCH_MARKER}
  final VoidCallback? onDelete;
""",
            "_ListCard fields",
        )
    elif PATCH_MARKER not in block:
        block = block.replace(
            "  final String? trailingLabel;\n",
            f"  final String? trailingLabel;\n  // {PATCH_MARKER}\n",
            1,
        )

    # ---------------------------------------------------------
    # 2. Replace ONLY the original trailing amount renderer.
    #
    # trailingLabel == null:
    #   exact old behaviour.
    #
    # trailingLabel != null:
    #   STATUS
    #   AMOUNT
    #
    # This means Milk / Party Ledger / other cards are untouched.
    # ---------------------------------------------------------
    trailing_start_marker = (
        "            if (trailing != null) ...<Widget>[\n"
    )
    trailing_end_marker = "            if (onDelete != null)"

    trailing_start = block.find(trailing_start_marker)
    trailing_end = block.find(trailing_end_marker, trailing_start)

    if trailing_start < 0 or trailing_end < 0:
        fail("Could not safely locate _ListCard trailing renderer.")

    current_trailing = block[trailing_start:trailing_end]

    if "trailingLabel == null" not in current_trailing:
        new_trailing = r'''            if (trailing != null) ...<Widget>[
              const SizedBox(width: 10),

              ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 118),

                child: trailingLabel == null
                    ? FittedBox(
                        fit: BoxFit.scaleDown,
                        alignment: Alignment.centerRight,
                        child: Text(
                          trailing!,
                          maxLines: 1,
                          softWrap: false,
                          style: TextStyle(
                            color: color,
                            fontSize: 19,
                            fontWeight: FontWeight.w800,
                            fontFeatures: AppStyles.tabularFigures,
                            letterSpacing: -.35,
                            shadows: AppStyles.inkGlow(
                              color,
                              strong: true,
                            ),
                          ),
                        ),
                      )
                    : Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: <Widget>[
                          Text(
                            trailingLabel!,
                            maxLines: 1,
                            softWrap: false,
                            overflow: TextOverflow.ellipsis,
                            textAlign: TextAlign.right,
                            style: TextStyle(
                              color: color.withAlpha(
                                dark ? 218 : 198,
                              ),
                              fontSize: 10.5,
                              height: 1,
                              fontWeight: FontWeight.w800,
                              letterSpacing: .68,
                              shadows: AppStyles.inkGlow(color),
                            ),
                          ),

                          const SizedBox(height: 5),

                          FittedBox(
                            fit: BoxFit.scaleDown,
                            alignment: Alignment.centerRight,
                            child: Text(
                              trailing!,
                              maxLines: 1,
                              softWrap: false,
                              style: TextStyle(
                                color: color,
                                fontSize: 19,
                                height: 1,
                                fontWeight: FontWeight.w800,
                                fontFeatures:
                                    AppStyles.tabularFigures,
                                letterSpacing: -.35,
                                shadows: AppStyles.inkGlow(
                                  color,
                                  strong: true,
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
              ),
            ],

'''

        block = (
            block[:trailing_start]
            + new_trailing
            + block[trailing_end:]
        )

    return source[:start] + block + source[end:]


def upgrade_credit_cards(source: str) -> str:
    start = source.find(CREDIT_CLASS)
    end = source.find(CREDIT_DETAIL_CLASS, start)

    if start < 0 or end < 0:
        fail("CreditScreen boundaries could not be located.")

    block = source[start:end]

    # ---------------------------------------------------------
    # 3. Status becomes its OWN semantic field.
    # ---------------------------------------------------------
    if "final String statusLabel = group.net > 0" not in block:
        block = replace_exact_once(
            block,
            """                  final Color color = _tone(group.net);
                  return _ListCard(
""",
            """                  final Color color = _tone(group.net);
                  final String statusLabel = group.net > 0
                      ? 'TO RECEIVE'
                      : group.net < 0
                      ? 'TO PAY'
                      : 'SETTLED';

                  return _ListCard(
""",
            "Credit status calculation",
        )

    # ---------------------------------------------------------
    # 4. Left subtitle = ONLY Last entry.
    # ---------------------------------------------------------
    old_subtitle = """                    subtitle:
                        '${group.net > 0
                            ? 'To Receive'
                            : group.net < 0
                            ? 'To Pay'
                            : 'Settled'} • Last ${_displayDate(group.lastDate)}',
"""

    new_subtitle = """                    subtitle:
                        'Last entry: ${_displayDate(group.lastDate)}',
"""

    if old_subtitle in block:
        block = block.replace(old_subtitle, new_subtitle, 1)
    elif "Last entry: ${_displayDate(group.lastDate)}" not in block:
        fail(
            "Credit subtitle is neither the expected old form "
            "nor the desired new form."
        )

    # ---------------------------------------------------------
    # 5. Right column = status above amount.
    # ---------------------------------------------------------
    if "trailingLabel: statusLabel," not in block:
        block = replace_exact_once(
            block,
            """                    trailing: _signedMoney(group.net),
""",
            """                    trailingLabel: statusLabel,
                    trailing: _signedMoney(group.net),
""",
            "Credit trailing amount",
        )

    return source[:start] + block + source[end:]


def verify(source: str) -> None:
    required = (
        "this.trailingLabel,",
        "final String? trailingLabel;",
        "trailingLabel == null",
        "final String statusLabel = group.net > 0",
        "? 'TO RECEIVE'",
        "? 'TO PAY'",
        ": 'SETTLED';",
        "'Last entry: ${_displayDate(group.lastDate)}'",
        "trailingLabel: statusLabel,",
        "trailing: _signedMoney(group.net),",
    )

    for token in required:
        if token not in source:
            fail(f"Verification failed — missing: {token}")

    credit_start = source.index(CREDIT_CLASS)
    credit_end = source.index(CREDIT_DETAIL_CLASS, credit_start)
    credit = source[credit_start:credit_end]

    if "• Last ${_displayDate(group.lastDate)}" in credit:
        fail("Old mixed Credit subtitle still exists.")

    # Core behavior for existing users must remain available.
    if "trailingLabel == null" not in source:
        fail("Legacy _ListCard trailing behavior was not preserved.")

    # Do not touch core credit calculations/navigation.
    protected = (
        "final Color color = _tone(group.net);",
        "trailing: _signedMoney(group.net),",
        "CreditDetailScreen(",
        "personName: group.name",
    )

    for token in protected:
        if token not in credit:
            fail(f"Protected Credit logic changed unexpectedly: {token}")


def main() -> None:
    if not TARGET.is_file():
        fail(f"main.dart not found: {TARGET}")

    original = TARGET.read_text(encoding="utf-8")

    patched = upgrade_list_card(original)
    patched = upgrade_credit_cards(patched)

    verify(patched)

    if patched == original:
        print("✅ Already fixed — no source changes required.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_name(
        f"main.dart.bak_credit_core_{timestamp}"
    )

    shutil.copy2(TARGET, backup)
    TARGET.write_text(patched, encoding="utf-8")

    written = TARGET.read_text(encoding="utf-8")

    if written != patched:
        shutil.copy2(backup, TARGET)
        fail(
            "Post-write verification failed. "
            "Original file restored automatically."
        )

    print("")
    print("✅ CREDIT CORE CARD FIX APPLIED")
    print(f"Target : {TARGET}")
    print(f"Backup : {backup}")
    print("")
    print("Credit Book card now:")
    print("")
    print("  Kabeerr                    TO RECEIVE")
    print("  Last entry: 3 Sep          +₹55,710")
    print("")
    print("  testing 1                  TO RECEIVE")
    print("  Last entry: 3 Sep          +₹50")
    print("")
    print("Removed:")
    print("  • To Receive • Last ... mixed subtitle")
    print("")
    print("Preserved:")
    print("  • amount calculations")
    print("  • red/green semantic colors")
    print("  • customer navigation")
    print("  • search")
    print("  • data/database logic")
    print("  • Milk/Party Ledger normal trailing layout")


if __name__ == "__main__":
    main()
