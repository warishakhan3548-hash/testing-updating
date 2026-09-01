from pathlib import Path
import re

main = Path('lib/main.dart')
test = Path('test/ui_micro_aesthetics_test.dart')
source = main.read_text()
before = source


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one anchor, found {count}')
    return text.replace(old, new, 1)


source = replace_once(
    source,
    """  late final AnimationController _pressController;
  Alignment _touchAlignment = Alignment.center;
""",
    """  late final AnimationController _pressController;
  late final Stopwatch _gestureClock;
  Alignment _touchAlignment = Alignment.center;
  Alignment? _releaseAlignment;
  Offset? _lastTouchPosition;
  int _lastTouchSampleMicros = 0;
  Offset _gestureVelocity = Offset.zero;
""",
    'press kinetic state',
)

source = replace_once(
    source,
    """  void initState() {
    super.initState();
    _pressController = AnimationController(
""",
    """  void initState() {
    super.initState();
    _gestureClock = Stopwatch()..start();
    _pressController = AnimationController(
""",
    'gesture clock initialization',
)

source = replace_once(
    source,
    """  void _resetPressFeedback() {
    _pressController.stop();
    if (_pressController.value != 0) _pressController.value = 0;
    _touchAlignment = Alignment.center;
  }
""",
    """  void _resetPressFeedback() {
    _pressController.stop();
    if (_pressController.value != 0) _pressController.value = 0;
    _touchAlignment = Alignment.center;
    _releaseAlignment = null;
    _lastTouchPosition = null;
    _lastTouchSampleMicros = 0;
    _gestureVelocity = Offset.zero;
  }
""",
    'press kinetic reset',
)

source = replace_once(
    source,
    """  void _captureTouch(TapDownDetails details) {
    _updateTouchAlignment(details.localPosition);
  }

  void _trackTouch(TapMoveDetails details) {
    if (widget.onTap == null || !widget.animatePress) return;
    final bool changed = _updateTouchAlignment(details.localPosition);
    if (changed && !_pressController.isAnimating && mounted) setState(() {});
  }
""",
    """  void _captureTouch(TapDownDetails details) {
    _releaseAlignment = null;
    _lastTouchPosition = details.localPosition;
    _lastTouchSampleMicros = _gestureClock.elapsedMicroseconds;
    _gestureVelocity = Offset.zero;
    _updateTouchAlignment(details.localPosition);
  }

  void _sampleGestureVelocity(Offset localPosition) {
    final int nowMicros = _gestureClock.elapsedMicroseconds;
    final Offset? previousPosition = _lastTouchPosition;
    final int previousMicros = _lastTouchSampleMicros;
    _lastTouchPosition = localPosition;
    _lastTouchSampleMicros = nowMicros;
    if (previousPosition == null || previousMicros == 0) return;

    final int elapsedMicros = nowMicros - previousMicros;
    if (elapsedMicros <= 0) return;
    final double samplesPerSecond =
        Duration.microsecondsPerSecond / elapsedMicros;
    Offset sample = (localPosition - previousPosition) * samplesPerSecond;
    const double maxTrackedSpeed = 7000;
    final double sampleSpeed = sample.distance;
    if (sampleSpeed > maxTrackedSpeed) {
      sample = sample * (maxTrackedSpeed / sampleSpeed);
    }
    _gestureVelocity = Offset.lerp(_gestureVelocity, sample, .42)!;
  }

  Offset _freshGestureVelocity() {
    if (_lastTouchSampleMicros == 0) return Offset.zero;
    final int ageMicros =
        _gestureClock.elapsedMicroseconds - _lastTouchSampleMicros;
    const int freshnessWindowMicros = 160000;
    if (ageMicros <= 0) return _gestureVelocity;
    if (ageMicros >= freshnessWindowMicros) return Offset.zero;
    final double freshness = 1 - (ageMicros / freshnessWindowMicros);
    return _gestureVelocity * freshness;
  }

  Alignment _projectReleaseAlignment(Offset velocity) {
    final RenderBox? box = context.findRenderObject() as RenderBox?;
    if (box == null || !box.hasSize || box.size.isEmpty) {
      return _touchAlignment;
    }
    final double xLead = (velocity.dx / math.max(box.size.width, 1) * .018)
        .clamp(-.18, .18)
        .toDouble();
    final double yLead = (velocity.dy / math.max(box.size.height, 1) * .018)
        .clamp(-.18, .18)
        .toDouble();
    return Alignment(
      (_touchAlignment.x + xLead).clamp(-.72, .72).toDouble(),
      (_touchAlignment.y + yLead).clamp(-.72, .72).toDouble(),
    );
  }

  double _releaseDepthVelocity(Offset velocity, {required bool cancelled}) {
    final RenderBox? box = context.findRenderObject() as RenderBox?;
    final double referenceExtent = box != null && box.hasSize && !box.size.isEmpty
        ? math.max(48, math.min(box.size.width, box.size.height)).toDouble()
        : 64;
    final double normalizedSpeed = velocity.distance / referenceExtent;
    final double gain = cancelled ? .24 : .18;
    return -(normalizedSpeed * gain).clamp(0.0, 2.2).toDouble();
  }

  void _trackTouch(TapMoveDetails details) {
    if (widget.onTap == null || !widget.animatePress) return;
    _releaseAlignment = null;
    _sampleGestureVelocity(details.localPosition);
    final bool changed = _updateTouchAlignment(details.localPosition);
    if (changed && !_pressController.isAnimating && mounted) setState(() {});
  }
""",
    'velocity-coupled touch tracking',
)

source = replace_once(
    source,
    """  void _press([TapDownDetails? details]) {
    if (widget.onTap == null || !widget.animatePress) return;
    if (details != null) _captureTouch(details);
    final double remainingTravel = (1 - _pressController.value)
        .clamp(0.0, 1.0)
        .toDouble();
""",
    """  void _press([TapDownDetails? details]) {
    if (widget.onTap == null || !widget.animatePress) return;
    if (details != null) _captureTouch(details);
    if (AppMotion.reduce(context)) {
      _pressController.stop();
      if (_pressController.value != 1) _pressController.value = 1;
      return;
    }
    final double remainingTravel = (1 - _pressController.value)
        .clamp(0.0, 1.0)
        .toDouble();
""",
    'reduced-motion press path',
)

source = replace_once(
    source,
    """  void _release({bool cancelled = false}) {
    if (widget.onTap == null || !widget.animatePress) return;
    final double rawVelocity = cancelled
        ? math.min(_pressController.velocity, 0.0)
        : _pressController.velocity;
    final double releaseVelocity = rawVelocity.clamp(-2.5, 2.5).toDouble();
    _pressController.animateWith(
      SpringSimulation(
        UIConstants.pressSpring,
        _pressController.value,
        0,
        releaseVelocity,
      ),
    );
  }
""",
    """  void _release({bool cancelled = false}) {
    if (widget.onTap == null || !widget.animatePress) return;
    final Offset gestureVelocity = _freshGestureVelocity();
    _releaseAlignment = _projectReleaseAlignment(gestureVelocity);
    if (AppMotion.reduce(context)) {
      _pressController.stop();
      if (_pressController.value != 0) _pressController.value = 0;
      return;
    }

    // A released surface must never keep travelling deeper because the short
    // press-in tween still has positive velocity. Couple the return spring to
    // the user's actual finger speed and force its initial direction outward.
    final double controllerVelocity = math.min(_pressController.velocity, 0.0);
    final double gestureReleaseVelocity = _releaseDepthVelocity(
      gestureVelocity,
      cancelled: cancelled,
    );
    final double releaseVelocity = math
        .min(controllerVelocity, gestureReleaseVelocity)
        .clamp(-2.5, 0.0)
        .toDouble();
    _pressController.animateWith(
      SpringSimulation(
        UIConstants.pressSpring,
        _pressController.value,
        0,
        releaseVelocity,
      ),
    );
  }
""",
    'outward velocity-coupled release',
)

source = replace_once(
    source,
    """  void dispose() {
    _pressController.dispose();
    super.dispose();
  }
""",
    """  void dispose() {
    _gestureClock.stop();
    _pressController.dispose();
    super.dispose();
  }
""",
    'gesture clock disposal',
)

source = replace_once(
    source,
    """          final double cardTilt = reduceMotion || widget.feedbackColor == null
              ? 0
              : pressed * .0145;
          final Matrix4 perspective = Matrix4.identity()
            ..setEntry(3, 2, .0013)
            ..rotateX(-_touchAlignment.y * cardTilt)
            ..rotateY(_touchAlignment.x * cardTilt);
""",
    """          final double cardTilt = reduceMotion || widget.feedbackColor == null
              ? 0
              : pressed * .0145;
          final Alignment spatialAlignment =
              _releaseAlignment ?? _touchAlignment;
          final Matrix4 perspective = Matrix4.identity()
            ..setEntry(3, 2, .0013)
            ..rotateX(-spatialAlignment.y * cardTilt)
            ..rotateY(spatialAlignment.x * cardTilt);
""",
    'release momentum perspective',
)


def normalized(items):
    return [re.sub(r'\s+', '', item) for item in items]


# Hard visual lock: no icon, color, explicit size, radius or padding token may
# change. The patch is allowed to alter only interaction state/physics.
visual_patterns = [
    r'Icons\.[A-Za-z0-9_]+',
    r'Colors\.[A-Za-z0-9_]+',
    r'Color\(\s*0x[0-9A-Fa-f]+\s*\)',
    r'IconData\([^)]*\)',
    r'\b(?:width|height)\s*:\s*-?[0-9]+(?:\.[0-9]+)?',
    r'BorderRadius\.[A-Za-z0-9_]+\([^)]*\)',
    r'EdgeInsets\.[A-Za-z0-9_]+\([^)]*\)',
]
for pattern in visual_patterns:
    old_tokens = sorted(normalized(re.findall(pattern, before)))
    new_tokens = sorted(normalized(re.findall(pattern, source)))
    if old_tokens != new_tokens:
        raise SystemExit(f'VISUAL LOCK VIOLATION: {pattern}')

main.write_text(source)

test_source = test.read_text()

test_source = replace_once(
    test_source,
    """    expect(source, contains('..rotateX(-_touchAlignment.y * cardTilt)'));
    expect(source, contains('..rotateY(_touchAlignment.x * cardTilt)'));
""",
    """    expect(source, contains('..rotateX(-spatialAlignment.y * cardTilt)'));
    expect(source, contains('..rotateY(spatialAlignment.x * cardTilt)'));
""",
    'kinetic perspective regression contract',
)

test_source = replace_once(
    test_source,
    """    expect(pressableSource, contains('math.min(_pressController.velocity, 0.0)'));
    expect(pressableSource, contains('() => _release(cancelled: true)'));
""",
    """    expect(pressableSource, contains('math.min(_pressController.velocity, 0.0)'));
    expect(pressableSource, contains('late final Stopwatch _gestureClock'));
    expect(pressableSource, contains('Offset _gestureVelocity = Offset.zero'));
    expect(pressableSource, contains('void _sampleGestureVelocity(Offset localPosition)'));
    expect(pressableSource, contains('Offset _freshGestureVelocity()'));
    expect(pressableSource, contains('Alignment _projectReleaseAlignment(Offset velocity)'));
    expect(pressableSource, contains('double _releaseDepthVelocity('));
    expect(pressableSource, contains('final double controllerVelocity ='));
    expect(pressableSource, contains('.clamp(-2.5, 0.0)'));
    expect(
      pressableSource,
      contains('final Alignment spatialAlignment ='),
    );
    expect(
      pressableSource.split('if (AppMotion.reduce(context)) {').length - 1,
      greaterThanOrEqualTo(2),
    );
    expect(pressableSource, contains('() => _release(cancelled: true)'));
""",
    'velocity release regression contract',
)

test.write_text(test_source)
