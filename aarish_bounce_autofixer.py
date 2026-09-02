#!/usr/bin/env python3
# Aarish Dairy Pro — global bounce-surface auto-fixer.
#
# Target: /root/Aarish Kingdom/repo/lib/main.dart
#
# Makes _Pressable the invariant bounce engine for tappable custom surfaces,
# fixes route-card bounce handoff, migrates remaining native TextButton/IconButton
# actions to the same motion language, and leaves static/form/scroll surfaces alone.

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime

DEFAULT_PROJECT = Path("/root/Aarish Kingdom/repo")
SENTINEL = "// BOUNCE_SURFACE_V1"


class PatchError(RuntimeError):
    pass


def replace_exact(
    source: str,
    old: str,
    new: str,
    *,
    label: str,
    count: int = 1,
) -> str:
    found = source.count(old)
    if found != count:
        raise PatchError(
            f"{label}: expected {count} exact match(es), found {found}. "
            "Source layout is different; refusing to guess."
        )
    return source.replace(old, new, count)


def regex_replace_exact(
    source: str,
    pattern: str,
    replacement: str,
    *,
    label: str,
    count: int,
) -> str:
    updated, found = re.subn(
        pattern,
        replacement,
        source,
        flags=re.MULTILINE,
    )
    if found != count:
        raise PatchError(
            f"{label}: expected {count} match(es), found {found}. "
            "Source layout is different; refusing to guess."
        )
    return updated


def verify_patched(source: str) -> None:
    checks = {
        "patch sentinel": SENTINEL in source,
        "route handoff": "routePressHandoff" in source,
        "bounce text action":
            "class _BounceTextButton extends StatelessWidget" in source,
        "bounce icon action":
            "class _BounceIconButton extends StatelessWidget" in source,
        "no animatePress escape hatch":
            "animatePress" not in source,
        "no native TextButton action left":
            re.search(r"\bTextButton\(", source) is None,
        "no native IconButton action left":
            re.search(r"\bIconButton\(", source) is None,
    }

    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise PatchError(
            "verification failed: " + ", ".join(failed)
        )


def run_command(
    command: list[str],
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def patch_main(source: str) -> str:
    if SENTINEL in source:
        verify_patched(source)
        return source

    # ------------------------------------------------------------
    # 1. ROUTE PRESS HANDOFF
    # ------------------------------------------------------------

    source = replace_exact(
        source,
        "  static const Duration pressOut = Duration(milliseconds: 210);\n"
        "  static const Duration globalRippleIntentDelay = Duration(milliseconds: 48);",
        "  static const Duration pressOut = Duration(milliseconds: 210);\n"
        f"  {SENTINEL}\n"
        "  // Allow the pressed surface to visibly release before navigation.\n"
        "  // Reduced Motion bypasses this delay completely.\n"
        "  static const Duration routePressHandoff = Duration(milliseconds: 72);\n"
        "  static const Duration globalRippleIntentDelay = Duration(milliseconds: 48);",
        label="insert route press handoff",
    )

    old_launcher = '''class _FastRouteLauncherState extends State<_FastRouteLauncher> {
  bool _routeOpen = false;

  void _open() {
    if (_routeOpen) return;
    _routeOpen = true;
    final NavigatorState navigator = Navigator.of(context);
    final PageRoute<Object?> route = _directRoute<Object?>(
      destinationBuilder: widget.destinationBuilder,
      reduceMotion: AppMotion.reduce(context),
    );
    unawaited(
      navigator.push<Object?>(route).whenComplete(() => _routeOpen = false),
    );
  }

  @override
  Widget build(BuildContext context) =>
      RepaintBoundary(child: widget.sourceBuilder(_open));
}'''

    new_launcher = '''class _FastRouteLauncherState extends State<_FastRouteLauncher> {
  bool _routeOpen = false;
  Timer? _launchTimer;

  void _open() {
    if (_routeOpen) return;
    _routeOpen = true;

    void launchRoute() {
      _launchTimer = null;
      if (!mounted) return;

      final NavigatorState navigator = Navigator.of(context);
      final PageRoute<Object?> route = _directRoute<Object?>(
        destinationBuilder: widget.destinationBuilder,
        reduceMotion: AppMotion.reduce(context),
      );

      unawaited(
        navigator.push<Object?>(route).whenComplete(() {
          if (mounted) _routeOpen = false;
        }),
      );
    }

    if (AppMotion.reduce(context)) {
      launchRoute();
    } else {
      _launchTimer = Timer(
        UIConstants.routePressHandoff,
        launchRoute,
      );
    }
  }

  @override
  void dispose() {
    _launchTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) =>
      RepaintBoundary(child: widget.sourceBuilder(_open));
}'''

    source = replace_exact(
        source,
        old_launcher,
        new_launcher,
        label="upgrade fast-route press handoff",
    )

    # ------------------------------------------------------------
    # 2. MAKE BOUNCE INTRINSIC TO _Pressable
    # ------------------------------------------------------------

    source = replace_exact(
        source,
        "    this.selected,\n"
        "    this.animatePress = true,\n",
        "    this.selected,\n",
        label="remove _Pressable animatePress constructor flag",
    )

    source = replace_exact(
        source,
        "  final bool? selected;\n"
        "  final bool animatePress;\n",
        "  final bool? selected;\n",
        label="remove _Pressable animatePress field",
    )

    source = replace_exact(
        source,
        '''    final bool interactionDisabled =
        (oldWidget.onTap != null && widget.onTap == null) ||
        (oldWidget.animatePress && !widget.animatePress);
    if (interactionDisabled) _resetPressFeedback();''',
        '''    if (oldWidget.onTap != null && widget.onTap == null) {
      _resetPressFeedback();
    }''',
        label="simplify _Pressable update reset",
    )

    source = replace_exact(
        source,
        "    if (widget.onTap == null || !widget.animatePress) return;",
        "    if (widget.onTap == null) return;",
        label="make _Pressable touch methods always animate",
        count=3,
    )

    source = replace_exact(
        source,
        '''      onTapDown: widget.onTap == null || !widget.animatePress ? null : _press,
      onTapMove: widget.onTap == null || !widget.animatePress
          ? null
          : _trackTouch,
      onTapCancel: widget.onTap == null || !widget.animatePress
          ? null
          : () => _release(cancelled: true),
      onTapUp: widget.onTap == null || !widget.animatePress
          ? null
          : (_) => _release(),''',
        '''      onTapDown: widget.onTap == null ? null : _press,
      onTapMove: widget.onTap == null ? null : _trackTouch,
      onTapCancel: widget.onTap == null
          ? null
          : () => _release(cancelled: true),
      onTapUp: widget.onTap == null ? null : (_) => _release(),''',
        label="make _Pressable gesture callbacks always animate",
    )

    # Remove caller-side bounce opt-outs.
    # Includes route list cards and other clickable custom cards.

    source = regex_replace_exact(
        source,
        r"^\s*animatePress:\s*(?:destinationBuilder == null|false),\n",
        "",
        label="remove route-card bounce opt-outs",
        count=4,
    )

    # ------------------------------------------------------------
    # 3. COMMON BOUNCE TEXT / ICON ACTIONS
    # ------------------------------------------------------------

    helper_anchor = "class _SearchBox extends StatefulWidget {"

    helper_code = r'''class _BounceTextButton extends StatelessWidget {
  const _BounceTextButton({
    required this.onTap,
    required this.child,
    this.semanticLabel,
    this.autofocus = false,
  });

  final VoidCallback? onTap;
  final Widget child;
  final String? semanticLabel;
  final bool autofocus;

  @override
  Widget build(BuildContext context) => FocusableActionDetector(
    enabled: onTap != null,
    autofocus: autofocus,
    shortcuts: const <ShortcutActivator, Intent>{
      SingleActivator(LogicalKeyboardKey.enter): ActivateIntent(),
      SingleActivator(LogicalKeyboardKey.space): ActivateIntent(),
    },
    actions: <Type, Action<Intent>>{
      ActivateIntent: CallbackAction<ActivateIntent>(
        onInvoke: (ActivateIntent intent) {
          onTap?.call();
          return null;
        },
      ),
    },
    child: _Pressable(
      onTap: onTap,
      semanticLabel: semanticLabel,
      borderRadius: BorderRadius.circular(12),
      child: ConstrainedBox(
        constraints: const BoxConstraints(
          minHeight: UIConstants.minTapTarget,
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(
            horizontal: 12,
            vertical: 8,
          ),
          child: Center(
            widthFactor: 1,
            child: DefaultTextStyle.merge(
              style: TextStyle(
                color: onTap == null
                    ? Theme.of(context).disabledColor
                    : Theme.of(context).colorScheme.primary,
                fontWeight: FontWeight.w700,
              ),
              child: child,
            ),
          ),
        ),
      ),
    ),
  );
}


class _BounceIconButton extends StatelessWidget {
  const _BounceIconButton({
    required this.onTap,
    required this.icon,
    required this.tooltip,
  });

  final VoidCallback? onTap;
  final Widget icon;
  final String tooltip;

  @override
  Widget build(BuildContext context) => Tooltip(
    message: tooltip,
    child: FocusableActionDetector(
      enabled: onTap != null,
      shortcuts: const <ShortcutActivator, Intent>{
        SingleActivator(LogicalKeyboardKey.enter): ActivateIntent(),
        SingleActivator(LogicalKeyboardKey.space): ActivateIntent(),
      },
      actions: <Type, Action<Intent>>{
        ActivateIntent: CallbackAction<ActivateIntent>(
          onInvoke: (ActivateIntent intent) {
            onTap?.call();
            return null;
          },
        ),
      },
      child: _Pressable(
        onTap: onTap,
        semanticLabel: tooltip,
        borderRadius: BorderRadius.circular(24),
        child: SizedBox.square(
          dimension: UIConstants.minTapTarget,
          child: Center(
            child: icon,
          ),
        ),
      ),
    ),
  );
}


'''

    source = replace_exact(
        source,
        helper_anchor,
        helper_code + helper_anchor,
        label="insert bounce-native action helpers",
    )

    # ------------------------------------------------------------
    # 4. CONFIRMATION DIALOG BUTTONS
    # ------------------------------------------------------------

    source = replace_exact(
        source,
        '''        TextButton(
          autofocus: dangerous,
          onPressed: () => Navigator.pop(context, false),
          child: const Text('Cancel'),
        ),
        TextButton(
          autofocus: !dangerous,
          onPressed: () {
            if (dangerous) HapticFeedback.heavyImpact();
            Navigator.pop(context, true);
          },
          child: Text(
            dangerous ? 'Delete' : 'Continue',
            style: TextStyle(color: dangerous ? appleRed : appleBlue),
          ),
        ),''',
        '''        _BounceTextButton(
          autofocus: dangerous,
          semanticLabel: 'Cancel',
          onTap: () => Navigator.pop(context, false),
          child: const Text('Cancel'),
        ),
        _BounceTextButton(
          autofocus: !dangerous,
          semanticLabel: dangerous ? 'Delete' : 'Continue',
          onTap: () {
            if (dangerous) HapticFeedback.heavyImpact();
            Navigator.pop(context, true);
          },
          child: Text(
            dangerous ? 'Delete' : 'Continue',
            style: TextStyle(
              color: dangerous ? appleRed : appleBlue,
            ),
          ),
        ),''',
        label="migrate confirmation dialog actions",
    )

    # ------------------------------------------------------------
    # 5. EXTERNAL AI READY CARD ACTIONS
    # ------------------------------------------------------------

    source = replace_exact(
        source,
        '''          TextButton(
            onPressed: onPaste,
            child: const Text(
              'Paste & Review',
              style: TextStyle(color: purple, fontWeight: FontWeight.w900),
            ),
          ),
          IconButton(
            tooltip: 'Dismiss external AI session',
            onPressed: onDismiss,
            icon: const Icon(Icons.close_rounded, size: 19),
          ),''',
        '''          _BounceTextButton(
            onTap: onPaste,
            semanticLabel: 'Paste and review external AI response',
            child: const Text(
              'Paste & Review',
              style: TextStyle(
                color: purple,
                fontWeight: FontWeight.w900,
              ),
            ),
          ),
          _BounceIconButton(
            tooltip: 'Dismiss external AI session',
            onTap: onDismiss,
            icon: const Icon(
              Icons.close_rounded,
              size: 19,
            ),
          ),''',
        label="migrate external AI ready-card actions",
    )

    # ------------------------------------------------------------
    # 6. AI BATCH RETRY / CANCEL
    # ------------------------------------------------------------

    source = replace_exact(
        source,
        '''              if (job.paused && !job.hasStateConflict)
                TextButton(onPressed: onRetry, child: const Text('Retry')),
              TextButton(
                onPressed: onCancel,
                child: const Text('Cancel', style: TextStyle(color: appleRed)),
              ),''',
        '''              if (job.paused && !job.hasStateConflict)
                _BounceTextButton(
                  onTap: onRetry,
                  semanticLabel: 'Retry AI batch',
                  child: const Text('Retry'),
                ),
              _BounceTextButton(
                onTap: onCancel,
                semanticLabel: 'Cancel AI batch',
                child: const Text(
                  'Cancel',
                  style: TextStyle(color: appleRed),
                ),
              ),''',
        label="migrate AI batch actions",
    )

    # ------------------------------------------------------------
    # 7. GEMINI API KEY VISIBILITY BUTTON
    # ------------------------------------------------------------

    source = replace_exact(
        source,
        '''                    suffixIcon: IconButton(
                      onPressed: () {
                        HapticFeedback.selectionClick();
                        setSheetState(() => obscure = !obscure);
                      },
                      icon: Icon(
                        obscure
                            ? Icons.visibility_rounded
                            : Icons.visibility_off_rounded,
                      ),
                    ),''',
        '''                    suffixIcon: _BounceIconButton(
                      tooltip: obscure
                          ? 'Show API key'
                          : 'Hide API key',
                      onTap: () =>
                          setSheetState(() => obscure = !obscure),
                      icon: Icon(
                        obscure
                            ? Icons.visibility_rounded
                            : Icons.visibility_off_rounded,
                      ),
                    ),''',
        label="migrate API-key visibility action",
    )

    # ------------------------------------------------------------
    # 8. AI REVIEW DIALOG BUTTONS
    # ------------------------------------------------------------

    source = replace_exact(
        source,
        '''          TextButton(
            autofocus: true,
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('रद्द करें'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: Text(
              '${plan.actions.length} बदलाव लागू करें',
              style: TextStyle(
                color: plan.deleteCount > 0 ? appleRed : appleBlue,
                fontWeight: FontWeight.w900,
              ),
            ),
          ),''',
        '''          _BounceTextButton(
            autofocus: true,
            semanticLabel: 'रद्द करें',
            onTap: () => Navigator.pop(dialogContext, false),
            child: const Text('रद्द करें'),
          ),
          _BounceTextButton(
            semanticLabel:
                '${plan.actions.length} बदलाव लागू करें',
            onTap: () => Navigator.pop(dialogContext, true),
            child: Text(
              '${plan.actions.length} बदलाव लागू करें',
              style: TextStyle(
                color:
                    plan.deleteCount > 0
                        ? appleRed
                        : appleBlue,
                fontWeight: FontWeight.w900,
              ),
            ),
          ),''',
        label="migrate AI review dialog actions",
    )

    verify_patched(source)
    return source


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Apply Aarish Dairy Pro global bounce interaction fix."
        )
    )

    parser.add_argument(
        "--project",
        type=Path,
        default=DEFAULT_PROJECT,
        help=f"Flutter project root (default: {DEFAULT_PROJECT})",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the patch without writing files.",
    )

    parser.add_argument(
        "--no-format",
        action="store_true",
        help="Skip dart format even when Dart is installed.",
    )

    parser.add_argument(
        "--analyze",
        action="store_true",
        help=(
            "After patching, run: "
            "flutter analyze --no-pub lib/main.dart"
        ),
    )

    args = parser.parse_args()

    project = args.project.expanduser().resolve()
    target = project / "lib" / "main.dart"

    if not target.is_file():
        print(
            f"ERROR: main.dart not found: {target}",
            file=sys.stderr,
        )
        print(
            'Expected project root: "/root/Aarish Kingdom/repo"',
            file=sys.stderr,
        )
        return 2

    original = target.read_text(encoding="utf-8")
    already_patched = SENTINEL in original

    try:
        patched = patch_main(original)
    except PatchError as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 3

    if already_patched:
        print(
            "OK: global bounce patch is already present and verified."
        )

        if args.analyze:
            flutter = shutil.which("flutter")

            if flutter is None:
                print(
                    "WARN: flutter not found; skipping analyze."
                )
                return 0

            result = run_command(
                [
                    flutter,
                    "analyze",
                    "--no-pub",
                    "lib/main.dart",
                ],
                project,
            )

            print(result.stdout.rstrip())
            return result.returncode

        return 0

    if args.dry_run:
        print(
            "DRY RUN OK: source matched every expected surgical target."
        )
        print(
            "Would patch only:",
            target,
        )
        return 0

    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    backup = target.with_name(
        f"main.dart.bounce-backup-{stamp}"
    )

    shutil.copy2(
        target,
        backup,
    )

    temp = target.with_name(
        ".main.dart.bounce-tmp"
    )

    temp.write_text(
        patched,
        encoding="utf-8",
    )

    os.replace(
        temp,
        target,
    )

    try:
        if not args.no_format:
            dart = shutil.which("dart")

            if dart is None:
                print(
                    "WARN: dart not found; "
                    "patch written but formatter skipped."
                )
            else:
                result = run_command(
                    [
                        dart,
                        "format",
                        "lib/main.dart",
                    ],
                    project,
                )

                if result.returncode != 0:
                    shutil.copy2(
                        backup,
                        target,
                    )

                    raise PatchError(
                        "dart format failed; "
                        "original main.dart was restored.\n"
                        + result.stdout
                    )

        final_source = target.read_text(
            encoding="utf-8"
        )

        verify_patched(
            final_source
        )

    except Exception as exc:
        if target.exists() and backup.exists():
            shutil.copy2(
                backup,
                target,
            )

        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )

        print(
            f"RESTORED: {backup} -> {target}",
            file=sys.stderr,
        )

        return 4

    print()
    print(
        "SUCCESS: global bounce interaction system patched."
    )
    print(
        f"TARGET : {target}"
    )
    print(
        f"BACKUP : {backup}"
    )
    print(
        "CHANGED: route cards + AI Hub + Party Ledger + "
        "Diary cards + native text/icon actions"
    )
    print(
        "UNCHANGED: static/info cards, text fields, dropdowns, "
        "scroll behavior, data logic"
    )

    if args.analyze:
        flutter = shutil.which("flutter")

        if flutter is None:
            print(
                "WARN: flutter not found; skipping analyze."
            )
            return 0

        result = run_command(
            [
                flutter,
                "analyze",
                "--no-pub",
                "lib/main.dart",
            ],
            project,
        )

        print(
            result.stdout.rstrip()
        )

        if result.returncode != 0:
            print(
                "WARN: analyze reported issues. "
                "Patch was kept; backup path is shown above.",
                file=sys.stderr,
            )
            return result.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
