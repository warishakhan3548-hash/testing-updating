import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('premium micro-aesthetics remain surgical and semantic', () {
    final String source = File('lib/main.dart').readAsStringSync();

    // Three-frequency depth physics: contact, ambient and long falloff.
    expect(source, contains('spreadRadius: -1.5'));
    expect(source, contains('blurRadius: 44'));
    expect(source, contains('withAlpha(dark ? 32 : 8)'));
    expect(source, contains("const Color(0xFF172033)"));

    // Glass keeps a restrained top specular and opposing bottom lowlight.
    expect(source, contains('Colors.white.withAlpha(dark ? 64 : 176)'));
    expect(source, contains('Colors.black.withAlpha(dark ? 48 : 10)'));

    // The icon family stays semantic, optically consistent and platform-native.
    expect(source, contains('Icons.share_rounded'));
    expect(source, contains('Icons.water_drop_rounded'));
    expect(source, contains('Icons.water_drop_outlined'));
    expect(source, contains('Icons.handshake_rounded'));
    expect(source, contains('Icons.handshake_outlined'));
    expect(source, contains('Icons.payments_rounded'));
    expect(source, contains('Icons.payments_outlined'));
    expect(source, contains('Icons.auto_stories_rounded'));
    expect(source, contains('Icons.auto_stories_outlined'));
    expect(source, contains('Icons.storefront_rounded'));
    expect(source, contains('Icons.storefront_outlined'));
    expect(source, contains('Icons.picture_as_pdf_rounded'));
    expect(source, contains('color: exportIndigo'));
    expect(source, contains('Icons.space_dashboard_rounded'));
    expect(source, contains('Icons.space_dashboard_outlined'));
    expect(source, contains('Icons.shopping_bag_rounded'));
    expect(source, contains('Icons.shopping_bag_outlined'));
    expect(source, isNot(contains('Icons.receipt_long_rounded')));
    expect(source, isNot(contains('Icons.ios_share_rounded')));
    expect(source, isNot(contains('Icons.local_drink_rounded')));
    expect(source, isNot(contains('Icons.volunteer_activism_rounded')));
    expect(source, isNot(contains('class _BottomNavGlyphPainter')));
    expect(source, contains('size: micro ? 19 : 21.5'));
    expect(source, contains('const IconData premiumDeleteIcon'));
    expect(source, contains('class _DeleteActionButton extends StatelessWidget'));
    expect(
      RegExp(r'Icons\.delete_outline_rounded').allMatches(source),
      hasLength(1),
    );
    expect(source, isNot(contains('Icons.delete_forever_rounded')));
    expect(source, contains('color: appleRed'));
    expect(source, isNot(contains('Icons.delete_rounded')));
    expect(source, contains('this.icon = Icons.add_rounded'));

    // Direct manipulation stays brief, tactile and accessibility-aware.
    expect(source, contains('Duration pressIn = Duration(milliseconds: 70)'));
    expect(source, contains('Duration pressOut = Duration(milliseconds: 210)'));
    expect(source, contains('curve: UIConstants.motionOut'));
    expect(source, contains('lowerBound: -.18'));
    expect(source, contains('Cubic(0.34, 1.42, 0.64, 1)'));
    expect(source, contains('feedback.clamp(0.0, 1.0).toDouble()'));
    expect(source, contains('offset: Offset(0, motion * 1.1)'));
    expect(source, contains('scale: 1 - (motion * .018)'));
    expect(source, contains('MediaQuery.of(context).disableAnimations'));

    // The dashboard AI entry reads as a real, labeled premium control.
    expect(source, contains('class _AiHubButton extends StatelessWidget'));
    expect(source, contains("semanticLabel: 'Open AI Hub'"));
    expect(source, contains("'AI HUB'"));
    expect(source, contains('Color(0xFF7957E8)'));

    // Navigation and pull-to-refresh keep the snappier feedback model.
    expect(source, contains('duration: UIConstants.motion'));
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
    expect(source, contains('duration: UIConstants.routeIn'));
    expect(source, contains('reverseDuration: UIConstants.routeOut'));

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
