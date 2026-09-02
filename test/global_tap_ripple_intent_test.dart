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
        contains(
          'void scheduleStart(Duration delay, VoidCallback onDue)',
        ),
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
      expect(source, isNot(contains('    pulse.start();')));
    });

    test('pending pointer-down state never enters the paint list or rebuilds',
        () {
      final int start = source.indexOf('void _handlePointerDown(');
      final int end = source.indexOf('void _handlePointerMove(', start);

      expect(start, greaterThanOrEqualTo(0));
      expect(end, greaterThan(start));

      final String handler = source.substring(start, end);

      expect(handler, contains('_livePulses.add(pulse);'));
      expect(
        handler,
        contains('_pointerPulses[event.pointer] = pulse;'),
      );
      expect(handler, isNot(contains('_pulses.add(pulse);')));
      expect(handler, isNot(contains('setState(()')));
    });

    test('promotion performs one meaningful visible-state transition', () {
      final int start = source.indexOf('void _startPulse(');
      final int end = source.indexOf('void _handlePointerDown(', start);

      expect(start, greaterThanOrEqualTo(0));
      expect(end, greaterThan(start));

      final String handler = source.substring(start, end);

      expect(handler, contains('!_livePulses.contains(pulse)'));
      expect(handler, contains('!pulse.prepareStart()'));
      expect(
        RegExp(r'setState\(\(\) \{').allMatches(handler),
        hasLength(1),
      );
      expect(handler, contains('_pulses.add(pulse);'));
      expect(handler, contains('pulse.play();'));
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
      expect(handler, isNot(contains('pulse?.startNow();')));
    });

    test('pre-intent scroll and cancellation cause no rebuild', () {
      expect(source, contains('bool cancel()'));
      expect(source, contains('if (!_started) return false;'));
      expect(
        source,
        contains(
          'final List<_RipplePulse> _livePulses = <_RipplePulse>[];',
        ),
      );
      expect(
        source.split('_removePulse(pulse, rebuild: false);').length - 1,
        greaterThanOrEqualTo(3),
      );
      expect(source, contains('_startTimer?.cancel();'));

      final int moveStart = source.indexOf('void _handlePointerMove(');
      final int moveEnd = source.indexOf('void _handlePointerUp(', moveStart);
      final String moveHandler = source.substring(moveStart, moveEnd);
      expect(
        moveHandler,
        contains('_removePulse(pulse, rebuild: false);'),
      );
      expect(
        moveHandler,
        isNot(contains('_removePulse(pulse, rebuild: true);')),
      );

      final int cancelStart = source.indexOf('void _handlePointerCancel(');
      final int cancelEnd = source.indexOf('void _finishPulse(', cancelStart);
      final String cancelHandler = source.substring(cancelStart, cancelEnd);
      expect(
        cancelHandler,
        contains('_removePulse(pulse, rebuild: false);'),
      );
      expect(
        cancelHandler,
        isNot(contains('_removePulse(pulse, rebuild: true);')),
      );
    });

    test('animation ticks remain painter-driven rather than widget-driven', () {
      final int start = source.indexOf(
        'class _GlobalTapRippleLayerState',
      );
      final int end = source.indexOf(
        'class _GlobalTapRipplePainter extends CustomPainter',
        start,
      );

      expect(start, greaterThanOrEqualTo(0));
      expect(end, greaterThan(start));

      final String layer = source.substring(start, end);

      expect(layer, contains('RepaintBoundary('));
      expect(layer, contains('CustomPaint('));
      expect(layer, contains('repaint: Listenable.merge('));
      expect(
        layer,
        contains(
          '(_RipplePulse pulse) => pulse.controller',
        ),
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
