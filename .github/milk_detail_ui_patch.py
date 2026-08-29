#!/usr/bin/env python3
from pathlib import Path

TARGET = Path('lib/main.dart')
code = TARGET.read_text(encoding='utf-8')
original = code


def replace_once(old: str, new: str, label: str) -> None:
    global code
    count = code.count(old)
    if count != 1:
        raise SystemExit(f'SAFETY STOP: {label} expected exactly once, found {count}')
    code = code.replace(old, new, 1)


hero_old = """                      _AmountHero(
                        label: 'Month Bill',
                        value: _signedMoney(totals.netAmount),
                        color: color,
                        trailingLabel: 'Total Milk',
                        trailingValue:
                            '${totals.netKg.abs().toStringAsFixed(2)} KG',
                      ),"""
hero_new = """                      _MilkDetailHero(
                        amount: _signedMoney(totals.netAmount),
                        totalKg: '${totals.netKg.abs().toStringAsFixed(2)} KG',
                        color: color,
                      ),"""
replace_once(hero_old, hero_new, 'Milk month hero')

share_old = """                          _MiniAction(
                            label: 'Share',
                            icon: Icons.ios_share_rounded,
                            color: appleBlue,
                            onTap: () => unawaited(
                              _ExportService.sharePdf(
                                '${widget.customerName} Milk Bill',"""
share_new = """                          _MilkShareAction(
                            label: 'Share',
                            icon: Icons.ios_share_rounded,
                            color: appleBlue,
                            onTap: () => unawaited(
                              _ExportService.sharePdf(
                                '${widget.customerName} Milk Bill',"""
replace_once(share_old, share_new, 'Milk Share action')

records_old = """                      if (records.isEmpty)
                        const _EmptyState(Icons.water_drop_outlined,
                            'No entries for this month')
                      else
                        _RecordsCard(
                          children: records.map((Map<String, dynamic> row) {
                            final String flow =
                                LedgerMath.milkFlow(row, profile);
                            final double quantity =
                                LedgerMath.milkQuantity(row);
                            final Color rowColor =
                                flow == 'taken' ? semanticRed : appleGreen;
                            return _RecordTile(
                              title: _displayDate(row['date']),
                              subtitle:
                                  'Morning ${LedgerMath.number(row['morning']).toStringAsFixed(2)} • Evening ${LedgerMath.number(row['evening']).toStringAsFixed(2)}',
                              amount:
                                  '${flow == 'taken' ? '-' : '+'}${quantity.toStringAsFixed(2)} KG',
                              color: rowColor,
                              onDelete: () =>
                                  unawaited(_deleteEntry('${row['id']}')),
                            );
                          }).toList(),
                        ),"""
records_new = """                      if (records.isEmpty)
                        const _EmptyState(Icons.water_drop_outlined,
                            'No entries for this month')
                      else
                        _MilkRecordsTable(
                          records: records,
                          profile: profile,
                          onDelete: (String id) =>
                              unawaited(_deleteEntry(id)),
                        ),"""
replace_once(records_old, records_new, 'Milk records list')

insert_anchor = "\nclass _MiniAction extends StatelessWidget {"
if code.count(insert_anchor) != 1:
    raise SystemExit(
        f'SAFETY STOP: _MiniAction insertion anchor expected once, found {code.count(insert_anchor)}'
    )

new_widgets = r'''

class _MilkDetailHero extends StatelessWidget {
  const _MilkDetailHero({
    required this.amount,
    required this.totalKg,
    required this.color,
  });

  final String amount;
  final String totalKg;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final bool dark = Theme.of(context).brightness == Brightness.dark;
    final Color surface = dark ? const Color(0xFF121720) : Colors.white;
    return Container(
      constraints: const BoxConstraints(minHeight: 150),
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 23),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: <Color>[
            color.withAlpha(dark ? 34 : 19),
            surface,
            color.withAlpha(dark ? 19 : 10),
          ],
          stops: const <double>[0, .58, 1],
        ),
        borderRadius: BorderRadius.circular(28),
        border: Border.all(color: color.withAlpha(dark ? 72 : 54)),
        boxShadow: dark
            ? const <BoxShadow>[]
            : <BoxShadow>[
                BoxShadow(
                  color: color.withAlpha(34),
                  blurRadius: 34,
                  spreadRadius: 1,
                  offset: const Offset(0, 14),
                ),
              ],
      ),
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final bool compact = constraints.maxWidth < 330;
          return Row(
            children: <Widget>[
              if (!compact) ...<Widget>[
                _LedgerIcon(
                  icon: Icons.local_drink_rounded,
                  color: color,
                  size: 54,
                ),
                const SizedBox(width: 16),
              ],
              Expanded(
                flex: 6,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      'MONTH BILL',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: color,
                        fontSize: 11.5,
                        fontWeight: FontWeight.w900,
                        letterSpacing: .85,
                      ),
                    ),
                    const SizedBox(height: 8),
                    FittedBox(
                      fit: BoxFit.scaleDown,
                      alignment: Alignment.centerLeft,
                      child: Text(
                        amount,
                        style: TextStyle(
                          color: color,
                          fontSize: compact ? 34 : 39,
                          height: 1,
                          fontWeight: FontWeight.w900,
                          letterSpacing: -1.4,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                width: 1,
                height: 82,
                margin: const EdgeInsets.symmetric(horizontal: 14),
                color: color.withAlpha(dark ? 48 : 28),
              ),
              Expanded(
                flex: 4,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: <Widget>[
                    Text(
                      'TOTAL MILK',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      textAlign: TextAlign.right,
                      style: TextStyle(
                        color: color,
                        fontSize: 11.5,
                        fontWeight: FontWeight.w900,
                        letterSpacing: .75,
                      ),
                    ),
                    const SizedBox(height: 9),
                    FittedBox(
                      fit: BoxFit.scaleDown,
                      alignment: Alignment.centerRight,
                      child: Text(
                        totalKg,
                        style: TextStyle(
                          color: color,
                          fontSize: compact ? 20 : 23,
                          fontWeight: FontWeight.w900,
                          letterSpacing: -.45,
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

class _MilkShareAction extends StatelessWidget {
  const _MilkShareAction({
    required this.label,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  final String label;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final bool dark = Theme.of(context).brightness == Brightness.dark;
    return Transform.rotate(
      angle: -0.026,
      child: _Pressable(
        onTap: onTap,
        semanticLabel: label,
        borderRadius: BorderRadius.circular(19),
        child: Container(
          constraints: const BoxConstraints(minHeight: 50),
          padding: const EdgeInsets.fromLTRB(10, 9, 15, 9),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: <Color>[
                dark ? color.withAlpha(42) : Colors.white,
                color.withAlpha(dark ? 26 : 25),
              ],
            ),
            borderRadius: BorderRadius.circular(19),
            border: Border.all(color: color.withAlpha(dark ? 78 : 58)),
            boxShadow: dark
                ? const <BoxShadow>[]
                : <BoxShadow>[
                    BoxShadow(
                      color: color.withAlpha(31),
                      blurRadius: 22,
                      offset: const Offset(0, 9),
                    ),
                  ],
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              Transform.rotate(
                angle: -0.11,
                child: Container(
                  width: 30,
                  height: 30,
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: <Color>[Color(0xFF3AA4FF), Color(0xFF006FEA)],
                    ),
                    borderRadius: BorderRadius.circular(9),
                    boxShadow: dark
                        ? const <BoxShadow>[]
                        : <BoxShadow>[
                            BoxShadow(
                              color: appleBlue.withAlpha(48),
                              blurRadius: 13,
                              offset: const Offset(0, 6),
                            ),
                          ],
                  ),
                  child: Icon(icon, color: Colors.white, size: 17),
                ),
              ),
              const SizedBox(width: 8),
              Text(
                label,
                style: TextStyle(
                  color: color,
                  fontSize: 13,
                  fontWeight: FontWeight.w900,
                  letterSpacing: -.2,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _MilkRecordsTable extends StatelessWidget {
  const _MilkRecordsTable({
    required this.records,
    required this.profile,
    required this.onDelete,
  });

  final List<Map<String, dynamic>> records;
  final Map<String, dynamic> profile;
  final ValueChanged<String> onDelete;

  String _quantityCell(dynamic value) {
    final double number = LedgerMath.number(value);
    if (number == 0) return '-';
    return NumberFormat('0.##').format(number);
  }

  @override
  Widget build(BuildContext context) {
    final bool dark = Theme.of(context).brightness == Brightness.dark;
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
                height: 58,
                padding: EdgeInsets.symmetric(horizontal: compact ? 8 : 12),
                color: dark
                    ? Colors.white.withAlpha(7)
                    : const Color(0xFFF9FBFE),
                child: Row(
                  children: <Widget>[
                    Expanded(
                      flex: 22,
                      child: _MilkTableHeader(
                        'DATE',
                        alignment: Alignment.centerLeft,
                        compact: compact,
                      ),
                    ),
                    Expanded(
                      flex: 20,
                      child: _MilkTableHeader('MORNING', compact: compact),
                    ),
                    Expanded(
                      flex: 20,
                      child: _MilkTableHeader('EVENING', compact: compact),
                    ),
                    Expanded(
                      flex: 21,
                      child: _MilkTableHeader('TOTAL', compact: compact),
                    ),
                    SizedBox(width: compact ? 44 : 50),
                  ],
                ),
              ),
              for (int i = 0; i < records.length; i++)
                _MilkTableRow(
                  row: records[i],
                  profile: profile,
                  compact: compact,
                  showDivider: i != records.length - 1,
                  quantityCell: _quantityCell,
                  onDelete: onDelete,
                ),
            ],
          );
        },
      ),
    );
  }
}

class _MilkTableHeader extends StatelessWidget {
  const _MilkTableHeader(
    this.label, {
    required this.compact,
    this.alignment = Alignment.center,
  });

  final String label;
  final bool compact;
  final Alignment alignment;

  @override
  Widget build(BuildContext context) => Align(
        alignment: alignment,
        child: Text(
          label,
          maxLines: 1,
          style: TextStyle(
            color: appleBlue,
            fontSize: compact ? 9.2 : 10.5,
            height: 1,
            fontWeight: FontWeight.w900,
            letterSpacing: compact ? .15 : .45,
          ),
        ),
      );
}

class _MilkTableRow extends StatelessWidget {
  const _MilkTableRow({
    required this.row,
    required this.profile,
    required this.compact,
    required this.showDivider,
    required this.quantityCell,
    required this.onDelete,
  });

  final Map<String, dynamic> row;
  final Map<String, dynamic> profile;
  final bool compact;
  final bool showDivider;
  final String Function(dynamic value) quantityCell;
  final ValueChanged<String> onDelete;

  @override
  Widget build(BuildContext context) {
    final bool dark = Theme.of(context).brightness == Brightness.dark;
    final String flow = LedgerMath.milkFlow(row, profile);
    final double quantity = LedgerMath.milkQuantity(row);
    final Color rowColor = flow == 'taken' ? semanticRed : appleGreen;
    final DateTime? parsed = LedgerMath.strictDate('${row['date']}');
    final String day = parsed == null
        ? _displayDate(row['date'])
        : DateFormat('dd').format(parsed);
    final String month = parsed == null ? '' : DateFormat('MMM').format(parsed);
    final String total =
        '${flow == 'taken' ? '-' : '+'}${quantity.toStringAsFixed(2)}';

    return Container(
      constraints: const BoxConstraints(minHeight: 88),
      padding: EdgeInsets.symmetric(horizontal: compact ? 8 : 12, vertical: 10),
      decoration: BoxDecoration(
        border: showDivider
            ? Border(
                bottom: BorderSide(
                  color: dark
                      ? Colors.white.withAlpha(15)
                      : const Color(0xFF183960).withAlpha(15),
                ),
              )
            : null,
      ),
      child: Row(
        children: <Widget>[
          Expanded(
            flex: 22,
            child: Align(
              alignment: Alignment.centerLeft,
              child: Container(
                constraints: BoxConstraints(minWidth: compact ? 48 : 54),
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 7),
                decoration: BoxDecoration(
                  color: rowColor.withAlpha(dark ? 29 : 18),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    Text(
                      day,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: rowColor,
                        fontSize: compact ? 15 : 17,
                        height: 1,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    if (month.isNotEmpty) ...<Widget>[
                      const SizedBox(height: 4),
                      Text(
                        month,
                        style: TextStyle(
                          color: rowColor,
                          fontSize: compact ? 10.5 : 11.5,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),
          Expanded(
            flex: 20,
            child: _MilkValueCell(
              quantityCell(row['morning']),
              color: rowColor,
              compact: compact,
            ),
          ),
          Expanded(
            flex: 20,
            child: _MilkValueCell(
              quantityCell(row['evening']),
              color: rowColor,
              compact: compact,
            ),
          ),
          Expanded(
            flex: 21,
            child: _MilkValueCell(
              total,
              color: rowColor,
              compact: compact,
              strong: true,
            ),
          ),
          SizedBox(
            width: compact ? 44 : 50,
            child: Align(
              alignment: Alignment.centerRight,
              child: _Pressable(
                onTap: () => onDelete('${row['id']}'),
                semanticLabel: 'Delete ${_displayDate(row['date'])} milk entry',
                borderRadius: BorderRadius.circular(14),
                child: Container(
                  width: compact ? 40 : 44,
                  height: compact ? 40 : 44,
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
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _MilkValueCell extends StatelessWidget {
  const _MilkValueCell(
    this.value, {
    required this.color,
    required this.compact,
    this.strong = false,
  });

  final String value;
  final Color color;
  final bool compact;
  final bool strong;

  @override
  Widget build(BuildContext context) => Center(
        child: FittedBox(
          fit: BoxFit.scaleDown,
          child: Text(
            value,
            maxLines: 1,
            style: TextStyle(
              color: color,
              fontSize: compact ? 13 : (strong ? 16 : 15),
              fontWeight: strong ? FontWeight.w900 : FontWeight.w800,
              letterSpacing: strong ? -.25 : 0,
            ),
          ),
        ),
      );
}
'''

code = code.replace(insert_anchor, new_widgets + insert_anchor, 1)

if code == original:
    raise SystemExit('SAFETY STOP: no changes produced')

TARGET.write_text(code, encoding='utf-8')
print('Milk detail premium UI migration applied successfully.')
