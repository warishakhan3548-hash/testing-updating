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


# 1) Keep card edge neutral. Semantic identity already comes from the left rail
# and the semantic shadow; tinting all four borders makes cards read as boxes.
replace_once(
'''  static Border glassBorder(BuildContext context, {Color? accent}) {
    final bool dark = isDark(context);
    final Color edge = accent == null
        ? Colors.white.withAlpha(dark ? 30 : 132)
        : Color.lerp(Colors.white, accent, dark ? .22 : .14)!
            .withAlpha(dark ? 64 : 86);
    // Keep all four sides identical so BoxDecoration paints one rounded RRect.
    return Border.all(color: edge, width: UIConstants.borderWidth);
  }
''',
'''  static Border glassBorder(BuildContext context, {Color? accent}) {
    final bool dark = isDark(context);
    return Border.all(
      color: Colors.white.withAlpha(dark ? 24 : 96),
      width: UIConstants.borderWidth,
    );
  }
''',
'neutral rounded glass edge',
)

# 2) Make cards crisper and more opaque so ambient color does not wash through
# the whole rectangular raster bounds on phones.
replace_once(
'''    if (tintColor == null) {
      surfaceColors = dark
          ? const <Color>[Color(0xDC121826), Color(0xBC080C18)]
          : const <Color>[Color(0xE0FFFFFF), Color(0xAEFFFFFF)];
    } else {
      surfaceColors = dark
          ? <Color>[
              Color.lerp(darkGlassTop, tintColor, .15)!.withAlpha(220),
              Color.lerp(darkGlassBottom, tintColor, .075)!.withAlpha(188),
            ]
          : <Color>[
              Color.lerp(Colors.white, tintColor, .08)!.withAlpha(224),
              Color.lerp(Colors.white, tintColor, .045)!.withAlpha(174),
            ];
    }
''',
'''    if (tintColor == null) {
      surfaceColors = dark
          ? const <Color>[Color(0xF0121826), Color(0xE3080C18)]
          : const <Color>[Color(0xFAFFFFFF), Color(0xF2FFFFFF)];
    } else {
      surfaceColors = dark
          ? <Color>[
              Color.lerp(darkGlassTop, tintColor, .12)!.withAlpha(240),
              Color.lerp(darkGlassBottom, tintColor, .06)!.withAlpha(224),
            ]
          : <Color>[
              Color.lerp(Colors.white, tintColor, .055)!.withAlpha(248),
              Color.lerp(Colors.white, tintColor, .028)!.withAlpha(236),
            ];
    }
''',
'crisp glass surface opacity',
)

# 3) Tighter contact shadow + controlled semantic lift.
replace_once(
'''  static List<BoxShadow> surfaceDepth(BuildContext context) {
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
''',
'''  static List<BoxShadow> surfaceDepth(BuildContext context) {
    final bool dark = isDark(context);
    return <BoxShadow>[
      BoxShadow(
        color: Colors.black.withAlpha(dark ? 56 : 12),
        blurRadius: 7,
        spreadRadius: -2,
        offset: const Offset(0, 2),
      ),
      BoxShadow(
        color: Colors.black.withAlpha(dark ? 66 : 15),
        blurRadius: dark ? 28 : 24,
        spreadRadius: -7,
        offset: const Offset(0, 9),
      ),
    ];
  }
''',
'contact and ambient shadow refinement',
)

replace_once(
'''      // Semantic lift: the card casts a soft shadow in its own module color.
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
''',
'''      BoxShadow(
        color: color.withAlpha(
          strong ? (dark ? 60 : 42) : (dark ? 44 : 30),
        ),
        blurRadius: strong ? 28 : 22,
        spreadRadius: -5,
        offset: const Offset(0, 8),
      ),
      if (strong)
        BoxShadow(
          color: color.withAlpha(dark ? 28 : 20),
          blurRadius: 40,
          spreadRadius: -10,
          offset: const Offset(0, 16),
        ),
''',
'semantic glow refinement',
)

# 4) Preserve the 4px rail but reduce the broad painted halo.
replace_once(
'''    canvas.drawPath(
      path,
      Paint()
        ..color = color.withAlpha(dark ? 64 : 50)
        ..style = PaintingStyle.stroke
        ..strokeWidth = UIConstants.accentStroke + 8
        ..strokeCap = StrokeCap.round
        ..strokeJoin = StrokeJoin.round,
    );
''',
'''    canvas.drawPath(
      path,
      Paint()
        ..color = color.withAlpha(dark ? 48 : 32)
        ..style = PaintingStyle.stroke
        ..strokeWidth = UIConstants.accentStroke + 4
        ..strokeCap = StrokeCap.round
        ..strokeJoin = StrokeJoin.round,
    );
''',
'rail halo refinement',
)

# 5) Keep semantic ink crisp; depth should come mostly from surfaces.
replace_once(
'''  static List<Shadow> inkGlow(Color color, {bool strong = false}) => <Shadow>[
        Shadow(
          color: color.withAlpha(strong ? 104 : 72),
          blurRadius: strong ? 12 : 8,
          offset: Offset.zero,
        ),
      ];
''',
'''  static List<Shadow> inkGlow(Color color, {bool strong = false}) => <Shadow>[
        Shadow(
          color: color.withAlpha(strong ? 58 : 34),
          blurRadius: strong ? 7 : 4,
          offset: Offset.zero,
        ),
      ];
''',
'crisper text and icon glow',
)

# 6) Header already has a soft drop shadow; remove the explicit hard separator.
replace_once(
'''              border: Border(bottom: AppStyles.hairline(context)),
''',
'''              // Soft elevation replaces a hard separator line.
''',
'header separator removal',
)

# 7) Bottom nav: one soft outer elevation cue is enough. Remove the hairline and
# inner white line, then calm the active state for financial-app hierarchy.
replace_once(
'''              border: Border(top: AppStyles.hairline(context)),
              boxShadow: <BoxShadow>[
                BoxShadow(
                  color: Colors.white.withAlpha(dark ? 16 : 90),
                  blurRadius: 1,
                  offset: const Offset(0, -1),
                ),
              ],
''',
'''              boxShadow: const <BoxShadow>[],
''',
'bottom navigation hard line removal',
)

replace_once(
'''                                    scale: active ? 1.13 : 1,
''',
'''                                    scale: active ? 1.08 : 1,
''',
'bottom navigation active scale',
)
replace_once(
'''                                      size: active ? 25 : 23,
''',
'''                                      size: active ? 24 : 22,
''',
'bottom navigation icon size',
)
replace_once(
'''                                          : color.withAlpha(dark ? 176 : 188),
''',
'''                                          : color.withAlpha(dark ? 148 : 145),
''',
'bottom navigation inactive icon alpha',
)
replace_once(
'''                                    width: active ? 40 : 0,
                                    height: 4,
''',
'''                                    width: active ? 34 : 0,
                                    height: 3,
''',
'bottom navigation indicator geometry',
)
replace_once(
'''                                                blurRadius: 18,
''',
'''                                                blurRadius: 12,
''',
'bottom navigation indicator glow',
)

MAIN.write_text(text, encoding='utf-8')

pub = PUBSPEC.read_text(encoding='utf-8')
old_version = 'version: 1.0.5+6'
new_version = 'version: 1.0.6+7'
if pub.count(old_version) != 1:
    raise SystemExit(f'version bump: expected exactly 1 match, found {pub.count(old_version)}')
PUBSPEC.write_text(pub.replace(old_version, new_version, 1), encoding='utf-8')
