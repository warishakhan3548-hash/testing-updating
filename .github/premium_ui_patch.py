from pathlib import Path

path = Path('lib/main.dart')
text = path.read_text(encoding='utf-8')


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 match, got {count}')
    text = text.replace(old, new, 1)


def replace_block(start_marker: str, end_marker: str, replacement: str, label: str) -> None:
    global text
    start = text.find(start_marker)
    if start < 0:
        raise SystemExit(f'{label}: start marker not found')
    end = text.find(end_marker, start)
    if end < 0:
        raise SystemExit(f'{label}: end marker not found')
    text = text[:start] + replacement.rstrip() + '\n\n' + text[end:]


# ---------------------------------------------------------------------------
# Centralized premium UI design tokens. Colors and business semantics stay intact.
# ---------------------------------------------------------------------------
anchor = "const Color darkGlassBottom = Color(0xFF080C18);\nconst Uuid _ids = Uuid();"
if 'abstract final class UIConstants' not in text:
    tokens = r'''const Color darkGlassBottom = Color(0xFF080C18);

abstract final class UIConstants {
  static const double minTapTarget = 48;
  static const double inputRadius = 20;
  static const double compactRadius = 18;
  static const double actionRadius = 22;
  static const double cardRadius = 26;
  static const double heroRadius = 28;
  static const double sheetRadius = 36;
  static const double accentStroke = 6;
  static const double borderWidth = 1;

  static const EdgeInsets cardPadding = EdgeInsets.all(18);
  static const EdgeInsets compactCardPadding = EdgeInsets.all(15);
  static const EdgeInsets inputPadding =
      EdgeInsets.symmetric(horizontal: 20, vertical: 18);
  static const EdgeInsets actionPadding =
      EdgeInsets.symmetric(horizontal: 22);

  static const Duration motion = Duration(milliseconds: 280);
}

abstract final class AppStyles {
  static bool isDark(BuildContext context) =>
      Theme.of(context).brightness == Brightness.dark;

  static BorderSide hairline(
    BuildContext context, {
    Color? accent,
    bool active = false,
  }) {
    final bool dark = isDark(context);
    final Color color = accent == null
        ? (dark ? Colors.white.withAlpha(31) : Colors.black.withAlpha(14))
        : accent.withAlpha(active ? (dark ? 112 : 92) : (dark ? 64 : 52));
    return BorderSide(color: color, width: UIConstants.borderWidth);
  }

  static List<BoxShadow> surfaceDepth(BuildContext context) {
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

  static List<BoxShadow> glow(
    BuildContext context,
    Color color, {
    bool strong = false,
  }) {
    final bool dark = isDark(context);
    return <BoxShadow>[
      BoxShadow(
        color: color.withAlpha(
          strong ? (dark ? 86 : 66) : (dark ? 58 : 44),
        ),
        blurRadius: strong ? 30 : 22,
        spreadRadius: strong ? 1 : 0,
        offset: Offset.zero,
      ),
      ...surfaceDepth(context),
    ];
  }

  static List<Shadow> inkGlow(Color color, {bool strong = false}) => <Shadow>[
        Shadow(
          color: color.withAlpha(strong ? 104 : 72),
          blurRadius: strong ? 12 : 8,
          offset: Offset.zero,
        ),
      ];
}

const Uuid _ids = Uuid();'''
    replace_once(anchor, tokens, 'insert UI constants')

# ---------------------------------------------------------------------------
# Theme-level geometry: one source of truth for all fields, sheets and dialogs.
# ---------------------------------------------------------------------------
replace_block(
    '    inputDecorationTheme: InputDecorationTheme(',
    '    snackBarTheme: SnackBarThemeData(',
    r'''    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: dark ? const Color(0x2EFFFFFF) : const Color(0xE8FFFFFF),
      contentPadding: UIConstants.inputPadding,
      hintStyle: const TextStyle(
        color: systemGray,
        fontSize: 16.5,
        fontWeight: FontWeight.w600,
      ),
      labelStyle: const TextStyle(fontSize: 15.5, fontWeight: FontWeight.w700),
      prefixIconColor: appleBlue,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(UIConstants.inputRadius),
        borderSide: BorderSide(color: outline, width: UIConstants.borderWidth),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(UIConstants.inputRadius),
        borderSide: BorderSide(
          color: dark ? Colors.white.withAlpha(34) : appleBlue.withAlpha(34),
          width: UIConstants.borderWidth,
        ),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(UIConstants.inputRadius),
        borderSide: const BorderSide(color: appleBlue, width: 1.4),
      ),
    ),''',
    'input decoration theme',
)
text = text.replace(
    'shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),',
    'shape: RoundedRectangleBorder(\n        borderRadius: BorderRadius.circular(UIConstants.compactRadius),\n      ),',
    1,
)
text = text.replace(
    'borderRadius: BorderRadius.vertical(top: Radius.circular(28)),',
    'borderRadius: BorderRadius.vertical(\n          top: Radius.circular(UIConstants.sheetRadius),\n        ),',
    1,
)
text = text.replace(
    'shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),',
    'shape: RoundedRectangleBorder(\n        borderRadius: BorderRadius.circular(UIConstants.cardRadius),\n      ),',
    1,
)

# Keep navigation centering mathematically aligned with the new tab width.
replace_once(
    'final double target = math.max(0, index * 74 - 120).toDouble();',
    'final double target = math.max(0, index * 82 - 120).toDouble();',
    'navigation scroll geometry',
)

# ---------------------------------------------------------------------------
# Premium bottom navigation: consistent active capsule, centered glow, 48+ target.
# ---------------------------------------------------------------------------
replace_block(
    'class _BottomLedgerNav extends StatelessWidget {',
    'class _Pressable extends StatefulWidget {',
    r'''class _BottomLedgerNav extends StatelessWidget {
  const _BottomLedgerNav({
    required this.sync,
    required this.selected,
    required this.controller,
    required this.onSelected,
  });

  final LedgerSyncService sync;
  final int selected;
  final ScrollController controller;
  final ValueChanged<int> onSelected;

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
        animation: sync,
        builder: (BuildContext context, Widget? child) =>
            _buildNavigation(context),
      );

  Widget _buildNavigation(BuildContext context) {
    final bool dark = Theme.of(context).brightness == Brightness.dark;
    final List<Color> colors = _moduleTabColors(sync.state);
    return DecoratedBox(
      decoration: BoxDecoration(
        color: dark ? const Color(0xE60B1220) : const Color(0xF2FFFFFF),
        border: Border(top: AppStyles.hairline(context)),
        boxShadow: AppStyles.surfaceDepth(context),
      ),
      child: SafeArea(
        top: false,
        child: SizedBox(
          height: 88,
          child: SingleChildScrollView(
            controller: controller,
            scrollDirection: Axis.horizontal,
            physics: const BouncingScrollPhysics(),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4),
              child: Row(
                children: List<Widget>.generate(_tabs.length, (int index) {
                  final _TabSpec spec = _tabs[index];
                  final bool active = index == selected;
                  final Color color = colors[index];
                  return _Pressable(
                    onTap: () => onSelected(index),
                    semanticLabel: '${spec.label} tab',
                    borderRadius: BorderRadius.circular(UIConstants.actionRadius),
                    child: AnimatedSlide(
                      offset: active ? const Offset(0, -.035) : Offset.zero,
                      duration: UIConstants.motion,
                      curve: const Cubic(0.32, 0.72, 0, 1),
                      child: AnimatedContainer(
                        duration: UIConstants.motion,
                        curve: const Cubic(0.32, 0.72, 0, 1),
                        width: 82,
                        height: 74,
                        margin: const EdgeInsets.symmetric(horizontal: 2),
                        decoration: BoxDecoration(
                          color: active
                              ? color.withAlpha(dark ? 42 : 22)
                              : Colors.transparent,
                          borderRadius:
                              BorderRadius.circular(UIConstants.actionRadius),
                          border: Border.fromBorderSide(
                            active
                                ? AppStyles.hairline(
                                    context,
                                    accent: color,
                                    active: true,
                                  )
                                : const BorderSide(color: Colors.transparent),
                          ),
                          boxShadow: active
                              ? AppStyles.glow(context, color)
                              : const <BoxShadow>[],
                        ),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: <Widget>[
                            AnimatedScale(
                              scale: active ? 1.13 : 1,
                              duration: UIConstants.motion,
                              curve: const Cubic(0.34, 1.18, 0.64, 1),
                              child: Icon(
                                spec.icon,
                                size: 27,
                                color: active ? color : systemGray,
                                shadows:
                                    active ? AppStyles.inkGlow(color) : null,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              spec.label,
                              style: TextStyle(
                                color: active ? color : systemGray,
                                fontSize: 12,
                                fontWeight:
                                    active ? FontWeight.w900 : FontWeight.w700,
                                shadows:
                                    active ? AppStyles.inkGlow(color) : null,
                              ),
                            ),
                            const SizedBox(height: 4),
                            AnimatedContainer(
                              duration: UIConstants.motion,
                              curve: const Cubic(0.32, 0.72, 0, 1),
                              width: active ? 38 : 0,
                              height: 4,
                              decoration: BoxDecoration(
                                color: color.withAlpha(active ? 145 : 0),
                                borderRadius: BorderRadius.circular(99),
                                boxShadow: active
                                    ? <BoxShadow>[
                                        BoxShadow(
                                          color: color.withAlpha(76),
                                          blurRadius: 12,
                                          offset: Offset.zero,
                                        ),
                                      ]
                                    : null,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  );
                }),
              ),
            ),
          ),
        ),
      ),
    );
  }
}''',
    'bottom navigation',
)

# ---------------------------------------------------------------------------
# Shared card primitive + true curved accent rail. This is the single source
# for Milk, Credit, Party Ledger, Diary and other accent list cards.
# ---------------------------------------------------------------------------
replace_block(
    'class _GlassCard extends StatelessWidget {',
    'class _ScreenHeader extends StatelessWidget {',
    r'''class _GlassCard extends StatelessWidget {
  const _GlassCard({
    required this.child,
    this.padding = UIConstants.cardPadding,
    this.accentColor,
    this.borderColor,
    this.shadowColor,
    this.tintColor,
    this.borderRadius = UIConstants.cardRadius,
  });

  final Widget child;
  final EdgeInsets padding;
  final Color? accentColor;
  final Color? borderColor;
  final Color? shadowColor;
  final Color? tintColor;
  final double borderRadius;

  @override
  Widget build(BuildContext context) {
    final bool dark = Theme.of(context).brightness == Brightness.dark;
    final List<Color> surfaceColors;
    if (tintColor == null) {
      surfaceColors = dark
          ? const <Color>[Color(0xE0121826), Color(0xC4080C18)]
          : const <Color>[Color(0xECFFFFFF), Color(0xBFFFFFFF)];
    } else {
      surfaceColors = dark
          ? <Color>[
              Color.lerp(darkGlassTop, tintColor, .15)!.withAlpha(228),
              Color.lerp(darkGlassBottom, tintColor, .075)!.withAlpha(202),
            ]
          : <Color>[
              Color.lerp(Colors.white, tintColor, .08)!.withAlpha(236),
              Color.lerp(Colors.white, tintColor, .045)!.withAlpha(186),
            ];
    }
    final BorderSide side = borderColor != null
        ? BorderSide(
            color: borderColor!,
            width: UIConstants.borderWidth,
          )
        : AppStyles.hairline(
            context,
            accent: accentColor,
            active: accentColor != null,
          );
    final List<BoxShadow> shadows = shadowColor != null
        ? AppStyles.glow(
            context,
            shadowColor!,
            strong: accentColor != null,
          )
        : AppStyles.surfaceDepth(context);
    return Container(
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: surfaceColors,
        ),
        borderRadius: BorderRadius.circular(borderRadius),
        border: Border.fromBorderSide(side),
        boxShadow: shadows,
      ),
      child: Stack(
        children: <Widget>[
          if (accentColor != null)
            Positioned.fill(
              child: IgnorePointer(
                child: CustomPaint(
                  painter: _CardAccentPainter(
                    color: accentColor!,
                    radius: borderRadius,
                    dark: dark,
                  ),
                ),
              ),
            ),
          Padding(
            padding: padding,
            child: child,
          ),
        ],
      ),
    );
  }
}

class _CardAccentPainter extends CustomPainter {
  const _CardAccentPainter({
    required this.color,
    required this.radius,
    required this.dark,
  });

  final Color color;
  final double radius;
  final bool dark;

  Path _rail(Size size) {
    final double r = math.min(radius, size.height / 2);
    final Path path = Path()
      ..moveTo(r * .72, 0)
      ..quadraticBezierTo(0, 0, 0, r)
      ..lineTo(0, size.height - r)
      ..quadraticBezierTo(0, size.height, r * .72, size.height);
    return path;
  }

  @override
  void paint(Canvas canvas, Size size) {
    if (size.isEmpty) return;
    final Path path = _rail(size);
    canvas.drawPath(
      path,
      Paint()
        ..color = color.withAlpha(dark ? 64 : 50)
        ..style = PaintingStyle.stroke
        ..strokeWidth = UIConstants.accentStroke + 8
        ..strokeCap = StrokeCap.round
        ..strokeJoin = StrokeJoin.round,
    );
    canvas.drawPath(
      path,
      Paint()
        ..color = color
        ..style = PaintingStyle.stroke
        ..strokeWidth = UIConstants.accentStroke
        ..strokeCap = StrokeCap.round
        ..strokeJoin = StrokeJoin.round,
    );
  }

  @override
  bool shouldRepaint(covariant _CardAccentPainter oldDelegate) =>
      oldDelegate.color != color ||
      oldDelegate.radius != radius ||
      oldDelegate.dark != dark;
}''',
    'glass card and accent rail',
)

# ---------------------------------------------------------------------------
# Headers and small actions share the same crisp lining and centered glow.
# ---------------------------------------------------------------------------
replace_block(
    'class _ScreenHeader extends StatelessWidget {',
    'class _CircleAction extends StatelessWidget {',
    r'''class _ScreenHeader extends StatelessWidget {
  const _ScreenHeader({
    required this.title,
    this.subtitle,
    this.subtitleTrailing,
    this.leading,
    this.actions = const <Widget>[],
    this.color,
  });

  final String title;
  final String? subtitle;
  final Widget? subtitleTrailing;
  final Widget? leading;
  final List<Widget> actions;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final bool dark = Theme.of(context).brightness == Brightness.dark;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: dark ? const Color(0xE6000000) : const Color(0xF7FFFFFF),
        border: Border(bottom: AppStyles.hairline(context)),
        boxShadow: AppStyles.surfaceDepth(context),
      ),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 14, 20, 16),
          child: Row(
            children: <Widget>[
              if (leading != null) ...<Widget>[
                leading!,
                const SizedBox(width: 11),
              ],
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: color,
                        fontSize: leading == null ? 30 : 26,
                        fontWeight: FontWeight.w900,
                        letterSpacing: -.5,
                        shadows:
                            color == null ? null : AppStyles.inkGlow(color!),
                      ),
                    ),
                    if (subtitle != null) ...<Widget>[
                      const SizedBox(height: 2),
                      Row(
                        children: <Widget>[
                          Flexible(
                            child: Text(
                              subtitle!,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                color: appleBlue,
                                fontSize: 10,
                                fontWeight: FontWeight.w900,
                                letterSpacing: 1.1,
                              ),
                            ),
                          ),
                          if (subtitleTrailing != null) ...<Widget>[
                            const SizedBox(width: 9),
                            subtitleTrailing!,
                          ],
                        ],
                      ),
                    ],
                  ],
                ),
              ),
              if (actions.isNotEmpty) ...<Widget>[
                const SizedBox(width: 8),
                ...actions,
              ],
            ],
          ),
        ),
      ),
    );
  }
}''',
    'screen header',
)

replace_block(
    'class _CircleAction extends StatelessWidget {',
    'class _SearchBox extends StatefulWidget {',
    r'''class _CircleAction extends StatelessWidget {
  const _CircleAction({
    required this.icon,
    required this.onTap,
    this.color = appleBlue,
    this.semanticLabel,
  });

  final IconData icon;
  final VoidCallback onTap;
  final Color color;
  final String? semanticLabel;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(left: 6),
        child: _Pressable(
          onTap: onTap,
          semanticLabel: semanticLabel,
          borderRadius: BorderRadius.circular(UIConstants.compactRadius),
          child: Container(
            width: 50,
            height: 50,
            decoration: BoxDecoration(
              color: color.withAlpha(23),
              borderRadius: BorderRadius.circular(UIConstants.compactRadius),
              border: Border.fromBorderSide(
                AppStyles.hairline(context, accent: color, active: true),
              ),
              boxShadow: AppStyles.glow(context, color),
            ),
            child: Icon(
              icon,
              size: 22,
              color: color,
              shadows: AppStyles.inkGlow(color),
            ),
          ),
        ),
      );
}

class _BackCircle extends StatelessWidget {
  const _BackCircle();

  @override
  Widget build(BuildContext context) => _Pressable(
        onTap: () => Navigator.of(context).maybePop(),
        borderRadius: BorderRadius.circular(25),
        child: Container(
          width: 50,
          height: 50,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: Theme.of(context).brightness == Brightness.dark
                ? Colors.white.withAlpha(13)
                : Colors.black.withAlpha(10),
            border: Border.fromBorderSide(AppStyles.hairline(context)),
            boxShadow: AppStyles.surfaceDepth(context),
          ),
          child: const Icon(Icons.chevron_left_rounded),
        ),
      );
}''',
    'circle and back actions',
)

# ---------------------------------------------------------------------------
# Search fields: taller, consistent radius, subtle tinted surface and clear focus.
# ---------------------------------------------------------------------------
replace_block(
    'class _SearchBoxState extends State<_SearchBox> {',
    'class _DateField extends StatelessWidget {',
    r'''class _SearchBoxState extends State<_SearchBox> {
  Timer? _debounce;

  void _onChanged(String value) {
    _debounce?.cancel();
    _debounce = Timer(
      const Duration(milliseconds: 140),
      () => widget.onChanged(value),
    );
  }

  @override
  void dispose() {
    _debounce?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bool dark = Theme.of(context).brightness == Brightness.dark;
    final OutlineInputBorder idleBorder = OutlineInputBorder(
      borderRadius: BorderRadius.circular(UIConstants.inputRadius),
      borderSide: AppStyles.hairline(
        context,
        accent: widget.color,
      ),
    );
    return TextField(
      onChanged: _onChanged,
      cursorColor: widget.color,
      textInputAction: TextInputAction.search,
      style: TextStyle(
        color: widget.color,
        fontSize: 16,
        fontWeight: FontWeight.w800,
        shadows: AppStyles.inkGlow(widget.color),
      ),
      decoration: InputDecoration(
        hintText: widget.hint,
        filled: true,
        fillColor: widget.color.withAlpha(dark ? 12 : 8),
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 19),
        hintStyle: TextStyle(
          color: widget.color.withAlpha(160),
          fontSize: 16,
          fontWeight: FontWeight.w800,
        ),
        prefixIcon: Icon(
          Icons.search_rounded,
          color: widget.color,
          shadows: AppStyles.inkGlow(widget.color),
        ),
        prefixIconConstraints: const BoxConstraints(minWidth: 54),
        enabledBorder: idleBorder,
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(UIConstants.inputRadius),
          borderSide: BorderSide(color: widget.color, width: 1.4),
        ),
      ),
    );
  }
}''',
    'search field',
)

# ---------------------------------------------------------------------------
# Empty state, primary buttons, summary hero and list cards.
# ---------------------------------------------------------------------------
replace_block(
    'class _EmptyState extends StatelessWidget {',
    'class _PrimaryButton extends StatelessWidget {',
    r'''class _EmptyState extends StatelessWidget {
  const _EmptyState(
    this.icon,
    this.message, {
    this.color = systemGray,
    this.prominent = false,
  });

  final IconData icon;
  final String message;
  final Color color;
  final bool prominent;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 58),
        child: Center(
          child: Column(
            children: <Widget>[
              Container(
                width: prominent ? 92 : 72,
                height: prominent ? 92 : 72,
                decoration: BoxDecoration(
                  color: color.withAlpha(prominent ? 24 : 14),
                  shape: BoxShape.circle,
                  border: Border.fromBorderSide(
                    AppStyles.hairline(
                      context,
                      accent: color,
                      active: prominent,
                    ),
                  ),
                  boxShadow: AppStyles.glow(
                    context,
                    color,
                    strong: prominent,
                  ),
                ),
                child: Icon(
                  icon,
                  size: prominent ? 42 : 32,
                  color: color.withAlpha(prominent ? 235 : 150),
                  shadows: AppStyles.inkGlow(color),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                message,
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: prominent ? color : systemGray,
                  fontSize: prominent ? 17 : 14,
                  fontWeight: prominent ? FontWeight.w900 : FontWeight.w700,
                  shadows:
                      prominent ? AppStyles.inkGlow(color) : const <Shadow>[],
                ),
              ),
            ],
          ),
        ),
      );
}''',
    'empty state',
)

replace_block(
    'class _PrimaryButton extends StatelessWidget {',
    'class _AmountHero extends StatelessWidget {',
    r'''class _PrimaryButton extends StatelessWidget {
  const _PrimaryButton({
    required this.label,
    required this.onTap,
    this.icon = Icons.add_rounded,
    this.color = appleBlue,
    this.foregroundColor = Colors.white,
    this.compact = false,
    this.tonal = false,
  });

  final String label;
  final VoidCallback onTap;
  final IconData icon;
  final Color color;
  final Color foregroundColor;
  final bool compact;
  final bool tonal;

  @override
  Widget build(BuildContext context) => _Pressable(
        onTap: onTap,
        borderRadius: BorderRadius.circular(UIConstants.actionRadius),
        child: Container(
          constraints: const BoxConstraints(minHeight: UIConstants.minTapTarget),
          height: compact ? 52 : 58,
          padding: UIConstants.actionPadding,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: tonal
                  ? <Color>[color.withAlpha(40), color.withAlpha(22)]
                  : <Color>[color, _toneCompanion(color)],
            ),
            borderRadius: BorderRadius.circular(UIConstants.actionRadius),
            border: Border.fromBorderSide(
              AppStyles.hairline(context, accent: color, active: true),
            ),
            boxShadow: AppStyles.glow(
              context,
              color,
              strong: !tonal,
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              Icon(
                icon,
                color: foregroundColor,
                size: compact ? 20 : 22,
                shadows: AppStyles.inkGlow(foregroundColor),
              ),
              const SizedBox(width: 8),
              Text(
                label,
                style: TextStyle(
                  color: foregroundColor,
                  fontSize: compact ? 15.5 : 17,
                  fontWeight: FontWeight.w900,
                  shadows: AppStyles.inkGlow(foregroundColor),
                ),
              ),
            ],
          ),
        ),
      );
}''',
    'primary buttons',
)

replace_block(
    'class _AmountHero extends StatelessWidget {',
    'class _HeroValue extends StatelessWidget {',
    r'''class _AmountHero extends StatelessWidget {
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

  @override
  Widget build(BuildContext context) {
    final bool dark = Theme.of(context).brightness == Brightness.dark;
    final Color textColor = dark
        ? Color.lerp(Colors.white, color, .72)!
        : Color.lerp(const Color(0xFF06111F), color, .60)!;
    final List<Color> background = dark
        ? <Color>[
            Color.lerp(darkGlassTop, color, .21)!.withAlpha(232),
            Color.lerp(darkGlassBottom, _toneCompanion(color), .16)!
                .withAlpha(218),
            Color.lerp(Colors.black, color, .18)!.withAlpha(204),
          ]
        : <Color>[
            Color.lerp(Colors.white, color, .11)!.withAlpha(240),
            Color.lerp(Colors.white, _toneCompanion(color), .08)!
                .withAlpha(218),
            Color.lerp(Colors.white, color, .13)!.withAlpha(194),
          ];
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: background,
        ),
        borderRadius: BorderRadius.circular(UIConstants.heroRadius),
        border: Border.fromBorderSide(
          AppStyles.hairline(context, accent: color, active: true),
        ),
        boxShadow: AppStyles.glow(context, color, strong: true),
      ),
      child: Row(
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
    );
  }
}''',
    'amount hero',
)

replace_block(
    'class _ListCard extends StatelessWidget {',
    'class _SectionTitle extends StatelessWidget {',
    r'''class _ListCard extends StatelessWidget {
  const _ListCard({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.color,
    required this.onTap,
    this.trailing,
    this.onDelete,
    this.avatarText,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;
  final String? trailing;
  final VoidCallback? onDelete;
  final String? avatarText;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 14),
        child: _Pressable(
          onTap: onTap,
          borderRadius: BorderRadius.circular(UIConstants.cardRadius),
          child: _GlassCard(
            borderRadius: UIConstants.cardRadius,
            padding: UIConstants.compactCardPadding,
            accentColor: color,
            shadowColor: color,
            child: Row(
              children: <Widget>[
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: color.withAlpha(29),
                    borderRadius:
                        BorderRadius.circular(UIConstants.compactRadius),
                    border: Border.fromBorderSide(
                      AppStyles.hairline(context, accent: color, active: true),
                    ),
                    boxShadow: AppStyles.glow(context, color),
                  ),
                  child: avatarText == null
                      ? Icon(
                          icon,
                          color: color,
                          size: 22,
                          shadows: AppStyles.inkGlow(color),
                        )
                      : Center(
                          child: Text(
                            avatarText!,
                            style: TextStyle(
                              color: color,
                              fontSize: 18,
                              fontWeight: FontWeight.w900,
                              shadows: AppStyles.inkGlow(color),
                            ),
                          ),
                        ),
                ),
                const SizedBox(width: 15),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(
                        title,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          color: color,
                          fontSize: 16.5,
                          fontWeight: FontWeight.w900,
                          shadows: AppStyles.inkGlow(color),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        subtitle,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          color: color.withAlpha(190),
                          fontSize: 13,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ],
                  ),
                ),
                if (trailing != null) ...<Widget>[
                  const SizedBox(width: 8),
                  Text(
                    trailing!,
                    style: TextStyle(
                      color: color,
                      fontSize: 15.5,
                      fontWeight: FontWeight.w900,
                      shadows: AppStyles.inkGlow(color),
                    ),
                  ),
                ],
                if (onDelete != null)
                  Padding(
                    padding: const EdgeInsets.only(left: 9),
                    child: _Pressable(
                      onTap: onDelete,
                      semanticLabel: 'Delete $title',
                      borderRadius:
                          BorderRadius.circular(UIConstants.compactRadius),
                      child: Container(
                        width: 44,
                        height: 44,
                        decoration: BoxDecoration(
                          color: appleRed.withAlpha(24),
                          borderRadius:
                              BorderRadius.circular(UIConstants.compactRadius),
                          border: Border.fromBorderSide(
                            AppStyles.hairline(
                              context,
                              accent: appleRed,
                              active: true,
                            ),
                          ),
                          boxShadow: AppStyles.glow(context, appleRed),
                        ),
                        child: const Icon(
                          Icons.delete_rounded,
                          color: appleRed,
                          size: 19,
                        ),
                      ),
                    ),
                  )
                else
                  Icon(
                    Icons.chevron_right_rounded,
                    color: color.withAlpha(150),
                    shadows: AppStyles.inkGlow(color),
                  ),
              ],
            ),
          ),
        ),
      );
}''',
    'list cards',
)

# ---------------------------------------------------------------------------
# Month/year controls and modal sheet geometry.
# ---------------------------------------------------------------------------
replace_block(
    'class _MonthYearPicker extends StatelessWidget {',
    'class _SheetFrame extends StatelessWidget {',
    r'''class _MonthYearPicker extends StatelessWidget {
  const _MonthYearPicker({
    required this.month,
    required this.year,
    required this.onChanged,
  });

  final int month;
  final int year;
  final void Function(int month, int year) onChanged;

  @override
  Widget build(BuildContext context) {
    final int currentYear = DateTime.now().year;
    return Row(
      children: <Widget>[
        Expanded(
          child: DropdownButtonFormField<int>(
            key: ValueKey<String>('month-$month'),
            initialValue: month,
            style: const TextStyle(
              color: appleBlue,
              fontWeight: FontWeight.w800,
            ),
            iconEnabledColor: appleBlue,
            decoration: _pickerDecoration(),
            items: List<DropdownMenuItem<int>>.generate(
              12,
              (int index) => DropdownMenuItem<int>(
                value: index + 1,
                child: Text(
                  DateFormat.MMMM().format(DateTime(2024, index + 1)),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ),
            onChanged: (int? value) {
              if (value != null) {
                HapticFeedback.selectionClick();
                onChanged(value, year);
              }
            },
          ),
        ),
        const SizedBox(width: 12),
        SizedBox(
          width: 118,
          child: DropdownButtonFormField<int>(
            key: ValueKey<String>('year-$year'),
            initialValue: year,
            style: const TextStyle(
              color: appleBlue,
              fontWeight: FontWeight.w800,
            ),
            iconEnabledColor: appleBlue,
            decoration: _pickerDecoration(),
            items: List<DropdownMenuItem<int>>.generate(
              12,
              (int index) {
                final int item = currentYear + 2 - index;
                return DropdownMenuItem<int>(value: item, child: Text('$item'));
              },
            ),
            onChanged: (int? value) {
              if (value != null) {
                HapticFeedback.selectionClick();
                onChanged(month, value);
              }
            },
          ),
        ),
      ],
    );
  }
}

InputDecoration _pickerDecoration() => InputDecoration(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 17),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(UIConstants.inputRadius),
        borderSide: BorderSide(
          color: appleBlue.withAlpha(55),
          width: UIConstants.borderWidth,
        ),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(UIConstants.inputRadius),
        borderSide: const BorderSide(color: appleBlue, width: 1.4),
      ),
    );''',
    'month year picker',
)

replace_block(
    'class _SheetFrame extends StatelessWidget {',
    'Future<T?> _openSheet<T>(BuildContext context, Widget child) =>',
    r'''class _SheetFrame extends StatelessWidget {
  const _SheetFrame({
    required this.title,
    required this.children,
    this.centerTitle = false,
  });

  final String title;
  final List<Widget> children;
  final bool centerTitle;

  @override
  Widget build(BuildContext context) {
    final bool dark = Theme.of(context).brightness == Brightness.dark;
    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: dark
              ? const <Color>[Color(0xF51C2230), Color(0xF00A0F1C)]
              : const <Color>[Color(0xFAFFFFFF), Color(0xF4FFFFFF)],
        ),
        borderRadius: const BorderRadius.vertical(
          top: Radius.circular(UIConstants.sheetRadius),
        ),
        border: Border(
          top: AppStyles.hairline(context),
        ),
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: Colors.black.withAlpha(dark ? 154 : 34),
            blurRadius: dark ? 70 : 58,
            spreadRadius: -5,
            offset: Offset.zero,
          ),
        ],
      ),
      child: SafeArea(
        top: false,
        child: SingleChildScrollView(
          padding: EdgeInsets.fromLTRB(
            24,
            12,
            24,
            MediaQuery.viewInsetsOf(context).bottom + 24,
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              Align(
                child: Container(
                  width: 54,
                  height: 6,
                  decoration: BoxDecoration(
                    color: dark
                        ? Colors.white.withAlpha(55)
                        : Colors.black.withAlpha(34),
                    borderRadius: BorderRadius.circular(99),
                  ),
                ),
              ),
              const SizedBox(height: 26),
              Text(
                title,
                textAlign: centerTitle ? TextAlign.center : TextAlign.start,
                style: const TextStyle(
                  fontSize: 30,
                  fontWeight: FontWeight.w900,
                  letterSpacing: -.5,
                ),
              ),
              const SizedBox(height: 24),
              ...children,
            ],
          ),
        ),
      ),
    );
  }
}''',
    'sheet frame',
)

# ---------------------------------------------------------------------------
# Dashboard cards/icons: same geometry and stamped icon treatment everywhere.
# ---------------------------------------------------------------------------
replace_block(
    'class _MetricCard extends StatelessWidget {',
    'class PartyLedgerScreen extends StatefulWidget {',
    r'''class _MetricCard extends StatelessWidget {
  const _MetricCard({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });

  final IconData icon;
  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) => _GlassCard(
        padding: UIConstants.compactCardPadding,
        borderRadius: UIConstants.cardRadius,
        tintColor: color,
        borderColor: color.withAlpha(77),
        shadowColor: color,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            _LedgerIcon(icon: icon, color: color, size: 46),
            const Spacer(),
            Text(
              label.toUpperCase(),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                color: systemGray,
                fontSize: 10,
                fontWeight: FontWeight.w900,
                letterSpacing: .65,
              ),
            ),
            const SizedBox(height: 4),
            FittedBox(
              fit: BoxFit.scaleDown,
              alignment: Alignment.centerLeft,
              child: Text(
                value,
                style: TextStyle(
                  color: color,
                  fontSize: 24,
                  fontWeight: FontWeight.w900,
                  letterSpacing: -.7,
                  shadows: AppStyles.inkGlow(color, strong: true),
                ),
              ),
            ),
          ],
        ),
      );
}

class _LedgerIcon extends StatelessWidget {
  const _LedgerIcon({
    required this.icon,
    required this.color,
    this.size = 48,
  });

  final IconData icon;
  final Color color;
  final double size;

  @override
  Widget build(BuildContext context) => Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          color: color.withAlpha(28),
          borderRadius: BorderRadius.circular(size * .32),
          border: Border.fromBorderSide(
            AppStyles.hairline(context, accent: color, active: true),
          ),
          boxShadow: AppStyles.glow(context, color),
        ),
        child: Icon(
          icon,
          size: size * .45,
          color: color,
          shadows: AppStyles.inkGlow(color, strong: true),
        ),
      );
}''',
    'metric cards and icons',
)

# Dashboard proportions and receive glyph, without changing any semantic colors.
replace_once('childAspectRatio: 1.05,', 'childAspectRatio: 1.0,', 'dashboard card ratio')
replace_once(
    "_MetricCard(\n                      icon: Icons.savings_rounded,\n                      label: 'To Receive (+)',",
    "_MetricCard(\n                      icon: Icons.volunteer_activism_rounded,\n                      label: 'To Receive (+)',",
    'receive metric icon',
)

# ---------------------------------------------------------------------------
# Detail action/table primitives also consume the same premium tokens.
# ---------------------------------------------------------------------------
replace_block(
    'class _MiniAction extends StatelessWidget {',
    'class SalaryScreen extends StatefulWidget {',
    r'''class _MiniAction extends StatelessWidget {
  const _MiniAction({
    required this.label,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  final String label;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => _Pressable(
        onTap: onTap,
        borderRadius: BorderRadius.circular(UIConstants.compactRadius),
        child: Container(
          constraints: const BoxConstraints(minHeight: UIConstants.minTapTarget),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: <Color>[color.withAlpha(35), color.withAlpha(17)],
            ),
            borderRadius: BorderRadius.circular(UIConstants.compactRadius),
            border: Border.fromBorderSide(
              AppStyles.hairline(context, accent: color, active: true),
            ),
            boxShadow: AppStyles.glow(context, color),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              Icon(
                icon,
                size: 17,
                color: color,
                shadows: AppStyles.inkGlow(color),
              ),
              const SizedBox(width: 6),
              Text(
                label,
                style: TextStyle(
                  color: color,
                  fontSize: 12,
                  fontWeight: FontWeight.w900,
                  shadows: AppStyles.inkGlow(color),
                ),
              ),
            ],
          ),
        ),
      );
}

class _RecordsCard extends StatelessWidget {
  const _RecordsCard({required this.children});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) => _GlassCard(
        padding: EdgeInsets.zero,
        borderRadius: UIConstants.cardRadius,
        child: Column(children: children),
      );
}

class _RecordTile extends StatelessWidget {
  const _RecordTile({
    required this.title,
    required this.subtitle,
    required this.amount,
    required this.color,
    this.onDelete,
  });

  final String title;
  final String subtitle;
  final String amount;
  final Color color;
  final VoidCallback? onDelete;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.fromLTRB(15, 13, 10, 13),
        decoration: BoxDecoration(
          border: Border(
            bottom:
                BorderSide(color: Theme.of(context).dividerColor.withAlpha(80)),
          ),
        ),
        child: Row(
          children: <Widget>[
            Container(
              width: 6,
              height: 42,
              decoration: BoxDecoration(
                color: color,
                borderRadius: BorderRadius.circular(99),
                boxShadow: <BoxShadow>[
                  BoxShadow(
                    color: color.withAlpha(78),
                    blurRadius: 13,
                    offset: Offset.zero,
                  ),
                ],
              ),
            ),
            const SizedBox(width: 13),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    title,
                    style: TextStyle(
                      color: color,
                      fontWeight: FontWeight.w900,
                      shadows: AppStyles.inkGlow(color),
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    subtitle,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: systemGray,
                      fontSize: 11.5,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Text(
              amount,
              style: TextStyle(
                color: color,
                fontSize: 15,
                fontWeight: FontWeight.w900,
                shadows: AppStyles.inkGlow(color),
              ),
            ),
            if (onDelete != null)
              Padding(
                padding: const EdgeInsets.only(left: 8),
                child: _Pressable(
                  onTap: onDelete,
                  semanticLabel: 'Delete $title record',
                  borderRadius:
                      BorderRadius.circular(UIConstants.compactRadius),
                  child: Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      color: appleRed.withAlpha(24),
                      borderRadius:
                          BorderRadius.circular(UIConstants.compactRadius),
                      border: Border.fromBorderSide(
                        AppStyles.hairline(
                          context,
                          accent: appleRed,
                          active: true,
                        ),
                      ),
                      boxShadow: AppStyles.glow(context, appleRed),
                    ),
                    child: const Icon(
                      Icons.delete_rounded,
                      color: appleRed,
                      size: 18,
                    ),
                  ),
                ),
              ),
          ],
        ),
      );
}''',
    'detail action and record primitives',
)

# Login card already matches the supplied reference; only remove the old offset
# drop shadow so it follows the global centered-depth rule.
replace_once(
    "BoxShadow(\n                        color: Colors.black.withAlpha(174),\n                        blurRadius: 58,\n                        offset: Offset(0, 18),\n                      ),",
    "BoxShadow(\n                        color: Colors.black.withAlpha(174),\n                        blurRadius: 58,\n                        spreadRadius: -6,\n                        offset: Offset.zero,\n                      ),",
    'login centered depth',
)

# Sanity guarantees: color semantics and finance logic must remain untouched.
required_invariants = [
    'Color _tone(double value, {Color neutral = appleBlue})',
    'if (value > .000001) return appleGreen;',
    'if (value < -.000001) return semanticRed;',
    "return neutral;",
    'LedgerMath.creditSigned',
    'LedgerMath.milkTotals',
]
for invariant in required_invariants:
    if invariant not in text:
        raise SystemExit(f'Invariant missing after UI migration: {invariant}')

path.write_text(text, encoding='utf-8')
print('Premium UI system migration applied successfully.')
