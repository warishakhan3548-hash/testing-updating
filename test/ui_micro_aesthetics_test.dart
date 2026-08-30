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

    // Direct manipulation stays brief, tactile and accessibility-aware.
    expect(source, contains('Duration(milliseconds: 55)'));
    expect(
        source, contains('reverseDuration: const Duration(milliseconds: 180)'));
    expect(source, contains('offset: Offset(0, motion * 1.1)'));
    expect(source, contains('scale: 1 - (motion * .017)'));
    expect(source, contains('MediaQuery.of(context).disableAnimations'));

    // Navigation and pull-to-refresh keep the snappier feedback model.
    expect(source, contains('Duration(milliseconds: 250)'));
    expect(source, contains('RefreshIndicator.adaptive('));
    expect(source, contains('HapticFeedback.lightImpact();'));

    // Cross-system motion keeps auth handoffs calm and all route motion optional.
    expect(source, contains('class _RootStage extends StatelessWidget'));
    expect(
        source, contains('FadeTransition(opacity: animation, child: child)'));
    expect(
      source,
      contains('MediaQuery.maybeOf(context)?.disableAnimations ?? false'),
    );

    // Sheets, dialogs and toasts use explicit native AnimationStyle timings.
    expect(source, contains('sheetAnimationStyle: reduceMotion'));
    expect(source, contains('animationStyle: reduceMotion'));
    expect(source, contains('snackBarAnimationStyle: reduceMotion'));
    expect(source, contains('duration: Duration(milliseconds: 240)'));
    expect(source, contains('reverseDuration: Duration(milliseconds: 190)'));

    // Destructive confirmation defaults keyboard focus to the safe action.
    expect(source, contains('autofocus: dangerous'));
    expect(source, contains('autofocus: !dangerous'));

    // Card accent rail stays fully inside the clip and remains uninterrupted.
    expect(
      source,
      contains('final double inset = UIConstants.accentStroke / 2 + 3;'),
    );
    expect(source, contains('final double reach = math.min(6.5'));
    expect(source, contains('..lineTo(inset, lowerTurn)'));
    expect(source, isNot(contains('..lineTo(0, size.height - r)')));

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
// the premium depth, icon, motion, accessibility and safety invariants together.
