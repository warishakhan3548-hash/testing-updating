#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path('/root/Aarish Kingdom/repo')
TARGET = ROOT / 'lib/main.dart'
MARK = '// SOFT_NEUMORPHIC_LUXE_SELECTED_V1'


def block(
    text: str,
    start_token: str,
    next_token: str,
) -> tuple[int, int, str]:
    a = text.find(start_token)
    if a < 0:
        raise RuntimeError(f'missing start anchor: {start_token}')

    b = text.find(next_token, a + len(start_token))
    if b < 0:
        raise RuntimeError(f'missing end anchor: {next_token}')

    return a, b, text[a:b]


def exact(
    s: str,
    old: str,
    new: str,
    label: str,
    count: int = 1,
) -> str:
    n = s.count(old)

    if n != count:
        raise RuntimeError(
            f'{label}: expected {count} exact match(es), found {n}'
        )

    return s.replace(old, new, count)


def patch(source: str) -> str:
    if MARK in source:
        return source

    text = source

    # ================================================================
    # 1. CENTRAL GLASS CARD
    #    Stronger semantic bloom + deeper physical grounding.
    #    This modifies the original card engine itself.
    # ================================================================
    a, b, s = block(
        text,
        'class _GlassCard extends StatelessWidget {',
        'class _CardAccentPainter extends CustomPainter {',
    )

    s = exact(
        s,
        """    final List<BoxShadow> shadows = semantic == null
        ? AppStyles.surfaceDepth(context)
        : accentColor != null
        ? AppStyles.railDepth(context, semantic)
        : AppStyles.glow(context, semantic, strong: tintColor != null);""",
        f"""    {MARK}
    final Color? ambient = semantic == null
        ? null
        : AppStyles._ambientHue(context, semantic);

    final List<BoxShadow> shadows = <BoxShadow>[
      if (ambient != null)
        BoxShadow(
          color: ambient.withAlpha(
            AppStyles._perceptualAlpha(
              ambient,
              accentColor != null
                  ? (dark ? 58 : 46)
                  : tintColor != null
                  ? (dark ? 64 : 52)
                  : (dark ? 50 : 40),
            ),
          ),
          blurRadius: accentColor != null
              ? 25
              : tintColor != null
              ? 29
              : 23,
          spreadRadius: accentColor != null ? -6 : -5,
          offset: const Offset(1, 7),
        ),

      if (ambient != null && tintColor != null)
        BoxShadow(
          color: ambient.withAlpha(
            AppStyles._perceptualAlpha(
              ambient,
              dark ? 26 : 21,
            ),
          ),
          blurRadius: 42,
          spreadRadius: -13,
          offset: const Offset(5, 13),
        ),

      // Neutral physical lift keeps semantic colors premium instead
      // of making the surface look neon.
      ...AppStyles.surfaceDepth(context),

      BoxShadow(
        color: (dark
                ? Colors.black
                : const Color(0xFF243247))
            .withAlpha(dark ? 34 : 9),
        blurRadius: 19,
        spreadRadius: -9,
        offset: const Offset(8, 13),
      ),
    ];""",
        'glass card depth',
    )

    s = exact(
        s,
        'Color.lerp(Colors.white, tintColor, .026)!',
        'Color.lerp(Colors.white, tintColor, .040)!',
        'glass tint top',
    )

    s = exact(
        s,
        "Color.lerp(const Color(0xFFFAFCFE), tintColor, .020)!",
        "Color.lerp(const Color(0xFFFAFCFE), tintColor, .028)!",
        'glass tint middle',
    )

    s = exact(
        s,
        "Color.lerp(const Color(0xFFEEF2F6), tintColor, .014)!",
        "Color.lerp(const Color(0xFFEEF2F6), tintColor, .018)!",
        'glass tint bottom',
    )

    s = exact(
        s,
        'Colors.white.withAlpha(dark ? 18 : 112)',
        'Colors.white.withAlpha(dark ? 22 : 148)',
        'glass crown highlight',
    )

    s = exact(
        s,
        'Colors.black.withAlpha(dark ? 26 : 10)',
        'Colors.black.withAlpha(dark ? 30 : 12)',
        'glass lower bevel',
    )

    s = exact(
        s,
        'semantic.withAlpha(dark ? 18 : 12)',
        'semantic.withAlpha(dark ? 22 : 15)',
        'glass inner semantic bloom',
    )

    text = text[:a] + s + text[b:]

    # ================================================================
    # 2. LIST STATUS RAIL
    #    Same original rail geometry, stronger soft aura.
    # ================================================================
    a, b, s = block(
        text,
        'class _CardAccentPainter extends CustomPainter {',
        'class _ScreenHeader extends StatelessWidget {',
    )

    s = exact(
        s,
        'color.withAlpha(dark ? 58 : 45)',
        'color.withAlpha(dark ? 70 : 54)',
        'rail aura alpha',
    )

    s = exact(
        s,
        'UIConstants.accentStroke + 5',
        'UIConstants.accentStroke + 8',
        'rail aura width',
    )

    text = text[:a] + s + text[b:]

    # ================================================================
    # 3. SHARED LIST CARDS
    #    Party Ledger / Milk / Credit / Salary / Expense etc.
    # ================================================================
    a, b, s = block(
        text,
        'class _ListCard extends StatelessWidget {',
        'class _SectionTitle extends StatelessWidget {',
    )

    s = exact(
        s,
        'final BorderRadius radius = BorderRadius.circular(26);',
        'final BorderRadius radius = BorderRadius.circular(28);',
        'list radius object',
    )

    s = exact(
        s,
        'borderRadius: 26,',
        'borderRadius: 28,',
        'list glass radius',
    )

    s = exact(
        s,
        'padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 17),',
        'padding: const EdgeInsets.symmetric(horizontal: 17, vertical: 15),',
        'list padding',
    )

    s = exact(
        s,
        'Color.lerp(Colors.white, color, .13)!',
        'Color.lerp(Colors.white, color, .16)!',
        'list badge tint top',
    )

    s = exact(
        s,
        "Color.lerp(const Color(0xFFF0F4F8), color, .07)!",
        "Color.lerp(const Color(0xFFF0F4F8), color, .085)!",
        'list badge tint bottom',
    )

    s = exact(
        s,
        'color.withAlpha(dark ? 92 : 72)',
        'color.withAlpha(dark ? 102 : 84)',
        'list badge border',
    )

    s = exact(
        s,
        'fontSize: 20,',
        'fontSize: 21,',
        'list avatar font',
    )

    s = exact(
        s,
        'fontSize: 18.5,',
        'fontSize: 19,',
        'list trailing amount font',
    )

    text = text[:a] + s + text[b:]

    # ================================================================
    # 4. DASHBOARD METRIC CARDS
    #    Keep layout intact; strengthen icon jewel and amount hierarchy.
    # ================================================================
    a, b, s = block(
        text,
        'class _MetricCard extends StatelessWidget {',
        'class _LedgerIcon extends StatelessWidget {',
    )

    s = exact(
        s,
        '_LedgerIcon(icon: icon, color: color, size: 50)',
        '_LedgerIcon(icon: icon, color: color, size: 52)',
        'metric jewel size',
    )

    s = exact(
        s,
        'fontSize: 25.5,',
        'fontSize: 27,',
        'metric amount font',
    )

    text = text[:a] + s + text[b:]

    # ================================================================
    # 5. CARD JEWEL ICON TILE
    #    Raised icon tile used on premium cards.
    # ================================================================
    a, b, s = block(
        text,
        'class _LedgerIcon extends StatelessWidget {',
        'class PartyLedgerScreen extends StatefulWidget {',
    )

    s = exact(
        s,
        'Color.lerp(Colors.white, color, .14)!',
        'Color.lerp(Colors.white, color, .17)!',
        'jewel tint top',
    )

    s = exact(
        s,
        "Color.lerp(const Color(0xFFF0F4F8), color, .07)!",
        "Color.lerp(const Color(0xFFF0F4F8), color, .09)!",
        'jewel tint bottom',
    )

    s = exact(
        s,
        'color.withAlpha(dark ? 92 : 74)',
        'color.withAlpha(dark ? 104 : 86)',
        'jewel border',
    )

    s = exact(
        s,
        'Colors.white.withAlpha(dark ? 70 : 210)',
        'Colors.white.withAlpha(dark ? 78 : 232)',
        'jewel lip highlight',
    )

    text = text[:a] + s + text[b:]

    # ================================================================
    # 6. DASHBOARD PARTY LEDGER HERO
    #    Selected reference has restrained purple glow/tint.
    # ================================================================
    old = """                    child: const _GlassCard(
                      borderRadius: 28,
                      shadowColor: Color(0xFF9333EA),
                      child: Row("""

    new = """                    child: const _GlassCard(
                      borderRadius: 28,
                      shadowColor: Color(0xFF9333EA),
                      tintColor: Color(0xFF9333EA),
                      child: Row("""

    text = exact(
        text,
        old,
        new,
        'dashboard Party Ledger purple tint',
    )

    return text


def verify(text: str) -> None:
    required = (
        MARK,
        'blurRadius: 42,',
        'UIConstants.accentStroke + 8',
        'final BorderRadius radius = BorderRadius.circular(28);',
        '_LedgerIcon(icon: icon, color: color, size: 52)',
        'tintColor: Color(0xFF9333EA)',
    )

    for token in required:
        if token not in text:
            raise RuntimeError(
                f'verification missing: {token}'
            )

    if text.count(MARK) != 1:
        raise RuntimeError(
            f'marker count is {text.count(MARK)}, expected 1'
        )


def write_atomic(path: Path, content: str) -> None:
    fd, tmp = tempfile.mkstemp(
        prefix='main.dart.',
        suffix='.tmp',
        dir=path.parent,
    )

    try:
        with os.fdopen(
            fd,
            'w',
            encoding='utf-8',
        ) as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

        shutil.copymode(path, tmp)
        os.replace(tmp, path)

    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--apply',
        action='store_true',
    )

    parser.add_argument(
        '--target',
        type=Path,
        default=TARGET,
        help=argparse.SUPPRESS,
    )

    args = parser.parse_args()

    target = args.target

    if not target.is_file():
        print(f'ERROR: not found: {target}')
        return 2

    before = target.read_text(
        encoding='utf-8',
    )

    if MARK in before:
        print(
            'OK: selected Soft Neumorphic Luxe '
            'card patch is already installed.'
        )
        return 0

    try:
        after = patch(before)
        verify(after)

    except Exception as error:
        print(f'ERROR: {error}')
        return 3

    diff = list(
        difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            n=1,
            lineterm='',
        )
    )

    print(
        f'VERIFIED: patch ready '
        f'({len(diff)} diff lines).'
    )

    if not args.apply:
        print(
            'DRY RUN ONLY. '
            'Add --apply to write changes.'
        )
        return 0

    backup_dir = (
        target.parent.parent
        / '.aarish_backups'
    )

    backup_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    backup = backup_dir / (
        'main.dart.before_soft_luxe_'
        f'{datetime.now():%Y%m%d_%H%M%S}.bak'
    )

    shutil.copy2(
        target,
        backup,
    )

    write_atomic(
        target,
        after,
    )

    print(f'APPLIED: {target}')
    print(f'BACKUP:  {backup}')

    print(
        'CHANGED: card depth, semantic glow/rail, '
        'list-card shape, card jewel tiles'
    )

    print(
        'UNTOUCHED: data/state logic, Firebase, '
        'navigation, search behavior, PDF logic'
    )

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
