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


def replace_method_in_class(
    class_name: str,
    start_marker: str,
    end_marker: str,
    new_method: str,
    label: str,
) -> None:
    global code
    start, end = class_region(class_name)
    region = code[start:end]
    method_start = region.find(start_marker)
    if method_start < 0:
        raise SystemExit(f'SAFETY STOP: {label} start marker not found')
    method_end = region.find(end_marker, method_start)
    if method_end < 0:
        raise SystemExit(f'SAFETY STOP: {label} end marker not found')
    region = region[:method_start] + new_method.rstrip() + '\n\n' + region[method_end:]
    code = code[:start] + region + code[end:]


# -----------------------------------------------------------------------------
# 1) SALARY NEW EMPLOYEE: direct Receives / Pays, no dropdown, no extra save.
# -----------------------------------------------------------------------------
salary_add_person = r'''  Future<void> _addPerson() async {
    final TextEditingController name = TextEditingController();
    final TextEditingController company = TextEditingController();
    final String? type = await _openSheet<String>(
      context,
      Builder(
        builder: (BuildContext sheetContext) => _SheetFrame(
          title: 'New Employee',
          children: <Widget>[
            TextField(
              controller: name,
              autofocus: true,
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(
                labelText: 'Employee Name',
                prefixIcon: Icon(Icons.person_rounded),
              ),
            ),
            const SizedBox(height: 13),
            TextField(
              controller: company,
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(
                labelText: 'Company / Details',
                prefixIcon: Icon(Icons.business_rounded),
              ),
            ),
            const SizedBox(height: 22),
            Row(
              children: <Widget>[
                Expanded(
                  child: _MilkCustomerRoleButton(
                    label: 'Receives',
                    icon: Icons.add_rounded,
                    color: salaryGreen,
                    semanticLabel: 'Create employee who receives salary',
                    onTap: () {
                      HapticFeedback.mediumImpact();
                      Navigator.pop(sheetContext, 'lene_wala');
                    },
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _MilkCustomerRoleButton(
                    label: 'Pays',
                    icon: Icons.remove_rounded,
                    color: appleRed,
                    semanticLabel: 'Create employee whose salary I pay',
                    onTap: () {
                      HapticFeedback.mediumImpact();
                      Navigator.pop(sheetContext, 'dene_wala');
                    },
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
    if (type == null || !mounted) {
      name.dispose();
      company.dispose();
      return;
    }
    final String personName = _cleanKey(name.text);
    final String companyName =
        company.text.trim().isEmpty ? '—' : company.text.trim();
    name.dispose();
    company.dispose();
    if (personName.isEmpty) {
      _toast(context, 'Enter a name.', error: true);
      return;
    }
    final Map<String, dynamic> database = _map(widget.sync.state['salaryDB']);
    if (database.keys
        .any((String key) => key.toLowerCase() == personName.toLowerCase())) {
      _toast(context, 'Person already exists.', error: true);
      return;
    }
    await _runMutation(
      context,
      () => widget.sync.write(
        'salaryDB/$personName',
        <String, dynamic>{
          'company': companyName,
          'type': type,
          'records': <dynamic>[],
        },
        reason: 'salary-profile-create',
      ),
      type == 'lene_wala'
          ? 'Receiving salary profile added!'
          : 'Paying salary profile added!',
    );
  }'''
replace_method_in_class(
    '_SalaryScreenState',
    '  Future<void> _addPerson() async {',
    '  @override\n  Widget build',
    salary_add_person,
    'Salary new employee flow',
)

# -----------------------------------------------------------------------------
# 2) SHARED TABLE SYSTEM: one canonical no-stick ledger presentation.
# -----------------------------------------------------------------------------
insert_anchor = '\nclass _RecordsCard extends StatelessWidget {'
if code.count(insert_anchor) != 1:
    raise SystemExit(
        f'SAFETY STOP: shared table insertion anchor expected once, found {code.count(insert_anchor)}'
    )

shared_table_widgets = r'''

class _LedgerTableRowData {
  const _LedgerTableRowData({
    required this.cells,
    required this.onDelete,
    required this.semanticLabel,
  });

  final List<Widget> cells;
  final VoidCallback onDelete;
  final String semanticLabel;
}

class _LedgerTableCard extends StatelessWidget {
  const _LedgerTableCard({
    required this.headers,
    required this.flexes,
    required this.rows,
  });

  final List<String> headers;
  final List<int> flexes;
  final List<_LedgerTableRowData> rows;

  @override
  Widget build(BuildContext context) {
    assert(headers.length == flexes.length);
    final bool dark = Theme.of(context).brightness == Brightness.dark;
    final Color divider = dark
        ? Colors.white.withAlpha(15)
        : const Color(0xFF183960).withAlpha(15);
    return Container(
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        color: dark ? const Color(0xFF12161D) : Colors.white,
        borderRadius: BorderRadius.circular(25),
        border: Border.all(
          color: dark ? Colors.white.withAlpha(18) : appleBlue.withAlpha(16),
        ),
        boxShadow: dark
            ? const <BoxShadow>[]
            : <BoxShadow>[
                BoxShadow(
                  color: const Color(0xFF183960).withAlpha(16),
                  blurRadius: 30,
                  offset: const Offset(0, 13),
                ),
              ],
      ),
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final bool compact = constraints.maxWidth < 350;
          return Column(
            children: <Widget>[
              Container(
                constraints: const BoxConstraints(minHeight: 58),
                padding: EdgeInsets.symmetric(horizontal: compact ? 10 : 14),
                color: dark
                    ? Colors.white.withAlpha(7)
                    : const Color(0xFFF9FBFE),
                child: Row(
                  children: <Widget>[
                    for (int i = 0; i < headers.length; i++)
                      Expanded(
                        flex: flexes[i],
                        child: Align(
                          alignment: Alignment.centerLeft,
                          child: Text(
                            headers[i],
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              color: appleBlue,
                              fontSize: compact ? 9.6 : 10.7,
                              height: 1,
                              fontWeight: FontWeight.w900,
                              letterSpacing: compact ? .15 : .55,
                            ),
                          ),
                        ),
                      ),
                    SizedBox(width: compact ? 46 : 52),
                  ],
                ),
              ),
              for (int rowIndex = 0; rowIndex < rows.length; rowIndex++)
                Container(
                  constraints: BoxConstraints(minHeight: compact ? 78 : 84),
                  padding: EdgeInsets.symmetric(
                    horizontal: compact ? 10 : 14,
                    vertical: 10,
                  ),
                  decoration: BoxDecoration(
                    border: rowIndex == rows.length - 1
                        ? null
                        : Border(bottom: BorderSide(color: divider)),
                  ),
                  child: Row(
                    children: <Widget>[
                      for (int i = 0; i < headers.length; i++)
                        Expanded(
                          flex: flexes[i],
                          child: rows[rowIndex].cells[i],
                        ),
                      SizedBox(
                        width: compact ? 46 : 52,
                        child: Align(
                          alignment: Alignment.centerRight,
                          child: _LedgerDeleteAction(
                            onTap: rows[rowIndex].onDelete,
                            semanticLabel: rows[rowIndex].semanticLabel,
                            compact: compact,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}

class _LedgerDeleteAction extends StatelessWidget {
  const _LedgerDeleteAction({
    required this.onTap,
    required this.semanticLabel,
    required this.compact,
  });

  final VoidCallback onTap;
  final String semanticLabel;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final bool dark = Theme.of(context).brightness == Brightness.dark;
    final double size = compact ? 40 : 44;
    return _Pressable(
      onTap: onTap,
      semanticLabel: semanticLabel,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: <Color>[
              dark ? appleRed.withAlpha(29) : Colors.white,
              appleRed.withAlpha(dark ? 23 : 20),
            ],
          ),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: appleRed.withAlpha(42)),
          boxShadow: dark
              ? const <BoxShadow>[]
              : <BoxShadow>[
                  BoxShadow(
                    color: appleRed.withAlpha(22),
                    blurRadius: 16,
                    offset: const Offset(0, 7),
                  ),
                ],
        ),
        child: const Icon(
          Icons.delete_rounded,
          color: appleRed,
          size: 17,
        ),
      ),
    );
  }
}

class _LedgerDateCell extends StatelessWidget {
  const _LedgerDateCell({
    required this.date,
    required this.color,
    this.stacked = false,
  });

  final dynamic date;
  final Color color;
  final bool stacked;

  @override
  Widget build(BuildContext context) {
    final DateTime? parsed = LedgerMath.strictDate('$date');
    if (parsed == null) {
      return Align(
        alignment: Alignment.centerLeft,
        child: Text(
          _displayDate(date),
          maxLines: stacked ? 2 : 1,
          overflow: TextOverflow.ellipsis,
          style: TextStyle(
            color: color,
            fontSize: 14,
            fontWeight: FontWeight.w900,
          ),
        ),
      );
    }
    if (stacked) {
      return Align(
        alignment: Alignment.centerLeft,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              DateFormat('dd').format(parsed),
              style: TextStyle(
                color: color,
                fontSize: 15,
                height: 1,
                fontWeight: FontWeight.w900,
              ),
            ),
            const SizedBox(height: 5),
            Text(
              DateFormat('MMM').format(parsed),
              style: TextStyle(
                color: color,
                fontSize: 12.5,
                height: 1,
                fontWeight: FontWeight.w900,
              ),
            ),
          ],
        ),
      );
    }
    return Align(
      alignment: Alignment.centerLeft,
      child: FittedBox(
        fit: BoxFit.scaleDown,
        alignment: Alignment.centerLeft,
        child: Text(
          DateFormat('dd MMM').format(parsed),
          maxLines: 1,
          style: TextStyle(
            color: color,
            fontSize: 14.5,
            fontWeight: FontWeight.w900,
            letterSpacing: -.15,
          ),
        ),
      ),
    );
  }
}

class _LedgerAmountCell extends StatelessWidget {
  const _LedgerAmountCell({
    required this.value,
    required this.color,
  });

  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) => Align(
        alignment: Alignment.centerLeft,
        child: FittedBox(
          fit: BoxFit.scaleDown,
          alignment: Alignment.centerLeft,
          child: Text(
            value,
            maxLines: 1,
            style: TextStyle(
              color: color,
              fontSize: 15.5,
              fontWeight: FontWeight.w900,
              letterSpacing: -.25,
            ),
          ),
        ),
      );
}

class _LedgerBadgeCell extends StatelessWidget {
  const _LedgerBadgeCell({
    required this.label,
    required this.color,
  });

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) => Align(
        alignment: Alignment.centerLeft,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
          decoration: BoxDecoration(
            color: color.withAlpha(15),
            borderRadius: BorderRadius.circular(9),
            border: Border.all(color: color.withAlpha(52)),
          ),
          child: Text(
            label,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              color: color,
              fontSize: 9.8,
              height: 1,
              fontWeight: FontWeight.w900,
              letterSpacing: .2,
            ),
          ),
        ),
      );
}

class _LedgerDetailCell extends StatelessWidget {
  const _LedgerDetailCell({
    required this.title,
    required this.badge,
    required this.color,
  });

  final String title;
  final String badge;
  final Color color;

  @override
  Widget build(BuildContext context) => Align(
        alignment: Alignment.centerLeft,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              title,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                color: color,
                fontSize: 13.5,
                fontWeight: FontWeight.w900,
              ),
            ),
            const SizedBox(height: 5),
            _LedgerBadgeCell(label: badge, color: color),
          ],
        ),
      );
}
'''
code = code.replace(insert_anchor, shared_table_widgets + insert_anchor, 1)

# -----------------------------------------------------------------------------
# 3) SALARY DETAIL: DATE / AMOUNT table, no left bars.
# -----------------------------------------------------------------------------
salary_records_old = """                      if (records.isEmpty)
                        const _EmptyState(Icons.currency_rupee_rounded,
                            'No salary entries for this month')
                      else
                        _RecordsCard(
                          children: records
                              .map(
                                (Map<String, dynamic> row) => _RecordTile(
                                  title: _displayDate(row['date']),
                                  subtitle:
                                      profile['company']?.toString() ?? '—',
                                  amount: _signedMoney(
                                    (profile['type'] == 'lene_wala' ? 1 : -1) *
                                        LedgerMath.number(row['amount']),
                                  ),
                                  color: color,
                                  onDelete: () =>
                                      unawaited(_deleteEntry('${row['id']}')),
                                ),
                              )
                              .toList(),
                        ),"""
salary_records_new = """                      if (records.isEmpty)
                        const _EmptyState(Icons.currency_rupee_rounded,
                            'No salary entries for this month')
                      else
                        _LedgerTableCard(
                          headers: const <String>['DATE', 'AMOUNT'],
                          flexes: const <int>[42, 42],
                          rows: records.map((Map<String, dynamic> row) {
                            final double rowSigned =
                                (profile['type'] == 'lene_wala' ? 1 : -1) *
                                    LedgerMath.number(row['amount']);
                            final Color rowColor = _tone(rowSigned);
                            return _LedgerTableRowData(
                              cells: <Widget>[
                                _LedgerDateCell(
                                  date: row['date'],
                                  color: rowColor,
                                ),
                                _LedgerAmountCell(
                                  value: _signedMoney(rowSigned),
                                  color: rowColor,
                                ),
                              ],
                              onDelete: () =>
                                  unawaited(_deleteEntry('${row['id']}')),
                              semanticLabel:
                                  'Delete ${_displayDate(row['date'])} salary entry',
                            );
                          }).toList(),
                        ),"""
replace_in_class(
    '_SalaryDetailScreenState',
    salary_records_old,
    salary_records_new,
    'Salary no-stick table',
)

# -----------------------------------------------------------------------------
# 4) CREDIT DETAIL: DATE / DETAIL / AMOUNT table, no left bars.
# -----------------------------------------------------------------------------
credit_records_old = """                      if (records.isEmpty)
                        const _EmptyState(Icons.account_balance_wallet_outlined,
                            'No entries found')
                      else
                        _RecordsCard(
                          children: records.map((Map<String, dynamic> row) {
                            final double signed = LedgerMath.creditSigned(row);
                            return _RecordTile(
                              title: _displayDate(row['date']),
                              subtitle: signed >= 0 ? 'Given' : 'Taken',
                              amount: _signedMoney(signed),
                              color: _tone(signed),
                              onDelete: () => unawaited(
                                  _deleteEntry(context, '${row['id']}')),
                            );
                          }).toList(),
                        ),"""
credit_records_new = """                      if (records.isEmpty)
                        const _EmptyState(Icons.account_balance_wallet_outlined,
                            'No entries found')
                      else
                        _LedgerTableCard(
                          headers: const <String>['DATE', 'DETAIL', 'AMOUNT'],
                          flexes: const <int>[29, 28, 31],
                          rows: records.map((Map<String, dynamic> row) {
                            final double signed = LedgerMath.creditSigned(row);
                            final Color rowColor = _tone(signed);
                            return _LedgerTableRowData(
                              cells: <Widget>[
                                _LedgerDateCell(
                                  date: row['date'],
                                  color: rowColor,
                                ),
                                _LedgerBadgeCell(
                                  label: signed >= 0 ? 'GIVEN' : 'TAKEN',
                                  color: rowColor,
                                ),
                                _LedgerAmountCell(
                                  value: _signedMoney(signed),
                                  color: rowColor,
                                ),
                              ],
                              onDelete: () => unawaited(
                                  _deleteEntry(context, '${row['id']}')),
                              semanticLabel:
                                  'Delete ${_displayDate(row['date'])} credit entry',
                            );
                          }).toList(),
                        ),"""
replace_in_class(
    'CreditDetailScreen',
    credit_records_old,
    credit_records_new,
    'Credit no-stick table',
)

# -----------------------------------------------------------------------------
# 5) EXPENSE DETAIL: DATE / AMOUNT table, no left bars.
# -----------------------------------------------------------------------------
expense_records_old = """                      if (records.isEmpty)
                        const _EmptyState(Icons.receipt_long_rounded,
                            'No expenses for this month')
                      else
                        _RecordsCard(
                          children: records
                              .map(
                                (Map<String, dynamic> row) => _RecordTile(
                                  title: _displayDate(row['date']),
                                  subtitle: widget.category,
                                  amount: '-${_money(row['amount'])}',
                                  color: semanticRed,
                                  onDelete: () =>
                                      unawaited(_deleteEntry('${row['id']}')),
                                ),
                              )
                              .toList(),
                        ),"""
expense_records_new = """                      if (records.isEmpty)
                        const _EmptyState(Icons.receipt_long_rounded,
                            'No expenses for this month')
                      else
                        _LedgerTableCard(
                          headers: const <String>['DATE', 'AMOUNT'],
                          flexes: const <int>[42, 42],
                          rows: records
                              .map(
                                (Map<String, dynamic> row) =>
                                    _LedgerTableRowData(
                                  cells: <Widget>[
                                    _LedgerDateCell(
                                      date: row['date'],
                                      color: semanticRed,
                                    ),
                                    _LedgerAmountCell(
                                      value: '-${_money(row['amount'])}',
                                      color: semanticRed,
                                    ),
                                  ],
                                  onDelete: () =>
                                      unawaited(_deleteEntry('${row['id']}')),
                                  semanticLabel:
                                      'Delete ${_displayDate(row['date'])} expense entry',
                                ),
                              )
                              .toList(),
                        ),"""
replace_in_class(
    '_ExpenseDetailScreenState',
    expense_records_old,
    expense_records_new,
    'Expense no-stick table',
)

# -----------------------------------------------------------------------------
# 6) BUSINESS DETAIL: DATE / DETAIL / AMOUNT table, no left bars.
# -----------------------------------------------------------------------------
business_records_old = """                      if (records.isEmpty)
                        const _EmptyState(Icons.business_center_outlined,
                            'No records logged yet')
                      else
                        _RecordsCard(
                          children: records.map((Map<String, dynamic> row) {
                            final String key =
                                _businessTones.containsKey('${row['color']}')
                                    ? '${row['color']}'
                                    : 'blue';
                            final _BusinessTone tone = _businessTones[key]!;
                            return _RecordTile(
                              title: '${row['title'] ?? 'Record'}',
                              subtitle:
                                  '${_displayDate(row['date'])} • ${tone.badge}',
                              amount: _money(row['amount']),
                              color: tone.color,
                              onDelete: () => unawaited(
                                  _deleteEntry(context, '${row['id']}')),
                            );
                          }).toList(),
                        ),"""
business_records_new = """                      if (records.isEmpty)
                        const _EmptyState(Icons.business_center_outlined,
                            'No records logged yet')
                      else
                        _LedgerTableCard(
                          headers: const <String>['DATE', 'DETAIL', 'AMOUNT'],
                          flexes: const <int>[24, 36, 28],
                          rows: records.map((Map<String, dynamic> row) {
                            final String key =
                                _businessTones.containsKey('${row['color']}')
                                    ? '${row['color']}'
                                    : 'blue';
                            final _BusinessTone tone = _businessTones[key]!;
                            return _LedgerTableRowData(
                              cells: <Widget>[
                                _LedgerDateCell(
                                  date: row['date'],
                                  color: tone.color,
                                  stacked: true,
                                ),
                                _LedgerDetailCell(
                                  title: '${row['title'] ?? 'Record'}',
                                  badge: tone.badge,
                                  color: tone.color,
                                ),
                                _LedgerAmountCell(
                                  value: _money(row['amount']),
                                  color: tone.color,
                                ),
                              ],
                              onDelete: () => unawaited(
                                  _deleteEntry(context, '${row['id']}')),
                              semanticLabel:
                                  'Delete ${row['title'] ?? 'Record'} business entry',
                            );
                          }).toList(),
                        ),"""
replace_in_class(
    'BusinessDetailScreen',
    business_records_old,
    business_records_new,
    'Business no-stick table',
)

# -----------------------------------------------------------------------------
# Guardrails: locked flows already implemented must remain intact.
# -----------------------------------------------------------------------------
required_locked_markers = <str>[
    "label: 'Seller'",
    "label: 'Buyer'",
    "label: 'Given'",
    "label: 'Taken'",
    'class _MilkRecordsTable extends StatelessWidget',
    'class _MilkShareAction extends StatelessWidget',
    'class _LedgerTableCard extends StatelessWidget',
    "label: 'Receives'",
    "label: 'Pays'",
]
for marker in required_locked_markers:
    if marker not in code:
        raise SystemExit(f'SAFETY STOP: locked marker missing after migration: {marker}')

# No old stick-card list should remain in these four locked detail screens.
for class_name in (
    '_SalaryDetailScreenState',
    'CreditDetailScreen',
    '_ExpenseDetailScreenState',
    'BusinessDetailScreen',
):
    start, end = class_region(class_name)
    region = code[start:end]
    if '_RecordsCard(' in region or '_RecordTile(' in region:
        raise SystemExit(f'SAFETY STOP: old stick list still present in {class_name}')

# Salary profile must not keep the old dropdown/create-button flow.
start, end = class_region('_SalaryScreenState')
salary_region = code[start:end]
for old_marker in ('Salary direction', "label: 'Create Profile'"):
    if old_marker in salary_region:
        raise SystemExit(f'SAFETY STOP: old salary profile UI still present: {old_marker}')

if code == original:
    raise SystemExit('SAFETY STOP: migration produced no changes')

TARGET.write_text(code, encoding='utf-8')
print('Locked UI batch migration applied successfully.')
