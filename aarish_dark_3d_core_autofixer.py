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

PREVIOUS_MARK = '// SOFT_NEUMORPHIC_LUXE_SELECTED_V1'
MARK = '// DARK_SOFT_NEUMORPHIC_DEPTH_V1'


class PatchError(RuntimeError):
    pass


def block(
    text: str,
    start_token: str,
    end_token: str,
) -> tuple[int, int, str]:
    start = text.find(start_token)
    if start < 0:
        raise PatchError(f'missing start anchor: {start_token}')

    end = text.find(end_token, start + len(start_token))
    if end < 0:
        raise PatchError(f'missing end anchor: {end_token}')

    return start, end, text[start:end]


def replace_exact(
    text: str,
    old: str,
    new: str,
    label: str,
    expected: int = 1,
) -> str:
    count = text.count(old)

    if count != expected:
        raise PatchError(
            f'{label}: expected {expected} exact match(es), found {count}'
        )

    return text.replace(old, new, expected)


def patch_app_styles(text: str) -> str:
    a, b, s = block(
        text,
        'abstract final class AppStyles {',
        'const Uuid _ids = Uuid();',
    )

    surface_anchor = (
        '    final Color ink = dark ? Colors.black : const Color(0xFF243247);\n'
    )

    surface_insert = surface_anchor + f"""
    {MARK}
    // Dark mode needs physical luminance separation, not just colored glow.
    // Light mode intentionally falls through to the existing implementation.
    if (dark) {{
      return <BoxShadow>[
        // Top-left reflected light defines the raised ceramic edge.
        BoxShadow(
          color: Colors.white.withAlpha(52),
          blurRadius: 17,
          spreadRadius: -5,
          offset: const Offset(-5, -5),
        ),

        // Tight contact shadow makes the surface visibly leave the canvas.
        BoxShadow(
          color: Colors.black.withAlpha(178),
          blurRadius: 5.5,
          spreadRadius: -1,
          offset: const Offset(0, 6),
        ),

        // Broad grounding shadow supplies the final depth layer.
        BoxShadow(
          color: Colors.black.withAlpha(138),
          blurRadius: 30,
          spreadRadius: -8,
          offset: const Offset(9, 15),
        ),
      ];
    }}
"""

    s = replace_exact(
        s,
        surface_anchor,
        surface_insert,
        'dark surface depth insertion',
    )

    jewel_anchor = """  static List<BoxShadow> jewelDepth(BuildContext context, Color color) {
    final bool dark = isDark(context);

"""

    jewel_new = jewel_anchor + """    if (dark) {
      return <BoxShadow>[
        BoxShadow(
          color: Colors.white.withAlpha(55),
          blurRadius: 12,
          spreadRadius: -4,
          offset: const Offset(-4, -4),
        ),
        BoxShadow(
          color: color.withAlpha(58),
          blurRadius: 15,
          spreadRadius: -5,
          offset: const Offset(2, 5),
        ),
        BoxShadow(
          color: Colors.black.withAlpha(176),
          blurRadius: 5,
          spreadRadius: -1,
          offset: const Offset(0, 6),
        ),
        BoxShadow(
          color: Colors.black.withAlpha(118),
          blurRadius: 21,
          spreadRadius: -7,
          offset: const Offset(7, 11),
        ),
      ];
    }

"""

    s = replace_exact(
        s,
        jewel_anchor,
        jewel_new,
        'dark jewel depth insertion',
    )

    return text[:a] + s + text[b:]


def patch_ambient(text: str) -> str:
    a, b, s = block(
        text,
        'class _AmbientPainter extends CustomPainter {',
        'class _OpaqueContentTransitionsBuilder extends PageTransitionsBuilder {',
    )

    s = replace_exact(
        s,
        'canvas.drawRect(bounds, Paint()..color = dark ? Colors.black : lightCanvas);',
        """canvas.drawRect(
      bounds,
      Paint()
        ..color = dark ? const Color(0xFF060B13) : lightCanvas,
    );""",
        'dark canvas',
    )

    s = replace_exact(
        s,
        'color: appleGreen.withAlpha(dark ? 47 : 28),',
        'color: appleGreen.withAlpha(dark ? 18 : 28),',
        'dark ambient green',
    )

    s = replace_exact(
        s,
        'color: appleBlue2.withAlpha(dark ? 48 : 24),',
        'color: appleBlue2.withAlpha(dark ? 24 : 24),',
        'dark ambient blue',
    )

    s = replace_exact(
        s,
        'color: diaryOrange.withAlpha(dark ? 17 : 10),',
        'color: diaryOrange.withAlpha(dark ? 8 : 10),',
        'dark ambient amber',
    )

    return text[:a] + s + text[b:]


def patch_glass_card(text: str) -> str:
    a, b, s = block(
        text,
        'class _GlassCard extends StatelessWidget {',
        'class _CardAccentPainter extends CustomPainter {',
    )

    # Neutral dark surface.
    s = replace_exact(
        s,
        """          ? const <Color>[
              Color(0xFF1A2230),
              Color(0xFF111823),
              Color(0xFF0A0F18),
            ]""",
        """          ? const <Color>[
              Color(0xFF202B39),
              Color(0xFF151E2B),
              Color(0xFF0B111B),
            ]""",
        'dark neutral glass surface',
    )

    # Semantic/tinted dark surface.
    s = replace_exact(
        s,
        "Color.lerp(const Color(0xFF1A2230), tintColor, .10)!",
        "Color.lerp(const Color(0xFF202B39), tintColor, .14)!",
        'dark tinted glass top',
    )

    s = replace_exact(
        s,
        "Color.lerp(const Color(0xFF111823), tintColor, .07)!",
        "Color.lerp(const Color(0xFF151E2B), tintColor, .09)!",
        'dark tinted glass middle',
    )

    s = replace_exact(
        s,
        "Color.lerp(const Color(0xFF0A0F18), tintColor, .04)!",
        "Color.lerp(const Color(0xFF0B111B), tintColor, .05)!",
        'dark tinted glass bottom',
    )

    # Raised rim. Light branch remains byte-for-byte unchanged.
    s = replace_exact(
        s,
        'dark ? Colors.white.withAlpha(30)',
        'dark ? Colors.white.withAlpha(48)',
        'dark neutral borders',
        expected=2,
    )

    s = replace_exact(
        s,
        'semantic.withAlpha(dark ? 28 : 17)',
        'semantic.withAlpha(dark ? 44 : 17)',
        'dark semantic border',
    )

    # This is the previous selected Luxe patch.
    # In dark mode remove its secondary long semantic halo:
    # physical depth should do the work instead of neon blur.
    s = replace_exact(
        s,
        'if (ambient != null && tintColor != null)',
        'if (!dark && ambient != null && tintColor != null)',
        'disable second dark semantic halo',
    )

    s = replace_exact(
        s,
        'dark ? 58 : 46',
        'dark ? 46 : 46',
        'dark rail glow restraint',
    )

    s = replace_exact(
        s,
        'dark ? 64 : 52',
        'dark ? 50 : 52',
        'dark strong glow restraint',
    )

    s = replace_exact(
        s,
        'dark ? 50 : 40',
        'dark ? 42 : 40',
        'dark base glow restraint',
    )

    # The first diagonal highlight is what makes the dark card visibly 3D.
    s = replace_exact(
        s,
        'Colors.white.withAlpha(dark ? 22 : 148)',
        'Colors.white.withAlpha(dark ? 64 : 148)',
        'dark glass highlight',
    )

    s = replace_exact(
        s,
        'Colors.black.withAlpha(dark ? 30 : 12)',
        'Colors.black.withAlpha(dark ? 42 : 12)',
        'dark lower bevel',
    )

    # Reduce interior neon wash slightly.
    s = replace_exact(
        s,
        'semantic.withAlpha(dark ? 22 : 15)',
        'semantic.withAlpha(dark ? 18 : 15)',
        'dark internal semantic tint',
    )

    return text[:a] + s + text[b:]


def patch_list_card(text: str) -> str:
    a, b, s = block(
        text,
        'class _ListCard extends StatelessWidget {',
        'class _SectionTitle extends StatelessWidget {',
    )

    s = replace_exact(
        s,
        "Color.lerp(const Color(0xFF1B2432), color, .18)!",
        "Color.lerp(const Color(0xFF202B39), color, .21)!",
        'list avatar dark top',
    )

    s = replace_exact(
        s,
        "Color.lerp(const Color(0xFF0D131C), color, .10)!",
        "Color.lerp(const Color(0xFF0B111B), color, .12)!",
        'list avatar dark bottom',
    )

    return text[:a] + s + text[b:]


def patch_ledger_icon(text: str) -> str:
    a, b, s = block(
        text,
        'class _LedgerIcon extends StatelessWidget {',
        'class PartyLedgerScreen extends StatefulWidget {',
    )

    s = replace_exact(
        s,
        "Color.lerp(const Color(0xFF1B2432), color, .18)!",
        "Color.lerp(const Color(0xFF202B39), color, .22)!",
        'ledger jewel dark top',
    )

    s = replace_exact(
        s,
        "Color.lerp(const Color(0xFF0D131C), color, .09)!",
        "Color.lerp(const Color(0xFF0B111B), color, .12)!",
        'ledger jewel dark bottom',
    )

    return text[:a] + s + text[b:]


def patch_circle_action(text: str) -> str:
    a, b, s = block(
        text,
        'class _CircleAction extends StatelessWidget {',
        'class _DeleteActionButton extends StatelessWidget {',
    )

    s = replace_exact(
        s,
        "Color.lerp(const Color(0xFF1B2432), color, .16)!",
        "Color.lerp(const Color(0xFF202B39), color, .19)!",
        'circle dark top',
    )

    s = replace_exact(
        s,
        "Color.lerp(const Color(0xFF0D131C), color, .08)!",
        "Color.lerp(const Color(0xFF0B111B), color, .10)!",
        'circle dark bottom',
    )

    s = replace_exact(
        s,
        'color.withAlpha(dark ? 84 : 62)',
        'color.withAlpha(dark ? 104 : 62)',
        'circle dark rim',
    )

    return text[:a] + s + text[b:]


def patch_back_button(text: str) -> str:
    a, b, s = block(
        text,
        'class _BackCircle extends StatelessWidget {',
        'class _BounceTextButton extends StatelessWidget {',
    )

    s = replace_exact(
        s,
        """colors: <Color>[Color(0xFF1B2432), Color(0xFF0D131C)],""",
        """colors: <Color>[Color(0xFF202B39), Color(0xFF0B111B)],""",
        'back button dark surface',
    )

    s = replace_exact(
        s,
        'appleBlue.withAlpha(dark ? 62 : 34)',
        'appleBlue.withAlpha(dark ? 90 : 34)',
        'back button dark rim',
    )

    return text[:a] + s + text[b:]


def patch_search(text: str) -> str:
    a, b, s = block(
        text,
        'class _SearchBoxState extends State<_SearchBox> {',
        'class _DateField extends StatelessWidget {',
    )

    s = replace_exact(
        s,
        """? const <Color>[Color(0xFF1A2230), Color(0xFF0D131D)]""",
        """? const <Color>[Color(0xFF202B39), Color(0xFF0B111B)]""",
        'search dark surface',
    )

    s = replace_exact(
        s,
        'dark ? Colors.white.withAlpha(28) : const Color(0xE8FFFFFF)',
        'dark ? Colors.white.withAlpha(44) : const Color(0xE8FFFFFF)',
        'search dark edge',
    )

    return text[:a] + s + text[b:]


def patch_bottom_nav(text: str) -> str:
    a, b, s = block(
        text,
        'class _BottomLedgerNav extends StatelessWidget {',
        '// PREMIUM_NAV_V2',
    )

    s = replace_exact(
        s,
        """? const <Color>[Color(0xFF18202D), Color(0xFF0B111A)]""",
        """? const <Color>[Color(0xFF1D2836), Color(0xFF0A1019)]""",
        'bottom nav dark surface',
    )

    s = replace_exact(
        s,
        'Colors.white.withAlpha(28)',
        'Colors.white.withAlpha(46)',
        'bottom nav dark rim',
    )

    return text[:a] + s + text[b:]


def patch_nav_icon(text: str) -> str:
    a, b, s = block(
        text,
        'class _PremiumNavIconFrame extends StatelessWidget {',
        'class _BottomNavGlyph extends StatelessWidget {',
    )

    s = replace_exact(
        s,
        "Color.lerp(const Color(0xFF1B2432), color, .18)!",
        "Color.lerp(const Color(0xFF202B39), color, .22)!",
        'nav jewel dark top',
    )

    s = replace_exact(
        s,
        "Color.lerp(const Color(0xFF0D131C), color, .09)!",
        "Color.lerp(const Color(0xFF0B111B), color, .12)!",
        'nav jewel dark bottom',
    )

    return text[:a] + s + text[b:]


def patch(source: str) -> str:
    if MARK in source:
        return source

    if PREVIOUS_MARK not in source:
        raise PatchError(
            'previous Soft Neumorphic Luxe patch marker was not found. '
            'Refusing to patch an unexpected source version.'
        )

    text = source

    text = patch_app_styles(text)
    text = patch_ambient(text)
    text = patch_glass_card(text)
    text = patch_list_card(text)
    text = patch_ledger_icon(text)
    text = patch_circle_action(text)
    text = patch_back_button(text)
    text = patch_search(text)
    text = patch_bottom_nav(text)
    text = patch_nav_icon(text)

    return text


def verify(before: str, after: str) -> None:
    required = (
        MARK,
        'Color(0xFF060B13)',
        'Color(0xFF202B39)',
        'Colors.white.withAlpha(52)',
        'Colors.black.withAlpha(178)',
        'if (!dark && ambient != null && tintColor != null)',
        'Color(0xFF1D2836)',
    )

    for token in required:
        if token not in after:
            raise PatchError(f'verification missing: {token}')

    if after.count(MARK) != 1:
        raise PatchError(
            f'new marker count is {after.count(MARK)}, expected exactly 1'
        )

    # White-mode contract: these selected Luxe light values must remain.
    light_contract = (
        'Color.lerp(Colors.white, tintColor, .040)!',
        "Color.lerp(const Color(0xFFFAFCFE), tintColor, .028)!",
        "Color.lerp(const Color(0xFFEEF2F6), tintColor, .018)!",
        'Colors.white.withAlpha(dark ? 64 : 148)',
        'Colors.black.withAlpha(dark ? 42 : 12)',
        'semantic.withAlpha(dark ? 18 : 15)',
    )

    for token in light_contract:
        if token not in after:
            raise PatchError(
                f'white-mode contract verification failed: {token}'
            )

    if before == after:
        raise PatchError('patch produced no changes')


def write_atomic(path: Path, content: str) -> None:
    fd, temp_path = tempfile.mkstemp(
        prefix='main.dart.',
        suffix='.tmp',
        dir=path.parent,
    )

    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())

        shutil.copymode(path, temp_path)
        os.replace(temp_path, path)

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def run_format(target: Path) -> bool:
    dart = shutil.which('dart')

    if dart is None:
        print('WARN: dart not found; formatting skipped.')
        return True

    result = subprocess.run(
        [dart, 'format', str(target)],
        cwd=ROOT,
        text=True,
    )

    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()

    if not TARGET.is_file():
        print(f'ERROR: target not found: {TARGET}')
        return 2

    before = TARGET.read_text(encoding='utf-8')

    if MARK in before:
        print('OK: dark premium 3D core patch is already installed.')
        return 0

    try:
        after = patch(before)
        verify(before, after)
    except Exception as error:
        print(f'ERROR: {error}')
        return 3

    diff = list(
        difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile='main.dart.before',
            tofile='main.dart.dark3d',
            n=1,
            lineterm='',
        )
    )

    print(f'VERIFIED: dark-only core patch ready ({len(diff)} diff lines).')
    print('WHITE MODE: protected / existing selected Luxe values preserved.')
    print('DARK MODE: background + surfaces + rims + shadows + jewels upgraded.')

    if not args.apply:
        print('DRY RUN ONLY. Nothing written.')
        return 0

    backup_dir = ROOT / '.aarish_backups'
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup = backup_dir / (
        'main.dart.before_dark_3d_'
        f'{datetime.now():%Y%m%d_%H%M%S}.bak'
    )

    shutil.copy2(TARGET, backup)

    try:
        write_atomic(TARGET, after)

        if not run_format(TARGET):
            raise PatchError('dart format failed')

        formatted = TARGET.read_text(encoding='utf-8')

        if MARK not in formatted:
            raise PatchError('marker disappeared after formatting')

    except Exception as error:
        shutil.copy2(backup, TARGET)
        print(f'ERROR: {error}')
        print('ROLLBACK: original main.dart restored automatically.')
        return 4

    print()
    print(f'APPLIED: {TARGET}')
    print(f'BACKUP:  {backup}')
    print()
    print('DARK 3D:')
    print('  ✓ deep navy-charcoal canvas')
    print('  ✓ brighter raised card faces')
    print('  ✓ top-left specular edge')
    print('  ✓ strong contact + grounding depth')
    print('  ✓ restrained semantic glow')
    print('  ✓ stronger icon/avatar jewel depth')
    print('  ✓ search/header/navigation dark surfaces')
    print()
    print('LIGHT MODE:')
    print('  ✓ existing selected design preserved')
    print()
    print('LOGIC:')
    print('  ✓ Firebase untouched')
    print('  ✓ ledger calculations untouched')
    print('  ✓ PDF/export untouched')
    print('  ✓ navigation/state untouched')
    print('  ✓ press/motion engine untouched')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
