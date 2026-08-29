from pathlib import Path

MAIN = Path('lib/main.dart')
text = MAIN.read_text(encoding='utf-8')
original = text

# Shared premium depth: neutral lift plus semantic color bloom.
styles_start = text.index('  static List<BoxShadow> surfaceDepth(BuildContext context) {')
styles_end = text.index('  static Border glassBorder(BuildContext context, {Color? accent}) {', styles_start)
new_depth = '''  static List<BoxShadow> surfaceDepth(BuildContext context) {
    final bool dark = isDark(context);
    return <BoxShadow>[
      BoxShadow(
        color: Colors.black.withAlpha(dark ? 58 : 11),
        blurRadius: 7,
        spreadRadius: -2,
        offset: const Offset(0, 2),
      ),
      BoxShadow(
        color: Colors.black.withAlpha(dark ? 74 : 20),
        blurRadius: dark ? 32 : 28,
        spreadRadius: -8,
        offset: const Offset(0, 10),
      ),
      if (!dark)
        BoxShadow(
          color: Colors.white.withAlpha(190),
          blurRadius: 18,
          spreadRadius: -12,
          offset: const Offset(0, -3),
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
          strong ? (dark ? 68 : 48) : (dark ? 48 : 34),
        ),
        blurRadius: strong ? 32 : 24,
        spreadRadius: strong ? -5 : -6,
        offset: const Offset(0, 9),
      ),
      if (strong)
        BoxShadow(
          color: color.withAlpha(dark ? 34 : 25),
          blurRadius: 46,
          spreadRadius: -12,
          offset: const Offset(0, 16),
        ),
      ...surfaceDepth(context),
    ];
  }

  static List<BoxShadow> railDepth(BuildContext context, Color color) {
    final bool dark = isDark(context);
    return <BoxShadow>[
      BoxShadow(
        color: color.withAlpha(dark ? 68 : 48),
        blurRadius: 22,
        spreadRadius: -5,
        offset: const Offset(-3, 1),
      ),
      BoxShadow(
        color: color.withAlpha(dark ? 38 : 27),
        blurRadius: 36,
        spreadRadius: -10,
        offset: const Offset(0, 13),
      ),
      ...surfaceDepth(context),
    ];
  }

  static List<BoxShadow> jewelDepth(BuildContext context, Color color) {
    final bool dark = isDark(context);
    return <BoxShadow>[
      BoxShadow(
        color: color.withAlpha(dark ? 62 : 47),
        blurRadius: 21,
        spreadRadius: -4,
        offset: const Offset(0, 7),
      ),
      BoxShadow(
        color: color.withAlpha(dark ? 31 : 23),
        blurRadius: 30,
        spreadRadius: -9,
        offset: Offset.zero,
      ),
    ];
  }

'''
text = text[:styles_start] + new_depth + text[styles_end:]

old_border = '''  static Border glassBorder(BuildContext context, {Color? accent}) {
    final bool dark = isDark(context);
    return Border.all(
      color: Colors.white.withAlpha(dark ? 24 : 96),
      width: UIConstants.borderWidth,
    );
  }
'''
new_border = '''  static Border glassBorder(BuildContext context, {Color? accent}) {
    final bool dark = isDark(context);
    return Border.all(
      color: Colors.white.withAlpha(dark ? 30 : 132),
      width: UIConstants.borderWidth,
    );
  }
'''
if text.count(old_border) != 1:
    raise SystemExit(f'glassBorder guard: expected 1 match, found {text.count(old_border)}')
text = text.replace(old_border, new_border, 1)

# One central press engine for all existing interactive surfaces.
press_start = text.index('class _Pressable extends StatefulWidget {')
press_end = text.index('class _GlassCard extends StatelessWidget {', press_start)
new_press = '''class _PressableScope extends InheritedWidget {
  const _PressableScope({required super.child});

  static bool contains(BuildContext context) =>
      context.getInheritedWidgetOfExactType<_PressableScope>() != null;

  @override
  bool updateShouldNotify(covariant _PressableScope oldWidget) => false;
}

class _Pressable extends StatefulWidget {
  const _Pressable({
    required this.child,
    required this.onTap,
    this.borderRadius,
    this.semanticLabel,
    this.visualOnly = false,
    this.pressScale = .986,
    this.softBounce = true,
  });

  final Widget child;
  final VoidCallback? onTap;
  final BorderRadius? borderRadius;
  final String? semanticLabel;
  final bool visualOnly;
  final double pressScale;
  final bool softBounce;

  @override
  State<_Pressable> createState() => _PressableState();
}

class _PressableState extends State<_Pressable>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pressController;

  bool get _canPress => widget.onTap != null || widget.visualOnly;

  bool get _reduceMotion =>
      MediaQuery.maybeOf(context)?.disableAnimations ?? false;

  @override
  void initState() {
    super.initState();
    _pressController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 82),
      reverseDuration: const Duration(milliseconds: 230),
    );
  }

  void _press() {
    if (!_canPress) return;
    if (_reduceMotion) {
      _pressController.value = 0;
      return;
    }
    _pressController.animateTo(
      1,
      duration: const Duration(milliseconds: 82),
      curve: const Cubic(0.20, 0, 0, 1),
    );
  }

  void _release() {
    if (!_canPress) return;
    if (_reduceMotion) {
      _pressController.value = 0;
      return;
    }
    _pressController.animateBack(
      0,
      duration: Duration(milliseconds: widget.softBounce ? 230 : 180),
      curve: widget.softBounce
          ? const Cubic(0.20, 1.08, 0.30, 1)
          : const Cubic(0.22, 1, 0.36, 1),
    );
  }

  @override
  void dispose() {
    _pressController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bool interactive = widget.onTap != null;
    final double pressScale = widget.pressScale.clamp(.96, 1.0).toDouble();
    return Semantics(
      button: interactive,
      label: widget.semanticLabel,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTapDown: _canPress ? (_) => _press() : null,
        onTapCancel: _canPress ? _release : null,
        onTapUp: _canPress ? (_) => _release() : null,
        onTap: !interactive
            ? null
            : () {
                HapticFeedback.selectionClick();
                widget.onTap!();
              },
        child: AnimatedBuilder(
          animation: _pressController,
          child: _PressableScope(child: widget.child),
          builder: (BuildContext context, Widget? child) {
            final double amount = _pressController.value;
            return Transform.scale(
              scale: 1 - ((1 - pressScale) * amount),
              child: Stack(
                clipBehavior: Clip.none,
                children: <Widget>[
                  child!,
                  Positioned.fill(
                    child: IgnorePointer(
                      child: ClipRRect(
                        borderRadius: widget.borderRadius ?? BorderRadius.zero,
                        child: ColoredBox(
                          color: (Theme.of(context).brightness == Brightness.dark
                                  ? Colors.white
                                  : Colors.black)
                              .withAlpha(
                            (amount *
                                    (Theme.of(context).brightness == Brightness.dark
                                        ? 11
                                        : 7))
                                .round(),
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}

'''
text = text[:press_start] + new_press + text[press_end:]

# Standalone/non-clickable glass cards get visual-only bounce. Cards already
# inside _Pressable are detected by the scope, so there is no double animation.
glass_start = text.index('class _GlassCard extends StatelessWidget {')
glass_end = text.index('class _CardAccentPainter extends CustomPainter {', glass_start)
glass = text[glass_start:glass_end]

old_return = '''    final BorderRadius radius = BorderRadius.circular(borderRadius);
    return DecoratedBox(
'''
new_return = '''    final BorderRadius radius = BorderRadius.circular(borderRadius);
    final Widget surface = DecoratedBox(
'''
if glass.count(old_return) != 1:
    raise SystemExit(f'_GlassCard return guard: expected 1 match, found {glass.count(old_return)}')
glass = glass.replace(old_return, new_return, 1)

tail = '\n    );\n  }\n}\n\n'
if not glass.endswith(tail):
    raise SystemExit('_GlassCard tail guard failed')
glass = glass[:-len(tail)] + '''
    );
    if (_PressableScope.contains(context)) return surface;
    return _Pressable(
      onTap: null,
      visualOnly: true,
      pressScale: .986,
      softBounce: true,
      borderRadius: radius,
      child: surface,
    );
  }
}

'''
text = text[:glass_start] + glass + text[glass_end:]

checks = [
    'class _PressableScope extends InheritedWidget',
    'visualOnly: true',
    'pressScale: .986',
    'if (_PressableScope.contains(context)) return surface;',
    'Colors.white.withAlpha(dark ? 30 : 132)',
]
for check in checks:
    if check not in text:
        raise SystemExit(f'post-patch guard failed: {check}')

if text == original:
    raise SystemExit('migration produced no changes')

MAIN.write_text(text, encoding='utf-8')
