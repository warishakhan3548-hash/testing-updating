#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime
import shutil
import sys

ROOT = Path("/root/Aarish Kingdom/repo")
TARGET = ROOT / "lib" / "main.dart"

AMOUNT_START = "class _AmountHero extends StatelessWidget {"
AMOUNT_END = "class _HeroValue extends StatelessWidget {"

MILK_START = "class _MilkDetailHero extends StatelessWidget {"
MILK_END = "class _SoftShareButton extends StatelessWidget {"

PATCH_MARKER = "UNIFIED_MILK_AMOUNT_HERO_V1"

OLD_MILK_CALL = """                  _MilkDetailHero(
                    amount: _signedMoney(totals.netAmount),
                    totalKg: '${totals.netKg.abs().toStringAsFixed(2)} KG',
                    color: color,
                  ),"""

NEW_MILK_CALL = """                  _AmountHero(
                    label: totals.netAmount > 0
                        ? 'To Receive'
                        : totals.netAmount < 0
                        ? 'To Pay'
                        : 'Net Balance',
                    value: _signedMoney(totals.netAmount),
                    color: color,
                    secondaryLabel: 'Total Milk',
                    secondaryValue:
                        '${totals.netKg.abs().toStringAsFixed(2)} KG',
                  ),"""

NEW_AMOUNT_HERO = r'''class _AmountHero extends StatelessWidget {
  const _AmountHero({
    required this.label,
    required this.value,
    required this.color,
    this.secondaryLabel,
    this.secondaryValue,
  });

  final String label;
  final String value;
  final Color color;
  final String? secondaryLabel;
  final String? secondaryValue;

  @override
  Widget build(BuildContext context) {
    // UNIFIED_MILK_AMOUNT_HERO_V1
    //
    // This stays the single visual source of truth for amount hero cards.
    // Existing Credit / Salary / Expense cards take the original single-value
    // path unchanged. Milk optionally adds one compact secondary statistic.
    final bool dark = Theme.of(context).brightness == Brightness.dark;
    final bool hasSecondary =
        secondaryLabel != null && secondaryValue != null;

    final Color textColor = dark
        ? Color.lerp(Colors.white, color, .72)!
        : Color.lerp(const Color(0xFF06111F), color, .60)!;

    final List<Color> background = dark
        ? <Color>[
            Color.lerp(darkGlassTop, color, .21)!.withAlpha(232),
            Color.lerp(
              darkGlassBottom,
              _toneCompanion(color),
              .16,
            )!.withAlpha(218),
            Color.lerp(Colors.black, color, .18)!.withAlpha(204),
          ]
        : <Color>[
            Color.lerp(Colors.white, color, .11)!.withAlpha(240),
            Color.lerp(
              Colors.white,
              _toneCompanion(color),
              .08,
            )!.withAlpha(218),
            Color.lerp(Colors.white, color, .13)!.withAlpha(194),
          ];

    final Widget primary = _HeroValue(
      label: label,
      value: value,
      color: textColor,
      glow: color,
    );

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: background,
        ),
        borderRadius: BorderRadius.circular(UIConstants.heroRadius),
        border: AppStyles.glassBorder(context),
        boxShadow: AppStyles.glow(context, color, strong: true),
      ),
      child: hasSecondary
          ? Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: <Widget>[
                Expanded(
                  flex: 7,
                  child: primary,
                ),
                const SizedBox(width: 14),
                Container(
                  width: 1,
                  height: 54,
                  color: color.withAlpha(dark ? 54 : 25),
                ),
                const SizedBox(width: 14),
                Expanded(
                  flex: 4,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: <Widget>[
                      Text(
                        secondaryLabel!.toUpperCase(),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        textAlign: TextAlign.right,
                        style: TextStyle(
                          color: textColor,
                          fontSize: 10.5,
                          fontWeight: FontWeight.w600,
                          letterSpacing: .75,
                          shadows: <Shadow>[
                            Shadow(
                              color: color.withAlpha(68),
                              blurRadius: 10,
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 5),
                      FittedBox(
                        fit: BoxFit.scaleDown,
                        alignment: Alignment.centerRight,
                        child: Text(
                          secondaryValue!,
                          maxLines: 1,
                          softWrap: false,
                          style: TextStyle(
                            color: textColor,
                            fontSize: 19,
                            fontWeight: FontWeight.w700,
                            fontFeatures: AppStyles.tabularFigures,
                            letterSpacing: -.35,
                            shadows: <Shadow>[
                              Shadow(
                                color: color.withAlpha(82),
                                blurRadius: 13,
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            )
          : primary,
    );
  }
}

'''


def fail(message: str) -> None:
    print(f"\nERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def replace_region(
    source: str,
    start_marker: str,
    end_marker: str,
    replacement: str,
    label: str,
) -> str:
    if source.count(start_marker) != 1:
        fail(
            f"{label}: expected exactly one start marker; "
            f"found {source.count(start_marker)}"
        )

    start = source.index(start_marker)

    if source[start:].count(end_marker) != 1:
        fail(
            f"{label}: expected exactly one end marker after start; "
            f"found {source[start:].count(end_marker)}"
        )

    end = source.index(end_marker, start)
    return source[:start] + replacement + source[end:]


def main() -> None:
    if not TARGET.is_file():
        fail(f"main.dart not found: {TARGET}")

    original = TARGET.read_text(encoding="utf-8")

    if PATCH_MARKER in original:
        print("UNIFIED_MILK_AMOUNT_HERO_V1 is already installed.")
        return

    if original.count(OLD_MILK_CALL) != 1:
        fail(
            "Current Milk hero call does not match the expected source. "
            "Nothing was changed."
        )

    patched = original.replace(
        OLD_MILK_CALL,
        NEW_MILK_CALL,
        1,
    )

    # Upgrade the original shared hero itself instead of creating another
    # wrapper or another competing card implementation.
    patched = replace_region(
        patched,
        AMOUNT_START,
        AMOUNT_END,
        NEW_AMOUNT_HERO,
        "_AmountHero",
    )

    # Completely remove the old oversized Milk-only hero implementation.
    patched = replace_region(
        patched,
        MILK_START,
        MILK_END,
        "",
        "_MilkDetailHero",
    )

    # Surgical verification.
    required = (
        PATCH_MARKER,
        "secondaryLabel: 'Total Milk'",
        "secondaryValue:",
        "label: totals.netAmount > 0",
        "class _AmountHero extends StatelessWidget {",
    )

    for token in required:
        if token not in patched:
            fail(f"Verification failed; missing token: {token}")

    if "class _MilkDetailHero extends StatelessWidget {" in patched:
        fail("Old _MilkDetailHero still exists after patch.")

    if "_MilkDetailHero(" in patched:
        fail("Old _MilkDetailHero call still exists after patch.")

    # Other shared hero consumers must remain present.
    protected = (
        "label: 'Total Salary (This Month)'",
        "label: 'Month Expense'",
        "label: 'Category Total'",
        "class CreditDetailScreen extends StatefulWidget",
        "class MilkDetailScreen extends StatefulWidget",
    )

    for token in protected:
        if token not in patched:
            fail(f"Protected existing UI path disappeared: {token}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_name(
        f"main.dart.bak_milk_hero_{timestamp}"
    )

    shutil.copy2(TARGET, backup)
    TARGET.write_text(patched, encoding="utf-8")

    verify = TARGET.read_text(encoding="utf-8")
    if verify != patched:
        shutil.copy2(backup, TARGET)
        fail("Write verification failed. Original backup restored.")

    print("")
    print("PATCH APPLIED SUCCESSFULLY")
    print(f"Target : {TARGET}")
    print(f"Backup : {backup}")
    print("")
    print("Milk customer hero is now unified with Credit hero:")
    print("  Amount surface = same _AmountHero engine")
    print("  Month amount   = same typography/layout logic")
    print("  Total Milk     = compact secondary stat")
    print("  Old oversized _MilkDetailHero = removed")
    print("  Credit/Salary/Expense existing appearance = preserved")


if __name__ == "__main__":
    main()
