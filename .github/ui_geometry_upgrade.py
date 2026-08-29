#!/usr/bin/env python3
from pathlib import Path

TARGET = Path('lib/main.dart')
code = TARGET.read_text(encoding='utf-8')
original = code


def class_region(class_name: str):
    global code
    marker = f'class {class_name}'
    start = code.find(marker)
    if start < 0:
        raise SystemExit(f'SAFETY STOP: class not found: {class_name}')
    next_start = code.find('\nclass ', start + len(marker))
    end = len(code) if next_start < 0 else next_start
    return start, end


def replace_once(old: str, new: str, label: str) -> None:
    global code
    count = code.count(old)
    if count != 1:
        raise SystemExit(f'SAFETY STOP: {label}: expected 1 match, found {count}')
    code = code.replace(old, new, 1)


def replace_in_class(class_name: str, old: str, new: str, label: str, expected: int = 1) -> None:
    global code
    start, end = class_region(class_name)
    region = code[start:end]
    count = region.count(old)
    if count != expected:
        raise SystemExit(
            f'SAFETY STOP: {label} in {class_name}: expected {expected}, found {count}'
        )
    region = region.replace(old, new)
    code = code[:start] + region + code[end:]


def replace_present(old: str, new: str, label: str) -> int:
    global code
    count = code.count(old)
    if count:
        code = code.replace(old, new)
        print(f'{label}: {count}')
    return count


# -----------------------------------------------------------------------------
# Core geometry tokens: cross-platform 48dp minimum target, 4/8-point rhythm.
# -----------------------------------------------------------------------------
replace_in_class(
    'UIConstants',
    '  static const double minTapTarget = 48;\n',
    '  static const double minTapTarget = 48;\n'
    '  static const double compactButtonHeight = 48;\n'
    '  static const double standardButtonHeight = 56;\n',
    'button height tokens',
)
for old, new, label in (
    ('  static const double inputRadius = 20;', '  static const double inputRadius = 16;', 'input radius'),
    ('  static const double compactRadius = 18;', '  static const double compactRadius = 16;', 'compact radius'),
    ('  static const double actionRadius = 22;', '  static const double actionRadius = 20;', 'action radius'),
    ('  static const double cardRadius = 26;', '  static const double cardRadius = 24;', 'card radius'),
    ('  static const double heroRadius = 28;', '  static const double heroRadius = 24;', 'hero radius'),
    ('  static const double sheetRadius = 36;', '  static const double sheetRadius = 32;', 'sheet radius'),
    ('  static const EdgeInsets cardPadding = EdgeInsets.all(18);', '  static const EdgeInsets cardPadding = EdgeInsets.all(20);', 'card padding'),
    ('  static const EdgeInsets compactCardPadding = EdgeInsets.all(15);', '  static const EdgeInsets compactCardPadding = EdgeInsets.all(16);', 'compact card padding'),
    ('      EdgeInsets.symmetric(horizontal: 20, vertical: 18);', '      EdgeInsets.symmetric(horizontal: 20, vertical: 16);', 'input padding'),
    ('  static const EdgeInsets actionPadding = EdgeInsets.symmetric(horizontal: 22);', '  static const EdgeInsets actionPadding = EdgeInsets.symmetric(horizontal: 20);', 'action padding'),
):
    replace_in_class('UIConstants', old, new, label)
replace_in_class(
    'UIConstants',
    '  static const EdgeInsets actionPadding = EdgeInsets.symmetric(horizontal: 20);\n',
    '  static const EdgeInsets actionPadding = EdgeInsets.symmetric(horizontal: 20);\n'
    '  static const EdgeInsets screenPadding = EdgeInsets.fromLTRB(20, 8, 20, 32);\n',
    'screen padding token',
)

# -----------------------------------------------------------------------------
# App shell + navigation geometry.
# -----------------------------------------------------------------------------
replace_in_class(
    '_AppShellState',
    'final double target = math.max(0, index * 82 - 120).toDouble();',
    'final double target = math.max(0, index * 88 - 120).toDouble();',
    'navigation centering geometry',
)
replace_in_class('_BottomLedgerNav', '          height: 88,', '          height: 80,', 'nav outer height')
replace_in_class(
    '_BottomLedgerNav',
    '                        width: 82,\n                        height: 74,\n                        margin: const EdgeInsets.symmetric(horizontal: 2),',
    '                        width: 80,\n                        height: 64,\n                        margin: const EdgeInsets.symmetric(horizontal: 4),',
    'nav item proportions',
)
replace_in_class('_BottomLedgerNav', '                                size: 27,', '                                size: 24,', 'nav icon size')
replace_in_class(
    '_BottomLedgerNav',
    '                                    active ? FontWeight.w900 : FontWeight.w700,',
    '                                    active ? FontWeight.w800 : FontWeight.w600,',
    'nav label hierarchy',
)
replace_in_class('_BottomLedgerNav', '                              width: active ? 38 : 0,', '                              width: active ? 40 : 0,', 'nav active indicator')

# -----------------------------------------------------------------------------
# Header, actions, search and primary controls.
# -----------------------------------------------------------------------------
replace_in_class(
    '_ScreenHeader',
    '          padding: const EdgeInsets.fromLTRB(24, 14, 20, 16),',
    '          padding: const EdgeInsets.fromLTRB(20, 16, 20, 16),',
    'header/list alignment',
)
replace_in_class('_ScreenHeader', '                const SizedBox(width: 11),', '                const SizedBox(width: 12),', 'header leading gap')
replace_in_class(
    '_ScreenHeader',
    '                        fontSize: leading == null ? 30 : 26,\n                        fontWeight: FontWeight.w900,\n                        letterSpacing: -.5,',
    '                        fontSize: leading == null ? 28 : 24,\n                        fontWeight: FontWeight.w800,\n                        letterSpacing: -.4,',
    'header title hierarchy',
)
replace_in_class(
    '_ScreenHeader',
    '                                fontWeight: FontWeight.w900,\n                                letterSpacing: 1.1,',
    '                                fontWeight: FontWeight.w700,\n                                letterSpacing: 1.0,',
    'header subtitle hierarchy',
)
replace_in_class('_CircleAction', '            width: 50,\n            height: 50,', '            width: 48,\n            height: 48,', 'circle action target')
replace_in_class('_BackCircle', '        borderRadius: BorderRadius.circular(25),', '        borderRadius: BorderRadius.circular(24),', 'back radius')
replace_in_class('_BackCircle', '          width: 50,\n          height: 50,', '          width: 48,\n          height: 48,', 'back target')
replace_in_class('_SearchBoxState', '        fontWeight: FontWeight.w800,', '        fontWeight: FontWeight.w700,', 'search text weight', expected=1)
replace_in_class(
    '_SearchBoxState',
    '        contentPadding:\n            const EdgeInsets.symmetric(horizontal: 20, vertical: 19),',
    '        contentPadding:\n            const EdgeInsets.symmetric(horizontal: 20, vertical: 16),',
    'search vertical density',
)
replace_in_class('_SearchBoxState', '          fontWeight: FontWeight.w800,', '          fontWeight: FontWeight.w600,', 'search hint weight', expected=1)
replace_in_class('_SearchBoxState', '        prefixIconConstraints: const BoxConstraints(minWidth: 54),', '        prefixIconConstraints: const BoxConstraints(minWidth: 48),', 'search icon proportion')
replace_in_class(
    '_PrimaryButton',
    '          height: compact ? 52 : 58,',
    '          height: compact\n              ? UIConstants.compactButtonHeight\n              : UIConstants.standardButtonHeight,',
    'primary button heights',
)
replace_in_class(
    '_PrimaryButton',
    '                  fontSize: compact ? 15.5 : 17,\n                  fontWeight: FontWeight.w900,',
    '                  fontSize: compact ? 15 : 16.5,\n                  fontWeight: FontWeight.w800,',
    'primary button typography',
)

# -----------------------------------------------------------------------------
# Hero/list hierarchy: preserve all semantic colors and glow behavior.
# -----------------------------------------------------------------------------
replace_in_class('_AmountHero', '      padding: const EdgeInsets.all(22),', '      padding: const EdgeInsets.all(20),', 'amount hero padding')
replace_in_class(
    '_HeroValue',
    '              fontSize: 10,\n              fontWeight: FontWeight.w900,',
    '              fontSize: 11,\n              fontWeight: FontWeight.w600,',
    'hero label hierarchy',
)
replace_in_class('_HeroValue', '          const SizedBox(height: 5),', '          const SizedBox(height: 4),', 'hero label/value gap')
replace_in_class(
    '_HeroValue',
    '              fontSize: 31,\n              fontWeight: FontWeight.w900,',
    '              fontSize: 32,\n              fontWeight: FontWeight.w700,',
    'hero amount hierarchy',
)
replace_in_class('_ListCard', '        padding: const EdgeInsets.only(bottom: 14),', '        padding: const EdgeInsets.only(bottom: 12),', 'list card rhythm')
replace_in_class('_ListCard', '                  width: 48,\n                  height: 48,', '                  width: 44,\n                  height: 44,', 'list avatar geometry')
replace_in_class('_ListCard', '                          size: 22,', '                          size: 20,', 'list avatar icon')
replace_in_class('_ListCard', '                              fontWeight: FontWeight.w900,', '                              fontWeight: FontWeight.w800,', 'list avatar letter weight')
replace_in_class('_ListCard', '                const SizedBox(width: 15),', '                const SizedBox(width: 16),', 'list content gap')
replace_in_class(
    '_ListCard',
    '                          fontSize: 16.5,\n                          fontWeight: FontWeight.w900,',
    '                          fontSize: 16,\n                          fontWeight: FontWeight.w700,',
    'list title hierarchy',
)
replace_in_class('_ListCard', '                          fontWeight: FontWeight.w800,', '                          fontWeight: FontWeight.w600,', 'list subtitle hierarchy')
replace_in_class(
    '_ListCard',
    '                      fontSize: 15.5,\n                      fontWeight: FontWeight.w900,',
    '                      fontSize: 16,\n                      fontWeight: FontWeight.w700,',
    'list amount hierarchy',
)
replace_in_class('_SectionTitle', '                  fontWeight: FontWeight.w900,', '                  fontWeight: FontWeight.w800,', 'section title hierarchy')

# -----------------------------------------------------------------------------
# Inputs/sheets and dual-action role controls.
# -----------------------------------------------------------------------------
replace_once(
    'contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 17),',
    'contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),',
    'month/year picker density',
)
replace_in_class('_SheetFrame', '                  width: 54,\n                  height: 6,', '                  width: 40,\n                  height: 4,', 'sheet handle geometry')
replace_in_class('_SheetFrame', '              const SizedBox(height: 26),', '              const SizedBox(height: 24),', 'sheet handle/title gap')
replace_in_class(
    '_SheetFrame',
    '                  fontSize: 30,\n                  fontWeight: FontWeight.w900,\n                  letterSpacing: -.5,',
    '                  fontSize: 24,\n                  fontWeight: FontWeight.w800,\n                  letterSpacing: -.4,',
    'sheet title hierarchy',
)
replace_in_class('_MilkCustomerRoleButton', '      borderRadius: BorderRadius.circular(22),', '      borderRadius: BorderRadius.circular(UIConstants.actionRadius),', 'role press radius')
replace_in_class('_MilkCustomerRoleButton', '          minHeight: 62,', '          minHeight: 56,', 'role button height')
replace_in_class('_MilkCustomerRoleButton', '        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),', '        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),', 'role button padding')
replace_in_class('_MilkCustomerRoleButton', '          borderRadius: BorderRadius.circular(22),', '          borderRadius: BorderRadius.circular(UIConstants.actionRadius),', 'role surface radius')
replace_in_class(
    '_MilkCustomerRoleButton',
    '                    fontSize: 17,\n                    fontWeight: FontWeight.w900,\n                    letterSpacing: -.25,',
    '                    fontSize: 16.5,\n                    fontWeight: FontWeight.w800,\n                    letterSpacing: -.2,',
    'role button typography',
)
replace_in_class('_MiniAction', '                  fontWeight: FontWeight.w900,', '                  fontWeight: FontWeight.w700,', 'mini action hierarchy')

# -----------------------------------------------------------------------------
# Shared no-stick ledger table: compact visual rows, 48dp destructive target.
# -----------------------------------------------------------------------------
replace_in_class('_LedgerTableCard', '        borderRadius: BorderRadius.circular(25),', '        borderRadius: BorderRadius.circular(UIConstants.cardRadius),', 'ledger table radius')
replace_in_class('_LedgerTableCard', '                constraints: const BoxConstraints(minHeight: 58),', '                constraints: const BoxConstraints(minHeight: 48),', 'ledger table header')
replace_in_class('_LedgerTableCard', '                              fontWeight: FontWeight.w900,', '                              fontWeight: FontWeight.w700,', 'ledger header typography')
replace_in_class('_LedgerTableCard', '                  constraints: BoxConstraints(minHeight: compact ? 78 : 84),', '                  constraints: const BoxConstraints(minHeight: 72),', 'ledger row height')
replace_in_class(
    '_LedgerTableCard',
    '                            semanticLabel: rows[rowIndex].semanticLabel,\n                            compact: compact,',
    '                            semanticLabel: rows[rowIndex].semanticLabel,',
    'ledger delete call',
)
replace_in_class('_LedgerDeleteAction', '    required this.semanticLabel,\n    required this.compact,', '    required this.semanticLabel,', 'delete constructor')
replace_in_class('_LedgerDeleteAction', '  final String semanticLabel;\n  final bool compact;', '  final String semanticLabel;', 'delete fields')
replace_in_class('_LedgerDeleteAction', '    final double size = compact ? 40 : 44;', '    const double size = UIConstants.minTapTarget;', 'delete tap target')
for cls, label in (
    ('_LedgerDateCell', 'date cell hierarchy'),
    ('_LedgerAmountCell', 'amount cell hierarchy'),
    ('_LedgerBadgeCell', 'badge hierarchy'),
    ('_LedgerDetailCell', 'detail hierarchy'),
):
    start, end = class_region(cls)
    region = code[start:end]
    count = region.count('FontWeight.w900')
    if count:
        region = region.replace('FontWeight.w900', 'FontWeight.w700')
        code = code[:start] + region + code[end:]
        print(f'{label}: {count}')

# -----------------------------------------------------------------------------
# Milk table parity with the compact ledger table.
# -----------------------------------------------------------------------------
replace_in_class('_MilkRecordsTable', '        borderRadius: BorderRadius.circular(25),', '        borderRadius: BorderRadius.circular(UIConstants.cardRadius),', 'milk table radius')
replace_in_class('_MilkRecordsTable', '                height: 58,', '                height: 48,', 'milk table header')
replace_in_class('_MilkTableHeader', '            fontWeight: FontWeight.w900,', '            fontWeight: FontWeight.w700,', 'milk header hierarchy')
replace_in_class('_MilkTableRow', '      constraints: const BoxConstraints(minHeight: 88),', '      constraints: const BoxConstraints(minHeight: 72),', 'milk row height')
replace_in_class('_MilkTableRow', '                  width: compact ? 40 : 44,\n                  height: compact ? 40 : 44,', '                  width: 48,\n                  height: 48,', 'milk delete target')
replace_in_class('_MilkValueCell', '              fontWeight: strong ? FontWeight.w900 : FontWeight.w800,', '              fontWeight: FontWeight.w700,', 'milk value hierarchy')

# Dashboard metrics: amount wins, label recedes.
replace_in_class('_MetricCard', '                fontWeight: FontWeight.w900,', '                fontWeight: FontWeight.w600,', 'metric label hierarchy', expected=1)
replace_in_class('_MetricCard', '                  fontWeight: FontWeight.w900,', '                  fontWeight: FontWeight.w700,', 'metric amount hierarchy', expected=1)

# -----------------------------------------------------------------------------
# Normalize common raw spacers and scrolling-body padding without adding a
# redundant 100+px tail: AppShell Scaffold already lays body above bottom nav.
# -----------------------------------------------------------------------------
for old, new, label in (
    ('const SizedBox(height: 13)', 'const SizedBox(height: 12)', '13→12 spacing'),
    ('const SizedBox(height: 18)', 'const SizedBox(height: 16)', '18→16 spacing'),
    ('const SizedBox(height: 22)', 'const SizedBox(height: 24)', '22→24 spacing'),
    ('const SizedBox(height: 23)', 'const SizedBox(height: 24)', '23→24 spacing'),
):
    replace_present(old, new, label)

for old in (
    'const EdgeInsets.fromLTRB(20, 8, 20, 30)',
    'const EdgeInsets.fromLTRB(20, 9, 20, 30)',
    'const EdgeInsets.fromLTRB(20, 8, 20, 32)',
    'const EdgeInsets.fromLTRB(20, 8, 20, 28)',
    'const EdgeInsets.fromLTRB(20, 10, 20, 34)',
):
    replace_present(old, 'UIConstants.screenPadding', f'screen padding {old}')

if code == original:
    raise SystemExit('SAFETY STOP: migration produced no changes')

TARGET.write_text(code, encoding='utf-8')
print('Applied guarded UI geometry and hierarchy upgrade.')
