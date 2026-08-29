#!/usr/bin/env python3
from pathlib import Path

path = Path('lib/main.dart')
code = path.read_text(encoding='utf-8')

replacements = []

replacements.append((
    '_AmountHero constructor',
    """class _AmountHero extends StatelessWidget {
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
""",
    """class _AmountHero extends StatelessWidget {
  const _AmountHero({
    required this.label,
    required this.value,
    required this.color,
  });

  final String label;
  final String value;
  final Color color;
""",
))

replacements.append((
    '_AmountHero child',
    """      child: Row(
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
""",
    """      child: _HeroValue(
        label: label,
        value: value,
        color: textColor,
        glow: color,
      ),
""",
))

replacements.append((
    '_HeroValue dead alignment/size API',
    """class _HeroValue extends StatelessWidget {
  const _HeroValue({
    required this.label,
    required this.value,
    required this.color,
    required this.glow,
    this.alignEnd = false,
    this.small = false,
  });

  final String label;
  final String value;
  final Color color;
  final Color glow;
  final bool alignEnd;
  final bool small;

  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment:
            alignEnd ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            label.toUpperCase(),
            style: TextStyle(
              color: color,
              fontSize: 10,
              fontWeight: FontWeight.w900,
              letterSpacing: .8,
              shadows: <Shadow>[
                Shadow(color: glow.withAlpha(78), blurRadius: 12),
              ],
            ),
          ),
          const SizedBox(height: 5),
          Text(
            value,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              color: color,
              fontSize: small ? 20 : 31,
              fontWeight: FontWeight.w900,
              letterSpacing: -.8,
              shadows: <Shadow>[
                Shadow(color: glow.withAlpha(94), blurRadius: 16),
              ],
            ),
          ),
        ],
      );
}
""",
    """class _HeroValue extends StatelessWidget {
  const _HeroValue({
    required this.label,
    required this.value,
    required this.color,
    required this.glow,
  });

  final String label;
  final String value;
  final Color color;
  final Color glow;

  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            label.toUpperCase(),
            style: TextStyle(
              color: color,
              fontSize: 10,
              fontWeight: FontWeight.w900,
              letterSpacing: .8,
              shadows: <Shadow>[
                Shadow(color: glow.withAlpha(78), blurRadius: 12),
              ],
            ),
          ),
          const SizedBox(height: 5),
          Text(
            value,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              color: color,
              fontSize: 31,
              fontWeight: FontWeight.w900,
              letterSpacing: -.8,
              shadows: <Shadow>[
                Shadow(color: glow.withAlpha(94), blurRadius: 16),
              ],
            ),
          ),
        ],
      );
}
""",
))

for label, old, new in replacements:
    count = code.count(old)
    if count != 1:
        raise SystemExit(f'SAFETY STOP: {label} expected exactly once, found {count}')
    code = code.replace(old, new, 1)

for dead in ('trailingLabel:', 'trailingValue:', 'alignEnd:', 'small: true'):
    if dead in code:
        raise SystemExit(f'SAFETY STOP: dead hero API still referenced: {dead}')

path.write_text(code, encoding='utf-8')
print('Removed dead shared hero API after Milk hero specialization.')
