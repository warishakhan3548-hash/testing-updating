#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_PROJECT = Path('/root/Aarish Kingdom/repo')
SENTINEL = '// SOFT_3D_UI_V2'


class PatchError(RuntimeError):
    pass


def replace_between(
    source: str,
    start: str,
    end: str,
    replacement: str,
    label: str,
) -> str:
    a = source.find(start)
    if a < 0:
        raise PatchError(f'{label}: start anchor not found')

    b = source.find(end, a + len(start))
    if b < 0:
        raise PatchError(f'{label}: end anchor not found')

    if source.find(start, a + 1) >= 0:
        raise PatchError(f'{label}: start anchor is not unique')

    return source[:a] + replacement + source[b:]


def class_segment(
    source: str,
    start: str,
    end: str,
) -> tuple[int, int, str]:
    a = source.find(start)
    if a < 0:
        raise PatchError(f'{start}: class not found')

    b = source.find(end, a + len(start))
    if b < 0:
        raise PatchError(f'{start}: end class anchor not found')

    return a, b, source[a:b]


def update_segment(
    source: str,
    start: str,
    end: str,
    transform,
) -> str:
    a, b, segment = class_segment(source, start, end)
    updated = transform(segment)
    return source[:a] + updated + source[b:]


def patch_table_segment(segment: str) -> str:
    wanted = 'boxShadow: AppStyles.surfaceDepth(context),'

    if wanted in segment:
        return segment

    pattern = re.compile(
        r'boxShadow:\s*[\s\S]*?\n\s*\),\n\s*child: LayoutBuilder\(',
        re.MULTILINE,
    )

    replacement = (
        'boxShadow: AppStyles.surfaceDepth(context),\n'
        '      ),\n'
        '      child: LayoutBuilder('
    )

    updated, count = pattern.subn(
        replacement,
        segment,
        count=1,
    )

    if count != 1:
        raise PatchError(
            'table outer shadow block not found safely'
        )

    return updated


def patch_ai_card(
    segment: str,
    color_name: str,
) -> str:
    wanted = (
        f'boxShadow: AppStyles.glow(context, {color_name}),'
    )

    if wanted in segment:
        return segment

    pattern = re.compile(
        rf'(border:\s*Border\.all'
        rf'\(color:\s*{re.escape(color_name)}'
        rf'\.withAlpha\([^\n]+\)\),)'
    )

    updated, count = pattern.subn(
        rf'\1\n        {wanted}',
        segment,
        count=1,
    )

    if count != 1:
        raise PatchError(
            f'{color_name} AI card border anchor '
            'not found safely'
        )

    return updated


def patch_ai_hub(segment: str) -> str:
    if 'boxShadow: AppStyles.jewelDepth(' in segment:
        return segment

    pattern = re.compile(
        r'boxShadow:\s*<BoxShadow>\['
        r'[\s\S]*?\n\s*\],',
        re.MULTILINE,
    )

    replacement = '''boxShadow: AppStyles.jewelDepth(
            context,
            const Color(0xFF7957E8),
          ),'''

    updated, count = pattern.subn(
        replacement,
        segment,
        count=1,
    )

    if count != 1:
        raise PatchError(
            'AI Hub shadow block not found safely'
        )

    return updated


def verify(source: str) -> None:
    missing: list[str] = []

    required = [
        SENTINEL,
        'Image-10 inspired soft raised surface',
        'Compact controls get a tighter raised profile',
        'Color(0xFFFDFEFF)',
    ]

    for item in required:
        if item not in source:
            missing.append(item)

    checks = [
        (
            'class _MilkRecordsTable',
            'class _MilkTableHeader',
            'boxShadow: AppStyles.surfaceDepth(context),',
            'Milk table',
        ),
        (
            'class _LedgerTableCard',
            'class _LedgerDeleteAction',
            'boxShadow: AppStyles.surfaceDepth(context),',
            'Ledger table',
        ),
        (
            'class _ExternalAiReadyCard',
            'class _AiBatchProgressCard',
            'boxShadow: AppStyles.glow(context, purple),',
            'AI ready card',
        ),
        (
            'class _AiHubButton',
            'class DashboardScreen',
            'boxShadow: AppStyles.jewelDepth(',
            'AI Hub',
        ),
    ]

    for start, end, needle, label in checks:
        try:
            _, _, segment = class_segment(
                source,
                start,
                end,
            )

            if needle not in segment:
                missing.append(label)

        except PatchError:
            if needle not in source:
                missing.append(label)

    if (
        'boxShadow: AppStyles.glow(context, appleBlue),'
        not in source
    ):
        missing.append('AI batch card')

    if missing:
        raise PatchError(
            'verification failed: '
            + ', '.join(missing)
        )


def patch(source: str) -> str:

    # ----------------------------------------------------------
    # MASTER CARD 3D DEPTH
    # ----------------------------------------------------------

    source = replace_between(
        source,
        '  static List<BoxShadow> surfaceDepth(BuildContext context) {',
        '  // Equal raw opacity makes yellow/green glows look much louder than blue or',
        '''  static List<BoxShadow> surfaceDepth(BuildContext context) {
    // SOFT_3D_UI_V2
    // Image-10 inspired soft raised surface:
    // bright upper-left key light,
    // compact contact shadow,
    // broad lower-right falloff.
    final bool dark = isDark(context);

    final Color ink =
        dark
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
        'surfaceDepth',
    )

    # ----------------------------------------------------------
    # COLORED CARD / BUTTON DEPTH
    # ----------------------------------------------------------

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
    final Color ambient =
        _ambientHue(context, color);

    return <BoxShadow>[
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
        'glow',
    )

    # ----------------------------------------------------------
    # LIST CARD ACCENT DEPTH
    # ----------------------------------------------------------

    source = replace_between(
        source,
        '  static List<BoxShadow> railDepth(BuildContext context, Color color) {',
        '  static List<BoxShadow> pressGlow(\n',
        '''  static List<BoxShadow> railDepth(
    BuildContext context,
    Color color,
  ) {
    final bool dark = isDark(context);
    final Color ambient =
        _ambientHue(context, color);

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
        'railDepth',
    )

    # ----------------------------------------------------------
    # COMPACT BUTTON 3D
    # ----------------------------------------------------------

    source = replace_between(
        source,
        '  static List<BoxShadow> jewelDepth(BuildContext context, Color color) {',
        '  static Border glassBorder(BuildContext context, {Color? accent}) {',
        '''  static List<BoxShadow> jewelDepth(
    BuildContext context,
    Color color,
  ) {
    // Compact controls get a tighter raised profile
    // than full-size cards.
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
        'jewelDepth',
    )

    # ----------------------------------------------------------
    # MASTER GLASS CARD COLORS
    # ----------------------------------------------------------

    source = replace_between(
        source,
        '    if (tintColor == null) {',
        '    final Border border =',
        '''    if (tintColor == null) {
      surfaceColors = dark
          ? const <Color>[
              Color(0xF2161D29),
              Color(0xED0B1019),
            ]
          : const <Color>[
              Color(0xFFFDFEFF),
              Color(0xFFF3F6FA),
            ];
    } else {
      surfaceColors = dark
          ? <Color>[
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
            ]
          : <Color>[
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
            ];
    }
''',
        'GlassCard palette',
    )

    # ----------------------------------------------------------
    # TABLE OUTER SHELLS
    # Individual rows stay flat.
    # ----------------------------------------------------------

    source = update_segment(
        source,
        'class _MilkRecordsTable',
        'class _MilkTableHeader',
        patch_table_segment,
    )

    source = update_segment(
        source,
        'class _LedgerTableCard',
        'class _LedgerDeleteAction',
        patch_table_segment,
    )

    # ----------------------------------------------------------
    # AI STATUS CARDS
    # ----------------------------------------------------------

    source = update_segment(
        source,
        'class _ExternalAiReadyCard',
        'class _AiBatchProgressCard',
        lambda segment:
            patch_ai_card(
                segment,
                'purple',
            ),
    )

    batch_start = 'class _AiBatchProgressCard'

    batch_candidates = [
        'class _ExternalAiSessionDivider',
        'class _AiChatBubble',
        'class _AiComposer',
        'class AiHubScreen',
        'class _AiHubScreenState',
    ]

    start_pos = source.find(batch_start)

    batch_end = next(
        (
            name
            for name in batch_candidates
            if source.find(
                name,
                start_pos + 1,
            ) >= 0
        ),
        None,
    )

    if batch_end is None:
        match = re.search(
            r'\nclass [A-Za-z_][A-Za-z0-9_]*',
            source[
                start_pos + len(batch_start):
            ],
        )

        if not match:
            raise PatchError(
                'AI batch end anchor not found'
            )

        batch_end = match.group(0).strip()

    source = update_segment(
        source,
        batch_start,
        batch_end,
        lambda segment:
            patch_ai_card(
                segment,
                'appleBlue',
            ),
    )

    # ----------------------------------------------------------
    # AI HUB COMPACT BUTTON
    # ----------------------------------------------------------

    source = update_segment(
        source,
        'class _AiHubButton',
        'class DashboardScreen',
        patch_ai_hub,
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
    parser = argparse.ArgumentParser()

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
            f'ERROR: main.dart not found: '
            f'{target}',
            file=sys.stderr,
        )
        return 2

    original = target.read_text(
        encoding='utf-8'
    )

    try:
        updated = patch(original)
    except PatchError as exc:
        print(
            f'ERROR: {exc}',
            file=sys.stderr,
        )
        return 3

    if args.dry_run:
        print()
        print(
            'DRY RUN OK: current source can '
            'be safely repaired/applied.'
        )
        print(
            f'TARGET: {target}'
        )
        return 0

    stamp = datetime.now().strftime(
        '%Y%m%d-%H%M%S'
    )

    backup = target.with_name(
        f'main.dart.soft3d-backup-{stamp}'
    )

    shutil.copy2(
        target,
        backup,
    )

    temp = target.with_name(
        '.main.dart.soft3d-v2-tmp'
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
            dart = shutil.which('dart')

            if dart:
                result = run(
                    [
                        dart,
                        'format',
                        'lib/main.dart',
                    ],
                    project,
                )

                if result.returncode != 0:
                    raise PatchError(
                        'dart format failed:\n'
                        + result.stdout
                    )
            else:
                print(
                    'WARN: dart not found; '
                    'format skipped.'
                )

        verify(
            target.read_text(
                encoding='utf-8'
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
            f'RESTORED: {backup}',
            file=sys.stderr,
        )

        return 4

    print()
    print(
        'SUCCESS: soft 3D V2 '
        'applied/repaired safely.'
    )

    print(
        f'BACKUP: {backup}'
    )

    print(
        'Cards: strong soft-3D'
    )

    print(
        'Buttons: compact premium 3D'
    )

    print(
        'Inputs/table rows: kept clean'
    )

    if args.analyze:
        flutter = shutil.which(
            'flutter'
        )

        if flutter:
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

        print(
            'WARN: flutter not found; '
            'analyze skipped.'
        )

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
