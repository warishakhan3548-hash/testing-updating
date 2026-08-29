from pathlib import Path

MAIN = Path('lib/main.dart')
text = MAIN.read_text(encoding='utf-8')

start = text.index('class _CardAccentPainter extends CustomPainter {')
end = text.index('\nclass _ScreenHeader extends StatelessWidget {', start)
old = text[start:end]

required_fragments = (
    '..moveTo(r * .72, 0)',
    '..quadraticBezierTo(0, 0, 0, r)',
    '..lineTo(0, size.height - r)',
    '..quadraticBezierTo(0, size.height, r * .72, size.height)',
)
for fragment in required_fragments:
    if fragment not in old:
        raise SystemExit(f'Guard failed: expected accent rail baseline fragment not found: {fragment}')

new = '''class _CardAccentPainter extends CustomPainter {
  const _CardAccentPainter({
    required this.color,
    required this.radius,
    required this.dark,
  });

  final Color color;
  final double radius;
  final bool dark;

  Path _rail(Size size) {
    // Keep the solid rail fully inside the rounded clip. The old path lived on
    // x=0/y=0, so half of its stroke was clipped and the curved ends could look
    // detached. Insetting by half the primary stroke preserves the same visual
    // edge while making the rail one continuous anti-aliased path.
    final double halfStroke = UIConstants.accentStroke / 2;
    final double x = halfStroke;
    final double top = halfStroke;
    final double bottom = math.max(top, size.height - halfStroke);
    final double availableRadius = math.max(0, (bottom - top) / 2);
    final double r = math.min(
      math.max(0, radius - halfStroke),
      availableRadius,
    );
    final double reach = x + (r * .72);

    return Path()
      ..moveTo(reach, top)
      ..quadraticBezierTo(x, top, x, top + r)
      ..lineTo(x, bottom - r)
      ..quadraticBezierTo(x, bottom, reach, bottom);
  }

  @override
  void paint(Canvas canvas, Size size) {
    if (size.isEmpty) return;
    final Path path = _rail(size);

    // Soft aura stays behind the rail, but the solid 4px stroke is never
    // clipped. This matches the continuous curved side rail in the reference.
    canvas.drawPath(
      path,
      Paint()
        ..color = color.withAlpha(dark ? 48 : 32)
        ..style = PaintingStyle.stroke
        ..strokeWidth = UIConstants.accentStroke + 4
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
}
'''

text = text[:start] + new + text[end:]
MAIN.write_text(text, encoding='utf-8')
