from __future__ import annotations

import re
from pathlib import Path

TARGET = Path("lib/main.dart")

NEW_CLASS = r'''class _TransactionPairButton extends StatelessWidget {
  const _TransactionPairButton({
    required this.label,
    required this.icon,
    required this.color,
    required this.onTap,
    this.semanticLabel,
  });

  final String label;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;
  final String? semanticLabel;

  @override
  Widget build(BuildContext context) {
    final bool dark = Theme.of(context).brightness == Brightness.dark;
    final Color companion = Color.lerp(color, Colors.black, .10)!;
    final bool negative = icon == Icons.remove_rounded;

    return _Pressable(
      onTap: onTap,
      semanticLabel: semanticLabel ?? label,
      borderRadius: BorderRadius.circular(UIConstants.actionRadius),
      child: SizedBox(
        width: double.infinity,
        height: UIConstants.standardButtonHeight,
        child: DecoratedBox(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: <Color>[color, companion],
            ),
            borderRadius: BorderRadius.circular(UIConstants.actionRadius),
            border: Border.all(
              color: dark ? Colors.white.withAlpha(34) : color.withAlpha(95),
              width: .8,
            ),
            boxShadow: dark
                ? const <BoxShadow>[]
                : <BoxShadow>[
                    BoxShadow(
                      color: color.withAlpha(50),
                      blurRadius: 28,
                      spreadRadius: 1,
                      offset: const Offset(0, 12),
                    ),
                  ],
          ),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              mainAxisSize: MainAxisSize.max,
              children: <Widget>[
                _TransactionPolarityGlyph(
                  negative: negative,
                  color: Colors.white,
                ),
                const SizedBox(width: 10),
                Flexible(
                  child: FittedBox(
                    fit: BoxFit.scaleDown,
                    child: Text(
                      label,
                      maxLines: 1,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 16.5,
                        height: 1,
                        fontWeight: FontWeight.w800,
                        letterSpacing: -.2,
                        shadows: <Shadow>[
                          Shadow(color: Colors.black26, blurRadius: 8),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _TransactionPolarityGlyph extends StatelessWidget {
  const _TransactionPolarityGlyph({
    required this.negative,
    required this.color,
  });

  final bool negative;
  final Color color;

  @override
  Widget build(BuildContext context) {
    const double lineLength = 20;
    const double stroke = 2.6;
    final BorderRadius round = BorderRadius.circular(99);

    return SizedBox.square(
      dimension: 26,
      child: Stack(
        alignment: Alignment.center,
        children: <Widget>[
          Container(
            width: lineLength,
            height: stroke,
            decoration: BoxDecoration(
              color: color,
              borderRadius: round,
              boxShadow: const <BoxShadow>[
                BoxShadow(color: Colors.black26, blurRadius: 6),
              ],
            ),
          ),
          if (!negative)
            Container(
              width: stroke,
              height: lineLength,
              decoration: BoxDecoration(
                color: color,
                borderRadius: round,
                boxShadow: const <BoxShadow>[
                  BoxShadow(color: Colors.black26, blurRadius: 6),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
'''


def fail(message: str) -> None:
    raise SystemExit(f"uniform_transaction_buttons_patch: {message}")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"expected exactly 1 {label}, found {count}")
    return text.replace(old, new, 1)


def validate(text: str) -> None:
    if "class _MilkCustomerRoleButton extends StatelessWidget" in text:
        fail("legacy milk-specific role button class remains")
    if "_MilkCustomerRoleButton(" in text:
        fail("legacy milk-specific role button call remains")

    pair_calls = len(re.findall(r"child:\s*_TransactionPairButton\(", text))
    if pair_calls != 10:
        fail(f"expected 10 unified transaction button call sites, found {pair_calls}")

    for label, expected in {
        "Seller": 1,
        "Buyer": 1,
        "Receives": 1,
        "Pays": 1,
        "Given": 3,
        "Taken": 3,
    }.items():
        count = len(
            re.findall(
                rf"_TransactionPairButton\(\s*label:\s*'{re.escape(label)}'",
                text,
                flags=re.DOTALL,
            )
        )
        if count != expected:
            fail(f"expected {expected} unified '{label}' buttons, found {count}")

    if re.search(
        r"_PrimaryButton\(\s*label:\s*'(Given|Taken)'",
        text,
        flags=re.DOTALL,
    ):
        fail("credit transaction sheet still uses generic PrimaryButton")

    if "const double lineLength = 20;" not in text or "const double stroke = 2.6;" not in text:
        fail("optically matched plus/minus geometry is missing")


def main() -> None:
    if not TARGET.exists():
        fail(f"missing {TARGET}")

    text = TARGET.read_text(encoding="utf-8")

    if "class _TransactionPairButton extends StatelessWidget" in text:
        validate(text)
        print("uniform_transaction_buttons_patch: already applied")
        return

    class_pattern = re.compile(
        r"class _MilkCustomerRoleButton extends StatelessWidget \{.*?\n\}\n\n(?=class MilkDetailScreen extends StatefulWidget)",
        flags=re.DOTALL,
    )
    text, class_count = class_pattern.subn(NEW_CLASS + "\n\n", text)
    if class_count != 1:
        fail(f"expected 1 legacy role button class, found {class_count}")

    legacy_calls = text.count("_MilkCustomerRoleButton(")
    if legacy_calls != 8:
        fail(f"expected 8 legacy role button call sites, found {legacy_calls}")
    text = text.replace("_MilkCustomerRoleButton(", "_TransactionPairButton(")

    primary_given = """_PrimaryButton(\n                    label: 'Given',\n                    icon: Icons.add_rounded,\n                    color: appleGreen,"""
    primary_taken = """_PrimaryButton(\n                    label: 'Taken',\n                    icon: Icons.remove_rounded,\n                    color: appleRed,"""
    text = replace_once(
        text,
        primary_given,
        """_TransactionPairButton(\n                    label: 'Given',\n                    icon: Icons.add_rounded,\n                    color: appleGreen,""",
        "Credit / Loan Given button",
    )
    text = replace_once(
        text,
        primary_taken,
        """_TransactionPairButton(\n                    label: 'Taken',\n                    icon: Icons.remove_rounded,\n                    color: appleRed,""",
        "Credit / Loan Taken button",
    )

    validate(text)
    TARGET.write_text(text, encoding="utf-8")
    print(
        "uniform_transaction_buttons_patch: unified 5 transaction pairs / 10 buttons "
        "with equal width, height, radius, alignment, and matched +/- geometry"
    )


if __name__ == "__main__":
    main()
