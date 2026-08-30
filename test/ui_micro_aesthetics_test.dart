import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('premium micro-aesthetics remain surgical and semantic', () {
    final String source = File('lib/main.dart').readAsStringSync();

    // Multi-frequency depth physics: contact, key, ambient and themed light.
    expect(source, contains('spreadRadius: -1.25'));
    expect(source, contains('blurRadius: 52'));
    expect(source, contains('withAlpha(dark ? 34 : 9)'));
    expect(source, contains("const Color(0xFF172033)"));
    expect(source, contains('color.computeLuminance()'));
    expect(source, contains('static List<BoxShadow> pressGlow('));
    expect(source, contains('final Color? resolvedGlowColor ='));
    expect(source, contains('shadowColor ?? tintColor ?? accentColor'));
    expect(source, contains('blurRadius: strong ? 16 : 14'));
    expect(source, contains('spreadRadius: strong ? -1.25 : -1.5'));
    expect(source, contains('blurRadius: strong ? 28 : 24'));
    expect(source, contains('spreadRadius: strong ? -7 : -6'));

    // Glass uses one continuous clipped face and one foreground edge, avoiding
    // short highlight strips that visually chop rounded corners.
    expect(source, contains('Colors.white.withAlpha(dark ? 15 : 31)'));
    expect(source, contains('Colors.black.withAlpha(dark ? 22 : 7)'));
    expect(source, contains('position: DecorationPosition.foreground'));
    expect(source, isNot(contains('Colors.white.withAlpha(dark ? 82 : 198)')));
    expect(source, isNot(contains('Colors.black.withAlpha(dark ? 58 : 14)')));
    expect(
      RegExp(r'GridView\.count\([\s\S]*?clipBehavior: Clip\.none,')
          .allMatches(source),
      hasLength(2),
    );

    // Base card fills remain byte-for-byte unchanged by the depth treatment.
    expect(source, contains('Color(0xFAFFFFFF), Color(0xF2FFFFFF)'));
    expect(source, contains('Color(0xF0121826), Color(0xE3080C18)'));

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
    expect(
      source,
      contains('class _DeleteActionButton extends StatelessWidget'),
    );
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
    expect(source, contains("import 'package:flutter/physics.dart';"));
    expect(source, contains('static const SpringDescription pressSpring'));
    expect(source, contains('stiffness: 520'));
    expect(source, contains('damping: 30'));
    expect(source, contains('SpringSimulation('));
    expect(source, contains('_pressController.velocity'));
    expect(source, contains('feedback.clamp(0.0, 1.0).toDouble()'));
    expect(source, contains('offset: Offset(0, motion * 1.25)'));
    expect(source, contains('scale: 1 - (motion * .014)'));
    expect(source, contains('_touchAlignment = Alignment(x, y)'));
    expect(source, contains('..setEntry(3, 2, .0012)'));
    expect(source, contains('..rotateX(-_touchAlignment.y * cardTilt)'));
    expect(source, contains('..rotateY(_touchAlignment.x * cardTilt)'));
    expect(source, contains('gradient: RadialGradient('));
    expect(source, contains('HapticFeedback.lightImpact();'));
    expect(source, contains('abstract final class AppMotion'));
    expect(
      source,
      contains('MediaQuery.maybeDisableAnimationsOf(context) ?? false'),
    );
    expect(source, contains('!reduce(context) && TickerMode.of(context)'));
    expect(source, isNot(contains('.disableAnimations ?? false')));
    expect(source, contains('oldWidget.onTap != null && widget.onTap == null'));
    expect(source, contains('this.feedbackColor'));
    expect(source, contains('feedbackColor: color'));
    expect(source, contains('feedbackColor: diaryOrange'));

    // Dashboard cards reveal once with a short, direction-neutral stagger.
    // Data-driven list rows deliberately avoid repeated decorative motion.
    expect(source, contains('static const Duration dashboardReveal'));
    expect(source, contains('Duration(milliseconds: 520)'));
    expect(source, contains('class DashboardScreen extends StatefulWidget'));
    expect(
      source,
      contains('class _DashboardCardReveal extends StatelessWidget'),
    );
    expect(
      source,
      contains('final double start = math.min(order * .06, .30).toDouble()'),
    );
    expect(source, contains('begin: const Offset(0, .045)'));
    expect(source, contains('child: RepaintBoundary(child: child)'));
    expect(source, contains('_revealController.value = 1'));
    expect(source, contains('WidgetsBinding.instance.addPostFrameCallback'));
    expect(source, contains('_revealScheduled = false'));

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
      source,
      contains('FadeTransition(opacity: animation, child: child)'),
    );
    expect(
      source,
      contains('final bool reduceMotion = AppMotion.reduce(context)'),
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
