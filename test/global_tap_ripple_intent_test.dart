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
      expect(source, contains('void scheduleStart(Duration delay)'));
      expect(
        source,
        contains('pulse.scheduleStart(UIConstants.globalRippleIntentDelay);'),
      );
      expect(source, isNot(contains('    pulse.start();')));
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
          'final _RipplePulse? pulse = _pointerPulses.remove(event.pointer);',
        ),
      );
      expect(handler, contains('pulse?.startNow();'));
    });

    test('scroll and cancellation discard pending invisible pulses', () {
      expect(source, contains('bool cancel()'));
      expect(source, contains('if (!_started) return false;'));
      expect(source, contains('if (pulse != null && !pulse.cancel()) {'));
      expect(
        source.split('_removePulse(pulse, rebuild: true);').length - 1,
        greaterThanOrEqualTo(2),
      );
      expect(source, contains('_startTimer?.cancel();'));
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
      expect(painter, contains('final double radius = 6 + 48 * expansion;'));
      expect(painter, contains('final int coreAlpha = (opacity * 31)'));
      expect(painter, contains('final int haloAlpha = (opacity * 14)'));
      expect(painter, contains('final int ringAlpha = (opacity * 112)'));
    });
  });
}
