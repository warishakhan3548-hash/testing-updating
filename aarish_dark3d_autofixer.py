#!/usr/bin/env python3

from __future__ import annotations

import argparse
import difflib
import shutil
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path("/root/Aarish Kingdom/repo")
TARGET = ROOT / "lib" / "main.dart"

GLASS_START = "class _GlassCard extends StatelessWidget {"
GLASS_END = "class _CardAccentPainter extends CustomPainter {"

JEWEL_START = "  static List<BoxShadow> jewelDepth(BuildContext context, Color color) {"
JEWEL_END = "  static Border glassBorder(BuildContext context, {Color? accent}) {"

PATCH_MARKER = "DARK_RAISED_3D_V1"


NEW_GLASS_CARD = r'''class _GlassCard extends StatelessWidget {
  const _GlassCard({
    required this.child,
    this.padding = UIConstants.cardPadding,
    this.accentColor,
    this.borderColor,
    this.shadowColor,
    this.tintColor,
    this.borderRadius = UIConstants.cardRadius,
  });

  final Widget child;
  final EdgeInsets padding;
  final Color? accentColor;
  final Color? borderColor;
  final Color? shadowColor;
  final Color? tintColor;
  final double borderRadius;

  @override
  Widget build(BuildContext context) {
    final bool dark = Theme.of(context).brightness == Brightness.dark;
    final Color? semantic = shadowColor ?? tintColor ?? accentColor;
    final BorderRadius radius = BorderRadius.circular(borderRadius);

    // DARK_RAISED_3D_V1
    //
    // Light mode deliberately keeps the existing premium ceramic recipe.
    //
    // Dark mode uses a physically readable four-part depth model:
    // 1. semantic rear illumination,
    // 2. cool top-left key light,
    // 3. tight contact shadow,
    // 4. broad lower-right extrusion shadow.
    //
    // This gives a raised 3D slab instead of a flat tinted rectangle while
    // keeping blur-layer count restrained for scrolling performance.
    final List<Color> surfaceColors;

    if (dark) {
      surfaceColors = tintColor == null
          ? const <Color>[
              Color(0xFF202936),
              Color(0xFF131A25),
              Color(0xFF080C13),
            ]
          : <Color>[
              Color.lerp(const Color(0xFF202936), tintColor, .145)!,
              Color.lerp(const Color(0xFF131A25), tintColor, .082)!,
              Color.lerp(const Color(0xFF080C13), tintColor, .038)!,
            ];
    } else {
      // Preserve the existing light-mode card face exactly.
      surfaceColors = tintColor == null
          ? const <Color>[
              Color(0xFFFFFFFF),
              Color(0xFFFAFCFE),
              Color(0xFFEEF2F6),
            ]
          : <Color>[
              Color.lerp(Colors.white, tintColor, .040)!,
              Color.lerp(const Color(0xFFFAFCFE), tintColor, .028)!,
              Color.lerp(const Color(0xFFEEF2F6), tintColor, .018)!,
            ];
    }

    final Color resolvedBorder;

    if (borderColor != null) {
      resolvedBorder = borderColor!;
    } else if (semantic == null) {
      resolvedBorder = dark
          ? Colors.white.withAlpha(46)
          : const Color(0xFFFFFFFF);
    } else {
      resolvedBorder = dark
          ? Color.alphaBlend(
              semantic.withAlpha(64),
              Colors.white.withAlpha(39),
            )
          : Color.alphaBlend(
              semantic.withAlpha(17),
              const Color(0xF0FFFFFF),
            );
    }

    final Color? ambient =
        semantic == null ? null : AppStyles._ambientHue(context, semantic);

    final List<BoxShadow> shadows;

    if (dark) {
      final int semanticGlowAlpha = accentColor != null
          ? 78
          : tintColor != null
              ? 86
              : 70;

      shadows = <BoxShadow>[
        // Colored light escaping from behind the physical card.
        if (ambient != null)
          BoxShadow(
            color: ambient.withAlpha(
              AppStyles._perceptualAlpha(ambient, semanticGlowAlpha),
            ),
            blurRadius: 31,
            spreadRadius: -6,
            offset: const Offset(0, 9),
          ),

        // Upper-left key light separates the slab from the black canvas.
        BoxShadow(
          color: Colors.white.withAlpha(27),
          blurRadius: 14,
          spreadRadius: -6,
          offset: const Offset(-7, -7),
        ),

        // Tight contact shadow creates the visible physical thickness.
        BoxShadow(
          color: Colors.black.withAlpha(188),
          blurRadius: 4.5,
          spreadRadius: -1,
          offset: const Offset(0, 5),
        ),

        // Broad lower-right extrusion anchors the card in space.
        BoxShadow(
          color: Colors.black.withAlpha(126),
          blurRadius: 25,
          spreadRadius: -7,
          offset: const Offset(9, 14),
        ),
      ];
    } else {
      // Existing light-mode depth is intentionally unchanged.
      shadows = <BoxShadow>[
        if (ambient != null)
          BoxShadow(
            color: ambient.withAlpha(
              AppStyles._perceptualAlpha(
                ambient,
                accentColor != null
                    ? 46
                    : tintColor != null
                        ? 52
                        : 40,
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
              AppStyles._perceptualAlpha(ambient, 21),
            ),
            blurRadius: 42,
            spreadRadius: -13,
            offset: const Offset(5, 13),
          ),
        ...AppStyles.surfaceDepth(context),
        BoxShadow(
          color: const Color(0xFF243247).withAlpha(9),
          blurRadius: 19,
          spreadRadius: -9,
          offset: const Offset(8, 13),
        ),
      ];
    }

    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: radius,
        boxShadow: shadows,
      ),
      child: ClipRRect(
        borderRadius: radius,
        clipBehavior: Clip.antiAlias,
        child: DecoratedBox(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              stops: const <double>[0, .52, 1],
              colors: surfaceColors,
            ),
            borderRadius: radius,
          ),
          child: DecoratedBox(
            position: DecorationPosition.foreground,
            decoration: BoxDecoration(
              borderRadius: radius,
              border: Border.all(
                color: resolvedBorder,
                width: UIConstants.borderWidth,
              ),
            ),
            child: Stack(
              children: <Widget>[
                // Bevel lighting across the card face.
                Positioned.fill(
                  child: IgnorePointer(
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          stops: const <double>[0, .23, .69, 1],
                          colors: <Color>[
                            Colors.white.withAlpha(dark ? 43 : 148),
                            Colors.transparent,
                            Colors.transparent,
                            Colors.black.withAlpha(dark ? 58 : 12),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),

                // Thin specular edge: cheap to render, but gives the upper
                // surface a crisp raised-material highlight in dark mode.
                if (dark)
                  Positioned(
                    left: borderRadius * .52,
                    right: borderRadius * .52,
                    top: 0,
                    height: 1.15,
                    child: IgnorePointer(
                      child: DecoratedBox(
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: <Color>[
                              Colors.transparent,
                              Colors.white.withAlpha(102),
                              Colors.white.withAlpha(42),
                              Colors.transparent,
                            ],
                            stops: const <double>[0, .34, .66, 1],
                          ),
                        ),
                      ),
                    ),
                  ),

                // Very restrained semantic reflection inside the lower surface.
                if (semantic != null)
                  Positioned.fill(
                    child: IgnorePointer(
                      child: DecoratedBox(
                        decoration: BoxDecoration(
                          gradient: RadialGradient(
                            center: Alignment.bottomRight,
                            radius: 1.28,
                            colors: <Color>[
                              semantic.withAlpha(dark ? 31 : 15),
                              Colors.transparent,
                            ],
                            stops: const <double>[0, .72],
                          ),
                        ),
                      ),
                    ),
                  ),

                if (accentColor != null)
                  Positioned.fill(
                    child: IgnorePointer(
                      child: CustomPaint(
                        painter: _CardAccentPainter(
                          color: accentColor!,
                          radius: borderRadius,
                          dark: dark,
                        ),
                      ),
                    ),
                  ),

                Padding(
                  padding: padding,
                  child: child,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

'''


NEW_JEWEL_DEPTH = r'''  static List<BoxShadow> jewelDepth(BuildContext context, Color color) {
    final bool dark = isDark(context);

    if (dark) {
      final Color ambient = _ambientHue(context, color);

      return <BoxShadow>[
        // Semantic light behind the raised icon/avatar tile.
        BoxShadow(
          color: ambient.withAlpha(_perceptualAlpha(ambient, 66)),
          blurRadius: 17,
          spreadRadius: -5,
          offset: const Offset(1, 6),
        ),

        // Small top-left highlight makes the tile read above the parent card.
        BoxShadow(
          color: Colors.white.withAlpha(28),
          blurRadius: 11,
          spreadRadius: -4,
          offset: const Offset(-5, -5),
        ),

        // Contact + extrusion pair.
        BoxShadow(
          color: Colors.black.withAlpha(150),
          blurRadius: 4,
          spreadRadius: -1,
          offset: const Offset(0, 4),
        ),
        BoxShadow(
          color: Colors.black.withAlpha(96),
          blurRadius: 19,
          spreadRadius: -7,
          offset: const Offset(6, 10),
        ),
      ];
    }

    // Original light-mode jewel depth remains unchanged.
    return <BoxShadow>[
      BoxShadow(
        color: Colors.white.withAlpha(238),
        blurRadius: 11,
        spreadRadius: -4,
        offset: const Offset(-4, -4),
      ),
      BoxShadow(
        color: color.withAlpha(40),
        blurRadius: 15,
        spreadRadius: -5,
        offset: const Offset(2, 5),
      ),
      BoxShadow(
        color: Colors.black.withAlpha(28),
        blurRadius: 3.5,
        spreadRadius: -1,
        offset: const Offset(0, 4),
      ),
      BoxShadow(
        color: Colors.black.withAlpha(17),
        blurRadius: 18,
        spreadRadius: -7,
        offset: const Offset(6, 9),
      ),
    ];
  }

'''


def fail(message: str) -> None:
    print(f"\nERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def replace_region(
    text: str,
    start_marker: str,
    end_marker: str,
    replacement: str,
    label: str,
) -> str:
    if text.count(start_marker) != 1:
        fail(
            f"{label}: expected exactly one start marker, "
            f"found {text.count(start_marker)}"
        )

    start = text.index(start_marker)

    end_count_after_start = text[start:].count(end_marker)
    if end_count_after_start != 1:
        fail(
            f"{label}: expected exactly one end marker after start, "
            f"found {end_count_after_start}"
        )

    end = text.index(end_marker, start)

    return text[:start] + replacement + text[end:]


def build_patched(original: str) -> str:
    if PATCH_MARKER in original:
        return original

    patched = replace_region(
        original,
        GLASS_START,
        GLASS_END,
        NEW_GLASS_CARD,
        "_GlassCard",
    )

    patched = replace_region(
        patched,
        JEWEL_START,
        JEWEL_END,
        NEW_JEWEL_DEPTH,
        "AppStyles.jewelDepth",
    )

    return patched


def verify(original: str, patched: str) -> None:
    if PATCH_MARKER not in patched:
        fail("3D patch marker is missing after patch generation")

    required = (
        "semanticGlowAlpha",
        "Colors.black.withAlpha(188)",
        "Colors.white.withAlpha(102)",
        "AppStyles._perceptualAlpha(ambient, semanticGlowAlpha)",
        "Original light-mode jewel depth remains unchanged.",
    )

    missing = [item for item in required if item not in patched]
    if missing:
        fail("verification failed; missing: " + ", ".join(missing))

    # The patch must not touch application/data architecture.
    protected_tokens = (
        "class LedgerSyncService",
        "class DashboardScreen",
        "class PartyLedgerScreen",
        "Firebase.initializeApp",
    )

    for token in protected_tokens:
        if original.count(token) != patched.count(token):
            fail(f"protected architecture changed unexpectedly: {token}")

    if patched.count(GLASS_START) != 1:
        fail("_GlassCard class count changed unexpectedly")

    if patched.count(JEWEL_START) != 1:
        fail("jewelDepth function count changed unexpectedly")


def print_summary(original: str, patched: str) -> None:
    if original == patched:
        print("No source changes required: DARK_RAISED_3D_V1 is already installed.")
        return

    old_lines = original.splitlines()
    new_lines = patched.splitlines()

    additions = 0
    deletions = 0

    for line in difflib.ndiff(old_lines, new_lines):
        if line.startswith("+ "):
            additions += 1
        elif line.startswith("- "):
            deletions += 1

    print("Patch verification: PASS")
    print(f"Target: {TARGET}")
    print(f"Lines added/changed-in:  {additions}")
    print(f"Lines removed/replaced: {deletions}")
    print("")
    print("Dark-mode visual result:")
    print("  • deeper raised 3D card face")
    print("  • semantic green/red/orange/blue/purple rear glow")
    print("  • crisp top-left specular rim")
    print("  • strong contact shadow + lower-right extrusion")
    print("  • 3D icon/avatar jewel tiles")
    print("  • light/white card recipe preserved")
    print("  • no ledger/data/navigation logic touched")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Surgical dark-mode 3D card upgrade for Aarish Dairy Pro"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not TARGET.is_file():
        fail(f"main.dart not found: {TARGET}")

    original = TARGET.read_text(encoding="utf-8")
    patched = build_patched(original)

    verify(original, patched)
    print_summary(original, patched)

    if args.dry_run:
        print("\nDRY RUN ONLY — no file was changed.")
        return

    if original == patched:
        print("\nAlready applied; nothing written.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_name(f"main.dart.bak_dark3d_{timestamp}")

    shutil.copy2(TARGET, backup)
    TARGET.write_text(patched, encoding="utf-8")

    written = TARGET.read_text(encoding="utf-8")
    if written != patched:
        shutil.copy2(backup, TARGET)
        fail("post-write verification failed; backup restored automatically")

    print(f"\nAPPLIED SUCCESSFULLY")
    print(f"Backup: {backup}")


if __name__ == "__main__":
    main()
