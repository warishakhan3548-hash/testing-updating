#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path('/root/Aarish Kingdom/repo')
TARGET = ROOT / 'lib/main.dart'

OLD_MARK = '// SOFT_NEUMORPHIC_LUXE_SELECTED_V1'
NEW_MARK = '// DARK_SOFT_NEUMORPHIC_LUXE_V2'


class PatchError(RuntimeError):
    pass


def region(
    text: str,
    start_token: str,
    end_token: str,
) -> tuple[int, int, str]:
    start = text.find(start_token)

    if start < 0:
        raise PatchError(
            f'missing start anchor: {start_token}'
        )

    end = text.find(
        end_token,
        start + len(start_token),
    )

    if end < 0:
        raise PatchError(
            f'missing end anchor: {end_token}'
        )

    return start, end, text[start:end]


def exact(
    text: str,
    old: str,
    new: str,
    label: str,
    expected: int = 1,
) -> str:
    count = text.count(old)

    if count != expected:
        raise PatchError(
            f'{label}: expected {expected} exact match(es), '
            f'found {count}'
        )

    return text.replace(
        old,
        new,
        expected,
    )


def patch_region(
    text: str,
    start: str,
    end: str,
    edits,
) -> str:
    a, b, body = region(
        text,
        start,
        end,
    )

    for old, new, label, count in edits:
        body = exact(
            body,
            old,
            new,
            label,
            count,
        )

    return text[:a] + body + text[b:]


def patch(source: str) -> str:
    if NEW_MARK in source:
        return source

    if OLD_MARK not in source:
        raise PatchError(
            'Soft Neumorphic Luxe marker missing. '
            'Unexpected main.dart; refusing blind patch.'
        )

    text = source

    # ============================================================
    # 1. SHARED DARK PHYSICAL DEPTH
    # Light values remain exactly unchanged.
    # ============================================================

    text = patch_region(
        text,
        '  static List<BoxShadow> surfaceDepth(BuildContext context) {',
        '  // Equal raw opacity makes yellow/green glows look much louder than blue or',
        [
            (
                'Colors.white.withAlpha(dark ? 12 : 248)',
                'Colors.white.withAlpha(dark ? 52 : 248)',
                'surface top highlight',
                1,
            ),
            (
                'blurRadius: dark ? 13 : 18,',
                'blurRadius: dark ? 17 : 18,',
                'surface highlight blur',
                1,
            ),
            (
                'ink.withAlpha(dark ? 102 : 38)',
                'ink.withAlpha(dark ? 148 : 38)',
                'surface contact shadow',
                1,
            ),
            (
                'blurRadius: 3.5,',
                'blurRadius: dark ? 5.5 : 3.5,',
                'surface contact blur',
                1,
            ),
            (
                'ink.withAlpha(dark ? 70 : 24)',
                'ink.withAlpha(dark ? 96 : 24)',
                'surface grounding shadow',
                1,
            ),
            (
                'blurRadius: dark ? 27 : 25,',
                'blurRadius: dark ? 34 : 25,',
                'surface grounding blur',
                1,
            ),
            (
                'offset: const Offset(8, 12),',
                'offset: Offset(dark ? 9 : 8, dark ? 15 : 12),',
                'surface grounding offset',
                1,
            ),
        ],
    )

    # ============================================================
    # 2. RAISED ICON / AVATAR JEWEL DEPTH
    # ============================================================

    text = patch_region(
        text,
        '  static List<BoxShadow> jewelDepth(BuildContext context, Color color) {',
        '  static Border glassBorder(BuildContext context, {Color? accent}) {',
        [
            (
                'Colors.white.withAlpha(dark ? 13 : 238)',
                'Colors.white.withAlpha(dark ? 58 : 238)',
                'jewel highlight',
                1,
            ),
            (
                'blurRadius: 11,',
                'blurRadius: dark ? 15 : 11,',
                'jewel highlight blur',
                1,
            ),
            (
                'color.withAlpha(dark ? 46 : 40)',
                'color.withAlpha(dark ? 58 : 40)',
                'jewel semantic light',
                1,
            ),
            (
                'Colors.black.withAlpha(dark ? 84 : 28)',
                'Colors.black.withAlpha(dark ? 126 : 28)',
                'jewel contact shadow',
                1,
            ),
            (
                'blurRadius: 3.5,',
                'blurRadius: dark ? 5 : 3.5,',
                'jewel contact blur',
                1,
            ),
            (
                'Colors.black.withAlpha(dark ? 66 : 17)',
                'Colors.black.withAlpha(dark ? 90 : 17)',
                'jewel grounding shadow',
                1,
            ),
            (
                'blurRadius: 18,',
                'blurRadius: dark ? 23 : 18,',
                'jewel grounding blur',
                1,
            ),
        ],
    )

    # ============================================================
    # 3. DARK BACKGROUND
    # Deep navy/charcoal instead of pure black.
    # Ambient glows reduced so cards stand forward.
    # ============================================================

    text = patch_region(
        text,
        'class _AmbientPainter extends CustomPainter {',
        'class _OpaqueContentTransitionsBuilder extends PageTransitionsBuilder {',
        [
            (
                'dark ? Colors.black : lightCanvas',
                'dark ? const Color(0xFF060A12) : lightCanvas',
                'dark canvas',
                1,
            ),
            (
                'appleGreen.withAlpha(dark ? 47 : 28)',
                'appleGreen.withAlpha(dark ? 24 : 28)',
                'ambient green',
                1,
            ),
            (
                'appleBlue2.withAlpha(dark ? 48 : 24)',
                'appleBlue2.withAlpha(dark ? 26 : 24)',
                'ambient blue',
                1,
            ),
            (
                'diaryOrange.withAlpha(dark ? 17 : 10)',
                'diaryOrange.withAlpha(dark ? 10 : 10)',
                'ambient orange',
                1,
            ),
        ],
    )

    # ============================================================
    # 4. CORE CARD MATERIAL
    # Most important part.
    # White Luxe branch is untouched.
    # ============================================================

    text = patch_region(
        text,
        'class _GlassCard extends StatelessWidget {',
        'class _CardAccentPainter extends CustomPainter {',
        [
            (
                """Color(0xFF1A2230),
              Color(0xFF111823),
              Color(0xFF0A0F18),""",
                """Color(0xFF202A38),
              Color(0xFF141C27),
              Color(0xFF0B111B),""",
                'glass neutral dark face',
                1,
            ),

            (
                'Color.lerp(const Color(0xFF1A2230), tintColor, .10)!',
                'Color.lerp(const Color(0xFF202A38), tintColor, .12)!',
                'glass tinted top',
                1,
            ),

            (
                'Color.lerp(const Color(0xFF111823), tintColor, .07)!',
                'Color.lerp(const Color(0xFF141C27), tintColor, .09)!',
                'glass tinted middle',
                1,
            ),

            (
                'Color.lerp(const Color(0xFF0A0F18), tintColor, .04)!',
                'Color.lerp(const Color(0xFF0B111B), tintColor, .055)!',
                'glass tinted bottom',
                1,
            ),

            (
                """? Colors.white.withAlpha(30)
          : const Color(0xFFFFFFFF);""",
                """? Colors.white.withAlpha(54)
          : const Color(0xFFFFFFFF);""",
                'glass neutral rim',
                1,
            ),

            (
                'semantic.withAlpha(dark ? 28 : 17)',
                'semantic.withAlpha(dark ? 46 : 17)',
                'glass semantic rim',
                1,
            ),

            (
                'dark ? Colors.white.withAlpha(30) : const Color(0xF0FFFFFF)',
                'dark ? Colors.white.withAlpha(48) : const Color(0xF0FFFFFF)',
                'glass semantic neutral rim',
                1,
            ),

            (
                """? (dark ? 58 : 46)
                  : tintColor != null
                  ? (dark ? 64 : 52)
                  : (dark ? 50 : 40)""",
                """? (dark ? 44 : 46)
                  : tintColor != null
                  ? (dark ? 48 : 52)
                  : (dark ? 38 : 40)""",
                'restrained dark glow',
                1,
            ),

            (
                'AppStyles._perceptualAlpha(ambient, dark ? 26 : 21)',
                'AppStyles._perceptualAlpha(ambient, dark ? 18 : 21)',
                'secondary glow',
                1,
            ),

            (
                '.withAlpha(dark ? 34 : 9)',
                '.withAlpha(dark ? 50 : 9)',
                'grounding alpha',
                1,
            ),

            (
                'blurRadius: 19,',
                'blurRadius: dark ? 24 : 19,',
                'grounding blur',
                1,
            ),

            (
                'Colors.white.withAlpha(dark ? 22 : 148)',
                'Colors.white.withAlpha(dark ? 72 : 148)',
                'specular bevel',
                1,
            ),

            (
                'Colors.black.withAlpha(dark ? 30 : 12)',
                'Colors.black.withAlpha(dark ? 46 : 12)',
                'lower bevel',
                1,
            ),

            (
                'semantic.withAlpha(dark ? 22 : 15)',
                'semantic.withAlpha(dark ? 30 : 15)',
                'inner semantic light',
                1,
            ),

            (
                OLD_MARK,
                OLD_MARK + '\n    ' + NEW_MARK,
                'dark marker',
                1,
            ),
        ],
    )

    # ============================================================
    # 5. HEADER ACTION BUTTONS
    # ============================================================

    text = patch_region(
        text,
        'class _CircleAction extends StatelessWidget {',
        'class _DeleteActionButton extends StatelessWidget {',
        [
            (
                'Color.lerp(const Color(0xFF1B2432), color, .16)!',
                'Color.lerp(const Color(0xFF202A38), color, .20)!',
                'circle top',
                1,
            ),
            (
                'Color.lerp(const Color(0xFF0D131C), color, .08)!',
                'Color.lerp(const Color(0xFF0B111A), color, .10)!',
                'circle bottom',
                1,
            ),
            (
                'color.withAlpha(dark ? 84 : 62)',
                'color.withAlpha(dark ? 98 : 62)',
                'circle rim',
                1,
            ),
        ],
    )

    # ============================================================
    # 6. BACK BUTTON
    # ============================================================

    text = patch_region(
        text,
        'class _BackCircle extends StatelessWidget {',
        'class _BounceTextButton extends StatelessWidget {',
        [
            (
                'colors: <Color>[Color(0xFF1B2432), Color(0xFF0D131C)]',
                'colors: <Color>[Color(0xFF202A38), Color(0xFF0B111A)]',
                'back face',
                1,
            ),
            (
                'appleBlue.withAlpha(dark ? 62 : 34)',
                'appleBlue.withAlpha(dark ? 88 : 34)',
                'back rim',
                1,
            ),
        ],
    )

    # ============================================================
    # 7. SEARCH BAR
    # ============================================================

    text = patch_region(
        text,
        'class _SearchBoxState extends State<_SearchBox> {',
        'class _DateField extends StatelessWidget {',
        [
            (
                'widget.color.withAlpha(dark ? 38 : 25)',
                'widget.color.withAlpha(dark ? 48 : 25)',
                'search semantic edge',
                1,
            ),
            (
                'dark ? Colors.white.withAlpha(28) : const Color(0xE8FFFFFF)',
                'dark ? Colors.white.withAlpha(44) : const Color(0xE8FFFFFF)',
                'search neutral edge',
                1,
            ),
            (
                '? const <Color>[Color(0xFF1A2230), Color(0xFF0D131D)]',
                '? const <Color>[Color(0xFF202A38), Color(0xFF0B111A)]',
                'search face',
                1,
            ),
        ],
    )

    # ============================================================
    # 8. PARTY LEDGER + ALL SHARED LIST CARD AVATARS
    # ============================================================

    text = patch_region(
        text,
        'class _ListCard extends StatelessWidget {',
        'class _SectionTitle extends StatelessWidget {',
        [
            (
                'Color.lerp(const Color(0xFF1B2432), color, .18)!',
                'Color.lerp(const Color(0xFF202A38), color, .24)!',
                'list avatar top',
                1,
            ),
            (
                'Color.lerp(const Color(0xFF0D131C), color, .10)!',
                'Color.lerp(const Color(0xFF0B111A), color, .13)!',
                'list avatar bottom',
                1,
            ),
            (
                'color.withAlpha(dark ? 102 : 84)',
                'color.withAlpha(dark ? 116 : 84)',
                'list avatar rim',
                1,
            ),
        ],
    )

    # ============================================================
    # 9. DASHBOARD / CARD ICON TILE
    # ============================================================

    text = patch_region(
        text,
        'class _LedgerIcon extends StatelessWidget {',
        'class PartyLedgerScreen extends StatefulWidget {',
        [
            (
                'Color.lerp(const Color(0xFF1B2432), color, .18)!',
                'Color.lerp(const Color(0xFF202A38), color, .24)!',
                'ledger icon top',
                1,
            ),
            (
                'Color.lerp(const Color(0xFF0D131C), color, .09)!',
                'Color.lerp(const Color(0xFF0B111A), color, .13)!',
                'ledger icon bottom',
                1,
            ),
            (
                'color.withAlpha(dark ? 104 : 86)',
                'color.withAlpha(dark ? 116 : 86)',
                'ledger icon rim',
                1,
            ),
            (
                'Colors.white.withAlpha(dark ? 78 : 232)',
                'Colors.white.withAlpha(dark ? 104 : 232)',
                'ledger icon highlight',
                1,
            ),
        ],
    )

    # ============================================================
    # 10. BOTTOM NAVIGATION SURFACE
    # ============================================================

    text = patch_region(
        text,
        'class _BottomLedgerNav extends StatelessWidget {',
        '// PREMIUM_NAV_V2',
        [
            (
                '? const <Color>[Color(0xFF18202D), Color(0xFF0B111A)]',
                '? const <Color>[Color(0xFF1E2937), Color(0xFF0A1019)]',
                'bottom nav face',
                1,
            ),
            (
                """? Colors.white.withAlpha(28)
                    : Colors.white.withAlpha(230)""",
                """? Colors.white.withAlpha(48)
                    : Colors.white.withAlpha(230)""",
                'bottom nav rim',
                1,
            ),
        ],
    )

    # ============================================================
    # 11. ACTIVE BOTTOM NAV ICON TILE
    # ============================================================

    text = patch_region(
        text,
        'class _PremiumNavIconFrame extends StatelessWidget {',
        'class _BottomNavGlyph extends StatelessWidget {',
        [
            (
                'Color.lerp(const Color(0xFF1B2432), color, .18)!',
                'Color.lerp(const Color(0xFF202A38), color, .23)!',
                'nav icon top',
                1,
            ),
            (
                'Color.lerp(const Color(0xFF0D131C), color, .09)!',
                'Color.lerp(const Color(0xFF0B111A), color, .12)!',
                'nav icon bottom',
                1,
            ),
            (
                'color.withAlpha(active ? (dark ? 82 : 66) : (dark ? 24 : 18))',
                'color.withAlpha(active ? (dark ? 104 : 66) : (dark ? 30 : 18))',
                'nav icon rim',
                1,
            ),
        ],
    )

    return text


def verify(before: str, after: str) -> None:
    if before == after:
        raise PatchError(
            'patch produced no changes'
        )

    if after.count(OLD_MARK) != 1:
        raise PatchError(
            'Soft Luxe marker verification failed'
        )

    if after.count(NEW_MARK) != 1:
        raise PatchError(
            'Dark V2 marker verification failed'
        )

    dark_required = (
        'Color(0xFF060A12)',
        'Color(0xFF202A38)',
        'Colors.white.withAlpha(dark ? 52 : 248)',
        'ink.withAlpha(dark ? 148 : 38)',
        'Colors.white.withAlpha(dark ? 72 : 148)',
        'Color(0xFF1E2937)',
    )

    for token in dark_required:
        if token not in after:
            raise PatchError(
                f'dark verification missing: {token}'
            )

    # White-mode selected Luxe contract.
    light_required = (
        'Color.lerp(Colors.white, tintColor, .040)!',
        'Color.lerp(const Color(0xFFFAFCFE), tintColor, .028)!',
        'Color.lerp(const Color(0xFFEEF2F6), tintColor, .018)!',
        'Colors.white.withAlpha(dark ? 72 : 148)',
        'Colors.black.withAlpha(dark ? 46 : 12)',
        'semantic.withAlpha(dark ? 30 : 15)',
    )

    for token in light_required:
        if token not in after:
            raise PatchError(
                f'white-mode contract missing: {token}'
            )


def write_atomic(
    path: Path,
    content: str,
) -> None:
    fd, temp_name = tempfile.mkstemp(
        prefix='main.dart.',
        suffix='.tmp',
        dir=path.parent,
    )

    try:
        with os.fdopen(
            fd,
            'w',
            encoding='utf-8',
        ) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())

        shutil.copymode(
            path,
            temp_name,
        )

        os.replace(
            temp_name,
            path,
        )

    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--apply',
        action='store_true',
    )

    args = parser.parse_args()

    if not TARGET.is_file():
        print(
            f'ERROR: target not found: {TARGET}'
        )
        return 2

    before = TARGET.read_text(
        encoding='utf-8',
    )

    if NEW_MARK in before:
        print(
            '✅ Dark Soft Neumorphic Luxe V2 '
            'already installed.'
        )
        return 0

    try:
        after = patch(before)
        verify(before, after)

    except Exception as error:
        print(f'ERROR: {error}')
        print(
            'NO WRITE: main.dart was not modified.'
        )
        return 3

    diff = list(
        difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            n=1,
            lineterm='',
        )
    )

    print()
    print(
        f'✅ PREFLIGHT OK: {len(diff)} diff lines verified.'
    )
    print(
        '✅ WHITE MODE CONTRACT: preserved.'
    )
    print(
        '✅ DARK 3D CORE: ready.'
    )

    if not args.apply:
        print(
            'DRY RUN ONLY: nothing written.'
        )
        return 0

    backup_dir = ROOT / '.aarish_backups'

    backup_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    backup = backup_dir / (
        'main.dart.before_dark_luxe_v2_'
        f'{datetime.now():%Y%m%d_%H%M%S}.bak'
    )

    shutil.copy2(
        TARGET,
        backup,
    )

    try:
        write_atomic(
            TARGET,
            after,
        )

        dart = shutil.which('dart')

        if dart:
            result = subprocess.run(
                [
                    dart,
                    'format',
                    str(TARGET),
                ],
                cwd=ROOT,
            )

            if result.returncode != 0:
                raise PatchError(
                    'dart format failed'
                )

        final = TARGET.read_text(
            encoding='utf-8',
        )

        if final.count(NEW_MARK) != 1:
            raise PatchError(
                'dark marker missing after format'
            )

        for token in (
            'Color(0xFF060A12)',
            'Color(0xFF202A38)',
            'Color(0xFF1E2937)',
        ):
            if token not in final:
                raise PatchError(
                    f'post-write verification failed: {token}'
                )

    except Exception as error:
        shutil.copy2(
            backup,
            TARGET,
        )

        print(
            f'ERROR: {error}'
        )
        print(
            '✅ ROLLBACK: previous main.dart restored.'
        )
        return 4

    print()
    print('======================================')
    print('✅ DARK 3D V2 APPLIED SUCCESSFULLY')
    print('======================================')
    print(f'TARGET : {TARGET}')
    print(f'BACKUP : {backup}')
    print()
    print('✅ White mode preserved')
    print('✅ Deep navy-charcoal dark background')
    print('✅ Raised dark card faces')
    print('✅ Strong top-left light edge')
    print('✅ Contact + grounding shadows')
    print('✅ Controlled green/red/blue/orange glow')
    print('✅ Raised dashboard icon tiles')
    print('✅ Raised Party Ledger avatar tiles')
    print('✅ Search bar upgraded')
    print('✅ Header action buttons upgraded')
    print('✅ Bottom navigation upgraded')
    print()
    print('✅ Firebase untouched')
    print('✅ Ledger calculations untouched')
    print('✅ PDF/export untouched')
    print('✅ Navigation/state logic untouched')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
