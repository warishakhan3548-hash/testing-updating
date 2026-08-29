from pathlib import Path

MAIN = Path("lib/main.dart")
text = MAIN.read_text(encoding="utf-8")

marker = "// PREMIUM_NAV_V2"
if marker in text:
    raise SystemExit("Premium navigation v2 is already applied.")

nav_start = text.find("class _BottomLedgerNav extends StatelessWidget")
icon_start = text.find("enum _BottomNavGlyphKind", nav_start)
pressable_start = text.find("class _Pressable extends StatefulWidget", icon_start)
if nav_start < 0 or icon_start < 0 or pressable_start < 0:
    raise SystemExit("Could not locate bottom navigation sections safely.")

new_nav = r'''class _BottomLedgerNav extends StatelessWidget {
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
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: Colors.black.withAlpha(dark ? 108 : 16),
            blurRadius: dark ? 42 : 34,
            spreadRadius: -12,
            offset: const Offset(0, -10),
          ),
        ],
      ),
      child: ClipRect(
        child: BackdropFilter(
          filter: ui.ImageFilter.blur(sigmaX: 22, sigmaY: 22),
          child: DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: dark
                    ? const <Color>[Color(0xE0121928), Color(0xD0080D18)]
                    : const <Color>[Color(0xF3FFFFFF), Color(0xE4FFFFFF)],
              ),
              border: Border(
                top: BorderSide(
                  color: dark
                      ? Colors.white.withAlpha(22)
                      : Colors.white.withAlpha(210),
                  width: .8,
                ),
              ),
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
                      children:
                          List<Widget>.generate(_tabs.length, (int index) {
                        final _TabSpec spec = _tabs[index];
                        final bool active = index == selected;
                        final Color color = colors[index];
                        return _Pressable(
                          onTap: () => onSelected(index),
                          semanticLabel: '${spec.label} tab',
                          borderRadius:
                              BorderRadius.circular(UIConstants.actionRadius),
                          child: AnimatedSlide(
                            offset:
                                active ? const Offset(0, -.025) : Offset.zero,
                            duration: UIConstants.motion,
                            curve: const Cubic(0.32, 0.72, 0, 1),
                            child: AnimatedContainer(
                              duration: UIConstants.motion,
                              curve: const Cubic(0.32, 0.72, 0, 1),
                              width: 84,
                              height: 70,
                              margin: const EdgeInsets.symmetric(horizontal: 4),
                              decoration: const BoxDecoration(
                                color: Colors.transparent,
                              ),
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: <Widget>[
                                  AnimatedScale(
                                    scale: active ? 1.045 : 1,
                                    duration: UIConstants.motion,
                                    curve: const Cubic(0.34, 1.18, 0.64, 1),
                                    child: _PremiumNavIconFrame(
                                      color: color,
                                      active: active,
                                      dark: dark,
                                      child: _BottomNavGlyph(
                                        label: spec.label,
                                        size: active ? 30 : 27.5,
                                        color: active
                                            ? color
                                            : color.withAlpha(dark ? 164 : 160),
                                        active: active,
                                        dark: dark,
                                      ),
                                    ),
                                  ),
                                  const SizedBox(height: 3),
                                  AnimatedDefaultTextStyle(
                                    duration: UIConstants.motion,
                                    curve: const Cubic(0.32, 0.72, 0, 1),
                                    style: TextStyle(
                                      color: active
                                          ? color
                                          : color.withAlpha(dark ? 176 : 188),
                                      fontSize: active ? 12.5 : 12,
                                      fontWeight: active
                                          ? FontWeight.w800
                                          : FontWeight.w600,
                                      letterSpacing: active ? -.12 : 0,
                                      shadows: active
                                          ? AppStyles.inkGlow(color)
                                          : null,
                                    ),
                                    child: Text(spec.label),
                                  ),
                                  const SizedBox(height: 4),
                                  AnimatedContainer(
                                    duration: UIConstants.motion,
                                    curve: const Cubic(0.32, 0.72, 0, 1),
                                    width: active ? 24 : 0,
                                    height: 2.5,
                                    decoration: BoxDecoration(
                                      color: color.withAlpha(active ? 188 : 0),
                                      borderRadius: BorderRadius.circular(99),
                                      boxShadow: active
                                          ? <BoxShadow>[
                                              BoxShadow(
                                                color: color.withAlpha(82),
                                                blurRadius: 11,
                                                spreadRadius: -2,
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
          ),
        ),
      ),
    );
  }
}

// PREMIUM_NAV_V2
'''

new_icons = r'''class _PremiumNavIconFrame extends StatelessWidget {
  const _PremiumNavIconFrame({
    required this.color,
    required this.active,
    required this.dark,
    required this.child,
  });

  final Color color;
  final bool active;
  final bool dark;
  final Widget child;

  @override
  Widget build(BuildContext context) => AnimatedContainer(
        duration: UIConstants.motion,
        curve: const Cubic(0.32, 0.72, 0, 1),
        width: active ? 46 : 39,
        height: active ? 39 : 35,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(active ? 15 : 13),
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: <Color>[
              color.withAlpha(active ? (dark ? 34 : 26) : (dark ? 16 : 11)),
              color.withAlpha(active ? (dark ? 14 : 9) : 0),
            ],
          ),
          border: Border.all(
            color: color.withAlpha(active ? (dark ? 70 : 54) : (dark ? 24 : 18)),
            width: active ? .9 : .7,
          ),
          boxShadow: active
              ? <BoxShadow>[
                  BoxShadow(
                    color: color.withAlpha(dark ? 48 : 34),
                    blurRadius: 16,
                    spreadRadius: -5,
                    offset: const Offset(0, 5),
                  ),
                  BoxShadow(
                    color: Colors.white.withAlpha(dark ? 12 : 88),
                    blurRadius: 1,
                    offset: const Offset(0, -1),
                  ),
                ]
              : null,
        ),
        child: child,
      );
}

enum _BottomNavGlyphKind { milk, credit, salary }

class _BottomNavGlyph extends StatelessWidget {
  const _BottomNavGlyph({
    required this.label,
    required this.size,
    required this.color,
    required this.active,
    required this.dark,
  });

  final String label;
  final double size;
  final Color color;
  final bool active;
  final bool dark;

  List<Shadow> get _shadows => active
      ? <Shadow>[
          Shadow(
            color: color.withAlpha(dark ? 86 : 62),
            blurRadius: 8,
            offset: Offset.zero,
          ),
        ]
      : <Shadow>[
          Shadow(
            color: color.withAlpha(dark ? 40 : 28),
            blurRadius: 5,
          ),
        ];

  @override
  Widget build(BuildContext context) {
    switch (label) {
      case 'Home':
        return Icon(
          active ? Icons.home_rounded : Icons.home_outlined,
          size: size,
          color: color,
          shadows: _shadows,
        );
      case 'Expenses':
        return Icon(
          active ? Icons.receipt_long_rounded : Icons.receipt_long_outlined,
          size: size,
          color: color,
          shadows: _shadows,
        );
      case 'Diary':
        return Icon(
          active ? Icons.menu_book_rounded : Icons.menu_book_outlined,
          size: size,
          color: color,
          shadows: _shadows,
        );
      case 'Business':
        return Icon(
          active ? Icons.work_rounded : Icons.work_outline_rounded,
          size: size,
          color: color,
          shadows: _shadows,
        );
      case 'Milk':
        return _custom(_BottomNavGlyphKind.milk);
      case 'Credit':
        return _custom(_BottomNavGlyphKind.credit);
      case 'Salary':
        return _custom(_BottomNavGlyphKind.salary);
      default:
        return const SizedBox.shrink();
    }
  }

  Widget _custom(_BottomNavGlyphKind kind) => SizedBox.square(
        dimension: size,
        child: CustomPaint(
          painter: _BottomNavGlyphPainter(
            kind: kind,
            color: color,
            active: active,
            dark: dark,
          ),
        ),
      );
}

class _BottomNavGlyphPainter extends CustomPainter {
  const _BottomNavGlyphPainter({
    required this.kind,
    required this.color,
    required this.active,
    required this.dark,
  });

  final _BottomNavGlyphKind kind;
  final Color color;
  final bool active;
  final bool dark;

  @override
  void paint(Canvas canvas, Size size) {
    if (size.isEmpty) return;
    final double scale = size.shortestSide / 28;
    canvas.save();
    canvas.translate(
      (size.width - 28 * scale) / 2,
      (size.height - 28 * scale) / 2,
    );
    canvas.scale(scale);

    final Paint wash = Paint()
      ..color = color.withAlpha(active ? (dark ? 34 : 24) : (dark ? 18 : 12))
      ..style = PaintingStyle.fill;
    final Paint aura = Paint()
      ..color = color.withAlpha(active ? (dark ? 84 : 62) : (dark ? 42 : 30))
      ..style = PaintingStyle.stroke
      ..strokeWidth = active ? 2.35 : 2.15
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round
      ..maskFilter = ui.MaskFilter.blur(
        ui.BlurStyle.normal,
        active ? 3.7 : 2.1,
      );
    final Paint ink = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = active ? 2.12 : 1.98
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    final Paint detail = Paint()
      ..color = color.withAlpha(active ? 210 : 170)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.15
      ..strokeCap = StrokeCap.round;

    switch (kind) {
      case _BottomNavGlyphKind.milk:
        _paintMilk(canvas, wash, aura, ink, detail);
        break;
      case _BottomNavGlyphKind.credit:
        _paintCredit(canvas, wash, aura, ink, detail);
        break;
      case _BottomNavGlyphKind.salary:
        _paintSalary(canvas, wash, aura, ink, detail);
        break;
    }
    canvas.restore();
  }

  void _paintMilk(
    Canvas canvas,
    Paint wash,
    Paint aura,
    Paint ink,
    Paint detail,
  ) {
    final RRect body = RRect.fromRectAndRadius(
      const Rect.fromLTWH(6.2, 7.1, 15.6, 17.2),
      const Radius.circular(3.5),
    );
    canvas.drawRRect(body, wash);
    canvas.drawRRect(body, aura);
    canvas.drawRRect(body, ink);
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(10, 3.2, 8, 4.7),
        const Radius.circular(1.45),
      ),
      ink,
    );
    canvas.drawLine(const Offset(8.7, 11), const Offset(19.3, 11), detail);
    canvas.drawLine(const Offset(9.1, 21), const Offset(18.9, 21), detail);
    final Path drop = Path()
      ..moveTo(14, 13.05)
      ..cubicTo(12.55, 14.95, 11.75, 16.05, 11.75, 17.3)
      ..cubicTo(11.75, 18.8, 12.72, 19.85, 14, 19.85)
      ..cubicTo(15.28, 19.85, 16.25, 18.8, 16.25, 17.3)
      ..cubicTo(16.25, 16.05, 15.45, 14.95, 14, 13.05);
    canvas.drawPath(drop, ink);
  }

  void _paintCredit(
    Canvas canvas,
    Paint wash,
    Paint aura,
    Paint ink,
    Paint detail,
  ) {
    const Offset coinCenter = Offset(16.2, 7.1);
    canvas.drawCircle(coinCenter, 5.05, wash);
    canvas.drawCircle(coinCenter, 5.05, aura);
    canvas.drawCircle(coinCenter, 5.05, ink);
    _paintDollar(canvas, const Offset(13.25, 2.25), 9.5);

    final Path palm = Path()
      ..moveTo(2.4, 18.1)
      ..lineTo(7.1, 18.1)
      ..cubicTo(8.6, 18.1, 9.45, 19.35, 11.2, 19.35)
      ..lineTo(15.6, 19.35)
      ..cubicTo(17.05, 19.35, 17.2, 17.35, 15.6, 17.35)
      ..lineTo(12.25, 17.35)
      ..cubicTo(10.9, 17.35, 10.2, 16.6, 9.05, 15.8)
      ..lineTo(7.3, 14.65);
    canvas.drawPath(palm, aura);
    canvas.drawPath(palm, ink);

    final Path support = Path()
      ..moveTo(15.5, 17.45)
      ..lineTo(21.15, 14.55)
      ..cubicTo(22.65, 13.8, 24.15, 14.55, 23.25, 16)
      ..cubicTo(21.2, 19.05, 17.65, 22.75, 13.6, 23.3)
      ..lineTo(7.2, 23.3)
      ..lineTo(3.35, 21.55);
    canvas.drawPath(support, aura);
    canvas.drawPath(support, ink);
    canvas.drawLine(const Offset(4.2, 20), const Offset(7.1, 20), detail);
  }

  void _paintSalary(
    Canvas canvas,
    Paint wash,
    Paint aura,
    Paint ink,
    Paint detail,
  ) {
    final Path bag = Path()
      ..moveTo(10.2, 7.4)
      ..cubicTo(6.7, 9.8, 5.1, 13.05, 5.1, 17.25)
      ..cubicTo(5.1, 21.7, 8.3, 24.1, 14, 24.1)
      ..cubicTo(19.7, 24.1, 22.9, 21.7, 22.9, 17.25)
      ..cubicTo(22.9, 13.05, 21.3, 9.8, 17.8, 7.4)
      ..close();
    canvas.drawPath(bag, wash);
    canvas.drawPath(bag, aura);
    canvas.drawPath(bag, ink);
    canvas.drawLine(const Offset(10.15, 4.15), const Offset(17.85, 4.15), ink);
    canvas.drawLine(const Offset(11.1, 4.15), const Offset(10.2, 7.35), ink);
    canvas.drawLine(const Offset(16.9, 4.15), const Offset(17.8, 7.35), ink);
    canvas.drawLine(const Offset(9.5, 9.8), const Offset(18.5, 9.8), detail);
    _paintDollar(canvas, const Offset(10.35, 11.45), 11.25);
  }

  void _paintDollar(Canvas canvas, Offset offset, double fontSize) {
    final TextPainter painter = TextPainter(
      textDirection: ui.TextDirection.ltr,
      text: TextSpan(
        text: r'$',
        style: TextStyle(
          color: color,
          fontSize: fontSize,
          fontWeight: FontWeight.w900,
          height: 1,
          shadows: active
              ? <Shadow>[
                  Shadow(
                    color: color.withAlpha(dark ? 92 : 66),
                    blurRadius: 5,
                  ),
                ]
              : null,
        ),
      ),
    )..layout();
    painter.paint(canvas, offset);
  }

  @override
  bool shouldRepaint(covariant _BottomNavGlyphPainter oldDelegate) =>
      oldDelegate.kind != kind ||
      oldDelegate.color != color ||
      oldDelegate.active != active ||
      oldDelegate.dark != dark;
}

'''

text = text[:nav_start] + new_nav + new_icons + text[pressable_start:]

# Guard the business logic: semantic colors must still come from live state.
if "final List<Color> colors = _moduleTabColors(sync.state);" not in text:
    raise SystemExit("Dynamic module color routing disappeared; refusing to write.")
if "final Color color = colors[index];" not in text:
    raise SystemExit("Per-tab dynamic semantic color selection disappeared.")
if "_tone(_creditGlobalNet(state))" not in text:
    raise SystemExit("Credit semantic tone logic disappeared.")
if "_tone(_salaryGlobalNet(state))" not in text:
    raise SystemExit("Salary semantic tone logic disappeared.")
if "_tone(_milkGlobalNet(state))" not in text:
    raise SystemExit("Milk semantic tone logic disappeared.")
if "color: appleBlue.withAlpha(active" in text[nav_start:text.find("class _Pressable extends StatefulWidget", nav_start)]:
    raise SystemExit("Found a hard-coded blue active indicator in premium nav.")
if text.count(marker) != 1:
    raise SystemExit("Premium navigation marker count is invalid.")

MAIN.write_text(text, encoding="utf-8")
print("Premium navigation v2 applied successfully.")
