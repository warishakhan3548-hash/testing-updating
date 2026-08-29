from pathlib import Path
import re

path = Path('lib/main.dart')
src = path.read_text(encoding='utf-8')

old = '''                                    child: Icon(
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

new = '''                                    child: _BottomNavModuleIcon(
                                      label: spec.label,
                                      fallbackIcon: spec.icon,
                                      active: active,
                                      color: active
                                          ? color
                                          : color.withAlpha(dark ? 148 : 145),
                                      shadows: active
                                          ? AppStyles.inkGlow(
                                              color,
                                              strong: true,
                                            )
                                          : <Shadow>[
                                              Shadow(
                                                color: color
                                                    .withAlpha(dark ? 48 : 34),
                                                blurRadius: 7,
                                              ),
                                            ],
                                    ),'''

if src.count(old) != 1:
    raise SystemExit(f'Expected exactly one bottom-nav Icon block, found {src.count(old)}')
src = src.replace(old, new, 1)

anchor = '''class _PressableScope extends InheritedWidget {'''
if src.count(anchor) != 1:
    raise SystemExit(f'Expected one _PressableScope anchor, found {src.count(anchor)}')

helper = r'''class _BottomNavModuleIcon extends StatelessWidget {
  const _BottomNavModuleIcon({
    required this.label,
    required this.fallbackIcon,
    required this.active,
    required this.color,
    required this.shadows,
  });

  final String label;
  final IconData fallbackIcon;
  final bool active;
  final Color color;
  final List<Shadow>? shadows;

  @override
  Widget build(BuildContext context) {
    final double size = active ? 24 : 22;
    switch (label) {
      case 'Credit':
        return _CreditMoneyHandIcon(
          size: size,
          color: color,
          glow: active,
        );
      case 'Expenses':
        return Icon(
          Icons.receipt_long_rounded,
          size: size,
          color: color,
          shadows: shadows,
        );
      case 'Salary':
        return _SalaryMoneyBagIcon(
          size: size,
          color: color,
          glow: active,
        );
      case 'Diary':
        return Icon(
          Icons.menu_book_rounded,
          size: size,
          color: color,
          shadows: shadows,
        );
      case 'Business':
        return Icon(
          Icons.business_center_rounded,
          size: size,
          color: color,
          shadows: shadows,
        );
      default:
        return Icon(
          fallbackIcon,
          size: size,
          color: color,
          shadows: shadows,
        );
    }
  }
}

class _CreditMoneyHandIcon extends StatelessWidget {
  const _CreditMoneyHandIcon({
    required this.size,
    required this.color,
    required this.glow,
  });

  final double size;
  final Color color;
  final bool glow;

  @override
  Widget build(BuildContext context) => SizedBox.square(
        dimension: size,
        child: CustomPaint(
          painter: _CreditMoneyHandPainter(color: color, glow: glow),
        ),
      );
}

class _CreditMoneyHandPainter extends CustomPainter {
  const _CreditMoneyHandPainter({required this.color, required this.glow});

  final Color color;
  final bool glow;

  Path _hand(Size size) {
    final double w = size.width;
    final double h = size.height;
    return Path()
      ..moveTo(w * .08, h * .66)
      ..lineTo(w * .25, h * .66)
      ..cubicTo(w * .32, h * .52, w * .43, h * .50, w * .53, h * .61)
      ..lineTo(w * .70, h * .61)
      ..quadraticBezierTo(w * .86, h * .60, w * .89, h * .70)
      ..quadraticBezierTo(w * .78, h * .87, w * .55, h * .84)
      ..lineTo(w * .31, h * .82)
      ..lineTo(w * .16, h * .91)
      ..lineTo(w * .08, h * .78);
  }

  @override
  void paint(Canvas canvas, Size size) {
    if (size.isEmpty) return;
    final Path hand = _hand(size);
    if (glow) {
      canvas.drawPath(
        hand,
        Paint()
          ..color = color.withAlpha(44)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 4.2
          ..strokeCap = StrokeCap.round
          ..strokeJoin = StrokeJoin.round
          ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 3),
      );
    }
    canvas.drawPath(
      hand,
      Paint()
        ..color = color
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.35
        ..strokeCap = StrokeCap.round
        ..strokeJoin = StrokeJoin.round,
    );

    final TextPainter money = TextPainter(
      text: TextSpan(
        text: r'$',
        style: TextStyle(
          color: color,
          fontSize: size.width * .38,
          height: 1,
          fontWeight: FontWeight.w900,
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    money.paint(
      canvas,
      Offset((size.width - money.width) / 2, size.height * .05),
    );
  }

  @override
  bool shouldRepaint(covariant _CreditMoneyHandPainter oldDelegate) =>
      oldDelegate.color != color || oldDelegate.glow != glow;
}

class _SalaryMoneyBagIcon extends StatelessWidget {
  const _SalaryMoneyBagIcon({
    required this.size,
    required this.color,
    required this.glow,
  });

  final double size;
  final Color color;
  final bool glow;

  @override
  Widget build(BuildContext context) => SizedBox.square(
        dimension: size,
        child: CustomPaint(
          painter: _SalaryMoneyBagPainter(color: color, glow: glow),
        ),
      );
}

class _SalaryMoneyBagPainter extends CustomPainter {
  const _SalaryMoneyBagPainter({required this.color, required this.glow});

  final Color color;
  final bool glow;

  Path _bag(Size size) {
    final double w = size.width;
    final double h = size.height;
    return Path()
      ..moveTo(w * .38, h * .13)
      ..quadraticBezierTo(w * .50, h * .06, w * .62, h * .13)
      ..lineTo(w * .57, h * .27)
      ..cubicTo(w * .78, h * .35, w * .87, h * .53, w * .84, h * .72)
      ..quadraticBezierTo(w * .81, h * .90, w * .50, h * .92)
      ..quadraticBezierTo(w * .19, h * .90, w * .16, h * .72)
      ..cubicTo(w * .13, h * .53, w * .22, h * .35, w * .43, h * .27)
      ..close();
  }

  @override
  void paint(Canvas canvas, Size size) {
    if (size.isEmpty) return;
    final Path bag = _bag(size);
    if (glow) {
      canvas.drawPath(
        bag,
        Paint()
          ..color = color.withAlpha(42)
          ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 3),
      );
    }
    canvas.drawPath(bag, Paint()..color = color);
    canvas.drawLine(
      Offset(size.width * .36, size.height * .29),
      Offset(size.width * .64, size.height * .29),
      Paint()
        ..color = color
        ..strokeWidth = 1.8
        ..strokeCap = StrokeCap.round,
    );

    final TextPainter money = TextPainter(
      text: TextSpan(
        text: r'$',
        style: TextStyle(
          color: ThemeData.estimateBrightnessForColor(color) == Brightness.dark
              ? Colors.white
              : const Color(0xFF102018),
          fontSize: size.width * .34,
          height: 1,
          fontWeight: FontWeight.w900,
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    money.paint(
      canvas,
      Offset((size.width - money.width) / 2, size.height * .43),
    );
  }

  @override
  bool shouldRepaint(covariant _SalaryMoneyBagPainter oldDelegate) =>
      oldDelegate.color != color || oldDelegate.glow != glow;
}

'''

src = src.replace(anchor, helper + anchor, 1)
path.write_text(src, encoding='utf-8')
