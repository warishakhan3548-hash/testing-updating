import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Android touch refresh boost is API-gated and policy-driven', () {
    final String source = File(
      'android/app/src/main/kotlin/com/aaris/diary/financial/MainActivity.kt',
    ).readAsStringSync();

    expect(source, contains('Build.VERSION.SDK_INT >= 35'));
    expect(
      source,
      contains('window.setFrameRateBoostOnTouchEnabled(true)'),
    );

    // Do not force a fixed refresh rate or display mode. Android keeps
    // authority over the actual panel rate and power policy.
    expect(source, isNot(contains('preferredRefreshRate')));
    expect(source, isNot(contains('preferredDisplayModeId')));
    expect(source, isNot(contains('setFrameRate(')));
  });
}
