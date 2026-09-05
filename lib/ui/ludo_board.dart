import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../game/ludo_engine.dart';
import 'game_palette.dart';

class LudoBoard extends StatelessWidget {
  const LudoBoard({
    super.key,
    required this.engine,
    required this.onTokenTap,
  });

  final LudoEngine engine;
  final ValueChanged<int> onTokenTap;

  static const List<(int, int)> _track = <(int, int)>[
    (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),
    (5, 6), (4, 6), (3, 6), (2, 6), (1, 6), (0, 6),
    (0, 7), (0, 8), (1, 8), (2, 8), (3, 8), (4, 8), (5, 8),
    (6, 9), (6, 10), (6, 11), (6, 12), (6, 13), (6, 14),
    (7, 14), (8, 14), (8, 13), (8, 12), (8, 11), (8, 10), (8, 9),
    (9, 8), (10, 8), (11, 8), (12, 8), (13, 8), (14, 8),
    (14, 7), (14, 6), (13, 6), (12, 6), (11, 6), (10, 6), (9, 6),
    (8, 5), (8, 4), (8, 3), (8, 2), (8, 1), (8, 0),
    (7, 0),
  ];

  static const Map<LudoColor, List<(int, int)>> _homeLanes = {
    LudoColor.red: [(7, 1), (7, 2), (7, 3), (7, 4), (7, 5)],
    LudoColor.green: [(1, 7), (2, 7), (3, 7), (4, 7), (5, 7)],
    LudoColor.yellow: [(7, 13), (7, 12), (7, 11), (7, 10), (7, 9)],
    LudoColor.blue: [(13, 7), (12, 7), (11, 7), (10, 7), (9, 7)],
  };

  @override
  Widget build(BuildContext context) {
    return AspectRatio(
      aspectRatio: 1,
      child: LayoutBuilder(
        builder: (context, constraints) {
          final size = math.min(constraints.maxWidth, constraints.maxHeight);
          final cell = size / 15;
          return ClipRRect(
            borderRadius: BorderRadius.circular(22),
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: GamePalette.cream,
                border: Border.all(color: Colors.white, width: 1.2),
              ),
              child: Stack(
                clipBehavior: Clip.none,
                children: [
                  Positioned.fill(
                    child: CustomPaint(
                      painter: _BoardPainter(activeColor: engine.currentColor),
                    ),
                  ),
                  for (final player in engine.players)
                    for (final token in player.tokens)
                      _buildToken(
                        player: player,
                        token: token,
                        cell: cell,
                      ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildToken({
    required LudoPlayer player,
    required LudoToken token,
    required double cell,
  }) {
    final center = _tokenCenter(player.color, token, cell);
    final tokenSize = cell * .78;
    final color = GamePalette.player(player.color);
    final isCurrent = engine.currentColor == player.color;
    final movable = isCurrent &&
        engine.awaitingMove &&
        engine.movableTokenIds.contains(token.id);

    return AnimatedPositioned(
      duration: const Duration(milliseconds: 360),
      curve: Curves.easeOutBack,
      left: center.dx - tokenSize / 2,
      top: center.dy - tokenSize / 2,
      width: tokenSize,
      height: tokenSize,
      child: Semantics(
        button: movable,
        enabled: movable,
        label: '${player.color.label} token ${token.id + 1}'
            '${movable ? ', tap to move' : ''}',
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTap: movable ? () => onTokenTap(token.id) : null,
          child: AnimatedScale(
            duration: const Duration(milliseconds: 190),
            curve: Curves.easeOutBack,
            scale: movable ? 1.22 : 1,
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 190),
              decoration: BoxDecoration(
                color: color,
                shape: BoxShape.circle,
                border: Border.all(
                  color: movable
                      ? Colors.white
                      : Colors.white.withValues(alpha: .78),
                  width: movable ? 2.8 : 1.8,
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: .25),
                    blurRadius: 4,
                    offset: const Offset(0, 2),
                  ),
                  if (movable)
                    BoxShadow(
                      color: color.withValues(alpha: .72),
                      blurRadius: 16,
                      spreadRadius: 3.5,
                    ),
                ],
              ),
              alignment: Alignment.center,
              child: FractionallySizedBox(
                widthFactor: .57,
                heightFactor: .57,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: Color.lerp(color, Colors.black, .14),
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: Colors.white.withValues(alpha: .6),
                      width: 1,
                    ),
                  ),
                  child: Center(
                    child: Text(
                      '${token.id + 1}',
                      style: TextStyle(
                        color: player.color == LudoColor.yellow
                            ? const Color(0xFF392E00)
                            : Colors.white,
                        fontWeight: FontWeight.w900,
                        fontSize: tokenSize * .27,
                      ),
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

  Offset _tokenCenter(LudoColor color, LudoToken token, double cell) {
    if (token.inYard) {
      final yard = _yardCell(color, token.id);
      return Offset((yard.$2 + .5) * cell, (yard.$1 + .5) * cell);
    }

    if (token.finished) {
      final base = switch (color) {
        LudoColor.red => const Offset(7.05, 7.5),
        LudoColor.green => const Offset(7.5, 7.05),
        LudoColor.yellow => const Offset(7.95, 7.5),
        LudoColor.blue => const Offset(7.5, 7.95),
      };
      final angle = (token.id * math.pi / 2) + math.pi / 4;
      final radius = cell * .17;
      return Offset(
        base.dx * cell + math.cos(angle) * radius,
        base.dy * cell + math.sin(angle) * radius,
      );
    }

    (int, int) boardCell;
    if (token.progress <= 51) {
      final global = (color.startIndex + token.progress) % 52;
      boardCell = _track[global];
    } else {
      final laneIndex = token.progress - 52;
      final lane = _homeLanes[color]!;
      final safeLaneIndex = laneIndex.clamp(0, lane.length - 1).toInt();
      boardCell = lane[safeLaneIndex];
    }

    var center = Offset(
      (boardCell.$2 + .5) * cell,
      (boardCell.$1 + .5) * cell,
    );

    final stacked = <LudoToken>[];
    for (final player in engine.players) {
      for (final other in player.tokens) {
        if (other.inYard || other.finished) continue;
        if (_sameBoardPosition(player.color, other, color, token)) {
          stacked.add(other);
        }
      }
    }
    if (stacked.length > 1) {
      final ownIndex = stacked.indexOf(token);
      final angle = (2 * math.pi * ownIndex) / stacked.length;
      final radius = cell * (stacked.length <= 2 ? .13 : .17);
      center += Offset(math.cos(angle), math.sin(angle)) * radius;
    }
    return center;
  }

  bool _sameBoardPosition(
    LudoColor aColor,
    LudoToken a,
    LudoColor bColor,
    LudoToken b,
  ) {
    if (identical(a, b)) return true;
    if (a.progress < 0 || b.progress < 0 || a.finished || b.finished) {
      return false;
    }
    if (a.progress <= 51 && b.progress <= 51) {
      return (aColor.startIndex + a.progress) % 52 ==
          (bColor.startIndex + b.progress) % 52;
    }
    return aColor == bColor && a.progress == b.progress;
  }

  (int, int) _yardCell(LudoColor color, int tokenId) {
    const offsets = <(int, int)>[(1, 1), (1, 4), (4, 1), (4, 4)];
    final base = switch (color) {
      LudoColor.red => (0, 0),
      LudoColor.green => (0, 9),
      LudoColor.yellow => (9, 9),
      LudoColor.blue => (9, 0),
    };
    final offset = offsets[tokenId];
    return (base.$1 + offset.$1, base.$2 + offset.$2);
  }
}

class _BoardPainter extends CustomPainter {
  const _BoardPainter({required this.activeColor});

  final LudoColor activeColor;
  static const List<(int, int)> _track = LudoBoard._track;

  @override
  void paint(Canvas canvas, Size size) {
    final cell = size.width / 15;

    canvas.drawRect(
      Offset.zero & size,
      Paint()..color = GamePalette.cream,
    );

    _paintYard(canvas, cell, const Rect.fromLTWH(0, 0, 6, 6), LudoColor.red);
    _paintYard(canvas, cell, const Rect.fromLTWH(9, 0, 6, 6), LudoColor.green);
    _paintYard(canvas, cell, const Rect.fromLTWH(9, 9, 6, 6), LudoColor.yellow);
    _paintYard(canvas, cell, const Rect.fromLTWH(0, 9, 6, 6), LudoColor.blue);

    final gridPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = math.max(.7, cell * .025)
      ..color = const Color(0x332B2B35);

    for (final pos in _track) {
      final rect = Rect.fromLTWH(pos.$2 * cell, pos.$1 * cell, cell, cell);
      canvas.drawRect(rect, Paint()..color = Colors.white);
      canvas.drawRect(rect, gridPaint);
    }

    _paintLane(canvas, cell, LudoColor.red);
    _paintLane(canvas, cell, LudoColor.green);
    _paintLane(canvas, cell, LudoColor.yellow);
    _paintLane(canvas, cell, LudoColor.blue);

    final startColors = <int, LudoColor>{
      0: LudoColor.red,
      13: LudoColor.green,
      26: LudoColor.yellow,
      39: LudoColor.blue,
    };
    for (final entry in startColors.entries) {
      final pos = _track[entry.key];
      final rect = Rect.fromLTWH(pos.$2 * cell, pos.$1 * cell, cell, cell);
      final color = GamePalette.player(entry.value);
      canvas.drawRect(rect.deflate(cell * .035), Paint()..color = color);
    }

    for (final index in LudoEngine.safeGlobalCells) {
      final pos = _track[index];
      final center = Offset((pos.$2 + .5) * cell, (pos.$1 + .5) * cell);
      final isStart = startColors.containsKey(index);
      _drawStar(
        canvas,
        center,
        cell * .22,
        isStart ? Colors.white : const Color(0xFF6D7185),
      );
    }

    final c = Offset(7.5 * cell, 7.5 * cell);
    final left = Offset(6 * cell, 7.5 * cell);
    final top = Offset(7.5 * cell, 6 * cell);
    final right = Offset(9 * cell, 7.5 * cell);
    final bottom = Offset(7.5 * cell, 9 * cell);
    _triangle(canvas, [left, top, c], GamePalette.red);
    _triangle(canvas, [top, right, c], GamePalette.green);
    _triangle(canvas, [right, bottom, c], GamePalette.yellow);
    _triangle(canvas, [bottom, left, c], GamePalette.blue);

    canvas.drawCircle(
      c,
      cell * .25,
      Paint()..color = Colors.white.withValues(alpha: .92),
    );
    _drawStar(canvas, c, cell * .15, const Color(0xFF6B5AF0));
  }

  void _paintYard(
    Canvas canvas,
    double cell,
    Rect gridRect,
    LudoColor colorKey,
  ) {
    final color = GamePalette.player(colorKey);
    final rect = Rect.fromLTWH(
      gridRect.left * cell,
      gridRect.top * cell,
      gridRect.width * cell,
      gridRect.height * cell,
    );
    final shade = Color.lerp(color, Colors.black, .13)!;
    final yardPaint = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: <Color>[color, shade],
      ).createShader(rect);
    canvas.drawRect(rect, yardPaint);

    if (activeColor == colorKey) {
      final glowPaint = Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = cell * .11
        ..color = Colors.white.withValues(alpha: .24);
      canvas.drawRect(rect.deflate(cell * .10), glowPaint);
    }

    final inner = rect.deflate(cell * .77);
    canvas.drawRRect(
      RRect.fromRectAndRadius(inner, Radius.circular(cell * .42)),
      Paint()..color = Colors.white.withValues(alpha: .97),
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(inner, Radius.circular(cell * .42)),
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = cell * .05
        ..color = color.withValues(alpha: .3),
    );
  }

  void _paintLane(Canvas canvas, double cell, LudoColor colorKey) {
    final laneColor = GamePalette.player(colorKey);
    for (final pos in LudoBoard._homeLanes[colorKey]!) {
      final rect = Rect.fromLTWH(pos.$2 * cell, pos.$1 * cell, cell, cell);
      canvas.drawRect(
        rect,
        Paint()..color = laneColor.withValues(alpha: .88),
      );
      canvas.drawRect(
        rect,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = math.max(.7, cell * .025)
          ..color = Colors.black.withValues(alpha: .13),
      );
    }
  }

  void _triangle(Canvas canvas, List<Offset> points, Color color) {
    final path = Path()
      ..moveTo(points[0].dx, points[0].dy)
      ..lineTo(points[1].dx, points[1].dy)
      ..lineTo(points[2].dx, points[2].dy)
      ..close();
    canvas.drawPath(path, Paint()..color = color);
  }

  void _drawStar(Canvas canvas, Offset center, double radius, Color color) {
    final path = Path();
    for (var i = 0; i < 10; i++) {
      final r = i.isEven ? radius : radius * .43;
      final angle = -math.pi / 2 + i * math.pi / 5;
      final point = Offset(
        center.dx + math.cos(angle) * r,
        center.dy + math.sin(angle) * r,
      );
      if (i == 0) {
        path.moveTo(point.dx, point.dy);
      } else {
        path.lineTo(point.dx, point.dy);
      }
    }
    path.close();
    canvas.drawPath(path, Paint()..color = color);
  }

  @override
  bool shouldRepaint(covariant _BoardPainter oldDelegate) =>
      oldDelegate.activeColor != activeColor;
}
