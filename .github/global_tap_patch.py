from pathlib import Path

p = Path('lib/main.dart')
s = p.read_text()

replacements = {
    "final int coreAlpha = (opacity * 34).round().clamp(0, 255);":
        "final int coreAlpha = (opacity * 34).round().clamp(0, 255).toInt();",
    "final int haloAlpha = (opacity * 15).round().clamp(0, 255);":
        "final int haloAlpha = (opacity * 15).round().clamp(0, 255).toInt();",
    "final int ringAlpha = (opacity * 118).round().clamp(0, 255);":
        "final int ringAlpha = (opacity * 118).round().clamp(0, 255).toInt();",
    "(opacity * (1 - echo) * 64).round().clamp(0, 255);":
        "(opacity * (1 - echo) * 64).round().clamp(0, 255).toInt();",
}

for old, new in replacements.items():
    count = s.count(old)
    if count != 1:
        raise SystemExit(f'Expected one occurrence of {old!r}, found {count}')
    s = s.replace(old, new, 1)

p.write_text(s)
