from pathlib import Path

main_path = Path('lib/main.dart')
test_path = Path('test/ui_micro_aesthetics_test.dart')

code = main_path.read_text(encoding='utf-8')
tests = test_path.read_text(encoding='utf-8')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 match, found {count}')
    return text.replace(old, new, 1)


def visual_contract(text: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Lock the user's visual contract: no color or size/padding token edits."""
    color_tokens = ('Color(', 'Colors.', 'color:', 'colors:', 'withAlpha(')
    layout_tokens = (
        'width:',
        'height:',
        'padding:',
        'margin:',
        'EdgeInsets',
        'childAspectRatio:',
        'crossAxisSpacing:',
        'mainAxisSpacing:',
        'borderRadius:',
    )
    color_lines = tuple(
        sorted(
            line.strip()
            for line in text.splitlines()
            if any(token in line for token in color_tokens)
        )
    )
    layout_lines = tuple(
        sorted(
            line.strip()
            for line in text.splitlines()
            if any(token in line for token in layout_tokens)
        )
    )
    return color_lines, layout_lines


locked_visuals = visual_contract(code)

# 1) Motion/ripple lifecycle: honor both reduced-motion and TickerMode. This
# prevents muted/offstage tickers from leaving stale global pulses alive.
code = replace_once(
    code,
    """  final List<_RipplePulse> _pulses = <_RipplePulse>[];
  final Map<int, _RipplePulse> _pointerPulses = <int, _RipplePulse>{};

  void _handlePointerDown(PointerDownEvent event) {
    if (AppMotion.reduce(context)) return;
""",
    """  final List<_RipplePulse> _pulses = <_RipplePulse>[];
  final Map<int, _RipplePulse> _pointerPulses = <int, _RipplePulse>{};

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (AppMotion.enabled(context) || _pulses.isEmpty) return;
    for (final _RipplePulse pulse in List<_RipplePulse>.of(_pulses)) {
      _removePulse(pulse, rebuild: false);
    }
  }

  void _handlePointerDown(PointerDownEvent event) {
    if (!AppMotion.enabled(context)) return;
""",
    'motion-aware global ripple lifecycle',
)

# 2) Bottom navigation: center the selected destination using the real viewport
# instead of a magic offset, without changing the existing 84px item geometry.
code = replace_once(
    code,
    """  void _scrollNavigation(int index) {
    final double target = math.max(0, index * 88 - 120).toDouble();
    if (_navController.hasClients) {
      _navController.animateTo(
        math.min(target, _navController.position.maxScrollExtent),
        duration: UIConstants.motion,
        curve: UIConstants.motionOut,
      );
    }
  }
""",
    """  void _scrollNavigation(int index) {
    if (!_navController.hasClients) return;
    final ScrollPosition position = _navController.position;
    if (!position.hasContentDimensions) return;

    // Existing geometry is 84 wide + 4 margin on each side. Keep those exact
    // dimensions, but center the selected destination in the visible viewport.
    const double itemExtent = 92;
    const double outerPadding = 4;
    final double target =
        (outerPadding +
                index * itemExtent +
                itemExtent / 2 -
                position.viewportDimension / 2)
            .clamp(position.minScrollExtent, position.maxScrollExtent)
            .toDouble();
    _navController.animateTo(
      target,
      duration: UIConstants.motion,
      curve: UIConstants.motionOut,
    );
  }
""",
    'viewport-aware navigation centering',
)

code = replace_once(
    code,
    """                          semanticLabel: '${spec.label} tab',
                          borderRadius: BorderRadius.circular(
""",
    """                          semanticLabel: '${spec.label} tab',
                          selected: active,
                          borderRadius: BorderRadius.circular(
""",
    'selected bottom-navigation semantics',
)

# 3) Offline state should be announced by assistive technology while keeping
# the exact same banner rendering, dimensions and colors.
code = replace_once(
    code,
    """  Widget build(BuildContext context) => SafeArea(
    bottom: false,
    child: Container(
      width: double.infinity,
      color: appleOrange,
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: const Text(
        'OFFLINE • Changes will sync automatically',
        textAlign: TextAlign.center,
        style: TextStyle(
          color: Colors.white,
          fontSize: 10,
          fontWeight: FontWeight.w900,
          letterSpacing: .6,
        ),
      ),
    ),
  );
""",
    """  Widget build(BuildContext context) => Semantics(
    container: true,
    liveRegion: true,
    label: 'Offline. Changes will sync automatically.',
    child: ExcludeSemantics(
      child: SafeArea(
        bottom: false,
        child: Container(
          width: double.infinity,
          color: appleOrange,
          padding: const EdgeInsets.symmetric(vertical: 5),
          child: const Text(
            'OFFLINE • Changes will sync automatically',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.white,
              fontSize: 10,
              fontWeight: FontWeight.w900,
              letterSpacing: .6,
            ),
          ),
        ),
      ),
    ),
  );
""",
    'offline live-region semantics',
)

# 4) Custom pressables: expose one clean semantic tap action, mark disabled
# surfaces correctly, and avoid a meaningless accessibility long-press action.
code = replace_once(
    code,
    """  void _handleLongPress() {
    _press();
    HapticFeedback.mediumImpact();
  }

  @override
  void dispose() {
""",
    """  void _handleLongPress() {
    _press();
    HapticFeedback.mediumImpact();
  }

  void _activate() {
    if (widget.onTap == null) return;
    if (widget.feedbackColor == null) {
      HapticFeedback.selectionClick();
    } else {
      HapticFeedback.lightImpact();
    }
    widget.onTap!();
  }

  @override
  void dispose() {
""",
    'pressable activation helper',
)

code = replace_once(
    code,
    """  Widget build(BuildContext context) => Semantics(
    button: true,
    label: widget.semanticLabel,
    selected: widget.selected,
    onLongPress: widget.onTap == null ? null : _handleLongPress,
    child: GestureDetector(
      behavior: HitTestBehavior.opaque,
""",
    """  Widget build(BuildContext context) => Semantics(
    button: widget.onTap != null,
    enabled: widget.onTap != null,
    label: widget.semanticLabel,
    selected: widget.selected,
    onTap: widget.onTap == null ? null : _activate,
    child: GestureDetector(
      excludeFromSemantics: true,
      behavior: HitTestBehavior.opaque,
""",
    'pressable semantics contract',
)

code = replace_once(
    code,
    """      onTap: widget.onTap == null
          ? null
          : () {
              if (widget.feedbackColor == null) {
                HapticFeedback.selectionClick();
              } else {
                HapticFeedback.lightImpact();
              }
              widget.onTap!();
            },
""",
    """      onTap: widget.onTap == null ? null : _activate,
""",
    'deduplicated pressable tap action',
)

code = replace_once(
    code,
    """class _BackCircle extends StatelessWidget {
  const _BackCircle();

  @override
  Widget build(BuildContext context) => _Pressable(
    onTap: () => Navigator.of(context).maybePop(),
    borderRadius: BorderRadius.circular(24),
""",
    """class _BackCircle extends StatelessWidget {
  const _BackCircle();

  @override
  Widget build(BuildContext context) => _Pressable(
    onTap: () => Navigator.of(context).maybePop(),
    semanticLabel: 'Back',
    borderRadius: BorderRadius.circular(24),
""",
    'back button semantic label',
)

# 5) Search feels immediate on submit and dismisses the keyboard naturally
# when the user taps outside. The existing debounce remains for live typing.
code = replace_once(
    code,
    """  void _onChanged(String value) {
    _debounce?.cancel();
    _debounce = Timer(
      const Duration(milliseconds: 140),
      () => widget.onChanged(value),
    );
  }

  @override
  void dispose() {
""",
    """  void _onChanged(String value) {
    _debounce?.cancel();
    _debounce = Timer(
      const Duration(milliseconds: 140),
      () => widget.onChanged(value),
    );
  }

  void _onSubmitted(String value) {
    _debounce?.cancel();
    widget.onChanged(value);
    FocusManager.instance.primaryFocus?.unfocus();
  }

  @override
  void dispose() {
""",
    'search submit handler',
)

code = replace_once(
    code,
    """    return TextField(
      onChanged: _onChanged,
      cursorColor: widget.color,
""",
    """    return TextField(
      onChanged: _onChanged,
      onSubmitted: _onSubmitted,
      onTapOutside: (_) => FocusManager.instance.primaryFocus?.unfocus(),
      cursorColor: widget.color,
""",
    'search keyboard ergonomics',
)

# 6) Display-only list cards are now first-class. This removes the misleading
# Party Ledger chevron/tap affordance that previously executed an empty action.
code = replace_once(
    code,
    """  }) : assert(
         (onTap == null) != (destinationBuilder == null),
         'Provide either onTap or destinationBuilder.',
       );
""",
    """  }) : assert(
         onTap == null || destinationBuilder == null,
         'Provide at most one of onTap or destinationBuilder.',
       );
""",
    'list-card interaction invariant',
)

code = replace_once(
    code,
    '    Widget buildCard(VoidCallback action) => _Pressable(\n',
    '    Widget buildCard(VoidCallback? action) => _Pressable(\n',
    'nullable list-card action',
)

list_start = code.find('class _ListCard extends StatelessWidget {')
list_end = code.find('class _SectionTitle extends StatelessWidget {', list_start)
if list_start < 0 or list_end <= list_start:
    raise SystemExit('list-card block not found')
list_block = code[list_start:list_end]
list_block = replace_once(
    list_block,
    """            else
              Icon(
                Icons.chevron_right_rounded,
""",
    """            else if (action != null)
              Icon(
                Icons.chevron_right_rounded,
""",
    'list-card interactive chevron',
)
list_block = replace_once(
    list_block,
    """    final Widget card = destinationBuilder == null
        ? buildCard(onTap!)
        : _FastRouteLauncher(
            destinationBuilder: destinationBuilder!,
            sourceBuilder: buildCard,
          );
""",
    """    final Widget card = destinationBuilder == null
        ? buildCard(onTap)
        : _FastRouteLauncher(
            destinationBuilder: destinationBuilder!,
            sourceBuilder: (VoidCallback action) => buildCard(action),
          );
""",
    'display-only list-card construction',
)
code = code[:list_start] + list_block + code[list_end:]

code = replace_once(
    code,
    """                      trailing: _signedMoney(item.net),
                      onTap: () {},
""",
    """                      trailing: _signedMoney(item.net),
""",
    'remove Party Ledger no-op tap',
)

# 7) Never hide digits in the large amount hero. Scale down only when needed,
# preserving the same typography, card geometry and palette.
hero_start = code.find('class _HeroValue extends StatelessWidget {')
hero_end = code.find('class _ListCard extends StatelessWidget {', hero_start)
if hero_start < 0 or hero_end <= hero_start:
    raise SystemExit('hero value block not found')
hero_block = code[hero_start:hero_end]
hero_block = replace_once(
    hero_block,
    """      Text(
        value,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: TextStyle(
          color: color,
          fontSize: 32,
          fontWeight: FontWeight.w700,
          fontFeatures: AppStyles.tabularFigures,
          letterSpacing: -.8,
          shadows: <Shadow>[Shadow(color: glow.withAlpha(94), blurRadius: 16)],
        ),
      ),
""",
    """      FittedBox(
        fit: BoxFit.scaleDown,
        alignment: Alignment.centerLeft,
        child: Text(
          value,
          maxLines: 1,
          softWrap: false,
          style: TextStyle(
            color: color,
            fontSize: 32,
            fontWeight: FontWeight.w700,
            fontFeatures: AppStyles.tabularFigures,
            letterSpacing: -.8,
            shadows: <Shadow>[
              Shadow(color: glow.withAlpha(94), blurRadius: 16),
            ],
          ),
        ),
      ),
""",
    'non-truncating hero amount',
)
code = code[:hero_start] + hero_block + code[hero_end:]

# Enforce the user's hard constraint after every source edit.
if visual_contract(code) != locked_visuals:
    raise SystemExit('visual contract violated: a color or size/padding token changed')

# Keep the source-guard test synchronized with the already-landed interaction
# engine v2.1, then add regression guards for this accessibility/comfort pass.
for old, new, label in (
    ('Duration pressIn = Duration(milliseconds: 70)', 'Duration pressIn = Duration(milliseconds: 55)', 'pressIn test'),
    ('stiffness: 520', 'stiffness: 460', 'spring stiffness test'),
    ('damping: 30', 'damping: 32', 'spring damping test'),
    ('offset: Offset(0, motion * 1.25)', 'offset: Offset(0, motion * 1.30)', 'press travel test'),
    ('scale: 1 - (motion * .014)', 'scale: 1 - (motion * .017)', 'press scale test'),
    ('..setEntry(3, 2, .0012)', '..setEntry(3, 2, .0013)', 'perspective test'),
):
    tests = replace_once(tests, old, new, label)

regression_anchor = """    // Brand/state color logic and Firebase integration must stay untouched.
"""
regression_checks = """    // UI comfort/accessibility v3: behavior improves without visual drift.
    expect(source, contains('if (!AppMotion.enabled(context)) return;'));
    expect(source, contains('selected: active,'));
    expect(source, contains("semanticLabel: 'Back',"));
    expect(source, contains('liveRegion: true,'));
    expect(source, contains('enabled: widget.onTap != null,'));
    expect(source, contains('excludeFromSemantics: true,'));
    expect(source, contains('onSubmitted: _onSubmitted,'));
    expect(source, contains('position.viewportDimension / 2'));
    expect(
      source,
      contains('Provide at most one of onTap or destinationBuilder.'),
    );
    expect(source, contains('? buildCard(onTap)'));
    expect(source, isNot(contains('onTap: () {},'));

"""
if regression_checks not in tests:
    tests = replace_once(
        tests,
        regression_anchor,
        regression_checks + regression_anchor,
        'UI comfort regression guards',
    )

main_path.write_text(code, encoding='utf-8')
test_path.write_text(tests, encoding='utf-8')

print('UI comfort v3 patch applied with card-size/color contract preserved.')
