from pathlib import Path

MAIN = Path('lib/main.dart')
PUBSPEC = Path('pubspec.yaml')

text = MAIN.read_text(encoding='utf-8')


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 match, found {count}')
    text = text.replace(old, new, 1)


def replace_in_section(start_marker: str, end_marker: str, old: str, new: str, label: str) -> None:
    global text
    start = text.find(start_marker)
    if start < 0:
        raise SystemExit(f'{label}: start marker not found')
    end = text.find(end_marker, start)
    if end < 0:
        raise SystemExit(f'{label}: end marker not found')
    section = text[start:end]
    count = section.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 section match, found {count}')
    section = section.replace(old, new, 1)
    text = text[:start] + section + text[end:]


old_physics = '''  static List<BoxShadow> surfaceDepth(BuildContext context) {
    final bool dark = isDark(context);
    return <BoxShadow>[
      BoxShadow(
        color: Colors.black.withAlpha(dark ? 82 : 10),
        blurRadius: dark ? 12 : 8,
        spreadRadius: -2,
        offset: const Offset(0, 2),
      ),
      BoxShadow(
        color: Colors.black.withAlpha(dark ? 112 : 22),
        blurRadius: dark ? 62 : 48,
        spreadRadius: dark ? -12 : -10,
        offset: const Offset(0, 16),
      ),
    ];
  }

  static List<BoxShadow> glow(
    BuildContext context,
    Color color, {
    bool strong = false,
  }) {
    final bool dark = isDark(context);
    return <BoxShadow>[
      BoxShadow(
        color: color.withAlpha(
          strong ? (dark ? 76 : 58) : (dark ? 50 : 38),
        ),
        blurRadius: strong ? 30 : 22,
        spreadRadius: strong ? -1 : -2,
        offset: const Offset(0, 8),
      ),
      if (strong)
        BoxShadow(
          color: color.withAlpha(dark ? 42 : 32),
          blurRadius: 68,
          spreadRadius: -8,
          offset: const Offset(0, 24),
        ),
      ...surfaceDepth(context),
    ];
  }

  static List<BoxShadow> railDepth(BuildContext context, Color color) {
    final bool dark = isDark(context);
    return <BoxShadow>[
      BoxShadow(
        color: color.withAlpha(dark ? 72 : 56),
        blurRadius: dark ? 28 : 22,
        spreadRadius: -5,
        offset: const Offset(-4, 0),
      ),
      ...surfaceDepth(context),
    ];
  }

  static List<BoxShadow> jewelDepth(BuildContext context, Color color) {
    final bool dark = isDark(context);
    return <BoxShadow>[
      BoxShadow(
        color: color.withAlpha(dark ? 68 : 48),
        blurRadius: 22,
        spreadRadius: -3,
        offset: const Offset(0, 8),
      ),
      BoxShadow(
        color: color.withAlpha(dark ? 34 : 24),
        blurRadius: 34,
        spreadRadius: -7,
        offset: Offset.zero,
      ),
    ];
  }

  static Border glassBorder(BuildContext context, {Color? accent}) {
    final bool dark = isDark(context);
    return Border(
      top: BorderSide(
        color: Colors.white.withAlpha(dark ? 31 : 174),
        width: UIConstants.borderWidth,
      ),
      right: BorderSide(
        color: Colors.white.withAlpha(dark ? 20 : 92),
        width: UIConstants.borderWidth,
      ),
      bottom: BorderSide(
        color: dark ? Colors.black.withAlpha(96) : Colors.white.withAlpha(66),
        width: UIConstants.borderWidth,
      ),
      left: accent == null
          ? BorderSide(
              color: Colors.white.withAlpha(dark ? 20 : 92),
              width: UIConstants.borderWidth,
            )
          : BorderSide(
              color: accent.withAlpha(dark ? 82 : 72),
              width: UIConstants.borderWidth,
            ),
    );
  }
'''

new_physics = '''  static List<BoxShadow> surfaceDepth(BuildContext context) {
    final bool dark = isDark(context);
    return <BoxShadow>[
      // Small contact shadow keeps the card grounded without a visible box.
      BoxShadow(
        color: Colors.black.withAlpha(dark ? 64 : 10),
        blurRadius: dark ? 10 : 8,
        spreadRadius: -2,
        offset: const Offset(0, 2),
      ),
      // Moderate falloff avoids large raster-filter bounds on mobile GPUs.
      BoxShadow(
        color: Colors.black.withAlpha(dark ? 76 : 16),
        blurRadius: dark ? 34 : 28,
        spreadRadius: -7,
        offset: const Offset(0, 10),
      ),
    ];
  }

  static List<BoxShadow> glow(
    BuildContext context,
    Color color, {
    bool strong = false,
  }) {
    final bool dark = isDark(context);
    return <BoxShadow>[
      // Semantic lift: the card casts a soft shadow in its own module color.
      BoxShadow(
        color: color.withAlpha(
          strong ? (dark ? 66 : 48) : (dark ? 48 : 34),
        ),
        blurRadius: strong ? 34 : 26,
        spreadRadius: strong ? -4 : -5,
        offset: const Offset(0, 12),
      ),
      if (strong)
        BoxShadow(
          color: color.withAlpha(dark ? 32 : 22),
          blurRadius: 44,
          spreadRadius: -10,
          offset: const Offset(0, 18),
        ),
      ...surfaceDepth(context),
    ];
  }

  static List<BoxShadow> railDepth(BuildContext context, Color color) {
    final bool dark = isDark(context);
    return <BoxShadow>[
      // A narrow side aura reinforces the semantic rail without drawing a box.
      BoxShadow(
        color: color.withAlpha(dark ? 62 : 44),
        blurRadius: 18,
        spreadRadius: -4,
        offset: const Offset(-3, 0),
      ),
      BoxShadow(
        color: color.withAlpha(dark ? 34 : 24),
        blurRadius: 30,
        spreadRadius: -8,
        offset: const Offset(0, 12),
      ),
      ...surfaceDepth(context),
    ];
  }

  static List<BoxShadow> jewelDepth(BuildContext context, Color color) {
    final bool dark = isDark(context);
    return <BoxShadow>[
      BoxShadow(
        color: color.withAlpha(dark ? 56 : 40),
        blurRadius: 18,
        spreadRadius: -4,
        offset: const Offset(0, 6),
      ),
      BoxShadow(
        color: color.withAlpha(dark ? 28 : 20),
        blurRadius: 26,
        spreadRadius: -8,
        offset: Offset.zero,
      ),
    ];
  }

  static Border glassBorder(BuildContext context, {Color? accent}) {
    final bool dark = isDark(context);
    final Color edge = accent == null
        ? Colors.white.withAlpha(dark ? 30 : 132)
        : Color.lerp(Colors.white, accent, dark ? .22 : .14)!
            .withAlpha(dark ? 64 : 86);
    // Keep all four sides identical so BoxDecoration can paint the border as
    // one rounded RRect. Non-uniform Border sides can expose square seams.
    return Border.all(color: edge, width: UIConstants.borderWidth);
  }
'''
replace_once(old_physics, new_physics, 'shadow and rounded border physics')

# Keep the shadow outside the clipping layer. This avoids rectangular save-layer
# edges while still clipping card content and the semantic rail to the RRect.
replace_in_section(
    'class _GlassCard extends StatelessWidget {',
    'class _CardAccentPainter extends CustomPainter {',
    '''    return Container(\n      clipBehavior: Clip.antiAlias,\n      decoration: BoxDecoration(''',
    '''    final BorderRadius radius = BorderRadius.circular(borderRadius);\n    return DecoratedBox(\n      decoration: BoxDecoration(''',
    'glass outer decoration',
)
replace_in_section(
    'class _GlassCard extends StatelessWidget {',
    'class _CardAccentPainter extends CustomPainter {',
    '        borderRadius: BorderRadius.circular(borderRadius),',
    '        borderRadius: radius,',
    'glass rounded radius token',
)
replace_in_section(
    'class _GlassCard extends StatelessWidget {',
    'class _CardAccentPainter extends CustomPainter {',
    '''      child: Stack(\n        children: <Widget>[''',
    '''      child: ClipRRect(\n        borderRadius: radius,\n        clipBehavior: Clip.antiAlias,\n        child: Stack(\n          children: <Widget>[''',
    'glass inner clip start',
)
replace_in_section(
    'class _GlassCard extends StatelessWidget {',
    'class _CardAccentPainter extends CustomPainter {',
    '''          Padding(\n            padding: padding,\n            child: child,\n          ),\n        ],\n      ),\n    );''',
    '''            Padding(\n              padding: padding,\n              child: child,\n            ),\n          ],\n        ),\n      ),\n    );''',
    'glass inner clip end',
)

# Dashboard metric cards should read as tinted glass with colored shadow, not a
# colored outline. The shared neutral rounded glass edge is cleaner.
replace_in_section(
    'class _MetricCard extends StatelessWidget {',
    'class _LedgerIcon extends StatelessWidget {',
    '        borderColor: color.withAlpha(77),\n',
    '',
    'metric card colored outline removal',
)

# Jewel icons get the compact shadow formula, avoiding oversized glow buffers.
replace_in_section(
    'class _LedgerIcon extends StatelessWidget {',
    'class PartyLedgerScreen extends StatefulWidget {',
    '          boxShadow: AppStyles.glow(context, color),',
    '          boxShadow: AppStyles.jewelDepth(context, color),',
    'ledger icon jewel shadow',
)

MAIN.write_text(text, encoding='utf-8')

pub = PUBSPEC.read_text(encoding='utf-8')
old_version = 'version: 1.0.4+5'
new_version = 'version: 1.0.5+6'
if pub.count(old_version) != 1:
    raise SystemExit(f'version bump: expected exactly 1 match, found {pub.count(old_version)}')
PUBSPEC.write_text(pub.replace(old_version, new_version, 1), encoding='utf-8')
