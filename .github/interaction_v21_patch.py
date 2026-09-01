from pathlib import Path
import re

path = Path('lib/main.dart')
code = path.read_text(encoding='utf-8')


def replace_once(old: str, new: str, label: str) -> None:
    global code
    count = code.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 match, found {count}')
    code = code.replace(old, new, 1)


# Dense, fast press physics without changing layout, color, or component sizes.
replace_once(
    '  static const Duration pressIn = Duration(milliseconds: 70);\n',
    '  static const Duration pressIn = Duration(milliseconds: 55);\n',
    'pressIn',
)
replace_once(
    '''  static const SpringDescription pressSpring = SpringDescription(\n    mass: 1,\n    stiffness: 520,\n    damping: 30,\n  );\n''',
    '''  static const SpringDescription pressSpring = SpringDescription(\n    mass: 1,\n    stiffness: 460,\n    damping: 32,\n  );\n''',
    'press spring',
)
replace_once('              : pressed * .012;\n', '              : pressed * .0145;\n', '3D tilt')
replace_once('            ..setEntry(3, 2, .0012)\n', '            ..setEntry(3, 2, .0013)\n', 'perspective')
replace_once('            offset: Offset(0, motion * 1.25),\n', '            offset: Offset(0, motion * 1.30),\n', 'press travel')
replace_once('              scale: 1 - (motion * .014),\n', '              scale: 1 - (motion * .017),\n', 'press compression')

# Replace the single-controller ripple with a pointer-aware two-pulse engine.
start = code.find('class _GlobalTapRippleLayerState extends State<_GlobalTapRippleLayer>')
end = code.find('class _AmbientBackground extends StatelessWidget {', start)
if start < 0 or end < 0 or end <= start:
    raise SystemExit('global ripple engine block not found')

new_engine = r'''class _RipplePulse {
  _RipplePulse({
    required this.pointer,
    required this.origin,
    required this.downPosition,
    required TickerProvider vsync,
  }) : controller = AnimationController(
         vsync: vsync,
         duration: const Duration(milliseconds: 200),
         reverseDuration: const Duration(milliseconds: 65),
       );

  final int pointer;
  final Offset origin;
  final Offset downPosition;
  final AnimationController controller;
  bool cancelled = false;
  bool disposed = false;

  void start() => controller.forward(from: 0);

  void cancel() {
    if (cancelled || disposed) return;
    cancelled = true;
    controller.animateBack(
      0,
      duration: const Duration(milliseconds: 65),
      curve: Curves.easeOutCubic,
    );
  }

  void dispose() {
    if (disposed) return;
    disposed = true;
    controller.dispose();
  }
}

class _GlobalTapRippleLayerState extends State<_GlobalTapRippleLayer>
    with TickerProviderStateMixin {
  static const double _scrollThreshold = 8;
  static const int _maxActivePulses = 2;

  final List<_RipplePulse> _pulses = <_RipplePulse>[];
  final Map<int, _RipplePulse> _pointerPulses = <int, _RipplePulse>{};

  void _handlePointerDown(PointerDownEvent event) {
    if (AppMotion.reduce(context)) return;

    final _RipplePulse? existing = _pointerPulses.remove(event.pointer);
    if (existing != null) _removePulse(existing, rebuild: false);

    while (_pulses.length >= _maxActivePulses) {
      _removePulse(_pulses.first, rebuild: false);
    }

    final _RipplePulse pulse = _RipplePulse(
      pointer: event.pointer,
      origin: event.localPosition,
      downPosition: event.position,
      vsync: this,
    );

    pulse.controller.addStatusListener((AnimationStatus status) {
      if (status == AnimationStatus.completed ||
          (pulse.cancelled && status == AnimationStatus.dismissed)) {
        _finishPulse(pulse);
      }
    });

    setState(() {
      _pulses.add(pulse);
      _pointerPulses[event.pointer] = pulse;
    });
    pulse.start();
  }

  void _handlePointerMove(PointerMoveEvent event) {
    final _RipplePulse? pulse = _pointerPulses[event.pointer];
    if (pulse == null || pulse.cancelled) return;

    if ((event.position - pulse.downPosition).distance > _scrollThreshold) {
      _pointerPulses.remove(event.pointer);
      pulse.cancel();
    }
  }

  void _handlePointerUp(PointerUpEvent event) {
    _pointerPulses.remove(event.pointer);
  }

  void _handlePointerCancel(PointerCancelEvent event) {
    final _RipplePulse? pulse = _pointerPulses.remove(event.pointer);
    pulse?.cancel();
  }

  void _finishPulse(_RipplePulse pulse) {
    if (!mounted || !_pulses.contains(pulse)) return;
    setState(() {
      _pulses.remove(pulse);
      if (_pointerPulses[pulse.pointer] == pulse) {
        _pointerPulses.remove(pulse.pointer);
      }
    });
    scheduleMicrotask(pulse.dispose);
  }

  void _removePulse(_RipplePulse pulse, {required bool rebuild}) {
    if (!_pulses.contains(pulse)) return;
    void remove() {
      _pulses.remove(pulse);
      if (_pointerPulses[pulse.pointer] == pulse) {
        _pointerPulses.remove(pulse.pointer);
      }
    }

    if (rebuild && mounted) {
      setState(remove);
    } else {
      remove();
    }
    pulse.dispose();
  }

  @override
  void dispose() {
    for (final _RipplePulse pulse in _pulses) {
      pulse.dispose();
    }
    _pulses.clear();
    _pointerPulses.clear();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    Widget surface = widget.child;
    if (_pulses.isNotEmpty) {
      final List<_RipplePulse> snapshot = List<_RipplePulse>.unmodifiable(
        _pulses,
      );
      final Listenable repaint = Listenable.merge(
        snapshot.map<Listenable>((_RipplePulse pulse) => pulse.controller).toList(),
      );
      surface = Stack(
        fit: StackFit.expand,
        children: <Widget>[
          widget.child,
          IgnorePointer(
            child: RepaintBoundary(
              child: CustomPaint(
                painter: _GlobalTapRipplePainter(
                  pulses: snapshot,
                  repaint: repaint,
                ),
              ),
            ),
          ),
        ],
      );
    }

    return Listener(
      behavior: HitTestBehavior.translucent,
      onPointerDown: _handlePointerDown,
      onPointerMove: _handlePointerMove,
      onPointerUp: _handlePointerUp,
      onPointerCancel: _handlePointerCancel,
      child: surface,
    );
  }
}

class _GlobalTapRipplePainter extends CustomPainter {
  _GlobalTapRipplePainter({
    required this.pulses,
    required Listenable repaint,
  }) : super(repaint: repaint);

  final List<_RipplePulse> pulses;

  @override
  void paint(Canvas canvas, Size size) {
    if (size.isEmpty) return;

    for (final _RipplePulse pulse in pulses) {
      if (pulse.disposed) continue;
      final double raw = pulse.controller.value.clamp(0.0, 1.0).toDouble();
      if (raw <= 0 || raw >= 1) continue;

      final double expansion = UIConstants.motionOut.transform(raw);
      final double arrival = Curves.easeOutCubic.transform(
        (raw / .16).clamp(0.0, 1.0).toDouble(),
      );
      final double fadeProgress = ((raw - .58) / .42)
          .clamp(0.0, 1.0)
          .toDouble();
      final double fade = 1 - Curves.easeInCubic.transform(fadeProgress);
      final double opacity = (arrival * fade).clamp(0.0, 1.0).toDouble();
      if (opacity <= 0) continue;

      final double radius = 6 + 48 * expansion;
      final Rect bounds = Rect.fromCircle(center: pulse.origin, radius: radius);
      final int coreAlpha = (opacity * 31).round().clamp(0, 255).toInt();
      final int haloAlpha = (opacity * 14).round().clamp(0, 255).toInt();
      final int ringAlpha = (opacity * 112).round().clamp(0, 255).toInt();

      canvas.drawCircle(
        pulse.origin,
        radius,
        Paint()
          ..shader = RadialGradient(
            colors: <Color>[
              appleBlue.withAlpha(coreAlpha),
              appleBlue.withAlpha(haloAlpha),
              Colors.transparent,
            ],
            stops: const <double>[0, .54, 1],
          ).createShader(bounds),
      );

      canvas.drawCircle(
        pulse.origin,
        radius * .86,
        Paint()
          ..color = appleBlue.withAlpha(ringAlpha)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.85 - expansion * .75,
      );

      if (!pulse.cancelled && raw > .18) {
        final double echo = ((raw - .18) / .64)
            .clamp(0.0, 1.0)
            .toDouble();
        if (echo < 1) {
          final int echoAlpha =
              (opacity * (1 - echo) * 58).round().clamp(0, 255).toInt();
          canvas.drawCircle(
            pulse.origin,
            5 + 26 * UIConstants.motionOut.transform(echo),
            Paint()
              ..color = appleBlue.withAlpha(echoAlpha)
              ..style = PaintingStyle.stroke
              ..strokeWidth = 1.2,
          );
        }
      }
    }
  }

  @override
  bool shouldRepaint(covariant _GlobalTapRipplePainter oldDelegate) => true;
}

'''

code = code[:start] + new_engine + code[end:]
path.write_text(code, encoding='utf-8')
