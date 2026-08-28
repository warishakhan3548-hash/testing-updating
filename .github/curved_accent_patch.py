from pathlib import Path

p = Path("lib/main.dart")
s = p.read_text(encoding="utf-8")
start = s.index("class _GlassCard extends StatelessWidget {")
tail = s[start:]
end = tail.index("\n}\n", tail.index("Widget build(BuildContext context)")) + 3
block = tail[:end]

old_border = """    final Border border = accentColor == null
        ? Border.all(color: borderColor ?? surfaceBorder)
        : Border(
            left: BorderSide(color: accentColor!, width: 4),
            top: BorderSide(color: surfaceBorder),
            right: BorderSide(
              color: dark
                  ? Colors.white.withAlpha(20)
                  : Colors.white.withAlpha(92),
            ),
            bottom: BorderSide(
              color: dark
                  ? Colors.black.withAlpha(97)
                  : Colors.white.withAlpha(66),
            ),
          );"""
new_border = """    final Border border = Border.all(
      color: borderColor ?? surfaceBorder,
    );"""
if block.count(old_border) != 1:
    raise SystemExit(f"old accent border count={block.count(old_border)}")
block = block.replace(old_border, new_border, 1)

old_return = """    return Container(
      padding: padding,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: surfaceColors,
        ),
        borderRadius: BorderRadius.circular(borderRadius),
        border: border,
        boxShadow: shadows,
      ),
      child: child,
    );"""
new_return = """    return Container(
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: surfaceColors,
        ),
        borderRadius: BorderRadius.circular(borderRadius),
        border: border,
        boxShadow: shadows,
      ),
      child: Stack(
        children: <Widget>[
          if (accentColor != null)
            Positioned(
              left: 0,
              top: 0,
              bottom: 0,
              width: 6,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: accentColor,
                  boxShadow: <BoxShadow>[
                    BoxShadow(
                      color: accentColor!.withAlpha(dark ? 92 : 72),
                      blurRadius: 16,
                      offset: const Offset(3, 0),
                    ),
                  ],
                ),
              ),
            ),
          Padding(
            padding: padding,
            child: child,
          ),
        ],
      ),
    );"""
if block.count(old_return) != 1:
    raise SystemExit(f"old glass card return count={block.count(old_return)}")
block = block.replace(old_return, new_return, 1)

s = s[:start] + block + tail[end:]
p.write_text(s, encoding="utf-8")
