from __future__ import annotations

from pathlib import Path

TARGET = Path('lib/main.dart')

OLD_DEPTH = '''  static List<BoxShadow> surfaceDepth(BuildContext context) {
    final bool dark = isDark(context);
    return <BoxShadow>[
      BoxShadow(
        color: Colors.black.withAlpha(dark ? 108 : 16),
        blurRadius: dark ? 34 : 24,
        spreadRadius: dark ? -3 : -5,
        offset: Offset.zero,
      ),
    ];
  }
'''

NEW_DEPTH = '''  static List<BoxShadow> surfaceDepth(BuildContext context) {
    final bool dark = isDark(context);
    return <BoxShadow>[
      // Tight key shadow: grounds the surface without making it look stamped.
      BoxShadow(
        color: Colors.black.withAlpha(dark ? 82 : 10),
        blurRadius: dark ? 6 : 5,
        spreadRadius: -2,
        offset: const Offset(0, 1),
      ),
      // Wide ambient shadow: creates the soft elevation falloff.
      BoxShadow(
        color: Colors.black.withAlpha(dark ? 90 : 13),
        blurRadius: dark ? 38 : 28,
        spreadRadius: dark ? -6 : -9,
        offset: const Offset(0, 4),
      ),
    ];
  }
'''

OLD_GLOW = '''    canvas.drawRect(
      bounds,
      Paint()
        ..shader = RadialGradient(
          center: center,
          radius: radius,
          colors: <Color>[color, Colors.transparent],
          stops: const <double>[0, 1],
        ).createShader(bounds),
    );
'''

NEW_GLOW = '''    canvas.drawRect(
      bounds,
      Paint()
        // Screen blending is additive enough for dark mode while srcOver keeps
        // the light theme clean instead of washing white surfaces out.
        ..blendMode = dark ? BlendMode.screen : BlendMode.srcOver
        ..shader = RadialGradient(
          center: center,
          radius: radius,
          colors: <Color>[
            color,
            color.withValues(alpha: color.a * .35),
            Colors.transparent,
          ],
          stops: const <double>[0, .45, 1],
        ).createShader(bounds),
    );
'''

OLD_PRESS_SCALE = '''              scale: 1 - (_pressController.value * .025),'''
NEW_PRESS_SCALE = '''              scale: 1 - (_pressController.value * .022),'''

OLD_PRESS_OVERLAY = '''                          color: Colors.white.withAlpha(
                            (_pressController.value * 18).round(),
                          ),'''
NEW_PRESS_OVERLAY = '''                          color: (Theme.of(context).brightness ==
                                      Brightness.dark
                                  ? Colors.white
                                  : Colors.black)
                              .withAlpha(
                            (_pressController.value *
                                    (Theme.of(context).brightness ==
                                            Brightness.dark
                                        ? 14
                                        : 9))
                                .round(),
                          ),'''

GLASS_CHILDREN = '''      child: Stack(
        children: <Widget>[
          if (accentColor != null)
'''

GLASS_CHILDREN_UPGRADED = '''      child: Stack(
        children: <Widget>[
          // Specular highlight: strongest near the top-center and feathered
          // toward the rounded corners so the card reads as a physical layer.
          Positioned(
            left: math.max(10, borderRadius * .48),
            right: math.max(10, borderRadius * .48),
            top: 0,
            height: 1,
            child: IgnorePointer(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: <Color>[
                      Colors.transparent,
                      Colors.white.withAlpha(dark ? 76 : 210),
                      Colors.transparent,
                    ],
                  ),
                ),
              ),
            ),
          ),
          // Opposing lowlight gives the surface a thin optical thickness
          // without changing its base color or layout.
          Positioned(
            left: math.max(12, borderRadius * .55),
            right: math.max(12, borderRadius * .55),
            bottom: 0,
            height: 1,
            child: IgnorePointer(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: <Color>[
                      Colors.transparent,
                      Colors.black.withAlpha(dark ? 64 : 16),
                      Colors.transparent,
                    ],
                  ),
                ),
              ),
            ),
          ),
          if (accentColor != null)
'''


def replace_exact(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'depth_visual_upgrade: expected 1 {label}, found {count}')
    return text.replace(old, new, 1)


def validate(text: str) -> None:
    required = [
        'blurRadius: dark ? 6 : 5,',
        'blurRadius: dark ? 38 : 28,',
        '..blendMode = dark ? BlendMode.screen : BlendMode.srcOver',
        'color.withValues(alpha: color.a * .35)',
        'stops: const <double>[0, .45, 1],',
        'Colors.white.withAlpha(dark ? 76 : 210)',
        'Colors.black.withAlpha(dark ? 64 : 16)',
        'scale: 1 - (_pressController.value * .022),',
    ]
    missing = [token for token in required if token not in text]
    if missing:
        raise SystemExit(f'depth_visual_upgrade: validation missing {missing}')

    if 'blurRadius: dark ? 34 : 24,' in text:
        raise SystemExit('depth_visual_upgrade: old single-layer surface shadow remains')
    if 'colors: <Color>[color, Colors.transparent]' in text:
        raise SystemExit('depth_visual_upgrade: old two-stop ambient glow remains')


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f'depth_visual_upgrade: missing {TARGET}')

    text = TARGET.read_text(encoding='utf-8')

    if 'blurRadius: dark ? 6 : 5,' in text:
        validate(text)
        print('depth_visual_upgrade: already applied')
        return

    text = replace_exact(text, OLD_DEPTH, NEW_DEPTH, 'surfaceDepth block')
    text = replace_exact(text, OLD_GLOW, NEW_GLOW, 'ambient glow block')
    text = replace_exact(text, OLD_PRESS_SCALE, NEW_PRESS_SCALE, 'press scale')
    text = replace_exact(text, OLD_PRESS_OVERLAY, NEW_PRESS_OVERLAY, 'press overlay')
    text = replace_exact(text, GLASS_CHILDREN, GLASS_CHILDREN_UPGRADED, 'glass edge block')

    validate(text)
    TARGET.write_text(text, encoding='utf-8')
    print('depth_visual_upgrade: applied layered shadows, optical edge depth, ambient falloff, and tactile press tuning')


if __name__ == '__main__':
    main()
