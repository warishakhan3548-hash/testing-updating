import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../game/ludo_engine.dart';

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
                color: Colors.white,
                border: Border.all(color: Colors.black12, width: 1.2),
              ),
              child: Stack(
                children: [
                  Positioned.fill(child: CustomPaint(painter: _BoardPainter())),
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
    final tokenSize = cell * .68;
    final isCurrent = engine.currentColor == player.color;
    final movable = isCurrent &&
        engine.awaitingMove &&
        engine.movableTokenIds.contains(token.id);

    return AnimatedPositioned(
      duration: const Duration(milliseconds: 320),
      curve: Curves.easeOutBack,
      left: center.dx - tokenSize / 2,
      top: center.dy - tokenSize / 2,
      width: tokenSize,
      height: tokenSize,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: movable ? () => onTokenTap(token.id) : null,
        child: AnimatedScale(
          duration: const Duration(milliseconds: 180),
          scale: movable ? 1.18 : 1,
          child: Container(
            decoration: BoxDecoration(
              color: _color(player.color),
              shape: BoxShape.circle,
              border: Border.all(
                color: movable ? Colors.white : Colors.black.withValues(alpha: .22),
                width: movable ? 3 : 1.5,
              ),
              boxShadow: [
                BoxShadow(
                  color: _color(player.color).withValues(alpha: movable ? .55 : .28),
                  blurRadius: movable ? 13 : 5,
                  spreadRadius: movable ? 3 : 0,
                ),
              ],
            ),
            alignment: Alignment.center,
            child: Text(
              '${token.id + 1}',
              style: TextStyle(
                color: player.color == LudoColor.yellow ? Colors.black87 : Colors.white,
                fontWeight: FontWeight.w900,
                fontSize: tokenSize * .36,
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
      final radius = cell * .16;
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
      boardCell = lane[laneIndex.clamp(0, lane.length - 1)];
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
      center += Offset(math.cos(angle), math.sin(angle)) * (cell * .14);
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
    if (a.progress < 0 || b.progress < 0 || a.finished || b.finished) return false;
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

  static Color _color(LudoColor color) => switch (color) {
        LudoColor.red => const Color(0xFFE84343),
        LudoColor.green => const Color(0xFF2CB76F),
        LudoColor.yellow => const Color(0xFFF4C542),
        LudoColor.blue => const Color(0xFF3978E8),
      };
}

class _BoardPainter extends CustomPainter {
  static const List<(int, int)> _track = LudoBoard._track;

  @override
  void paint(Canvas canvas, Size size) {
    final cell = size.width / 15;
    final gridPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = .8
      ..color = Colors.black.withValues(alpha: .16);

    _paintYard(canvas, cell, const Rect.fromLTWH(0, 0, 6, 6), const Color(0xFFE84343));
    _paintYard(canvas, cell, const Rect.fromLTWH(9, 0, 6, 6), const Color(0xFF2CB76F));
    _paintYard(canvas, cell, const Rect.fromLTWH(9, 9, 6, 6), const Color(0xFFF4C542));
    _paintYard(canvas, cell, const Rect.fromLTWH(0, 9, 6, 6), const Color(0xFF3978E8));

    for (final pos in _track) {
      final rect = Rect.fromLTWH(pos.$2 * cell, pos.$1 * cell, cell, cell);
      canvas.drawRect(rect, Paint()..color = Colors.white);
      canvas.drawRect(rect, gridPaint);
    }

    _paintLane(canvas, cell, LudoColor.red, const Color(0xFFE84343));
    _paintLane(canvas, cell, LudoColor.green, const Color(0xFF2CB76F));
    _paintLane(canvas, cell, LudoColor.yellow, const Color(0xFFF4C542));
    _paintLane(canvas, cell, LudoColor.blue, const Color(0xFF3978E8));

    final startColors = <int, Color>{
      0: const Color(0xFFE84343),
      13: const Color(0xFF2CB76F),
      26: const Color(0xFFF4C542),
      39: const Color(0xFF3978E8),
    };
    for (final entry in startColors.entries) {
      final pos = _track[entry.key];
      final rect = Rect.fromLTWH(pos.$2 * cell, pos.$1 * cell, cell, cell);
      canvas.drawRect(rect.deflate(1.2), Paint()..color = entry.value.withValues(alpha: .88));
    }

    for (final index in LudoEngine.safeGlobalCells) {
      final pos = _track[index];
      final center = Offset((pos.$2 + .5) * cell, (pos.$1 + .5) * cell);
      canvas.drawCircle(
        center,
        cell * .13,
        Paint()..color = Colors.black.withValues(alpha: .22),
      );
    }

    final c = Offset(7.5 * cell, 7.5 * cell);
    final left = Offset(6 * cell, 7.5 * cell);
    final top = Offset(7.5 * cell, 6 * cell);
    final right = Offset(9 * cell, 7.5 * cell);
    final bottom = Offset(7.5 * cell, 9 * cell);
    _triangle(canvas, [left, top, c], const Color(0xFFE84343));
    _triangle(canvas, [top, right, c], const Color(0xFF2CB76F));
    _triangle(canvas, [right, bottom, c], const Color(0xFFF4C542));
    _triangle(canvas, [bottom, left, c], const Color(0xFF3978E8));
  }

  void _paintYard(Canvas canvas, double cell, Rect gridRect, Color color) {
    final rect = Rect.fromLTWH(
      gridRect.left * cell,
      gridRect.top * cell,
      gridRect.width * cell,
      gridRect.height * cell,
    );
    canvas.drawRect(rect, Paint()..color = color.withValues(alpha: .88));
    final inner = rect.deflate(cell * .82);
    canvas.drawRRect(
      RRect.fromRectAndRadius(inner, Radius.circular(cell * .35)),
      Paint()..color = Colors.white,
    );
  }

  void _paintLane(Canvas canvas, double cell, LudoColor color, Color laneColor) {
    for (final pos in LudoBoard._homeLanes[color]!) {
      final rect = Rect.fromLTWH(pos.$2 * cell, pos.$1 * cell, cell, cell);
      canvas.drawRect(rect, Paint()..color = laneColor.withValues(alpha: .82));
      canvas.drawRect(
        rect,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = .8
          ..color = Colors.black.withValues(alpha: .16),
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

  @override
  bool shouldRepaint(covariant _BoardPainter oldDelegate) => false;
}
