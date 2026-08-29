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


replace_once(
    "import 'dart:math' as math;\n",
    "import 'dart:math' as math;\nimport 'dart:ui' as ui;\n",
    'dart:ui import',
)

replace_once(
    "const Color lightCanvas = Color(0xFFF8FBFF);",
    "const Color lightCanvas = Color(0xFFF5F5F7);",
    'light canvas',
)

replace_once(
    """  static const double heroRadius = 24;\n  static const double sheetRadius = 32;\n  static const double accentStroke = 6;""",
    """  static const double heroRadius = 28;\n  static const double sheetRadius = 36;\n  static const double accentStroke = 4;""",
    'geometry tokens',
)

old_depth = """  static List<BoxShadow> surfaceDepth(BuildContext context) {\n    final bool dark = isDark(context);\n    return <BoxShadow>[\n      // Tight key shadow: grounds the surface without making it look stamped.\n      BoxShadow(\n        color: Colors.black.withAlpha(dark ? 82 : 10),\n        blurRadius: dark ? 6 : 5,\n        spreadRadius: -2,\n        offset: const Offset(0, 1),\n      ),\n      // Wide ambient shadow: creates the soft elevation falloff.\n      BoxShadow(\n        color: Colors.black.withAlpha(dark ? 90 : 13),\n        blurRadius: dark ? 38 : 28,\n        spreadRadius: dark ? -6 : -9,\n        offset: const Offset(0, 4),\n      ),\n    ];\n  }"""
new_depth = """  static List<BoxShadow> surfaceDepth(BuildContext context) {\n    final bool dark = isDark(context);\n    return <BoxShadow>[\n      BoxShadow(\n        color: Colors.black.withAlpha(dark ? 82 : 10),\n        blurRadius: dark ? 12 : 8,\n        spreadRadius: -2,\n        offset: const Offset(0, 2),\n      ),\n      BoxShadow(\n        color: Colors.black.withAlpha(dark ? 112 : 22),\n        blurRadius: dark ? 62 : 48,\n        spreadRadius: dark ? -12 : -10,\n        offset: const Offset(0, 16),\n      ),\n    ];\n  }"""
replace_once(old_depth, new_depth, 'surface depth')

old_glow = """  static List<BoxShadow> glow(\n    BuildContext context,\n    Color color, {\n    bool strong = false,\n  }) {\n    final bool dark = isDark(context);\n    return <BoxShadow>[\n      BoxShadow(\n        color: color.withAlpha(\n          strong ? (dark ? 86 : 66) : (dark ? 58 : 44),\n        ),\n        blurRadius: strong ? 30 : 22,\n        spreadRadius: strong ? 1 : 0,\n        offset: Offset.zero,\n      ),\n      ...surfaceDepth(context),\n    ];\n  }\n\n  static List<Shadow> inkGlow"""
new_glow = """  static List<BoxShadow> glow(\n    BuildContext context,\n    Color color, {\n    bool strong = false,\n  }) {\n    final bool dark = isDark(context);\n    return <BoxShadow>[\n      BoxShadow(\n        color: color.withAlpha(\n          strong ? (dark ? 76 : 58) : (dark ? 50 : 38),\n        ),\n        blurRadius: strong ? 30 : 22,\n        spreadRadius: strong ? -1 : -2,\n        offset: const Offset(0, 8),\n      ),\n      if (strong)\n        BoxShadow(\n          color: color.withAlpha(dark ? 42 : 32),\n          blurRadius: 68,\n          spreadRadius: -8,\n          offset: const Offset(0, 24),\n        ),\n      ...surfaceDepth(context),\n    ];\n  }\n\n  static List<BoxShadow> railDepth(BuildContext context, Color color) {\n    final bool dark = isDark(context);\n    return <BoxShadow>[\n      BoxShadow(\n        color: color.withAlpha(dark ? 72 : 56),\n        blurRadius: dark ? 28 : 22,\n        spreadRadius: -5,\n        offset: const Offset(-4, 0),\n      ),\n      ...surfaceDepth(context),\n    ];\n  }\n\n  static List<BoxShadow> jewelDepth(BuildContext context, Color color) {\n    final bool dark = isDark(context);\n    return <BoxShadow>[\n      BoxShadow(\n        color: color.withAlpha(dark ? 68 : 48),\n        blurRadius: 22,\n        spreadRadius: -3,\n        offset: const Offset(0, 8),\n      ),\n      BoxShadow(\n        color: color.withAlpha(dark ? 34 : 24),\n        blurRadius: 34,\n        spreadRadius: -7,\n        offset: Offset.zero,\n      ),\n    ];\n  }\n\n  static Border glassBorder(BuildContext context, {Color? accent}) {\n    final bool dark = isDark(context);\n    return Border(\n      top: BorderSide(\n        color: Colors.white.withAlpha(dark ? 31 : 174),\n        width: UIConstants.borderWidth,\n      ),\n      right: BorderSide(\n        color: Colors.white.withAlpha(dark ? 20 : 92),\n        width: UIConstants.borderWidth,\n      ),\n      bottom: BorderSide(\n        color: dark ? Colors.black.withAlpha(96) : Colors.white.withAlpha(66),\n        width: UIConstants.borderWidth,\n      ),\n      left: accent == null\n          ? BorderSide(\n              color: Colors.white.withAlpha(dark ? 20 : 92),\n              width: UIConstants.borderWidth,\n            )\n          : BorderSide(\n              color: accent.withAlpha(dark ? 82 : 72),\n              width: UIConstants.borderWidth,\n            ),\n    );\n  }\n\n  static List<Shadow> inkGlow"""
replace_once(old_glow, new_glow, 'glow helpers')

replace_once(
    """      surfaceColors = dark\n          ? const <Color>[Color(0xE0121826), Color(0xC4080C18)]\n          : const <Color>[Color(0xECFFFFFF), Color(0xBFFFFFFF)];""",
    """      surfaceColors = dark\n          ? const <Color>[Color(0xDC121826), Color(0xBC080C18)]\n          : const <Color>[Color(0xE0FFFFFF), Color(0xAEFFFFFF)];""",
    'plain glass gradient',
)
replace_once(
    """              Color.lerp(darkGlassTop, tintColor, .15)!.withAlpha(228),\n              Color.lerp(darkGlassBottom, tintColor, .075)!.withAlpha(202),""",
    """              Color.lerp(darkGlassTop, tintColor, .15)!.withAlpha(220),\n              Color.lerp(darkGlassBottom, tintColor, .075)!.withAlpha(188),""",
    'dark tinted glass gradient',
)
replace_once(
    """              Color.lerp(Colors.white, tintColor, .08)!.withAlpha(236),\n              Color.lerp(Colors.white, tintColor, .045)!.withAlpha(186),""",
    """              Color.lerp(Colors.white, tintColor, .08)!.withAlpha(224),\n              Color.lerp(Colors.white, tintColor, .045)!.withAlpha(174),""",
    'light tinted glass gradient',
)

old_card_edges = """    final BorderSide side = borderColor != null\n        ? BorderSide(\n            color: borderColor!,\n            width: UIConstants.borderWidth,\n          )\n        : AppStyles.hairline(\n            context,\n            accent: accentColor,\n            active: accentColor != null,\n          );\n    final List<BoxShadow> shadows = shadowColor != null\n        ? AppStyles.glow(\n            context,\n            shadowColor!,\n            strong: accentColor != null,\n          )\n        : AppStyles.surfaceDepth(context);"""
new_card_edges = """    final Border border = borderColor != null\n        ? Border.all(color: borderColor!, width: UIConstants.borderWidth)\n        : AppStyles.glassBorder(context, accent: accentColor);\n    final List<BoxShadow> shadows = shadowColor != null\n        ? accentColor != null\n            ? AppStyles.railDepth(context, shadowColor!)\n            : AppStyles.glow(\n                context,\n                shadowColor!,\n                strong: tintColor != null,\n              )\n        : AppStyles.surfaceDepth(context);"""
replace_once(old_card_edges, new_card_edges, 'glass card edge physics')
replace_once('        border: Border.fromBorderSide(side),', '        border: border,', 'glass card border')

old_header_start = """    return DecoratedBox(\n      decoration: BoxDecoration(\n        color: dark ? const Color(0xE6000000) : const Color(0xF7FFFFFF),\n        border: Border(bottom: AppStyles.hairline(context)),\n        boxShadow: AppStyles.surfaceDepth(context),\n      ),\n      child: SafeArea(\n        bottom: false,\n        child: Padding(\n          padding: const EdgeInsets.fromLTRB(20, 16, 20, 16),\n          child: Row(\n            children: <Widget>["""
new_header_start = """    return DecoratedBox(\n      decoration: BoxDecoration(\n        boxShadow: <BoxShadow>[\n          BoxShadow(\n            color: Colors.black.withAlpha(dark ? 82 : 9),\n            blurRadius: dark ? 30 : 24,\n            spreadRadius: -12,\n            offset: const Offset(0, 8),\n          ),\n        ],\n      ),\n      child: ClipRect(\n        child: BackdropFilter(\n          filter: ui.ImageFilter.blur(sigmaX: 18, sigmaY: 18),\n          child: DecoratedBox(\n            decoration: BoxDecoration(\n              gradient: LinearGradient(\n                begin: Alignment.topLeft,\n                end: Alignment.bottomRight,\n                colors: dark\n                    ? const <Color>[Color(0xD8101726), Color(0xCC060A12)]\n                    : const <Color>[Color(0xE8FFFFFF), Color(0xD5FFFFFF)],\n              ),\n              border: Border(bottom: AppStyles.hairline(context)),\n            ),\n            child: SafeArea(\n              bottom: false,\n              child: Padding(\n                padding: const EdgeInsets.fromLTRB(20, 16, 20, 16),\n                child: Row(\n                  children: <Widget>["""
replace_once(old_header_start, new_header_start, 'frosted screen header start')

old_header_end = """              if (actions.isNotEmpty) ...<Widget>[\n                const SizedBox(width: 8),\n                ...actions,\n              ],\n            ],\n          ),\n        ),\n      ),\n    );\n  }\n}\n\nclass _CircleAction"""
new_header_end = """              if (actions.isNotEmpty) ...<Widget>[\n                const SizedBox(width: 8),\n                ...actions,\n              ],\n                  ],\n                ),\n              ),\n            ),\n          ),\n        ),\n      ),\n    );\n  }\n}\n\nclass _CircleAction"""
replace_once(old_header_end, new_header_end, 'frosted screen header end')

replace_once(
    '              boxShadow: AppStyles.glow(context, color),',
    '              boxShadow: AppStyles.jewelDepth(context, color),',
    'circle action jewel shadow',
)
replace_once(
    """        border: Border.fromBorderSide(\n          AppStyles.hairline(context, accent: color, active: true),\n        ),\n        boxShadow: AppStyles.glow(context, color, strong: true),""",
    """        border: AppStyles.glassBorder(context),\n        boxShadow: AppStyles.glow(context, color, strong: true),""",
    'hero glass border',
)

old_avatar = """                  decoration: BoxDecoration(\n                    color: color.withAlpha(29),\n                    borderRadius:\n                        BorderRadius.circular(UIConstants.compactRadius),\n                    border: Border.fromBorderSide(\n                      AppStyles.hairline(context, accent: color, active: true),\n                    ),\n                    boxShadow: AppStyles.glow(context, color),\n                  ),"""
new_avatar = """                  decoration: BoxDecoration(\n                    gradient: LinearGradient(\n                      begin: Alignment.topLeft,\n                      end: Alignment.bottomRight,\n                      colors: <Color>[\n                        color.withAlpha(34),\n                        color.withAlpha(16),\n                      ],\n                    ),\n                    borderRadius:\n                        BorderRadius.circular(UIConstants.compactRadius),\n                    border: Border.fromBorderSide(\n                      AppStyles.hairline(context, accent: color, active: true),\n                    ),\n                    boxShadow: AppStyles.jewelDepth(context, color),\n                  ),"""
replace_once(old_avatar, new_avatar, 'list avatar jewel')

old_nav_start = """    return DecoratedBox(\n      decoration: BoxDecoration(\n        color: dark ? const Color(0xE60B1220) : const Color(0xF2FFFFFF),\n        border: Border(top: AppStyles.hairline(context)),\n        boxShadow: AppStyles.surfaceDepth(context),\n      ),\n      child: SafeArea(\n        top: false,\n        child: SizedBox("""
new_nav_start = """    return DecoratedBox(\n      decoration: BoxDecoration(\n        boxShadow: <BoxShadow>[\n          BoxShadow(\n            color: Colors.black.withAlpha(dark ? 104 : 14),\n            blurRadius: dark ? 40 : 32,\n            spreadRadius: -12,\n            offset: const Offset(0, -10),\n          ),\n        ],\n      ),\n      child: ClipRect(\n        child: BackdropFilter(\n          filter: ui.ImageFilter.blur(sigmaX: 20, sigmaY: 20),\n          child: DecoratedBox(\n            decoration: BoxDecoration(\n              gradient: LinearGradient(\n                begin: Alignment.topCenter,\n                end: Alignment.bottomCenter,\n                colors: dark\n                    ? const <Color>[Color(0xD9121928), Color(0xC9080D18)]\n                    : const <Color>[Color(0xE9FFFFFF), Color(0xD8FFFFFF)],\n              ),\n              border: Border(top: AppStyles.hairline(context)),\n              boxShadow: <BoxShadow>[\n                BoxShadow(\n                  color: Colors.white.withAlpha(dark ? 16 : 90),\n                  blurRadius: 1,\n                  offset: const Offset(0, -1),\n                ),\n              ],\n            ),\n            child: SafeArea(\n              top: false,\n              child: SizedBox("""
replace_once(old_nav_start, new_nav_start, 'frosted navigation start')

old_nav_surface = """                        decoration: BoxDecoration(\n                          color: active\n                              ? color.withAlpha(dark ? 42 : 22)\n                              : Colors.transparent,\n                          borderRadius:\n                              BorderRadius.circular(UIConstants.actionRadius),\n                          border: Border.fromBorderSide(\n                            active\n                                ? AppStyles.hairline(\n                                    context,\n                                    accent: color,\n                                    active: true,\n                                  )\n                                : const BorderSide(color: Colors.transparent),\n                          ),\n                          boxShadow: active\n                              ? AppStyles.glow(context, color)\n                              : const <BoxShadow>[],\n                        ),"""
replace_once(old_nav_surface, """                        decoration: const BoxDecoration(\n                          color: Colors.transparent,\n                        ),""", 'navigation clean item surface')

old_nav_icon = """                              child: Icon(\n                                spec.icon,\n                                size: 24,\n                                color: active ? color : systemGray,\n                                shadows:\n                                    active ? AppStyles.inkGlow(color) : null,\n                              ),"""
new_nav_icon = """                              child: Icon(\n                                spec.icon,\n                                size: active ? 25 : 23,\n                                color: active\n                                    ? color\n                                    : color.withAlpha(dark ? 176 : 188),\n                                shadows: active\n                                    ? AppStyles.inkGlow(color, strong: true)\n                                    : <Shadow>[\n                                        Shadow(\n                                          color: color.withAlpha(dark ? 48 : 34),\n                                          blurRadius: 7,\n                                        ),\n                                      ],\n                              ),"""
replace_once(old_nav_icon, new_nav_icon, 'semantic navigation icon')
replace_once(
    '                                color: active ? color : systemGray,',
    """                                color: active\n                                    ? color\n                                    : color.withAlpha(dark ? 170 : 182),""",
    'semantic navigation label',
)
replace_once(
    '                                color: color.withAlpha(active ? 145 : 0),',
    '                                color: appleBlue.withAlpha(active ? 96 : 0),',
    'navigation indicator color',
)
replace_once(
    """                                          color: color.withAlpha(76),\n                                          blurRadius: 12,""",
    """                                          color: appleBlue.withAlpha(72),\n                                          blurRadius: 18,""",
    'navigation indicator glow',
)
old_nav_end = """              ),\n            ),\n          ),\n        ),\n      ),\n    );\n  }\n}\n\nclass _Pressable"""
new_nav_end = """              ),\n            ),\n          ),\n        ),\n      ),\n    ),\n  ),\n),\n);\n  }\n}\n\nclass _Pressable"""
replace_once(old_nav_end, new_nav_end, 'frosted navigation end')

old_ledger_icon = """  @override\n  Widget build(BuildContext context) => Container(\n        width: size,\n        height: size,\n        decoration: BoxDecoration(\n          color: color.withAlpha(28),\n          borderRadius: BorderRadius.circular(size * .32),\n          border: Border.fromBorderSide(\n            AppStyles.hairline(context, accent: color, active: true),\n          ),\n          boxShadow: AppStyles.glow(context, color),\n        ),\n        child: Icon(\n          icon,\n          size: size * .45,\n          color: color,\n          shadows: AppStyles.inkGlow(color, strong: true),\n        ),\n      );"""
new_ledger_icon = """  @override\n  Widget build(BuildContext context) {\n    final bool dark = Theme.of(context).brightness == Brightness.dark;\n    final double radius = size * .32;\n    return Container(\n      width: size,\n      height: size,\n      clipBehavior: Clip.antiAlias,\n      decoration: BoxDecoration(\n        gradient: LinearGradient(\n          begin: Alignment.topLeft,\n          end: Alignment.bottomRight,\n          colors: <Color>[\n            color.withAlpha(dark ? 48 : 34),\n            color.withAlpha(dark ? 26 : 16),\n          ],\n        ),\n        borderRadius: BorderRadius.circular(radius),\n        border: Border.all(\n          color: color.withAlpha(dark ? 88 : 72),\n          width: UIConstants.borderWidth,\n        ),\n        boxShadow: AppStyles.jewelDepth(context, color),\n      ),\n      child: Stack(\n        fit: StackFit.expand,\n        children: <Widget>[\n          Positioned(\n            left: radius * .55,\n            right: radius * .55,\n            top: 0,\n            height: 1,\n            child: DecoratedBox(\n              decoration: BoxDecoration(\n                gradient: LinearGradient(\n                  colors: <Color>[\n                    Colors.transparent,\n                    Colors.white.withAlpha(dark ? 68 : 178),\n                    Colors.transparent,\n                  ],\n                ),\n              ),\n            ),\n          ),\n          Center(\n            child: Icon(\n              icon,\n              size: size * .43,\n              color: color,\n              shadows: AppStyles.inkGlow(color, strong: true),\n            ),\n          ),\n        ],\n      ),\n    );\n  }"""
replace_once(old_ledger_icon, new_ledger_icon, 'ledger icon jewel')
replace_once(
    """        tintColor: color,\n        borderColor: color.withAlpha(77),\n        shadowColor: color,""",
    """        tintColor: color,\n        shadowColor: color,""",
    'dashboard white glass edge',
)

old_transaction_shadow = """            boxShadow: dark\n                ? const <BoxShadow>[]\n                : <BoxShadow>[\n                    BoxShadow(\n                      color: color.withAlpha(50),\n                      blurRadius: 28,\n                      spreadRadius: 1,\n                      offset: const Offset(0, 12),\n                    ),\n                  ],"""
replace_once(
    old_transaction_shadow,
    '            boxShadow: AppStyles.glow(context, color, strong: true),',
    'transaction button depth',
)

MAIN.write_text(text, encoding='utf-8')

pub = PUBSPEC.read_text(encoding='utf-8')
if pub.count('version: 1.0.3+4') != 1:
    raise SystemExit('pubspec version precondition failed')
pub = pub.replace('version: 1.0.3+4', 'version: 1.0.4+5', 1)
PUBSPEC.write_text(pub, encoding='utf-8')

print('Native glass translation applied successfully.')
