from pathlib import Path

MAIN = Path('lib/main.dart')
PUBSPEC = Path('pubspec.yaml')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 match, found {count}')
    return text.replace(old, new, 1)


def main() -> None:
    text = MAIN.read_text(encoding='utf-8')

    # The previous adaptive implementation collapsed compact share actions to an
    # icon-only control on common 360-390dp Android widths. That made the new UI
    # look almost identical to the legacy share icon. Keep a real metallic pill
    # everywhere, only shrinking its geometry when horizontal space is tight.
    text = replace_once(
        text,
        """    final bool iconOnly = compact && viewportWidth < 390;\n    final bool micro = compact && viewportWidth < 340;\n    final double height = micro ? 48 : (compact ? 50 : 54);\n    final double width = iconOnly ? height : (compact ? 104 : 138);\n""",
        """    final bool micro = compact && viewportWidth < 340;\n    final double height = micro ? 46 : (compact ? 48 : 54);\n    final double width = compact ? (micro ? 96 : 108) : 138;\n""",
        'adaptive geometry',
    )

    text = replace_once(
        text,
        """                    padding: EdgeInsets.symmetric(\n                      horizontal: iconOnly ? 7 : (compact ? 8 : 10),\n                    ),\n                    child: iconOnly\n                        ? Center(\n                            child: _PremiumShareGlyph(\n                              icon: icon,\n                              neon: neon,\n                              size: micro ? 29 : 31,\n                            ),\n                          )\n                        : Row(\n""",
        """                    padding: EdgeInsets.symmetric(\n                      horizontal: compact ? 7 : 10,\n                    ),\n                    child: Row(\n""",
        'compact content branch',
    )

    if 'iconOnly' in text:
        raise SystemExit('legacy iconOnly share fallback still exists')

    MAIN.write_text(text, encoding='utf-8')

    pubspec = PUBSPEC.read_text(encoding='utf-8')
    if 'version: 1.0.2+3' not in pubspec:
        pubspec = replace_once(
            pubspec,
            'version: 1.0.1+2\n',
            'version: 1.0.2+3\n',
            'build version',
        )
        PUBSPEC.write_text(pubspec, encoding='utf-8')

    print('premium share fix applied: compact buttons now always show SHARE pill')


if __name__ == '__main__':
    main()
