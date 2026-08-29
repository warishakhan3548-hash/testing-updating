from pathlib import Path
import re

TARGET = Path('lib/main.dart')

SOFT_SHARE = r'''class _SoftShareButton extends StatelessWidget {
  const _SoftShareButton({
    required this.onTap,
    this.label = 'Share',
    this.icon = Icons.ios_share_rounded,
    this.color = appleBlue,
    this.semanticLabel,
    this.compact = false,
  });

  final String label;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;
  final String? semanticLabel;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final bool dark = Theme.of(context).brightness == Brightness.dark;
    final double viewportWidth = MediaQuery.sizeOf(context).width;
    final bool micro = compact && viewportWidth < 350;
    final double height = micro ? 46 : (compact ? 48 : 52);
    final double width = micro ? 96 : (compact ? 108 : 118);
    final double radius = compact ? 17 : 19;

    final Color fill = dark
        ? Color.alphaBlend(color.withAlpha(24), const Color(0xFF1B2230))
        : Color.alphaBlend(color.withAlpha(13), Colors.white);
    final Color border = color.withAlpha(dark ? 92 : 62);

    return _Pressable(
      onTap: onTap,
      semanticLabel: semanticLabel ?? label,
      borderRadius: BorderRadius.circular(radius),
      child: Container(
        width: width,
        height: height,
        padding: EdgeInsets.symmetric(horizontal: micro ? 10 : 13),
        decoration: BoxDecoration(
          color: fill,
          borderRadius: BorderRadius.circular(radius),
          border: Border.all(color: border, width: 1),
          boxShadow: dark
              ? const <BoxShadow>[]
              : <BoxShadow>[
                  BoxShadow(
                    color: color.withAlpha(15),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ],
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Icon(
              icon,
              color: color,
              size: micro ? 20 : 22,
            ),
            SizedBox(width: micro ? 6 : 8),
            Flexible(
              child: FittedBox(
                fit: BoxFit.scaleDown,
                child: Text(
                  label,
                  maxLines: 1,
                  style: TextStyle(
                    color: color,
                    fontSize: compact ? 15.5 : 16.5,
                    height: 1,
                    fontWeight: FontWeight.w800,
                    letterSpacing: -.2,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
'''


def fail(message: str) -> None:
    raise SystemExit(f'soft_share_patch: {message}')


def main() -> None:
    if not TARGET.exists():
        fail(f'missing {TARGET}')

    text = TARGET.read_text(encoding='utf-8')

    if 'class _SoftShareButton extends StatelessWidget' in text:
        if '_PremiumShareButton(' in text or 'class _PremiumShareButton' in text:
            fail('partial share migration detected')
        print('soft_share_patch: already applied')
        return

    call_pattern = re.compile(r'(?m)^(?P<indent>\s*)_PremiumShareButton\(')
    text, call_count = call_pattern.subn(
        lambda match: f"{match.group('indent')}_SoftShareButton(",
        text,
    )
    if call_count != 7:
        fail(f'expected 7 premium share call sites, found {call_count}')

    class_pattern = re.compile(
        r'class _PremiumShareButton extends StatelessWidget \{.*?\n\}\n\n'
        r'class _PremiumShareGlyph extends StatelessWidget \{.*?\n\}\n\n'
        r'class _PremiumShareCircuitPainter extends CustomPainter \{.*?\n\}\n\n'
        r'(?=class _MilkRecordsTable extends StatelessWidget)',
        re.DOTALL,
    )
    text, class_count = class_pattern.subn(SOFT_SHARE + '\n', text)
    if class_count != 1:
        fail(f'expected one premium share class cluster, found {class_count}')

    if '_PremiumShareButton(' in text or 'class _PremiumShareButton' in text:
        fail('old premium share component remains')
    if '_PremiumShareGlyph' in text or '_PremiumShareCircuitPainter' in text:
        fail('old premium share helper code remains')

    soft_calls = len(re.findall(r'(?m)^\s*_SoftShareButton\(', text))
    if soft_calls != 7:
        fail(f'expected 7 soft share call sites, found {soft_calls}')

    TARGET.write_text(text, encoding='utf-8')
    print('soft_share_patch: migrated all 7 share buttons to soft washed UI')


if __name__ == '__main__':
    main()
