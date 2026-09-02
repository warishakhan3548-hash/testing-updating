import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  late String source;

  setUpAll(() {
    source = File('lib/main.dart').readAsStringSync();
  });

  group('global tap ripple gesture intent', () {
    test('defers pointer-down paint until tap intent is known', () {
      expect(
        source,
        contains('globalRippleIntentDelay = Duration(milliseconds: 48)'),
      );
      expect(source, contains('Timer? _startTimer;'));
      expect(
        source,
        contains('void scheduleStart(Duration delay, VoidCallback onDue)'),
      );
      expect(source, contains('bool prepareStart()'));
      expect(source, contains('void play()'));
      expect(
        source,
        contains(
          'pulse.scheduleStart(\n'
          '      UIConstants.globalRippleIntentDelay,\n'
          '      () => _startPulse(pulse),\n'
          '    );',
        ),
      );
    });

    test('pending pointer-down state never enters paint state', () {
      final int start = source.indexOf('void _handlePointerDown(');
      final int end = source.indexOf('void _handlePointerMove(', start);
      expect(start, greaterThanOrEqualTo(0));
      expect(end, greaterThan(start));

      final String handler = source.substring(start, end);
      expect(handler, contains('_livePulses.add(pulse);'));
      expect(handler, contains('_pointerPulses[event.pointer] = pulse;'));
      expect(handler, isNot(contains('_pulses.add(pulse);')));
      expect(handler, isNot(contains('setState(')));
    });

    test('promotion mutates only paint-owned state', () {
      final int start = source.indexOf('void _startPulse(');
      final int end = source.indexOf('void _handlePointerDown(', start);
      expect(start, greaterThanOrEqualTo(0));
      expect(end, greaterThan(start));

      final String handler = source.substring(start, end);
      expect(handler, contains('!_livePulses.contains(pulse)'));
      expect(handler, contains('!pulse.prepareStart()'));
      expect(handler, contains('_pulses.add(pulse);'));
      expect(handler, contains('pulse.play();'));
      expect(handler, isNot(contains('setState(')));
    });

    test('quick taps activate immediately on pointer release', () {
      final int start = source.indexOf('void _handlePointerUp(');
      final int end = source.indexOf('void _handlePointerCancel(', start);
      expect(start, greaterThanOrEqualTo(0));
      expect(end, greaterThan(start));

      final String handler = source.substring(start, end);
      expect(
        handler,
        contains(
          'final _RipplePulse? pulse = '
          '_pointerPulses.remove(event.pointer);',
        ),
      );
      expect(handler, contains('_startPulse(pulse);'));
    });

    test('scroll cancellation removes intent without widget rebuilds', () {
      final int layerStart = source.indexOf(
        'class _GlobalTapRippleLayerState',
      );
      final int layerEnd = source.indexOf(
        'class _GlobalTapRipplePainter extends CustomPainter',
        layerStart,
      );
      final String layer = source.substring(layerStart, layerEnd);

      expect(layer, isNot(contains('setState(')));
      expect(layer, isNot(contains('rebuild:')));
      expect(layer, contains('if (!pulse.cancel()) {'));
      expect(layer, contains('_removePulse(pulse);'));
    });

    test('uses one persistent paint plane and typed repaint signal', () {
      final int start = source.indexOf('class _RippleRepaintSignal');
      final int end = source.indexOf(
        'class _GlobalTapRipplePainter extends CustomPainter',
        start,
      );
      final String layer = source.substring(start, end);

      expect(
        layer,
        contains('class _RippleRepaintSignal extends ChangeNotifier'),
      );
      expect(
        layer,
        contains('void markNeedsPaint() => notifyListeners();'),
      );
      expect(
        layer,
        contains(
          'final _RippleRepaintSignal _rippleRepaint = '
          '_RippleRepaintSignal();',
        ),
      );
      expect(layer, contains('pulses: _pulses,'));
      expect(layer, contains('repaint: _rippleRepaint,'));
      expect(layer, contains('onTick: _rippleRepaint.markNeedsPaint,'));
      expect(layer, isNot(contains('Listenable.merge(')));
      expect(layer, isNot(contains('if (snapshot.isNotEmpty)')));
    });

    test('controller detaches repaint callback before disposal', () {
      final int start = source.indexOf('class _RipplePulse {');
      final int end = source.indexOf(
        'class _GlobalTapRippleLayerState',
        start,
      );
      final String pulse = source.substring(start, end);

      expect(pulse, contains('controller.addListener(_onTick);'));
      expect(pulse, contains('controller.removeListener(_onTick);'));
      expect(
        pulse.indexOf('controller.removeListener(_onTick);'),
        lessThan(pulse.indexOf('controller.dispose();')),
      );
    });

    test('ripple painter visual contract stays unchanged', () {
      final int start = source.indexOf(
        'class _GlobalTapRipplePainter extends CustomPainter',
      );
      final int end = source.indexOf(
        'class _AmbientBackground extends StatelessWidget',
        start,
      );
      expect(start, greaterThanOrEqualTo(0));
      expect(end, greaterThan(start));

      final String painter = source.substring(start, end);
      expect(
        painter,
        contains('final double radius = 6 + 48 * expansion;'),
      );
      expect(
        painter,
        contains('final int coreAlpha = (opacity * 31)'),
      );
      expect(
        painter,
        contains('final int haloAlpha = (opacity * 14)'),
      );
      expect(
        painter,
        contains('final int ringAlpha = (opacity * 112)'),
      );
    });
  });
}
