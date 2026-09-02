import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('premium micro-aesthetics remain surgical and semantic', () {
    final String source = File('lib/main.dart').readAsStringSync();
    final String manifest = File('pubspec.yaml').readAsStringSync();

    // Multi-frequency depth physics: contact, key, ambient and themed light.
    expect(source, contains('spreadRadius: -1.25'));
    expect(source, contains('blurRadius: 52'));
    expect(source, contains('withAlpha(dark ? 76 : 22)'));
    expect(source, contains('withAlpha(dark ? 56 : 18)'));
    expect(source, contains('withAlpha(dark ? 40 : 12)'));
    expect(source, contains("const Color(0xFF172033)"));
    expect(source, contains('color.computeLuminance()'));
    expect(source, contains('static List<BoxShadow> pressGlow('));
    expect(source, contains('final Color? resolvedGlowColor ='));
    expect(source, contains('shadowColor ?? tintColor ?? accentColor'));
    expect(source, contains('blurRadius: strong ? 16 : 14'));
    expect(source, contains('spreadRadius: strong ? -1.25 : -1.5'));
    expect(source, contains('blurRadius: strong ? 28 : 24'));
    expect(source, contains('spreadRadius: strong ? -7 : -6'));

    // The app mark is the website's exact Font Awesome 6.6 solid leaf path.
    expect(source, contains('class _FontAwesomeLeafPainter'));
    expect(source, contains('..moveTo(272, 96)'));
    expect(source, contains('..cubicTo(455.9, 72.1, 418.7, 96, 376, 96)'));
    expect(source, contains('dimension: size * .52'));
    expect(source, isNot(contains('Icons.eco_rounded')));

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
    expect(source, contains('Duration pressIn = Duration(milliseconds: 55)'));
    expect(
      source,
      contains('Duration pressReengageFloor = Duration(milliseconds: 24)'),
    );
    expect(source, contains('Duration pressOut = Duration(milliseconds: 210)'));
    expect(source, contains('curve: UIConstants.motionOut'));
    expect(source, contains('lowerBound: -.18'));
    expect(source, contains("import 'package:flutter/physics.dart';"));
    expect(source, contains('static const SpringDescription pressSpring'));
    expect(source, contains('stiffness: 460'));
    expect(source, contains('damping: 32'));
    expect(source, contains('SpringSimulation('));
    expect(source, contains('_pressController.velocity'));
    expect(source, contains('feedback.clamp(0.0, 1.0).toDouble()'));
    expect(source, contains('offset: Offset(0, motion * 1.30)'));
    expect(source, contains('scale: 1 - (motion * .017)'));
    expect(source, contains('_touchAlignment = nextAlignment'));
    expect(source, contains('..setEntry(3, 2, .0013)'));
    expect(source, contains('..rotateX(-spatialAlignment.y * cardTilt)'));
    expect(source, contains('..rotateY(spatialAlignment.x * cardTilt)'));
    expect(source, contains('gradient: RadialGradient('));
    expect(source, contains('HapticFeedback.lightImpact();'));
    expect(source, contains('abstract final class AppMotion'));
    expect(
      source,
      contains('MediaQuery.maybeDisableAnimationsOf(context) ?? false'),
    );
    expect(
      source,
      contains('!reduce(context) && TickerMode.valuesOf(context).enabled'),
    );
    expect(source, isNot(contains('.disableAnimations ?? false')));
    expect(source, contains('oldWidget.onTap != null && widget.onTap == null'));
    expect(source, contains('oldWidget.animatePress && !widget.animatePress'));
    expect(source, contains('void _resetPressFeedback()'));
    expect(
      source,
      contains('bool _updateTouchAlignment(Offset localPosition)'),
    );
    expect(
      source,
      contains('static const double _touchAlignmentEpsilonSquared = .0004'),
    );
    expect(source, contains('deltaX * deltaX + deltaY * deltaY'));
    expect(source, contains('void _trackTouch(TapMoveDetails details)'));
    expect(source, contains('onTapMove:'));
    expect(source, contains(': _trackTouch,'));
    expect(source, contains('this.feedbackColor'));
    expect(source, contains('feedbackColor: color'));
    expect(source, contains('feedbackColor: diaryOrange'));

    final int pressableStart = source.indexOf('class _PressableState');
    final int pressableEnd = source.indexOf('class _GlassCard', pressableStart);
    expect(pressableStart, greaterThanOrEqualTo(0));
    expect(pressableEnd, greaterThan(pressableStart));
    final String pressableSource = source.substring(
      pressableStart,
      pressableEnd,
    );
    expect(pressableSource, contains('final double remainingTravel ='));
    expect(
      pressableSource,
      contains('duration: Duration(microseconds: adaptiveMicros)'),
    );
    expect(
      pressableSource,
      contains('void _release({bool cancelled = false})'),
    );
    expect(
      pressableSource,
      contains('math.min(_pressController.velocity, 0.0)'),
    );
    expect(pressableSource, contains('late final Stopwatch _gestureClock'));
    expect(pressableSource, contains('Offset _gestureVelocity = Offset.zero'));
    expect(
      pressableSource,
      contains('void _sampleGestureVelocity(Offset localPosition)'),
    );
    expect(pressableSource, contains('Offset _freshGestureVelocity()'));
    expect(pressableSource, contains('velocityResponsePerSecond = 32'));
    expect(
      pressableSource,
      contains('math.exp(-velocityResponsePerSecond * elapsedSeconds)'),
    );
    expect(pressableSource, contains('easedFreshness = freshness * freshness'));
    expect(pressableSource, contains('void didChangeDependencies()'));
    expect(
      pressableSource,
      contains('Alignment _projectReleaseAlignment(Offset velocity)'),
    );
    expect(pressableSource, contains('double _releaseDepthVelocity('));
    expect(pressableSource, contains('final double controllerVelocity ='));
    expect(pressableSource, contains('.clamp(-2.5, 0.0)'));
    expect(pressableSource, contains('final Alignment spatialAlignment ='));
    expect(pressableSource, contains('_pressController.value.abs() <= .0001'));
    expect(pressableSource, contains('releaseVelocity.abs() <= .0001'));
    expect(
      pressableSource.split('if (AppMotion.reduce(context)) {').length - 1,
      greaterThanOrEqualTo(2),
    );
    expect(pressableSource, contains('() => _release(cancelled: true)'));
    expect(pressableSource, isNot(contains('onLongPress:')));
    expect(pressableSource, isNot(contains('_handleLongPress')));

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
    expect(source, contains('Duration _adaptivePageDuration('));
    expect(source, contains('math.sqrt(remainingPages)'));
    expect(source, contains('duration: pageDuration'));
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

    // Frequent card navigation is direct and compositing-friendly. The fully
    // opaque destination canvas prevents ghosting while a four-percent content
    // settle avoids a hard flash without zooming, bending, or bouncing cards.
    expect(manifest, isNot(contains('animations:')));
    expect(source, isNot(contains('OpenContainer')));
    expect(source, isNot(contains('CupertinoPageTransition')));
    expect(source, isNot(contains('_premiumRoute')));
    expect(
      source,
      contains(
        'static const Duration directRouteIn = Duration(milliseconds: 210)',
      ),
    );
    expect(
      source,
      contains(
        'static const Duration directRouteOut = Duration(milliseconds: 210)',
      ),
    );

    final int transitionStart = source.indexOf(
      'class _OpaqueContentTransitionsBuilder',
    );
    final int transitionEnd = source.indexOf(
      'PageRoute<T> _directRoute<T>',
      transitionStart,
    );
    expect(transitionStart, greaterThanOrEqualTo(0));
    expect(transitionEnd, greaterThan(transitionStart));
    final String transitionSource = source.substring(
      transitionStart,
      transitionEnd,
    );
    expect(
      transitionSource,
      contains('final Widget surface = _AmbientBackground(child: child);'),
    );
    expect(transitionSource, contains('return _AmbientBackground('));
    expect(
      transitionSource,
      contains('FadeTransition(opacity: contentOpacity, child: child)'),
    );
    expect(transitionSource, isNot(contains('ScaleTransition(')));

    final int directStart = source.indexOf('PageRoute<T> _directRoute<T>');
    final int directEnd = source.indexOf('class _LaunchScreen', directStart);
    expect(directStart, greaterThanOrEqualTo(0));
    expect(directEnd, greaterThan(directStart));
    final String directSource = source.substring(directStart, directEnd);
    expect(directSource, contains('PageRouteBuilder<T>('));
    expect(directSource, contains('opaque: true'));
    expect(directSource, contains('allowSnapshotting: true'));
    expect(directSource, contains('? Duration.zero'));
    expect(directSource, contains('class _DirectRouteTransition'));
    expect(directSource, contains('Tween<double>(begin: .96, end: 1)'));
    expect(directSource, contains('child: _AmbientBackground('));
    expect(directSource, contains('FadeTransition('));
    expect(directSource, contains('RepaintBoundary(child: child)'));
    expect(directSource, contains('class _FastRouteLauncher'));
    expect(directSource, contains('bool _routeOpen = false'));
    expect(directSource, contains('if (_routeOpen) return'));
    expect(directSource, isNot(contains('RadialGradient(')));
    expect(directSource, isNot(contains('Transform.translate(')));
    expect(directSource, isNot(contains('Transform.scale(')));
    expect(directSource, isNot(contains('sourceRadius')));
    expect(directSource, isNot(contains('localToGlobal(')));
    expect(directSource, isNot(contains('BackdropFilter(')));
    expect(directSource, isNot(contains('ImageFilter.blur(')));
    expect(source, contains('animatePress: destinationBuilder == null'));
    expect(
      RegExp(r'animatePress:\s*false').allMatches(source).length,
      greaterThanOrEqualTo(3),
    );

    expect(
      RegExp(r'destinationBuilder:\s*\(_\)\s*=>').allMatches(source),
      hasLength(8),
    );
    for (final String destination in <String>[
      'AiHubScreen(sync: sync)',
      'PartyLedgerScreen(sync: sync)',
      'MilkDetailScreen(sync: widget.sync, customerName: name)',
      'SalaryDetailScreen(sync: widget.sync, personName: name)',
      'CreditDetailScreen(',
      'ExpenseDetailScreen(',
      'DiaryDetailScreen(',
      'BusinessDetailScreen(',
    ]) {
      expect(source, contains(destination));
    }

    // Export Center uses one adaptive visual language instead of rainbow
    // report cards. Labels stay single-line and scale down as a complete unit,
    // so narrow devices and larger text settings never fade off their suffix.
    final int exportStart = source.indexOf('class _ExportScopeSpec');
    final int exportEnd = source.indexOf('class _ExportDataset', exportStart);
    expect(exportStart, greaterThanOrEqualTo(0));
    expect(exportEnd, greaterThan(exportStart));
    final String exportSource = source.substring(exportStart, exportEnd);
    expect(exportSource, contains('class _ExportCenterPalette'));
    expect(exportSource, contains('static const _ExportCenterPalette _dark'));
    expect(exportSource, contains('static const _ExportCenterPalette _light'));
    expect(exportSource, contains('class _ExportButtonContent'));
    expect(exportSource, contains('ExcludeSemantics('));
    expect(exportSource, contains('FittedBox('));
    expect(exportSource, contains('fit: BoxFit.scaleDown'));
    expect(exportSource, contains('maxLines: 1'));
    expect(exportSource, contains('softWrap: false'));
    expect(exportSource, isNot(contains('TextOverflow.fade')));
    expect(exportSource, isNot(contains('_scopeGradient')));
    expect(exportSource, isNot(contains('required this.color')));
    expect(exportSource, isNot(contains('appleRed')));
    expect(exportSource, isNot(contains('appleOrange')));
    expect(exportSource, isNot(contains('salaryGreen')));
    for (final String label in <String>[
      'Premium PDF',
      'Milk Records',
      'Credit Ledger',
      'Personal Diary',
    ]) {
      expect(exportSource, contains("'$label'"));
    }
    expect(source, contains('selected: widget.selected'));
    expect(exportSource, contains('selected: selected'));

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

    // UI comfort/accessibility v3: behavior improves without visual drift.
    expect(source, contains('(event.buttons & kPrimaryButton) == 0'));
    expect(source, contains('selected: active,'));
    expect(source, contains("semanticLabel: 'Back',"));
    expect(source, contains('liveRegion: true,'));
    expect(source, contains('enabled: widget.onTap != null,'));
    expect(source, contains('excludeFromSemantics: true,'));
    expect(source, contains('onSubmitted: _onSubmitted,'));
    expect(source, contains('position.viewportDimension / 2'));
    expect(source, contains('(position.pixels - target).abs() < .5'));
    expect(source, contains('int _settledPage = 0;'));
    expect(source, contains('int? _programmaticPageTarget;'));
    expect(source, contains('final int generation = ++_pageMotionGeneration'));
    expect(
      source,
      contains('_finishProgrammaticPageMotion(index, generation)'),
    );
    expect(RegExp(r'active: _settledPage ==').allMatches(source), hasLength(7));
    expect(source, isNot(contains('active: _tab ==')));
    expect(source, contains('int _pageMotionGeneration = 0'));
    expect(source, contains('bool _userPageDragActive = false'));
    expect(source, contains('final Set<int> _dragHapticPages = <int>{}'));
    expect(source, contains('_dragHapticPages.add(index)'));
    expect(source, contains('_dragHapticPages.add(settledIndex)'));
    expect(source, contains('_dragHapticPages.clear()'));
    expect(source, contains('_pageMotionGeneration != generation'));
    expect(source, contains('notification.dragDetails != null'));
    expect(source, contains('NotificationListener<ScrollNotification>'));
    expect(source, contains('_finishUserPageMotion()'));
    expect(
      source,
      contains('class _LedgerPagePhysics extends PageScrollPhysics'),
    );
    expect(source, contains('mass: .78'));
    expect(source, contains('stiffness: 300'));
    expect(source, contains('damping: 30'));
    expect(source, contains('physics: const _LedgerPagePhysics('));
    expect(source, contains('if (_userPageDragActive) {'));
    expect(source, contains('setState(() => _tab = index);'));
    expect(
      source,
      contains('final int pageDistance = (index - currentPage).abs()'),
    );
    expect(source, contains('if (pageDistance > 1)'));
    expect(source, contains('_pageController.jumpToPage(stagingPage)'));
    expect(source, contains('!listEquals(oldDelegate.pulses, pulses)'));
    expect(source, contains('_pageController.jumpToPage(index);'));
    expect(source, contains('position.jumpTo(target);'));
    expect(
      source,
      contains('final Duration navMotion = AppMotion.reduce(context)'),
    );
    expect(
      source,
      contains('Provide at most one of onTap or destinationBuilder.'),
    );
    expect(source, contains('? buildCard(onTap)'));
    expect(source, isNot(contains('onTap: () {},')));

    // Stable global feedback must never reparent the application subtree.
    final int rippleStart = source.indexOf('class _GlobalTapRippleLayerState');
    final int rippleEnd = source.indexOf(
      'class _GlobalTapRipplePainter',
      rippleStart,
    );
    expect(rippleStart, greaterThanOrEqualTo(0));
    expect(rippleEnd, greaterThan(rippleStart));
    final String rippleSource = source.substring(rippleStart, rippleEnd);
    expect(rippleSource, isNot(contains('Widget surface = widget.child;')));
    expect(
      rippleSource,
      contains(
        'final List<_RipplePulse> snapshot = List<_RipplePulse>.unmodifiable(',
      ),
    );
    expect(rippleSource, contains('child: Stack('));
    expect(rippleSource, contains('if (snapshot.isNotEmpty)'));
    expect(rippleSource, contains('widget.child,'));

    // Swipe depth is a compositor concern; the live ledger screen below
    // it remains its own repaint boundary so 60/90/120Hz transforms do
    // not force every card and row to repaint on each gesture frame.
    final int shellStart = source.indexOf(
      'class _AppShellState extends State<AppShell>',
    );
    final int shellEnd = source.indexOf(
      'class _KeepAlivePage extends StatefulWidget',
      shellStart,
    );
    expect(shellStart, greaterThanOrEqualTo(0));
    expect(shellEnd, greaterThan(shellStart));
    final String shellSource = source.substring(shellStart, shellEnd);
    expect(shellSource, contains('child: RepaintBoundary(child: child),'));
    // Brand/state color logic and Firebase integration must stay untouched.
    expect(source, contains("import 'firebase_sync.dart';"));
    expect(source, contains('Firebase.initializeApp('));
    expect(
      source,
      contains(
        'final List<Color> colors = _moduleTabColors(sync.currentProjection);',
      ),
    );
  });
}

// This source guard intentionally lives in test/ so every future UI edit rechecks
// the premium depth, icon, motion, accessibility and safety invariants together.
