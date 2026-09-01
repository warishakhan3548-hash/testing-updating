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


def replace_region(text: str, start: str, end: str, new: str, label: str) -> str:
    if text.count(start) != 1:
        raise SystemExit(f'{label}: start anchor count={text.count(start)}')
    start_at = text.index(start)
    end_at = text.find(end, start_at + len(start))
    if end_at < 0:
        raise SystemExit(f'{label}: end anchor missing')
    return text[:start_at] + new + text[end_at:]


# Ignore tiny pointer jitter while preserving the approved press physics.
source = replace_once(
    source,
    """class _PressableState extends State<_Pressable>\n    with SingleTickerProviderStateMixin {\n  late final AnimationController _pressController;\n""",
    """class _PressableState extends State<_Pressable>\n    with SingleTickerProviderStateMixin {\n  static const double _touchAlignmentEpsilonSquared = .0004;\n\n  late final AnimationController _pressController;\n""",
    'press tracking epsilon constant',
)
source = replace_once(
    source,
    """    final Alignment nextAlignment = Alignment(x, y);\n    if (nextAlignment == _touchAlignment) return false;\n    _touchAlignment = Alignment(x, y);\n    return true;\n""",
    """    final Alignment nextAlignment = Alignment(x, y);\n    final double deltaX = nextAlignment.x - _touchAlignment.x;\n    final double deltaY = nextAlignment.y - _touchAlignment.y;\n    if (deltaX * deltaX + deltaY * deltaY <\n        _touchAlignmentEpsilonSquared) {\n      return false;\n    }\n    _touchAlignment = nextAlignment;\n    return true;\n""",
    'press touch alignment deadband',
)

# Give every programmatic page motion a transaction identity. This prevents
# stale completion callbacks from winning rapid A -> B -> A tab sequences and
# explicitly hands control back to a user's drag when they interrupt motion.
source = replace_once(
    source,
    """  int? _programmaticPageTarget;\n""",
    """  int? _programmaticPageTarget;\n  int _pageMotionGeneration = 0;\n  bool _userPageDragActive = false;\n""",
    'navigation generation fields',
)

new_select_tab = """  void _selectTab(int index) {
    if (index < 0 || index >= _tabs.length) return;

    final bool alreadySettled =
        _tab == index &&
        _settledPage == index &&
        _programmaticPageTarget == null;
    if (alreadySettled || _programmaticPageTarget == index) return;

    final bool reduceMotion = AppMotion.reduce(context);
    final int generation = ++_pageMotionGeneration;
    _userPageDragActive = false;

    if (reduceMotion) {
      _programmaticPageTarget = null;
      setState(() {
        _tab = index;
        _settledPage = index;
      });
      _scrollNavigation(index);
      if (_pageController.hasClients) _pageController.jumpToPage(index);
      return;
    }

    if (_tab != index) setState(() => _tab = index);
    _scrollNavigation(index);

    if (!_pageController.hasClients) {
      _programmaticPageTarget = null;
      return;
    }
    _programmaticPageTarget = index;

    final double livePage = _pageController.page ?? _settledPage.toDouble();
    final int currentPage = livePage
        .round()
        .clamp(0, _tabs.length - 1)
        .toInt();
    final int pageDistance = (index - currentPage).abs();

    // Distant tab changes stay constant-time: stage beside the destination and
    // animate only the final page instead of traversing every intermediate view.
    if (pageDistance > 1) {
      final int stagingPage = index > currentPage ? index - 1 : index + 1;
      _pageController.jumpToPage(stagingPage);
    }

    unawaited(
      _pageController
          .animateToPage(
            index,
            duration: UIConstants.motion,
            curve: UIConstants.motionOut,
          )
          .whenComplete(
            () => _finishProgrammaticPageMotion(index, generation),
          ),
    );
  }

"""
source = replace_region(
    source,
    '  void _selectTab(int index) {',
    '  void _finishProgrammaticPageMotion',
    new_select_tab,
    'select-tab transaction',
)

new_motion_completion = """  void _finishProgrammaticPageMotion(int target, int generation) {
    if (!mounted ||
        _pageMotionGeneration != generation ||
        _programmaticPageTarget != target) {
      return;
    }
    _programmaticPageTarget = null;
    if (!_pageController.hasClients) return;

    final double? page = _pageController.page;
    if (page == null) return;
    final int settledIndex = page.round().clamp(0, _tabs.length - 1).toInt();
    final bool selectionChanged = settledIndex != _tab;
    final bool pageChanged = settledIndex != _settledPage;
    if (!selectionChanged && !pageChanged) return;
    setState(() {
      _tab = settledIndex;
      _settledPage = settledIndex;
    });
    if (selectionChanged) _scrollNavigation(settledIndex);
  }

  bool _handlePageScrollNotification(ScrollNotification notification) {
    if (notification is ScrollStartNotification &&
        notification.dragDetails != null) {
      _userPageDragActive = true;
      if (_programmaticPageTarget != null) {
        _pageMotionGeneration++;
        _programmaticPageTarget = null;
      }
    } else if (notification is ScrollEndNotification &&
        _userPageDragActive) {
      _userPageDragActive = false;
      _finishUserPageMotion();
    }
    return false;
  }

  void _finishUserPageMotion() {
    if (!mounted || !_pageController.hasClients) return;
    final double? page = _pageController.page;
    if (page == null) return;

    final int settledIndex = page.round().clamp(0, _tabs.length - 1).toInt();
    if (_tab == settledIndex && _settledPage == settledIndex) return;

    final bool selectionChanged = _tab != settledIndex;
    if (selectionChanged) HapticFeedback.selectionClick();
    setState(() {
      _tab = settledIndex;
      _settledPage = settledIndex;
    });
    if (selectionChanged) _scrollNavigation(settledIndex);
  }

"""
source = replace_region(
    source,
    '  void _finishProgrammaticPageMotion',
    '  void _handlePageChanged(int index) {',
    new_motion_completion,
    'motion completion and gesture handoff',
)

# Observe only the PageView's scroll lifecycle. NotificationListener is
# behavior-only and adds no visual/layout decoration.
page_pattern = re.compile(
    r'(?P<indent>^[ \t]*)PageView\(\s*'
    r'controller:\s*_pageController,\s*'
    r'physics:\s*const PageScrollPhysics\(\s*'
    r'parent:\s*BouncingScrollPhysics\(\),\s*'
    r'\),\s*'
    r'allowImplicitScrolling:\s*true,\s*'
    r'onPageChanged:\s*_handlePageChanged,\s*'
    r'children:\s*screens,\s*'
    r'\)',
    re.MULTILINE,
)
matches = list(page_pattern.finditer(source))
if len(matches) != 1:
    raise SystemExit(
        f'PageView event surface: expected exactly one canonical match, found {len(matches)}'
    )
match = matches[0]
indent = match.group('indent')
page_replacement = (
    f'{indent}NotificationListener<ScrollNotification>(\n'
    f'{indent}  onNotification: _handlePageScrollNotification,\n'
    f'{indent}  child: PageView(\n'
    f'{indent}    controller: _pageController,\n'
    f'{indent}    physics: const PageScrollPhysics(\n'
    f'{indent}      parent: BouncingScrollPhysics(),\n'
    f'{indent}    ),\n'
    f'{indent}    allowImplicitScrolling: true,\n'
    f'{indent}    onPageChanged: _handlePageChanged,\n'
    f'{indent}    children: screens,\n'
    f'{indent}  ),\n'
    f'{indent})'
)
source = page_pattern.sub(page_replacement, source, count=1)

# The painter already listens to its animation via repaint; unrelated parent
# rebuilds no longer force a redundant paint pass.
source = replace_once(
    source,
    """  bool shouldRepaint(covariant _GlobalTapRipplePainter oldDelegate) => true;\n""",
    """  bool shouldRepaint(covariant _GlobalTapRipplePainter oldDelegate) =>\n      !listEquals(oldDelegate.pulses, pulses);\n""",
    'ripple painter rebuild guard',
)

# Visual lock: icon identifiers/codepoints, colors and explicit dimensions must
# remain byte-equivalent as multisets before and after the behavior patch.
def normalized(items):
    return [re.sub(r'\s+', '', item) for item in items]


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
    """    expect(\n      source,\n      contains('bool _updateTouchAlignment(Offset localPosition)'),\n    );\n    expect(source, contains('void _trackTouch(TapMoveDetails details)'));\n""",
    """    expect(\n      source,\n      contains('bool _updateTouchAlignment(Offset localPosition)'),\n    );\n    expect(\n      source,\n      contains('static const double _touchAlignmentEpsilonSquared = .0004'),\n    );\n    expect(source, contains('deltaX * deltaX + deltaY * deltaY'));\n    expect(source, contains('void _trackTouch(TapMoveDetails details)'));\n""",
    'press tracking regression checks',
)
test_source = replace_once(
    test_source,
    """    expect(RegExp(r'active: _settledPage ==').allMatches(source), hasLength(7));\n    expect(source, isNot(contains('active: _tab ==')));\n""",
    """    expect(RegExp(r'active: _settledPage ==').allMatches(source), hasLength(7));\n    expect(source, isNot(contains('active: _tab ==')));\n    expect(source, contains('int _pageMotionGeneration = 0'));\n    expect(source, contains('bool _userPageDragActive = false'));\n    expect(source, contains('_pageMotionGeneration != generation'));\n    expect(source, contains('notification.dragDetails != null'));\n    expect(source, contains('NotificationListener<ScrollNotification>'));\n    expect(source, contains('_finishUserPageMotion()'));\n    expect(source, contains('final int pageDistance = (index - currentPage).abs()'));\n    expect(source, contains('if (pageDistance > 1)'));\n    expect(source, contains('_pageController.jumpToPage(stagingPage)'));\n    expect(source, contains('!listEquals(oldDelegate.pulses, pulses)'));\n""",
    'navigation race regression checks',
)
test.write_text(test_source)
