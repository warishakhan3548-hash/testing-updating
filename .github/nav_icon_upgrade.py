from pathlib import Path

MAIN = Path("lib/main.dart")
text = MAIN.read_text(encoding="utf-8")

if "class _BottomNavGlyph extends StatelessWidget" in text:
    raise SystemExit("Bottom navigation glyph upgrade is already present; refusing to layer another override.")

nav_start = text.find("class _BottomLedgerNav extends StatelessWidget")
nav_end = text.find("\nclass _Pressable extends StatefulWidget", nav_start)
if nav_start < 0 or nav_end < 0:
    raise SystemExit("Could not locate the guarded _BottomLedgerNav section.")

nav = text[nav_start:nav_end]
old_icon = '''                                    child: Icon(
                                      spec.icon,
                                      size: active ? 24 : 22,
                                      color: active
                                          ? color
                                          : color.withAlpha(dark ? 148 : 145),
                                      shadows: active
                                          ? AppStyles.inkGlow(color,
                                              strong: true)
                                          : <Shadow>[
                                              Shadow(
                                                color: color
                                                    .withAlpha(dark ? 48 : 34),
                                                blurRadius: 7,
                                              ),
                                            ],
                                    ),'''

new_icon = '''                                    child: _BottomNavGlyph(
                                      label: spec.label,
                                      size: active ? 24 : 22,
                                      color: active
                                          ? color
                                          : color.withAlpha(dark ? 148 : 145),
                                      active: active,
                                      dark: dark,
                                    ),'''

if nav.count(old_icon) != 1:
    raise SystemExit(
        f"Expected exactly one old bottom-nav icon renderer, found {nav.count(old_icon)}."
    )

nav = nav.replace(old_icon, new_icon, 1)
text = text[:nav_start] + nav + text[nav_end:]
nav_end = text.find("\nclass _Pressable extends StatefulWidget", nav_start)

new_glyph_code = r'''

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
      ? AppStyles.inkGlow(color, strong: true)
      : <Shadow>[
          Shadow(
            color: color.withAlpha(dark ? 48 : 34),
            blurRadius: 7,
          ),
        ];

  @override
  Widget build(BuildContext context) {
    switch (label) {
      case 'Home':
        return Icon(
          Icons.home_rounded,
          size: size,
          color: color,
          shadows: _shadows,
        );
      case 'Expenses':
        return Icon(
          Icons.receipt_long_rounded,
          size: size,
          color: color,
          shadows: _shadows,
        );
      case 'Diary':
        return Icon(
          Icons.book_rounded,
          size: size,
          color: color,
          shadows: _shadows,
        );
      case 'Business':
        return Icon(
          Icons.business_center_rounded,
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
    final double scale = size.shortestSide / 24;
    canvas.save();
    canvas.translate((size.width - 24 * scale) / 2, (size.height - 24 * scale) / 2);
    canvas.scale(scale);

    final Paint glow = Paint()
      ..color = color.withAlpha(active ? (dark ? 74 : 58) : (dark ? 38 : 28))
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.35
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round
      ..maskFilter = MaskFilter.blur(BlurStyle.normal, active ? 3.2 : 1.8);
    final Paint ink = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.15
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;

    switch (kind) {
      case _BottomNavGlyphKind.milk:
        _paintMilk(canvas, glow);
        _paintMilk(canvas, ink);
      case _BottomNavGlyphKind.credit:
        _paintCredit(canvas, glow, glowPass: true);
        _paintCredit(canvas, ink);
      case _BottomNavGlyphKind.salary:
        _paintSalary(canvas, glow, glowPass: true);
        _paintSalary(canvas, ink);
    }
    canvas.restore();
  }

  void _paintMilk(Canvas canvas, Paint paint) {
    final RRect body = RRect.fromRectAndRadius(
      const Rect.fromLTWH(6.25, 6.7, 11.5, 14.1),
      const Radius.circular(2.8),
    );
    canvas.drawRRect(body, paint);
    canvas.drawLine(const Offset(9.1, 3.6), const Offset(14.9, 3.6), paint);
    canvas.drawLine(const Offset(9.7, 3.6), const Offset(9.7, 6.5), paint);
    canvas.drawLine(const Offset(14.3, 3.6), const Offset(14.3, 6.5), paint);
    canvas.drawLine(const Offset(8.6, 10.1), const Offset(15.4, 10.1), paint);
    canvas.drawPath(
      Path()
        ..moveTo(12, 12.1)
        ..cubicTo(10.8, 13.7, 10.2, 14.5, 10.2, 15.5)
        ..cubicTo(10.2, 16.7, 11, 17.5, 12, 17.5)
        ..cubicTo(13, 17.5, 13.8, 16.7, 13.8, 15.5)
        ..cubicTo(13.8, 14.5, 13.2, 13.7, 12, 12.1),
      paint,
    );
  }

  void _paintCredit(Canvas canvas, Paint paint, {bool glowPass = false}) {
    canvas.drawPath(
      Path()
        ..moveTo(2.9, 16.1)
        ..lineTo(7.1, 16.1)
        ..cubicTo(8.7, 16.1, 9.5, 17.2, 11, 17.2)
        ..lineTo(14.5, 17.2)
        ..cubicTo(15.7, 17.2, 15.8, 15.5, 14.5, 15.5)
        ..lineTo(11.7, 15.5)
        ..cubicTo(10.4, 15.5, 9.7, 14.8, 8.7, 14.1)
        ..lineTo(7.2, 13.1),
      paint,
    );
    canvas.drawPath(
      Path()
        ..moveTo(14.4, 15.6)
        ..lineTo(18.8, 13.3)
        ..cubicTo(20.1, 12.6, 21.2, 13.2, 20.5, 14.3)
        ..cubicTo(18.7, 16.8, 15.9, 19.8, 12.6, 20.3)
        ..lineTo(7.4, 20.3)
        ..lineTo(3.7, 18.7),
      paint,
    );
    _paintDollar(canvas, const Offset(9.2, 1.25), 9.3, glowPass: glowPass);
  }

  void _paintSalary(Canvas canvas, Paint paint, {bool glowPass = false}) {
    canvas.drawLine(const Offset(9.1, 4.1), const Offset(14.9, 4.1), paint);
    canvas.drawLine(const Offset(10.1, 4.1), const Offset(9.1, 7), paint);
    canvas.drawLine(const Offset(13.9, 4.1), const Offset(14.9, 7), paint);
    canvas.drawPath(
      Path()
        ..moveTo(9.2, 7)
        ..cubicTo(6.2, 9.1, 4.8, 12, 4.8, 15.5)
        ..cubicTo(4.8, 19.3, 7.6, 21.1, 12, 21.1)
        ..cubicTo(16.4, 21.1, 19.2, 19.3, 19.2, 15.5)
        ..cubicTo(19.2, 12, 17.8, 9.1, 14.8, 7)
        ..close(),
      paint,
    );
    _paintDollar(canvas, const Offset(9.15, 10), 8.8, glowPass: glowPass);
  }

  void _paintDollar(
    Canvas canvas,
    Offset offset,
    double fontSize, {
    required bool glowPass,
  }) {
    final TextPainter painter = TextPainter(
      textDirection: TextDirection.ltr,
      text: TextSpan(
        text: r'$',
        style: TextStyle(
          color: glowPass
              ? color.withAlpha(active ? (dark ? 90 : 72) : (dark ? 50 : 38))
              : color,
          fontSize: fontSize,
          fontWeight: FontWeight.w900,
          height: 1,
          shadows: glowPass
              ? <Shadow>[
                  Shadow(
                    color: color.withAlpha(active ? 80 : 38),
                    blurRadius: active ? 5 : 3,
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

text = text[:nav_end] + new_glyph_code + text[nav_end:]

# Safety invariants: dynamic semantic tab colors must remain the source of truth.
if "final List<Color> colors = _moduleTabColors(sync.state);" not in text:
    raise SystemExit("Semantic module color routing disappeared; refusing to write.")
if "final Color color = colors[index];" not in text:
    raise SystemExit("Per-tab semantic color selection disappeared; refusing to write.")
if "spec.icon" in text[text.find("class _BottomLedgerNav extends StatelessWidget"):text.find("class _Pressable extends StatefulWidget")]:
    raise SystemExit("Old bottom-nav IconData renderer is still present after replacement.")
if text.count("class _BottomNavGlyph extends StatelessWidget") != 1:
    raise SystemExit("Expected exactly one new bottom-nav glyph implementation.")

MAIN.write_text(text, encoding="utf-8")
print("Bottom navigation icon design upgraded successfully.")
