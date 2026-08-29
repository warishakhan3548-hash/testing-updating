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
    'root stage handoff',
    '''        home: _booting\n            ? const _LaunchScreen()\n            : _userId == null\n                ? _LoginScreen(sync: widget.sync)\n                : AppShell(sync: widget.sync),''',
    '''        home: _RootStage(\n          booting: _booting,\n          userId: _userId,\n          sync: widget.sync,\n        ),''',
  );

  replaceExact(
    'root stage class insertion',
    '''      );\n}\n\nThemeData _theme(Brightness brightness) {''',
    '''      );\n}\n\nclass _RootStage extends StatelessWidget {\n  const _RootStage({\n    required this.booting,\n    required this.userId,\n    required this.sync,\n  });\n\n  final bool booting;\n  final String? userId;\n  final LedgerSyncService sync;\n\n  @override\n  Widget build(BuildContext context) {\n    final bool reduceMotion =\n        MediaQuery.maybeOf(context)?.disableAnimations ?? false;\n    final Widget stage;\n    final String stageKey;\n    if (booting) {\n      stage = const _LaunchScreen();\n      stageKey = 'launch';\n    } else if (userId == null) {\n      stage = _LoginScreen(sync: sync);\n      stageKey = 'login';\n    } else {\n      stage = AppShell(sync: sync);\n      stageKey = 'app';\n    }\n\n    return AnimatedSwitcher(\n      duration: reduceMotion\n          ? Duration.zero\n          : const Duration(milliseconds: 180),\n      reverseDuration: reduceMotion\n          ? Duration.zero\n          : const Duration(milliseconds: 140),\n      switchInCurve: Curves.easeOutCubic,\n      switchOutCurve: Curves.easeInCubic,\n      transitionBuilder: (Widget child, Animation<double> animation) =>\n          FadeTransition(opacity: animation, child: child),\n      child: KeyedSubtree(\n        key: ValueKey<String>(stageKey),\n        child: stage,\n      ),\n    );\n  }\n}\n\nThemeData _theme(Brightness brightness) {''',
  );

  replaceExact(
    'page transition reduced motion',
    '''  ) {\n    final Animation<double> curved = CurvedAnimation(''',
    '''  ) {\n    if (MediaQuery.maybeOf(context)?.disableAnimations ?? false) {\n      return child;\n    }\n    final Animation<double> curved = CurvedAnimation(''',
  );

  replaceExact(
    'custom route reduced motion',
    '''      transitionsBuilder: (_, Animation<double> animation, __, Widget child) {\n        final Animation<double> curved = CurvedAnimation(''',
    '''      transitionsBuilder: (\n        BuildContext context,\n        Animation<double> animation,\n        Animation<double> secondaryAnimation,\n        Widget child,\n      ) {\n        if (MediaQuery.maybeOf(context)?.disableAnimations ?? false) {\n          return child;\n        }\n        final Animation<double> curved = CurvedAnimation(''',
  );

  replaceExact(
    'modal sheet motion',
    '''Future<T?> _openSheet<T>(BuildContext context, Widget child) =>\n    showModalBottomSheet<T>(\n      context: context,\n      isScrollControlled: true,\n      useSafeArea: true,\n      backgroundColor: Colors.transparent,\n      barrierColor: Colors.black.withAlpha(105),\n      elevation: 0,\n      builder: (BuildContext context) => child,\n    );''',
    '''Future<T?> _openSheet<T>(BuildContext context, Widget child) {\n  final bool reduceMotion =\n      MediaQuery.maybeOf(context)?.disableAnimations ?? false;\n  return showModalBottomSheet<T>(\n    context: context,\n    isScrollControlled: true,\n    useSafeArea: true,\n    requestFocus: true,\n    backgroundColor: Colors.transparent,\n    barrierColor: Colors.black.withAlpha(105),\n    elevation: 0,\n    sheetAnimationStyle: reduceMotion\n        ? AnimationStyle.noAnimation\n        : const AnimationStyle(\n            duration: Duration(milliseconds: 250),\n            reverseDuration: Duration(milliseconds: 190),\n          ),\n    builder: (BuildContext context) => child,\n  );\n}''',
  );

  replaceExact(
    'confirmation dialog motion and safe focus',
    '''Future<bool> _confirm(\n  BuildContext context,\n  String title,\n  String message, {\n  bool dangerous = true,\n}) async {\n  final bool? result = await showDialog<bool>(\n    context: context,\n    builder: (BuildContext context) => AlertDialog(\n      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w900)),\n      content: Text(message),\n      actions: <Widget>[\n        TextButton(\n          onPressed: () => Navigator.pop(context, false),\n          child: const Text('Cancel'),\n        ),\n        TextButton(\n          onPressed: () {\n            if (dangerous) HapticFeedback.heavyImpact();\n            Navigator.pop(context, true);\n          },\n          child: Text(\n            dangerous ? 'Delete' : 'Continue',\n            style: TextStyle(color: dangerous ? appleRed : appleBlue),\n          ),\n        ),\n      ],\n    ),\n  );\n  return result ?? false;\n}''',
    '''Future<bool> _confirm(\n  BuildContext context,\n  String title,\n  String message, {\n  bool dangerous = true,\n}) async {\n  final bool reduceMotion =\n      MediaQuery.maybeOf(context)?.disableAnimations ?? false;\n  final bool? result = await showDialog<bool>(\n    context: context,\n    requestFocus: true,\n    animationStyle: reduceMotion\n        ? AnimationStyle.noAnimation\n        : const AnimationStyle(\n            duration: Duration(milliseconds: 240),\n            reverseDuration: Duration(milliseconds: 180),\n          ),\n    builder: (BuildContext context) => AlertDialog(\n      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w900)),\n      content: Text(message),\n      actions: <Widget>[\n        TextButton(\n          autofocus: dangerous,\n          onPressed: () => Navigator.pop(context, false),\n          child: const Text('Cancel'),\n        ),\n        TextButton(\n          autofocus: !dangerous,\n          onPressed: () {\n            if (dangerous) HapticFeedback.heavyImpact();\n            Navigator.pop(context, true);\n          },\n          child: Text(\n            dangerous ? 'Delete' : 'Continue',\n            style: TextStyle(color: dangerous ? appleRed : appleBlue),\n          ),\n        ),\n      ],\n    ),\n  );\n  return result ?? false;\n}''',
  );

  replaceExact(
    'toast motion',
    '''void _toast(BuildContext context, String message, {bool error = false}) {\n  if (error) HapticFeedback.errorNotification();\n  final ScaffoldMessengerState messenger = ScaffoldMessenger.of(context);\n  messenger.hideCurrentSnackBar();\n  messenger.showSnackBar(\n    SnackBar(\n      content: Row(\n        children: <Widget>[\n          Icon(\n            error ? Icons.error_rounded : Icons.check_circle_rounded,\n            color: error ? appleRed : appleGreen,\n            size: 20,\n          ),\n          const SizedBox(width: 10),\n          Expanded(child: Text(message)),\n        ],\n      ),\n      duration: const Duration(seconds: 2),\n    ),\n  );\n}''',
    '''void _toast(BuildContext context, String message, {bool error = false}) {\n  if (error) HapticFeedback.errorNotification();\n  final bool reduceMotion =\n      MediaQuery.maybeOf(context)?.disableAnimations ?? false;\n  final ScaffoldMessengerState messenger = ScaffoldMessenger.of(context);\n  messenger.hideCurrentSnackBar();\n  messenger.showSnackBar(\n    SnackBar(\n      content: Row(\n        children: <Widget>[\n          Icon(\n            error ? Icons.error_rounded : Icons.check_circle_rounded,\n            color: error ? appleRed : appleGreen,\n            size: 20,\n          ),\n          const SizedBox(width: 10),\n          Expanded(child: Text(message)),\n        ],\n      ),\n      duration: const Duration(seconds: 2),\n    ),\n    snackBarAnimationStyle: reduceMotion\n        ? AnimationStyle.noAnimation\n        : const AnimationStyle(\n            duration: Duration(milliseconds: 180),\n            reverseDuration: Duration(milliseconds: 140),\n          ),\n  );\n}''',
  );

  replaceExact(
    'AI review dialog motion',
    '''  Future<bool> _confirmAiActions(List<Map<String, dynamic>> actions) async {\n    final bool? result = await showDialog<bool>(\n      context: context,\n      builder: (BuildContext dialogContext) => AlertDialog(''',
    '''  Future<bool> _confirmAiActions(List<Map<String, dynamic>> actions) async {\n    final bool reduceMotion =\n        MediaQuery.maybeOf(context)?.disableAnimations ?? false;\n    final bool? result = await showDialog<bool>(\n      context: context,\n      requestFocus: true,\n      animationStyle: reduceMotion\n          ? AnimationStyle.noAnimation\n          : const AnimationStyle(\n              duration: Duration(milliseconds: 240),\n              reverseDuration: Duration(milliseconds: 180),\n            ),\n      builder: (BuildContext dialogContext) => AlertDialog(''',
  );

  replaceExact(
    'AI review safe focus',
    '''        actions: <Widget>[\n          TextButton(\n            onPressed: () => Navigator.pop(dialogContext, false),\n            child: const Text('Cancel'),\n          ),''',
    '''        actions: <Widget>[\n          TextButton(\n            autofocus: true,\n            onPressed: () => Navigator.pop(dialogContext, false),\n            child: const Text('Cancel'),\n          ),''',
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

  final File self = File('tool/apply_cross_system_motion_upgrade.dart');
  if (self.existsSync()) self.deleteSync();
  final File workflow =
      File('.github/workflows/apply-cross-system-motion-upgrade.yml');
  if (workflow.existsSync()) workflow.deleteSync();
}
