#!/usr/bin/env python3
from pathlib import Path

TARGET = Path('lib/main.dart')
code = TARGET.read_text(encoding='utf-8')
original = code


def replace_once(old: str, new: str, label: str) -> None:
    global code
    count = code.count(old)
    if count != 1:
        raise SystemExit(
            f'SAFETY STOP: {label} expected exactly once, found {count}'
        )
    code = code.replace(old, new, 1)


def class_region(class_name: str):
    marker = f'class {class_name}'
    start = code.find(marker)
    if start < 0:
        raise SystemExit(f'SAFETY STOP: class not found: {class_name}')
    next_start = code.find('\nclass ', start + len(marker))
    end = len(code) if next_start < 0 else next_start
    return start, end


def replace_in_class(class_name: str, old: str, new: str, label: str) -> None:
    global code
    start, end = class_region(class_name)
    region = code[start:end]
    count = region.count(old)
    if count != 1:
        raise SystemExit(
            f'SAFETY STOP: {label} in {class_name} expected exactly once, found {count}'
        )
    region = region.replace(old, new, 1)
    code = code[:start] + region + code[end:]


# -----------------------------------------------------------------------------
# 1) GLOBAL MODULE CHROME PARITY
# HTML reference contract:
# positive = green, negative = red, zero = blue.
# Milk/Credit/Salary bottom tabs follow their calculated global net.
# Expenses are red when the current month has expense, blue when zero.
# Diary stays orange; Business stays blue.
# -----------------------------------------------------------------------------
replace_once(
    """List<Color> _moduleTabColors(Map<String, dynamic> state) => const <Color>[\n      appleBlue,\n      appleGreen,\n      appleGreen,\n      appleBlue,\n      salaryGreen,\n      diaryOrange,\n      appleBlue,\n    ];""",
    """double _expenseCurrentMonthTotal(Map<String, dynamic> state) {\n  final DateTime now = DateTime.now();\n  return _rows(state['expenseDB'])\n      .where(\n        (Map<String, dynamic> row) =>\n            LedgerMath.inMonth(row, now.month, now.year),\n      )\n      .fold<double>(\n        0,\n        (double sum, Map<String, dynamic> row) =>\n            sum + LedgerMath.number(row['amount']).abs(),\n      );\n}\n\nColor _expenseToneForTotal(double total) =>\n    total > .000001 ? semanticRed : appleBlue;\n\nList<Color> _moduleTabColors(Map<String, dynamic> state) => <Color>[\n      appleBlue,\n      _tone(_milkGlobalNet(state)),\n      _tone(_creditGlobalNet(state)),\n      _expenseToneForTotal(_expenseCurrentMonthTotal(state)),\n      _tone(_salaryGlobalNet(state)),\n      diaryOrange,\n      appleBlue,\n    ];""",
    'dynamic module tab tone map',
)


# -----------------------------------------------------------------------------
# 2) CREDIT MAIN SCREEN
# Global credit net owns title + Entry button + hero + bottom tab.
# Person cards/detail/rows already use their own signed net and stay untouched.
# Static search/share/table UI stays blue; detail Add stays green; delete stays red.
# -----------------------------------------------------------------------------
replace_in_class(
    '_CreditScreenState',
    """    final double net = _creditGlobalNet(widget.sync.state);\n    final Color moduleColor = appleGreen;\n    final Color balanceColor = _tone(net, neutral: appleGreen);""",
    """    final double net = _creditGlobalNet(widget.sync.state);\n    final Color moduleColor = _tone(net);\n    final Color balanceColor = moduleColor;""",
    'credit global tone source',
)


# -----------------------------------------------------------------------------
# 3) EXPENSE MAIN SCREEN
# Expense amount is stored positive, but its financial meaning is outflow.
# Any non-zero current-month total therefore paints the module red; zero is blue.
# Share/static labels remain blue and Add/Delete remain red.
# -----------------------------------------------------------------------------
replace_in_class(
    '_ExpenseScreenState',
    """    final double total = groups.fold<double>(\n      0,\n      (double sum, _ExpenseGroup group) => sum + group.total,\n    );\n    return Column(""",
    """    final double total = groups.fold<double>(\n      0,\n      (double sum, _ExpenseGroup group) => sum + group.total,\n    );\n    final Color moduleColor = _expenseToneForTotal(total);\n    return Column(""",
    'expense module tone calculation',
)
replace_in_class(
    '_ExpenseScreenState',
    """        _ScreenHeader(\n          title: 'Expenses',\n          color: appleBlue,""",
    """        _ScreenHeader(\n          title: 'Expenses',\n          color: moduleColor,""",
    'expense title follows module tone',
)
replace_in_class(
    '_ExpenseScreenState',
    """              _AmountHero(\n                label: 'Month Expense',\n                value: _money(total),\n                color: appleBlue,""",
    """              _AmountHero(\n                label: 'Month Expense',\n                value: _money(total),\n                color: moduleColor,""",
    'expense hero follows module tone',
)


# -----------------------------------------------------------------------------
# 4) EXPENSE DETAIL SCREEN
# Selected month/category total owns only semantic chrome (title + hero).
# Entry rows remain red outflows; Share/table headings stay blue; Add/Delete red.
# -----------------------------------------------------------------------------
replace_in_class(
    '_ExpenseDetailScreenState',
    """          final double total = records.fold<double>(\n            0,\n            (double sum, Map<String, dynamic> row) =>\n                sum + LedgerMath.number(row['amount']).abs(),\n          );\n          return Scaffold(""",
    """          final double total = records.fold<double>(\n            0,\n            (double sum, Map<String, dynamic> row) =>\n                sum + LedgerMath.number(row['amount']).abs(),\n          );\n          final Color detailColor = _expenseToneForTotal(total);\n          return Scaffold(""",
    'expense detail tone calculation',
)
replace_in_class(
    '_ExpenseDetailScreenState',
    """                _ScreenHeader(\n                  leading: const _BackCircle(),\n                  title: widget.category,\n                  color: semanticRed,""",
    """                _ScreenHeader(\n                  leading: const _BackCircle(),\n                  title: widget.category,\n                  color: detailColor,""",
    'expense detail title follows total',
)
replace_in_class(
    '_ExpenseDetailScreenState',
    """                      _AmountHero(\n                        label: 'Category Total',\n                        value: '-${_money(total)}',\n                        color: semanticRed,""",
    """                      _AmountHero(\n                        label: 'Category Total',\n                        value: '-${_money(total)}',\n                        color: detailColor,""",
    'expense detail hero follows total',
)


# -----------------------------------------------------------------------------
# 5) CONTRACT ASSERTIONS
# Milk + Salary are already wired correctly in the Flutter source. Verify those
# anchors so this migration cannot silently land against an incompatible tree.
# Business and Diary are intentionally fixed semantic modules.
# -----------------------------------------------------------------------------
required_markers = [
    "final Color moduleColor = _tone(_milkGlobalNet(widget.sync.state));",
    "final Color color = _tone(totals.netAmount);",
    "final Color moduleColor = _tone(_salaryGlobalNet(widget.sync.state));",
    "final Color color = _tone(net);",
    "'green': _BusinessTone(",
    "'red': _BusinessTone(",
    "'blue': _BusinessTone(",
    "'orange': _BusinessTone(",
    "title: 'Personal Diary',\n          color: diaryOrange,",
]
for marker in required_markers:
    if marker not in code:
        raise SystemExit(f'SAFETY STOP: required semantic marker missing: {marker}')

if "final Color moduleColor = appleGreen;" in code:
    raise SystemExit('SAFETY STOP: static Credit module color is still present')

if code == original:
    raise SystemExit('SAFETY STOP: migration produced no changes')

TARGET.write_text(code, encoding='utf-8')
print('Applied calculation-linked semantic color parity to Flutter UI.')
