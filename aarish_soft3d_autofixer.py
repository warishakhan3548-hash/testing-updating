#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime

DEFAULT_PROJECT = Path('/root/Aarish Kingdom/repo')
SENTINEL = '// SOFT_3D_UI_V1'


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
            f'{label}: expected {count} exact match(es), '
            f'found {found}. Refusing to guess.'
        )
    return source.replace(old, new, count)


def replace_between(
    source: str,
    start: str,
    end: str,
    replacement: str,
    *,
    label: str,
) -> str:
    a = source.find(start)

    if a < 0:
        raise PatchError(
            f'{label}: start anchor not found.'
        )

    b = source.find(
        end,
        a + len(start),
    )

    if b < 0:
        raise PatchError(
            f'{label}: end anchor not found.'
        )

    if source.find(start, a + 1) >= 0:
        raise PatchError(
            f'{label}: start anchor is not unique.'
        )

    return (
        source[:a]
        + replacement
        + source[b:]
    )


def verify(source: str) -> None:
    checks = {
        'sentinel':
            SENTINEL in source,

        '3D surface system':
            'Image-10 inspired soft raised surface'
            in source,

        '3D jewel system':
            'Compact controls get a tighter raised profile'
            in source,

        'glass card palette':
            'Color(0xFFFDFEFF)' in source,

        'tables use central depth':
            source.count(
                'boxShadow: AppStyles.surfaceDepth(context),'
            ) >= 2,

        'AI ready card depth':
            'boxShadow: AppStyles.glow(context, purple),'
            in source,

        'AI batch card depth':
            'boxShadow: AppStyles.glow(context, appleBlue),'
            in source,

        'AI Hub central depth':
            (
                'boxShadow: AppStyles.jewelDepth('
                in source
                and
                'const Color(0xFF7957E8)'
                in source
            ),
    }

    failed = [
        name
        for name, ok in checks.items()
        if not ok
    ]

    if failed:
        raise PatchError(
            'verification failed: '
            + ', '.join(failed)
        )


def patch(source: str) -> str:
    if SENTINEL in source:
        verify(source)
        return source

    # ==========================================================
    # CORE SOFT 3D CARD DEPTH
    # ==========================================================

    source = replace_between(
        source,
        '  static List<BoxShadow> surfaceDepth(BuildContext context) {',
        '  // Equal raw opacity makes yellow/green glows look much louder than blue or',
        '''  static List<BoxShadow> surfaceDepth(BuildContext context) {
    // SOFT_3D_UI_V1
    // Image-10 inspired soft raised surface: bright upper-left key light,
    // tight contact shadow, then a broad lower-right falloff.
    final bool dark = isDark(context);
    final Color ink = dark
        ? Colors.black
        : const Color(0xFF26364D);

    return <BoxShadow>[
      BoxShadow(
        color: Colors.white.withAlpha(
          dark ? 9 : 190,
        ),
        blurRadius: dark ? 12 : 18,
        spreadRadius: dark ? -6 : -5,
        offset: const Offset(-5, -5),
      ),
      BoxShadow(
        color: ink.withAlpha(
          dark ? 92 : 24,
        ),
        blurRadius: 6,
        spreadRadius: -2,
        offset: const Offset(0, 3),
      ),
      BoxShadow(
        color: ink.withAlpha(
          dark ? 72 : 25,
        ),
        blurRadius: dark ? 26 : 30,
        spreadRadius: -7,
        offset: const Offset(8, 11),
      ),
      BoxShadow(
        color: ink.withAlpha(
          dark ? 38 : 12,
        ),
        blurRadius: 52,
        spreadRadius: -16,
        offset: const Offset(12, 20),
      ),
    ];
  }

''',
        label='surfaceDepth',
    )

    # ==========================================================
    # COLORED CARD DEPTH
    # ==========================================================

    source = replace_between(
        source,
        '  static List<BoxShadow> glow(\n',
        '  static List<BoxShadow> railDepth(BuildContext context, Color color) {',
        '''  static List<BoxShadow> glow(
    BuildContext context,
    Color color, {
    bool strong = false,
  }) {
    final bool dark = isDark(context);
    final Color ambient = _ambientHue(
      context,
      color,
    );

    return <BoxShadow>[
      // Accent stays close to the surface.
      // Depth comes from the physical shadow,
      // not from a neon halo.
      BoxShadow(
        color: ambient.withAlpha(
          _perceptualAlpha(
            ambient,
            strong
                ? (dark ? 50 : 29)
                : (dark ? 37 : 20),
          ),
        ),
        blurRadius: strong ? 18 : 14,
        spreadRadius: strong ? -3 : -4,
        offset: const Offset(1, 4),
      ),
      if (strong)
        BoxShadow(
          color: ambient.withAlpha(
            _perceptualAlpha(
              ambient,
              dark ? 22 : 13,
            ),
          ),
          blurRadius: 34,
          spreadRadius: -12,
          offset: const Offset(5, 10),
        ),
      ...surfaceDepth(context),
    ];
  }

''',
        label='glow',
    )

    # ==========================================================
    # LIST / ACCENT RAIL CARDS
    # ==========================================================

    source = replace_between(
        source,
        '  static List<BoxShadow> railDepth(BuildContext context, Color color) {',
        '  static List<BoxShadow> pressGlow(\n',
        '''  static List<BoxShadow> railDepth(
    BuildContext context,
    Color color,
  ) {
    final bool dark = isDark(context);
    final Color ambient = _ambientHue(
      context,
      color,
    );

    return <BoxShadow>[
      BoxShadow(
        color: ambient.withAlpha(
          _perceptualAlpha(
            ambient,
            dark ? 43 : 24,
          ),
        ),
        blurRadius: 17,
        spreadRadius: -4,
        offset: const Offset(1, 5),
      ),
      ...surfaceDepth(context),
    ];
  }

''',
        label='railDepth',
    )

    # ==========================================================
    # SMALL BUTTON / ICON DEPTH
    # ==========================================================

    source = replace_between(
        source,
        '  static List<BoxShadow> jewelDepth(BuildContext context, Color color) {',
        '  static Border glassBorder(BuildContext context, {Color? accent}) {',
        '''  static List<BoxShadow> jewelDepth(
    BuildContext context,
    Color color,
  ) {
    // Compact controls get a tighter raised profile than full-size cards.
    final bool dark = isDark(context);

    return <BoxShadow>[
      BoxShadow(
        color: Colors.white.withAlpha(
          dark ? 11 : 165,
        ),
        blurRadius: 10,
        spreadRadius: -5,
        offset: const Offset(-3, -3),
      ),
      BoxShadow(
        color: color.withAlpha(
          dark ? 38 : 24,
        ),
        blurRadius: 14,
        spreadRadius: -5,
        offset: const Offset(2, 5),
      ),
      BoxShadow(
        color: Colors.black.withAlpha(
          dark ? 72 : 18,
        ),
        blurRadius: 18,
        spreadRadius: -6,
        offset: const Offset(6, 9),
      ),
    ];
  }

''',
        label='jewelDepth',
    )

    # ==========================================================
    # MASTER GLASS CARD SURFACE
    # ==========================================================

    source = replace_exact(
        source,
        '''      surfaceColors = dark
          ? const <Color>[Color(0xF0121826), Color(0xE3080C18)]
          : const <Color>[Color(0xFAFFFFFF), Color(0xF2FFFFFF)];''',
        '''      surfaceColors = dark
          ? const <Color>[
              Color(0xF2161D29),
              Color(0xED0B1019),
            ]
          : const <Color>[
              Color(0xFFFDFEFF),
              Color(0xFFF3F6FA),
            ];''',
        label='GlassCard neutral surface palette',
    )

    source = replace_exact(
        source,
        '''          : <Color>[
              Color.lerp(Colors.white, tintColor, .055)!.withAlpha(248),
              Color.lerp(Colors.white, tintColor, .028)!.withAlpha(236),
            ];''',
        '''          : <Color>[
              Color.lerp(
                const Color(0xFFFDFEFF),
                tintColor,
                .075,
              )!.withAlpha(252),
              Color.lerp(
                const Color(0xFFF1F5F9),
                tintColor,
                .045,
              )!.withAlpha(244),
            ];''',
        label='GlassCard tinted light palette',
    )

    source = replace_exact(
        source,
        '''          ? <Color>[
              Color.lerp(darkGlassTop, tintColor, .12)!.withAlpha(240),
              Color.lerp(darkGlassBottom, tintColor, .06)!.withAlpha(224),
            ]''',
        '''          ? <Color>[
              Color.lerp(
                darkGlassTop,
                tintColor,
                .14,
              )!.withAlpha(244),
              Color.lerp(
                darkGlassBottom,
                tintColor,
                .075,
              )!.withAlpha(230),
            ]''',
        label='GlassCard tinted dark palette',
    )

    # ==========================================================
    # TABLE OUTER SHELLS
    # Keep individual rows flat and readable.
    # ==========================================================

    table_shadow_old = '''        boxShadow: dark
            ? const <BoxShadow>[]
            : <BoxShadow>[
                BoxShadow(
                  color: const Color(0xFF183960).withAlpha(16),
                  blurRadius: 30,
                  offset: const Offset(0, 13),
                ),
              ],'''

    source = replace_exact(
        source,
        table_shadow_old,
        '''        boxShadow:
            AppStyles.surfaceDepth(context),''',
        label='table outer 3D depth',
        count=2,
    )

    # ==========================================================
    # AI READY CARD
    # ==========================================================

    source = replace_exact(
        source,
        '''        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: purple.withAlpha(dark ? 78 : 48)),
      ),''',
        '''        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: purple.withAlpha(
            dark ? 78 : 48,
          ),
        ),
        boxShadow: AppStyles.glow(
          context,
          purple,
        ),
      ),''',
        label='External AI ready card depth',
    )

    # ==========================================================
    # AI BATCH STATUS CARD
    # ==========================================================

    source = replace_exact(
        source,
        '''        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: appleBlue.withAlpha(dark ? 68 : 42)),
      ),''',
        '''        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: appleBlue.withAlpha(
            dark ? 68 : 42,
          ),
        ),
        boxShadow: AppStyles.glow(
          context,
          appleBlue,
        ),
      ),''',
        label='AI batch card depth',
    )

    # ==========================================================
    # AI HUB
    # Compact button => tighter 3D, not full card depth.
    # ==========================================================

    source = replace_exact(
        source,
        '''          boxShadow: <BoxShadow>[
            BoxShadow(
              color: const Color(0xFF7957E8).withAlpha(dark ? 76 : 54),
              blurRadius: 18,
              spreadRadius: -5,
              offset: const Offset(0, 6),
            ),
            BoxShadow(
              color: Colors.black.withAlpha(dark ? 34 : 12),
              blurRadius: 6,
              spreadRadius: -2,
              offset: const Offset(0, 2),
            ),
          ],''',
        '''          boxShadow: AppStyles.jewelDepth(
            context,
            const Color(0xFF7957E8),
          ),''',
        label='AI Hub compact 3D depth',
    )

    verify(source)

    return source


def run(
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            'Apply smart Image-10 inspired '
            'soft 3D UI styling to Aarish Dairy Pro.'
        ),
    )

    parser.add_argument(
        '--project',
        type=Path,
        default=DEFAULT_PROJECT,
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
    )

    parser.add_argument(
        '--no-format',
        action='store_true',
    )

    parser.add_argument(
        '--analyze',
        action='store_true',
        help=(
            'Run flutter analyze --no-pub '
            'lib/main.dart after patching.'
        ),
    )

    args = parser.parse_args()

    project = (
        args.project
        .expanduser()
        .resolve()
    )

    target = (
        project
        / 'lib'
        / 'main.dart'
    )

    if not target.is_file():
        print(
            f'ERROR: main.dart not found: {target}',
            file=sys.stderr,
        )

        print(
            'Expected project: '
            '/root/Aarish Kingdom/repo',
            file=sys.stderr,
        )

        return 2

    original = target.read_text(
        encoding='utf-8',
    )

    already = SENTINEL in original

    try:
        updated = patch(original)

    except PatchError as exc:
        print(
            f'ERROR: {exc}',
            file=sys.stderr,
        )

        return 3

    if already:
        print(
            'OK: soft 3D UI patch is already '
            'present and verified.'
        )

        if args.analyze:
            flutter = shutil.which(
                'flutter',
            )

            if flutter is None:
                print(
                    'WARN: flutter not found; '
                    'skipping analyze.'
                )
                return 0

            result = run(
                [
                    flutter,
                    'analyze',
                    '--no-pub',
                    'lib/main.dart',
                ],
                project,
            )

            print(
                result.stdout.rstrip()
            )

            return result.returncode

        return 0

    if args.dry_run:
        print(
            'DRY RUN OK: every expected '
            '3D UI target matched safely.'
        )

        print(
            f'Would patch: {target}'
        )

        return 0

    stamp = datetime.now().strftime(
        '%Y%m%d-%H%M%S',
    )

    backup = target.with_name(
        f'main.dart.soft3d-backup-{stamp}',
    )

    shutil.copy2(
        target,
        backup,
    )

    temp = target.with_name(
        '.main.dart.soft3d-tmp',
    )

    temp.write_text(
        updated,
        encoding='utf-8',
    )

    os.replace(
        temp,
        target,
    )

    try:
        if not args.no_format:
            dart = shutil.which(
                'dart',
            )

            if dart is None:
                print(
                    'WARN: dart not found; '
                    'formatter skipped.'
                )

            else:
                result = run(
                    [
                        dart,
                        'format',
                        'lib/main.dart',
                    ],
                    project,
                )

                if result.returncode != 0:
                    shutil.copy2(
                        backup,
                        target,
                    )

                    raise PatchError(
                        'dart format failed; '
                        'original restored.\n'
                        + result.stdout
                    )

        verify(
            target.read_text(
                encoding='utf-8',
            )
        )

    except Exception as exc:
        shutil.copy2(
            backup,
            target,
        )

        print(
            f'ERROR: {exc}',
            file=sys.stderr,
        )

        print(
            f'RESTORED: {backup} -> {target}',
            file=sys.stderr,
        )

        return 4

    print()
    print(
        'SUCCESS: smart soft-3D UI system applied.'
    )

    print(
        f'TARGET : {target}'
    )

    print(
        f'BACKUP : {backup}'
    )

    print(
        '3D STRONG : Glass cards, metric/list/'
        'diary/business/party cards, hero cards'
    )

    print(
        '3D MEDIUM : Add/Share/transaction/mini/'
        'circle/delete/back/AI Hub buttons'
    )

    print(
        '3D SUBTLE : Milk + ledger table outer '
        'shells, AI status cards'
    )

    print(
        'KEPT CLEAN: text fields, search fields, '
        'dropdowns, table rows, dividers, '
        'page backgrounds'
    )

    if args.analyze:
        flutter = shutil.which(
            'flutter',
        )

        if flutter is None:
            print(
                'WARN: flutter not found; '
                'skipping analyze.'
            )

            return 0

        result = run(
            [
                flutter,
                'analyze',
                '--no-pub',
                'lib/main.dart',
            ],
            project,
        )

        print(
            result.stdout.rstrip()
        )

        if result.returncode != 0:
            print(
                'WARN: flutter analyze reported '
                'issues. Patch kept; backup '
                'is available.',
                file=sys.stderr,
            )

        return result.returncode

    return 0


if __name__ == '__main__':
    raise SystemExit(
        main()
    )
