from __future__ import annotations

import re
from pathlib import Path

TARGET = Path("lib/main.dart")

PREMIUM_WIDGET = r'''class _PremiumShareButton extends StatelessWidget {
  const _PremiumShareButton({
    required this.onTap,
    this.label = 'Share',
    this.icon = Icons.ios_share_rounded,
    this.color = appleBlue,
    this.semanticLabel,
    this.compact = false,
  });

  final String label;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;
  final String? semanticLabel;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final double viewportWidth = MediaQuery.sizeOf(context).width;
    final bool iconOnly = compact && viewportWidth < 390;
    final bool micro = compact && viewportWidth < 340;
    final double height = micro ? 48 : (compact ? 50 : 54);
    final double width = iconOnly ? height : (compact ? 104 : 138);
    final double radius = height * .44;
    final Color neon =
        Color.lerp(const Color(0xFF00E8FF), color, .24) ?? const Color(0xFF19D8FF);
    final Color neonSoft =
        Color.lerp(Colors.white, neon, .62) ?? const Color(0xFF9BF5FF);

    return Transform.rotate(
      angle: compact ? -0.018 : -0.022,
      child: _Pressable(
        onTap: onTap,
        semanticLabel: semanticLabel ?? label,
        borderRadius: BorderRadius.circular(radius + 2),
        child: Container(
          width: width,
          height: height,
          padding: const EdgeInsets.all(2),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(radius + 2),
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: <Color>[
                Color(0xFFD0DBE3),
                Color(0xFF596B78),
                Color(0xFF22313D),
                Color(0xFF8396A4),
                Color(0xFF263642),
                Color(0xFFC0D2DE),
              ],
              stops: <double>[0, .16, .38, .58, .78, 1],
            ),
            border: Border.all(color: Colors.white.withAlpha(105), width: .7),
            boxShadow: <BoxShadow>[
              BoxShadow(
                color: neon.withAlpha(compact ? 62 : 82),
                blurRadius: compact ? 16 : 24,
                spreadRadius: compact ? 0 : 1,
                offset: Offset.zero,
              ),
              BoxShadow(
                color: Colors.black.withAlpha(92),
                blurRadius: 16,
                offset: const Offset(0, 7),
              ),
            ],
          ),
          child: Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(radius),
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: <Color>[
                  Color(0xFF0B2638),
                  Color(0xFF071722),
                  Color(0xFF092B3E),
                  Color(0xFF06121B),
                ],
                stops: <double>[0, .34, .7, 1],
              ),
              border: Border.all(color: neon.withAlpha(205), width: 1),
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(radius - 1),
              child: Stack(
                fit: StackFit.expand,
                children: <Widget>[
                  CustomPaint(
                    painter: _PremiumShareCircuitPainter(color: neon),
                  ),
                  Positioned(
                    left: 9,
                    right: 9,
                    top: 3,
                    height: 1,
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: <Color>[
                            Colors.transparent,
                            neonSoft.withAlpha(138),
                            Colors.transparent,
                          ],
                        ),
                      ),
                    ),
                  ),
                  Padding(
                    padding: EdgeInsets.symmetric(
                      horizontal: iconOnly ? 7 : (compact ? 8 : 10),
                    ),
                    child: iconOnly
                        ? Center(
                            child: _PremiumShareGlyph(
                              icon: icon,
                              neon: neon,
                              size: micro ? 29 : 31,
                            ),
                          )
                        : Row(
                            mainAxisSize: MainAxisSize.min,
                            children: <Widget>[
                              _PremiumShareGlyph(
                                icon: icon,
                                neon: neon,
                                size: compact ? 30 : 34,
                              ),
                              SizedBox(width: compact ? 6 : 8),
                              Expanded(
                                child: Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: <Widget>[
                                    FittedBox(
                                      fit: BoxFit.scaleDown,
                                      alignment: Alignment.centerLeft,
                                      child: Text(
                                        label.toUpperCase(),
                                        maxLines: 1,
                                        style: TextStyle(
                                          color: const Color(0xFFEAFDFF),
                                          fontSize: compact ? 12.5 : 15.5,
                                          height: 1,
                                          fontWeight: FontWeight.w900,
                                          letterSpacing: compact ? .15 : .45,
                                          shadows: <Shadow>[
                                            Shadow(
                                              color: neon.withAlpha(118),
                                              blurRadius: 9,
                                            ),
                                          ],
                                        ),
                                      ),
                                    ),
                                    if (!compact) ...<Widget>[
                                      const SizedBox(height: 3),
                                      FittedBox(
                                        fit: BoxFit.scaleDown,
                                        alignment: Alignment.centerLeft,
                                        child: Text(
                                          'DISTRIBUTE | CONNECT',
                                          maxLines: 1,
                                          style: TextStyle(
                                            color: neonSoft,
                                            fontSize: 7.2,
                                            height: 1,
                                            fontWeight: FontWeight.w800,
                                            letterSpacing: .18,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ],
                                ),
                              ),
                            ],
                          ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _PremiumShareGlyph extends StatelessWidget {
  const _PremiumShareGlyph({
    required this.icon,
    required this.neon,
    required this.size,
  });

  final IconData icon;
  final Color neon;
  final double size;

  @override
  Widget build(BuildContext context) => Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(size * .31),
          gradient: const LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: <Color>[Color(0xFF0E4771), Color(0xFF082235)],
          ),
          border: Border.all(color: neon.withAlpha(210), width: .8),
          boxShadow: <BoxShadow>[
            BoxShadow(
              color: neon.withAlpha(90),
              blurRadius: 10,
              spreadRadius: .2,
            ),
          ],
        ),
        child: Icon(
          icon,
          color: const Color(0xFFE8FCFF),
          size: size * .54,
          shadows: <Shadow>[
            Shadow(color: neon.withAlpha(180), blurRadius: 8),
          ],
        ),
      );
}

class _PremiumShareCircuitPainter extends CustomPainter {
  const _PremiumShareCircuitPainter({required this.color});

  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final Paint trace = Paint()
      ..color = color.withAlpha(42)
      ..strokeWidth = .8
      ..style = PaintingStyle.stroke;
    final Paint node = Paint()..color = color.withAlpha(95);

    final Path lower = Path()
      ..moveTo(size.width * .48, size.height * .78)
      ..lineTo(size.width * .61, size.height * .78)
      ..lineTo(size.width * .67, size.height * .66)
      ..lineTo(size.width * .85, size.height * .66)
      ..lineTo(size.width * .9, size.height * .56)
      ..lineTo(size.width * .98, size.height * .56);
    canvas.drawPath(lower, trace);

    final Path upper = Path()
      ..moveTo(size.width * .56, size.height * .18)
      ..lineTo(size.width * .69, size.height * .18)
      ..lineTo(size.width * .74, size.height * .29)
      ..lineTo(size.width * .91, size.height * .29);
    canvas.drawPath(upper, trace);

    for (final Offset point in <Offset>[
      Offset(size.width * .61, size.height * .78),
      Offset(size.width * .67, size.height * .66),
      Offset(size.width * .85, size.height * .66),
      Offset(size.width * .69, size.height * .18),
      Offset(size.width * .74, size.height * .29),
    ]) {
      canvas.drawCircle(point, 1.15, node);
    }

    final Rect sheen = Rect.fromLTWH(0, 0, size.width, size.height * .52);
    canvas.drawRect(
      sheen,
      Paint()
        ..shader = LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: <Color>[
            Colors.white.withAlpha(31),
            Colors.white.withAlpha(7),
            Colors.transparent,
          ],
          stops: const <double>[0, .46, 1],
        ).createShader(sheen),
    );
  }

  @override
  bool shouldRepaint(covariant _PremiumShareCircuitPainter oldDelegate) =>
      oldDelegate.color != color;
}
'''


def fail(message: str) -> None:
    raise SystemExit(f"premium_share_patch: {message}")


def main() -> None:
    if not TARGET.exists():
        fail(f"missing {TARGET}")

    text = TARGET.read_text(encoding="utf-8")

    # Idempotent guard for CI re-runs.
    if "class _PremiumShareButton extends StatelessWidget" in text:
        forbidden = (
            "class _MilkShareAction extends StatelessWidget",
            "_MilkShareAction(",
        )
        leftovers = [token for token in forbidden if token in text]
        if leftovers:
            fail(f"partial migration detected: {leftovers}")
        if re.search(
            r"_MiniAction\(\s*label:\s*'Share'\s*,\s*icon:\s*Icons\.ios_share_rounded",
            text,
        ):
            fail("legacy mini share action remains")
        if re.search(
            r"_CircleAction\(\s*icon:\s*Icons\.ios_share_rounded",
            text,
        ):
            fail("legacy circle share action remains")
        print("premium_share_patch: already applied")
        return

    milk_pattern = re.compile(r"(?m)^(?P<indent>\s*)_MilkShareAction\(")
    text, milk_count = milk_pattern.subn(
        lambda match: f"{match.group('indent')}_PremiumShareButton(",
        text,
    )
    if milk_count != 1:
        fail(f"expected 1 milk share action, found {milk_count}")

    mini_pattern = re.compile(
        r"_MiniAction\(\n(?P<indent>\s*)(?=label:\s*'Share'\s*,\n\s*icon:\s*Icons\.ios_share_rounded)"
    )
    text, mini_count = mini_pattern.subn(
        lambda match: f"_PremiumShareButton(\n{match.group('indent')}",
        text,
    )
    if mini_count != 4:
        fail(f"expected 4 mini share actions, found {mini_count}")

    circle_pattern = re.compile(
        r"_CircleAction\(\n(?P<indent>\s*)(?=icon:\s*Icons\.ios_share_rounded)"
    )
    text, circle_count = circle_pattern.subn(
        lambda match: (
            "_PremiumShareButton(\n"
            f"{match.group('indent')}compact: true,\n"
            f"{match.group('indent')}"
        ),
        text,
    )
    if circle_count != 2:
        fail(f"expected 2 compact circle share actions, found {circle_count}")

    old_class_pattern = re.compile(
        r"class _MilkShareAction extends StatelessWidget \{.*?\n\}\n\n(?=class _MilkRecordsTable extends StatelessWidget)",
        re.DOTALL,
    )
    text, class_count = old_class_pattern.subn(PREMIUM_WIDGET + "\n\n", text)
    if class_count != 1:
        fail(f"expected 1 legacy milk share widget class, found {class_count}")

    if "class _MilkShareAction extends StatelessWidget" in text or "_MilkShareAction(" in text:
        fail("legacy milk share UI was not fully removed")
    if re.search(
        r"_MiniAction\(\s*label:\s*'Share'\s*,\s*icon:\s*Icons\.ios_share_rounded",
        text,
    ):
        fail("legacy mini share UI remains after migration")
    if re.search(r"_CircleAction\(\s*icon:\s*Icons\.ios_share_rounded", text):
        fail("legacy circle share UI remains after migration")

    premium_calls = len(re.findall(r"(?m)^\s*_PremiumShareButton\(", text))
    if premium_calls != 7:
        fail(f"expected 7 premium share call sites, found {premium_calls}")

    TARGET.write_text(text, encoding="utf-8")
    print(
        "premium_share_patch: migrated 7 share actions "
        "(1 milk, 4 section, 2 compact)"
    )


if __name__ == "__main__":
    main()
