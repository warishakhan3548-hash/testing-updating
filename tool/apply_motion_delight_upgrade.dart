import 'dart:io';

void main() {
  final File mainFile = File('lib/main.dart');
  String source = mainFile.readAsStringSync();

  void replaceExact(String label, String oldText, String newText) {
    final int count = RegExp(RegExp.escape(oldText)).allMatches(source).length;
    if (count != 1) {
      throw StateError('$label expected exactly once, found $count');
    }
    source = source.replaceFirst(oldText, newText);
  }

  replaceExact(
    'global motion token',
    'static const Duration motion = Duration(milliseconds: 280);',
    'static const Duration motion = Duration(milliseconds: 240);',
  );

  replaceExact(
    'theme motion',
    'themeAnimationDuration: const Duration(milliseconds: 420),',
    'themeAnimationDuration: const Duration(milliseconds: 300),',
  );

  replaceExact(
    'tab page motion',
    '''_pageController.animateToPage(
        index,
        duration: const Duration(milliseconds: 300),
        curve: const Cubic(0.32, 0.72, 0, 1),
      );''',
    '''_pageController.animateToPage(
        index,
        duration: const Duration(milliseconds: 250),
        curve: const Cubic(0.2, 0.82, 0.2, 1),
      );''',
  );

  replaceExact(
    'navigation rail scroll motion',
    '''duration: const Duration(milliseconds: 280),
        curve: const Cubic(0.32, 0.72, 0, 1),''',
    '''duration: const Duration(milliseconds: 235),
        curve: const Cubic(0.2, 0.82, 0.2, 1),''',
  );

  replaceExact(
    'route timing',
    '''transitionDuration: const Duration(milliseconds: 260),
      reverseTransitionDuration: const Duration(milliseconds: 220),''',
    '''transitionDuration: const Duration(milliseconds: 235),
      reverseTransitionDuration: const Duration(milliseconds: 195),''',
  );

  replaceExact(
    'route travel distance',
    'begin: const Offset(.045, 0),',
    'begin: const Offset(.032, 0),',
  );

  replaceExact(
    'press controller timing',
    '''_pressController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 70),
      reverseDuration: const Duration(milliseconds: 220),
    );''',
    '''_pressController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 55),
      reverseDuration: const Duration(milliseconds: 180),
    );''',
  );

  replaceExact(
    'press down timing',
    '''duration: const Duration(milliseconds: 70),
      curve: const Cubic(0.2, 0, 0, 1),''',
    '''duration: const Duration(milliseconds: 55),
      curve: const Cubic(0.18, 0.72, 0.2, 1),''',
  );

  replaceExact(
    'press release timing',
    '''duration: const Duration(milliseconds: 220),
      curve: const Cubic(0.34, 1.18, 0.64, 1),''',
    '''duration: const Duration(milliseconds: 180),
      curve: const Cubic(0.2, 1.08, 0.3, 1),''',
  );

  replaceExact(
    'press visual physics',
    '''child: AnimatedBuilder(
            animation: _pressController,
            child: widget.child,
            builder: (BuildContext context, Widget? child) => Transform.scale(
              scale: 1 - (_pressController.value * .022),
              child: Stack(
                clipBehavior: Clip.none,
                children: <Widget>[
                  child!,
                  Positioned.fill(
                    child: IgnorePointer(
                      child: ClipRRect(
                        borderRadius: widget.borderRadius ?? BorderRadius.zero,
                        child: ColoredBox(
                          color:
                              (Theme.of(context).brightness == Brightness.dark
                                      ? Colors.white
                                      : Colors.black)
                                  .withAlpha(
                            (_pressController.value *
                                    (Theme.of(context).brightness ==
                                            Brightness.dark
                                        ? 14
                                        : 9))
                                .round(),
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),''',
    '''child: AnimatedBuilder(
            animation: _pressController,
            child: widget.child,
            builder: (BuildContext context, Widget? child) {
              final bool dark =
                  Theme.of(context).brightness == Brightness.dark;
              final bool reduceMotion = MediaQuery.of(context).disableAnimations;
              final double feedback = Curves.easeOutCubic.transform(
                _pressController.value,
              );
              final double motion = reduceMotion ? 0 : feedback;
              return Transform.translate(
                offset: Offset(0, motion * 1.1),
                child: Transform.scale(
                  scale: 1 - (motion * .017),
                  child: Stack(
                    clipBehavior: Clip.none,
                    children: <Widget>[
                      child!,
                      Positioned.fill(
                        child: IgnorePointer(
                          child: ClipRRect(
                            borderRadius:
                                widget.borderRadius ?? BorderRadius.zero,
                            child: DecoratedBox(
                              decoration: BoxDecoration(
                                gradient: LinearGradient(
                                  begin: Alignment.topCenter,
                                  end: Alignment.bottomCenter,
                                  colors: <Color>[
                                    Colors.white.withAlpha(
                                      (feedback * (dark ? 12 : 20)).round(),
                                    ),
                                    Colors.black.withAlpha(
                                      (feedback * (dark ? 7 : 10)).round(),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),''',
  );

  final int refreshCount = RegExp(r'(?<!\.)RefreshIndicator\(')
      .allMatches(source)
      .length;
  if (refreshCount < 1) {
    throw StateError('No RefreshIndicator found');
  }
  source = source.replaceAll('RefreshIndicator(', 'RefreshIndicator.adaptive(');

  replaceExact(
    'dashboard refresh feedback',
    '''onRefresh: () async {
              await sync.reconcile(reason: 'pull-to-refresh');
            },''',
    '''onRefresh: () async {
              HapticFeedback.lightImpact();
              await sync.reconcile(reason: 'pull-to-refresh');
              if (context.mounted) HapticFeedback.selectionClick();
            },''',
  );

  mainFile.writeAsStringSync(source);

  final ProcessResult formatResult = Process.runSync(
    'dart',
    <String>['format', 'lib/main.dart'],
  );
  stdout.write(formatResult.stdout);
  stderr.write(formatResult.stderr);
  if (formatResult.exitCode != 0) {
    exitCode = formatResult.exitCode;
    return;
  }

  final File self = File('tool/apply_motion_delight_upgrade.dart');
  if (self.existsSync()) self.deleteSync();
  final File workflow = File('.github/workflows/apply-motion-delight.yml');
  if (workflow.existsSync()) workflow.deleteSync();
}
