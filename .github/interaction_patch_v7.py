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
    "import 'package:flutter/gestures.dart' show TapMoveDetails;",
    "import 'package:flutter/gestures.dart' show TapMoveDetails, kPrimaryButton;",
    'primary pointer import',
)

source = replace_once(
    source,
    """  void _handlePointerDown(PointerDownEvent event) {
    if (!AppMotion.enabled(context)) return;

    final _RipplePulse? existing = _pointerPulses.remove(event.pointer);
""",
    """  void _handlePointerDown(PointerDownEvent event) {
    if (!AppMotion.enabled(context) ||
        (event.buttons & kPrimaryButton) == 0) {
      return;
    }

    final _RipplePulse? existing = _pointerPulses.remove(event.pointer);
""",
    'primary pointer ripple gate',
)

source = replace_once(
    source,
    """  int _pageMotionGeneration = 0;
  bool _userPageDragActive = false;
  final ScrollController _navController = ScrollController();
""",
    """  int _pageMotionGeneration = 0;
  bool _userPageDragActive = false;
  final Set<int> _dragHapticPages = <int>{};
  final ScrollController _navController = ScrollController();
""",
    'drag haptic state',
)

source = replace_once(
    source,
    """    final bool reduceMotion = AppMotion.reduce(context);
    final int generation = ++_pageMotionGeneration;
    _userPageDragActive = false;

    if (reduceMotion) {
""",
    """    final bool reduceMotion = AppMotion.reduce(context);
    final int generation = ++_pageMotionGeneration;
    _userPageDragActive = false;
    _dragHapticPages.clear();

    if (reduceMotion) {
""",
    'programmatic page gesture reset',
)

source = replace_once(
    source,
    """  bool _handlePageScrollNotification(ScrollNotification notification) {
    if (notification is ScrollStartNotification &&
        notification.dragDetails != null) {
      _userPageDragActive = true;
      if (_programmaticPageTarget != null) {
        _pageMotionGeneration++;
        _programmaticPageTarget = null;
      }
    } else if (notification is ScrollEndNotification && _userPageDragActive) {
      _userPageDragActive = false;
      _finishUserPageMotion();
    }
    return false;
  }
""",
    """  bool _handlePageScrollNotification(ScrollNotification notification) {
    if (notification is ScrollStartNotification &&
        notification.dragDetails != null) {
      _userPageDragActive = true;
      _dragHapticPages
        ..clear()
        ..add(_tab);
      if (_programmaticPageTarget != null) {
        _pageMotionGeneration++;
        _programmaticPageTarget = null;
      }
    } else if (notification is ScrollEndNotification && _userPageDragActive) {
      _userPageDragActive = false;
      _finishUserPageMotion();
      _dragHapticPages.clear();
    }
    return false;
  }
""",
    'page drag haptic lifecycle',
)

source = replace_once(
    source,
    """    final bool selectionChanged = _tab != settledIndex;
    if (selectionChanged) HapticFeedback.selectionClick();
    setState(() {
      _tab = settledIndex;
      _settledPage = settledIndex;
    });
""",
    """    final bool selectionChanged = _tab != settledIndex;
    if (selectionChanged && _dragHapticPages.add(settledIndex)) {
      HapticFeedback.selectionClick();
    }
    setState(() {
      _tab = settledIndex;
      _settledPage = settledIndex;
    });
""",
    'settled page haptic coalescing',
)

source = replace_once(
    source,
    """    if (_userPageDragActive) {
      if (!selectionChanged) return;
      HapticFeedback.selectionClick();
      setState(() => _tab = index);
      _scrollNavigation(index);
      return;
    }
""",
    """    if (_userPageDragActive) {
      if (!selectionChanged) return;
      if (_dragHapticPages.add(index)) HapticFeedback.selectionClick();
      setState(() => _tab = index);
      _scrollNavigation(index);
      return;
    }
""",
    'live page haptic coalescing',
)

source = replace_once(
    source,
    """    final double target =
        (outerPadding +
                index * itemExtent +
                itemExtent / 2 -
                position.viewportDimension / 2)
            .clamp(position.minScrollExtent, position.maxScrollExtent)
            .toDouble();
    if (AppMotion.reduce(context)) {
""",
    """    final double target =
        (outerPadding +
                index * itemExtent +
                itemExtent / 2 -
                position.viewportDimension / 2)
            .clamp(position.minScrollExtent, position.maxScrollExtent)
            .toDouble();
    if ((position.pixels - target).abs() < .5) return;
    if (AppMotion.reduce(context)) {
""",
    'navigation no-op guard',
)

source = replace_once(
    source,
    """    final double releaseVelocity = math
        .min(controllerVelocity, gestureReleaseVelocity)
        .clamp(-2.5, 0.0)
        .toDouble();
    _pressController.animateWith(
""",
    """    final double releaseVelocity = math
        .min(controllerVelocity, gestureReleaseVelocity)
        .clamp(-2.5, 0.0)
        .toDouble();
    if (_pressController.value.abs() <= .0001 &&
        releaseVelocity.abs() <= .0001) {
      if (_pressController.value != 0) _pressController.value = 0;
      return;
    }
    _pressController.animateWith(
""",
    'zero energy release guard',
)


def normalized(items):
    return [re.sub(r'\s+', '', item) for item in items]


# Strict visual lock: interaction work may not alter existing colors, icons,
# dimensions, radii, padding or font sizes.
visual_patterns = [
    r'Icons\.[A-Za-z0-9_]+',
    r'Colors\.[A-Za-z0-9_]+',
    r'Color\(\s*0x[0-9A-Fa-f]+\s*\)',
    r'IconData\([^)]*\)',
    r'\b(?:width|height|minWidth|maxWidth|minHeight|maxHeight|fontSize)\s*:\s*-?[0-9]+(?:\.[0-9]+)?',
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
    """    expect(source, contains('if (!AppMotion.enabled(context)) return;'));
    expect(source, contains('selected: active,'));
""",
    """    expect(source, contains('(event.buttons & kPrimaryButton) == 0'));
    expect(source, contains('selected: active,'));
""",
    'primary pointer regression contract',
)

test_source = replace_once(
    test_source,
    """    expect(pressableSource, contains('final Alignment spatialAlignment ='));
    expect(
      pressableSource.split('if (AppMotion.reduce(context)) {').length - 1,
      greaterThanOrEqualTo(2),
    );
""",
    """    expect(pressableSource, contains('final Alignment spatialAlignment ='));
    expect(
      pressableSource,
      contains('_pressController.value.abs() <= .0001'),
    );
    expect(pressableSource, contains('releaseVelocity.abs() <= .0001'));
    expect(
      pressableSource.split('if (AppMotion.reduce(context)) {').length - 1,
      greaterThanOrEqualTo(2),
    );
""",
    'zero energy release regression contract',
)

test_source = replace_once(
    test_source,
    """    expect(source, contains('bool _userPageDragActive = false'));
    expect(source, contains('_pageMotionGeneration != generation'));
""",
    """    expect(source, contains('bool _userPageDragActive = false'));
    expect(source, contains('final Set<int> _dragHapticPages = <int>{}'));
    expect(source, contains('_dragHapticPages.add(index)'));
    expect(source, contains('_dragHapticPages.add(settledIndex)'));
    expect(source, contains('_dragHapticPages.clear()'));
    expect(source, contains('_pageMotionGeneration != generation'));
""",
    'page haptic coalescing regression contract',
)

test_source = replace_once(
    test_source,
    """    expect(source, contains('position.viewportDimension / 2'));
    expect(source, contains('int _settledPage = 0;'));
""",
    """    expect(source, contains('position.viewportDimension / 2'));
    expect(source, contains('(position.pixels - target).abs() < .5'));
    expect(source, contains('int _settledPage = 0;'));
""",
    'navigation no-op regression contract',
)

test.write_text(test_source)
