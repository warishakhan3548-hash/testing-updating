#!/usr/bin/env python3
from pathlib import Path

path = Path('lib/main.dart')
code = path.read_text(encoding='utf-8')

constructor_old = """class _AmountHero extends StatelessWidget {
  const _AmountHero({
    required this.label,
    required this.value,
    required this.color,
    this.trailingLabel,
    this.trailingValue,
  });

  final String label;
  final String value;
  final Color color;
  final String? trailingLabel;
  final String? trailingValue;
"""
constructor_new = """class _AmountHero extends StatelessWidget {
  const _AmountHero({
    required this.label,
    required this.value,
    required this.color,
  });

  final String label;
  final String value;
  final Color color;
"""

child_old = """      child: Row(
        children: <Widget>[
          Expanded(
            child: _HeroValue(
              label: label,
              value: value,
              color: textColor,
              glow: color,
            ),
          ),
          if (trailingLabel != null && trailingValue != null)
            _HeroValue(
              label: trailingLabel!,
              value: trailingValue!,
              color: textColor,
              glow: color,
              alignEnd: true,
              small: true,
            ),
        ],
      ),
"""
child_new = """      child: _HeroValue(
        label: label,
        value: value,
        color: textColor,
        glow: color,
      ),
"""

for label, old, new in (
    ('_AmountHero constructor', constructor_old, constructor_new),
    ('_AmountHero child', child_old, child_new),
):
    count = code.count(old)
    if count != 1:
        raise SystemExit(f'SAFETY STOP: {label} expected exactly once, found {count}')
    code = code.replace(old, new, 1)

if 'trailingLabel:' in code or 'trailingValue:' in code:
    raise SystemExit('SAFETY STOP: a trailing _AmountHero call still exists after Milk migration')

path.write_text(code, encoding='utf-8')
print('Removed now-dead _AmountHero trailing API after Milk hero specialization.')
