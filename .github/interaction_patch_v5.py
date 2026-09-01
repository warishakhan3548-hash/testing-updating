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
    "class AppShell extends StatefulWidget {\n",
    """class _LedgerPagePhysics extends PageScrollPhysics {
  const _LedgerPagePhysics({super.parent});

  static const SpringDescription _pageSettleSpring = SpringDescription(
    mass: .78,
    stiffness: 300,
    damping: 30,
  );

  @override
  _LedgerPagePhysics applyTo(ScrollPhysics? ancestor) =>
      _LedgerPagePhysics(parent: buildParent(ancestor));

  @override
  SpringDescription get spring => _pageSettleSpring;
}

class AppShell extends StatefulWidget {
""",
    'ledger page physics',
)

source = replace_once(
    source,
    """                  physics: const PageScrollPhysics(
                    parent: BouncingScrollPhysics(),
                  ),
""",
    """                  physics: const _LedgerPagePhysics(
                    parent: BouncingScrollPhysics(),
                  ),
""",
    'PageView physics',
)

old_page_changed = """  void _handlePageChanged(int index) {
    // animateToPage can report every intermediate page. The selected tab is
    // already the user's requested destination, so suppress those callbacks
    // and their haptics until the driven motion settles.
    if (_programmaticPageTarget != null) return;
    if (_tab == index && _settledPage == index) return;
    final bool selectionChanged = _tab != index;
    if (selectionChanged) HapticFeedback.selectionClick();
    setState(() {
      _tab = index;
      _settledPage = index;
    });
    if (selectionChanged) _scrollNavigation(index);
  }
"""

new_page_changed = """  void _handlePageChanged(int index) {
    // Driven tab motion owns selection while active. During a live user swipe,
    // preview only the navigation selection and defer the expensive active-sync
    // listener handoff until ScrollEnd settles on the final page.
    if (_programmaticPageTarget != null) return;

    final bool selectionChanged = _tab != index;
    if (_userPageDragActive) {
      if (!selectionChanged) return;
      HapticFeedback.selectionClick();
      setState(() => _tab = index);
      _scrollNavigation(index);
      return;
    }

    if (!selectionChanged && _settledPage == index) return;
    if (selectionChanged) HapticFeedback.selectionClick();
    setState(() {
      _tab = index;
      _settledPage = index;
    });
    if (selectionChanged) _scrollNavigation(index);
  }
"""

source = replace_once(
    source,
    old_page_changed,
    new_page_changed,
    'deferred active-sync page handoff',
)


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
    """    expect(source, contains('NotificationListener<ScrollNotification>'));
    expect(source, contains('_finishUserPageMotion()'));
""",
    """    expect(source, contains('NotificationListener<ScrollNotification>'));
    expect(source, contains('_finishUserPageMotion()'));
    expect(source, contains('class _LedgerPagePhysics extends PageScrollPhysics'));
    expect(source, contains('mass: .78'));
    expect(source, contains('stiffness: 300'));
    expect(source, contains('damping: 30'));
    expect(source, contains('physics: const _LedgerPagePhysics('));
    expect(source, contains('if (_userPageDragActive) {'));
    expect(source, contains('setState(() => _tab = index);'));
""",
    'gesture settle regression checks',
)
test.write_text(test_source)
