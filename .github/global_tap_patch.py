from pathlib import Path

p = Path('lib/main.dart')
s = p.read_text()


def replace_once(old: str, new: str, label: str) -> None:
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 occurrence, found {count}')
    s = s.replace(old, new, 1)


# Remove the previous clickable-only ripple implementation completely.
replace_once(
    "  static const Duration tapRipple = Duration(milliseconds: 200);\n",
    "",
    "tapRipple duration",
)
replace_once(
    "class _PressableState extends State<_Pressable>\n    with TickerProviderStateMixin {",
    "class _PressableState extends State<_Pressable>\n    with SingleTickerProviderStateMixin {",
    "Pressable ticker mixin",
)
replace_once(
    "  late final AnimationController _pressController;\n  late final AnimationController _rippleController;\n  Alignment _touchAlignment = Alignment.center;\n",
    "  late final AnimationController _pressController;\n  Alignment _touchAlignment = Alignment.center;\n",
    "Pressable ripple controller declaration",
)
replace_once(
    """    _pressController = AnimationController(
      vsync: this,
      value: 0,
      lowerBound: -.18,
      upperBound: 1,
      duration: UIConstants.pressIn,
      reverseDuration: UIConstants.pressOut,
    );
    _rippleController = AnimationController(
      vsync: this,
      duration: UIConstants.tapRipple,
    );
""",
    """    _pressController = AnimationController(
      vsync: this,
      value: 0,
      lowerBound: -.18,
      upperBound: 1,
      duration: UIConstants.pressIn,
      reverseDuration: UIConstants.pressOut,
    );
""",
    "Pressable controller init",
)
replace_once(
    """      _pressController.stop();
      _pressController.value = 0;
      _rippleController.stop();
      _rippleController.value = 0;
""",
    """      _pressController.stop();
      _pressController.value = 0;
""",
    "Pressable disabled reset",
)
replace_once(
    """  void _press([TapDownDetails? details]) {
    if (widget.onTap == null) return;
    if (details != null) {
      _captureTouch(details);
      if (!AppMotion.reduce(context)) _rippleController.forward(from: 0);
    }
    if (!widget.animatePress) return;
    _pressController.animateTo(
      1,
      duration: UIConstants.pressIn,
      curve: Curves.easeOutCubic,
    );
  }
""",
    """  void _press([TapDownDetails? details]) {
    if (widget.onTap == null || !widget.animatePress) return;
    if (details != null) _captureTouch(details);
    _pressController.animateTo(
      1,
      duration: UIConstants.pressIn,
      curve: Curves.easeOutCubic,
    );
  }
""",
    "Pressable press handler",
)
replace_once(
    """  void dispose() {
    _pressController.dispose();
    _rippleController.dispose();
    super.dispose();
  }
""",
    """  void dispose() {
    _pressController.dispose();
    super.dispose();
  }
""",
    "Pressable dispose",
)
replace_once(
    "      onTapDown: widget.onTap == null ? null : _press,\n",
    "      onTapDown: widget.onTap == null || !widget.animatePress ? null : _press,\n",
    "Pressable tap down",
)
replace_once(
    """      child: AnimatedBuilder(
        animation: Listenable.merge(<Listenable>[
          _pressController,
          _rippleController,
        ]),
        child: widget.child,
""",
    """      child: AnimatedBuilder(
        animation: _pressController,
        child: widget.child,
""",
    "Pressable animation source",
)
replace_once(
    """          final double pressed = feedback.clamp(0.0, 1.0).toDouble();
          final double rippleProgress = reduceMotion ? 0 : _rippleController.value;
          final double rippleWave = Curves.easeOutCubic.transform(
            rippleProgress.clamp(0.0, 1.0).toDouble(),
          );
          final double rippleFade = (1 - rippleProgress)
              .clamp(0.0, 1.0)
              .toDouble();
          final Color rippleColor =
              widget.feedbackColor ?? Theme.of(context).colorScheme.primary;
          final double motion = reduceMotion ? 0 : feedback;
""",
    """          final double pressed = feedback.clamp(0.0, 1.0).toDouble();
          final double motion = reduceMotion ? 0 : feedback;
""",
    "Pressable ripple variables",
)
replace_once(
    """                            if (rippleProgress > 0 && rippleProgress < 1)
                              DecoratedBox(
                                decoration: BoxDecoration(
                                  gradient: RadialGradient(
                                    center: _touchAlignment,
                                    radius: .16 + rippleWave * 1.08,
                                    colors: <Color>[
                                      rippleColor.withAlpha(
                                        (rippleFade * (dark ? 16 : 12)).round(),
                                      ),
                                      Colors.transparent,
                                      rippleColor.withAlpha(
                                        (rippleFade * (dark ? 82 : 64)).round(),
                                      ),
                                      Colors.transparent,
                                    ],
                                    stops: const <double>[0, .38, .66, 1],
                                  ),
                                ),
                              ),
""",
    "",
    "Pressable ripple painter block",
)

# Remove color plumbing added only for the old ripple.
replace_once(
    """        semanticLabel: semanticLabel,
        borderRadius: BorderRadius.circular(24),
        feedbackColor: color,
        child: Container(
""",
    """        semanticLabel: semanticLabel,
        borderRadius: BorderRadius.circular(24),
        child: Container(
""",
    "CircleAction ripple color",
)
replace_once(
    """        semanticLabel: semanticLabel,
        borderRadius: radius,
        feedbackColor: appleRed,
        child: Container(
""",
    """        semanticLabel: semanticLabel,
        borderRadius: radius,
        child: Container(
""",
    "DeleteAction ripple color",
)
replace_once(
    """  Widget build(BuildContext context) => _Pressable(
    onTap: onTap,
    borderRadius: BorderRadius.circular(UIConstants.actionRadius),
    feedbackColor: color,
    child: Container(
""",
    """  Widget build(BuildContext context) => _Pressable(
    onTap: onTap,
    borderRadius: BorderRadius.circular(UIConstants.actionRadius),
    child: Container(
""",
    "PrimaryButton ripple color",
)

# Install exactly one root-level touch engine.
replace_once(
    """    builder: (BuildContext context, Widget? child) =>
        _AmbientBackground(child: child ?? const SizedBox.shrink()),
""",
    """    builder: (BuildContext context, Widget? child) => _GlobalTapRippleLayer(
      child: _AmbientBackground(child: child ?? const SizedBox.shrink()),
    ),
""",
    "MaterialApp root builder",
)

ambient_anchor = "class _AmbientBackground extends StatelessWidget {\n"
if s.count(ambient_anchor) != 1:
    raise SystemExit(f'Ambient anchor count={s.count(ambient_anchor)}')

global_ripple_code = '''class _GlobalTapRippleLayer extends StatefulWidget {
  const _GlobalTapRippleLayer({required this.child});

  final Widget child;

  @override
  State<_GlobalTapRippleLayer> createState() => _GlobalTapRippleLayerState();
}

class _GlobalTapRippleLayerState extends State<_GlobalTapRippleLayer>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 200),
  );
  Offset _origin = Offset.zero;

  void _handlePointerDown(PointerDownEvent event) {
    if (AppMotion.reduce(context)) return;
    _origin = event.localPosition;
    _controller.forward(from: 0);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Listener(
    behavior: HitTestBehavior.translucent,
    onPointerDown: _handlePointerDown,
    child: AnimatedBuilder(
      animation: _controller,
      child: widget.child,
      builder: (BuildContext context, Widget? child) {
        final double raw = _controller.value;
        if (raw <= 0 || raw >= 1) return child!;
        final double progress = Curves.easeOutCubic.transform(raw);
        final double opacity = (1 - raw).clamp(0.0, 1.0).toDouble();
        return Stack(
          fit: StackFit.expand,
          children: <Widget>[
            child!,
            IgnorePointer(
              child: RepaintBoundary(
                child: CustomPaint(
                  painter: _GlobalTapRipplePainter(
                    origin: _origin,
                    progress: progress,
                    opacity: opacity,
                  ),
                ),
              ),
            ),
          ],
        );
      },
    ),
  );
}

class _GlobalTapRipplePainter extends CustomPainter {
  const _GlobalTapRipplePainter({
    required this.origin,
    required this.progress,
    required this.opacity,
  });

  final Offset origin;
  final double progress;
  final double opacity;

  @override
  void paint(Canvas canvas, Size size) {
    if (size.isEmpty || opacity <= 0) return;

    final double radius = 7 + 47 * progress;
    final Rect bounds = Rect.fromCircle(center: origin, radius: radius);
    final int coreAlpha = (opacity * 34).round().clamp(0, 255);
    final int haloAlpha = (opacity * 15).round().clamp(0, 255);
    final int ringAlpha = (opacity * 118).round().clamp(0, 255);

    canvas.drawCircle(
      origin,
      radius,
      Paint()
        ..shader = RadialGradient(
          colors: <Color>[
            appleBlue.withAlpha(coreAlpha),
            appleBlue.withAlpha(haloAlpha),
            Colors.transparent,
          ],
          stops: const <double>[0, .54, 1],
        ).createShader(bounds),
    );

    canvas.drawCircle(
      origin,
      radius * .86,
      Paint()
        ..color = appleBlue.withAlpha(ringAlpha)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.9 - progress * .8,
    );

    final double echo = ((progress - .18) / .82).clamp(0.0, 1.0).toDouble();
    if (echo > 0 && echo < 1) {
      final int echoAlpha =
          (opacity * (1 - echo) * 64).round().clamp(0, 255);
      canvas.drawCircle(
        origin,
        5 + 25 * echo,
        Paint()
          ..color = appleBlue.withAlpha(echoAlpha)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.25,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _GlobalTapRipplePainter oldDelegate) =>
      oldDelegate.origin != origin ||
      oldDelegate.progress != progress ||
      oldDelegate.opacity != opacity;
}

'''

s = s.replace(ambient_anchor, global_ripple_code + ambient_anchor, 1)
p.write_text(s)
