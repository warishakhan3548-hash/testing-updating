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
    '''_pageController.animateToPage(\n        index,\n        duration: const Duration(milliseconds: 300),\n        curve: const Cubic(0.32, 0.72, 0, 1),\n      );''',
    '''_pageController.animateToPage(\n        index,\n        duration: const Duration(milliseconds: 250),\n        curve: const Cubic(0.2, 0.82, 0.2, 1),\n      );''',
  );

  replaceExact(
    'navigation rail scroll motion',
    '''duration: const Duration(milliseconds: 280),\n        curve: const Cubic(0.32, 0.72, 0, 1),''',
    '''duration: const Duration(milliseconds: 235),\n        curve: const Cubic(0.2, 0.82, 0.2, 1),''',
  );

  replaceExact(
    'route timing',
    '''transitionDuration: const Duration(milliseconds: 260),\n      reverseTransitionDuration: const Duration(milliseconds: 220),''',
    '''transitionDuration: const Duration(milliseconds: 235),\n      reverseTransitionDuration: const Duration(milliseconds: 195),''',
  );

  replaceExact(
    'route travel distance',
    'begin: const Offset(.045, 0),',
    'begin: const Offset(.032, 0),',
  );

  replaceExact(
    'press controller timing',
    '''_pressController = AnimationController(\n      vsync: this,\n      duration: const Duration(milliseconds: 70),\n      reverseDuration: const Duration(milliseconds: 220),\n    );''',
    '''_pressController = AnimationController(\n      vsync: this,\n      duration: const Duration(milliseconds: 55),\n      reverseDuration: const Duration(milliseconds: 180),\n    );''',
  );

  replaceExact(
    'press down timing',
    '''duration: const Duration(milliseconds: 70),\n      curve: const Cubic(0.2, 0, 0, 1),''',
    '''duration: const Duration(milliseconds: 55),\n      curve: const Cubic(0.18, 0.72, 0.2, 1),''',
  );

  replaceExact(
    'press release timing',
    '''duration: const Duration(milliseconds: 220),\n      curve: const Cubic(0.34, 1.18, 0.64, 1),''',
    '''duration: const Duration(milliseconds: 180),\n      curve: const Cubic(0.2, 1.08, 0.3, 1),''',
  );

  replaceExact(
    'press visual physics',
    '''child: AnimatedBuilder(\n            animation: _pressController,\n            child: widget.child,\n            builder: (BuildContext context, Widget? child) => Transform.scale(\n              scale: 1 - (_pressController.value * .022),\n              child: Stack(\n                clipBehavior: Clip.none,\n                children: <Widget>[\n                  child!,\n                  Positioned.fill(\n                    child: IgnorePointer(\n                      child: ClipRRect(\n                        borderRadius: widget.borderRadius ?? BorderRadius.zero,\n                        child: ColoredBox(\n                          color:\n                              (Theme.of(context).brightness == Brightness.dark\n                                      ? Colors.white\n                                      : Colors.black)\n                                  .withAlpha(\n                            (_pressController.value *\n                                    (Theme.of(context).brightness ==\n                                            Brightness.dark\n                                        ? 14\n                                        : 9))\n                                .round(),\n                          ),\n                        ),\n                      ),\n                    ),\n                  ),\n                ],\n              ),\n            ),\n          ),''',
    '''child: AnimatedBuilder(\n            animation: _pressController,\n            child: widget.child,\n            builder: (BuildContext context, Widget? child) {\n              final bool dark =\n                  Theme.of(context).brightness == Brightness.dark;\n              final bool reduceMotion = MediaQuery.of(context).disableAnimations;\n              final double feedback = Curves.easeOutCubic.transform(\n                _pressController.value,\n              );\n              final double motion = reduceMotion ? 0 : feedback;\n              return Transform.translate(\n                offset: Offset(0, motion * 1.1),\n                child: Transform.scale(\n                  scale: 1 - (motion * .017),\n                  child: Stack(\n                    clipBehavior: Clip.none,\n                    children: <Widget>[\n                      child!,\n                      Positioned.fill(\n                        child: IgnorePointer(\n                          child: ClipRRect(\n                            borderRadius:\n                                widget.borderRadius ?? BorderRadius.zero,\n                            child: DecoratedBox(\n                              decoration: BoxDecoration(\n                                gradient: LinearGradient(\n                                  begin: Alignment.topCenter,\n                                  end: Alignment.bottomCenter,\n                                  colors: <Color>[\n                                    Colors.white.withAlpha(\n                                      (feedback * (dark ? 12 : 20)).round(),\n                                    ),\n                                    (dark ? Colors.black : Colors.black)\n                                        .withAlpha(\n                                      (feedback * (dark ? 7 : 10)).round(),\n                                    ),\n                                  ],\n                                ),\n                              ),\n                            ),\n                          ),\n                        ),\n                      ),\n                    ],\n                  ),\n                ),\n              );\n            },\n          ),''',
  );

  final int refreshCount = RegExp(r'(?<!\\.)RefreshIndicator\\(')
      .allMatches(source)
      .length;
  if (refreshCount < 1) {
    throw StateError('No RefreshIndicator found');
  }
  source = source.replaceAll('RefreshIndicator(', 'RefreshIndicator.adaptive(');

  replaceExact(
    'dashboard refresh feedback',
    '''onRefresh: () async {\n              await sync.reconcile(reason: 'pull-to-refresh');\n            },''',
    '''onRefresh: () async {\n              HapticFeedback.lightImpact();\n              await sync.reconcile(reason: 'pull-to-refresh');\n              if (context.mounted) HapticFeedback.selectionClick();\n            },''',
  );

  mainFile.writeAsStringSync(source);

  final ProcessResult formatResult = Process.runSync(\n    'dart',\n    <String>['format', 'lib/main.dart'],\n  );
  stdout.write(formatResult.stdout);\n  stderr.write(formatResult.stderr);\n  if (formatResult.exitCode != 0) {\n    exitCode = formatResult.exitCode;\n    return;\n  }\n\n  final File self = File('tool/apply_motion_delight_upgrade.dart');\n  if (self.existsSync()) self.deleteSync();\n  final File workflow = File('.github/workflows/apply-motion-delight.yml');\n  if (workflow.existsSync()) workflow.deleteSync();\n}\n