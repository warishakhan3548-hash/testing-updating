import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('premium micro-aesthetics remain surgical and semantic', () {
    final String source = File('lib/main.dart').readAsStringSync();

    // Three-frequency depth physics: contact, ambient and long falloff.
    expect(source, contains('spreadRadius: -2.2'));
    expect(source, contains('blurRadius: 44'));

    // Glass keeps a restrained top specular and opposing bottom lowlight.
    expect(source, contains('Colors.white.withAlpha(dark ? 64 : 176)'));
    expect(source, contains('Colors.black.withAlpha(dark ? 48 : 10)'));

    // Fintech actions retain the researched optical icon choices.
    expect(source, contains('Icons.ios_share_rounded'));
    expect(source, contains('size: micro ? 19 : 21.5'));
    expect(source, contains('Icons.delete_outline_rounded'));
    expect(source, isNot(contains('Icons.delete_rounded')));
    expect(source, contains('this.icon = Icons.add_rounded'));

    // Brand/state color logic and Firebase integration must stay untouched.
    expect(source, contains("import 'firebase_sync.dart';"));
    expect(source, contains('Firebase.initializeApp('));
    expect(
      source,
      contains('final List<Color> colors = _moduleTabColors(sync.state);'),
    );
  });
}

// This source guard intentionally lives in test/ so every future UI edit rechecks
// the premium depth/icon invariants together with the app's normal Flutter CI.
