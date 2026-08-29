#!/usr/bin/env python3
from pathlib import Path

path = Path('lib/main.dart')
code = path.read_text(encoding='utf-8')

class_start = code.find('class CreditDetailScreen extends StatelessWidget {')
if class_start < 0:
    raise SystemExit('SAFETY STOP: CreditDetailScreen not found')

method_start = code.find('  Future<void> _addEntry(BuildContext context) async {', class_start)
if method_start < 0:
    raise SystemExit('SAFETY STOP: CreditDetailScreen._addEntry not found')

method_end = code.find('  Future<void> _deleteEntry(BuildContext context, String id) async {', method_start)
if method_end < 0:
    raise SystemExit('SAFETY STOP: CreditDetailScreen._deleteEntry anchor not found')

old_method = code[method_start:method_end]
for required in (
    'SegmentedButton<String>',
    "label: 'Save Entry'",
    "value: 'credit'",
    "value: 'debit'",
    "reason: 'credit-entry-save'",
):
    if required not in old_method:
        raise SystemExit(f'SAFETY STOP: expected old Credit detail marker missing: {required}')

new_method = r'''  Future<void> _addEntry(BuildContext context) async {
    final TextEditingController date = TextEditingController(text: _today());
    final TextEditingController amount = TextEditingController();
    final String? type = await _openSheet<String>(
      context,
      Builder(
        builder: (BuildContext sheetContext) => _SheetFrame(
          title: '$personName Credit Entry',
          children: <Widget>[
            _DateField(controller: date),
            const SizedBox(height: 13),
            TextField(
              controller: amount,
              autofocus: true,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              inputFormatters: <TextInputFormatter>[
                FilteringTextInputFormatter.allow(RegExp(r'[0-9.]')),
              ],
              decoration:
                  const InputDecoration(labelText: 'Amount', prefixText: '₹ '),
            ),
            const SizedBox(height: 22),
            Row(
              children: <Widget>[
                Expanded(
                  child: _MilkCustomerRoleButton(
                    label: 'Given',
                    icon: Icons.add_rounded,
                    color: appleGreen,
                    semanticLabel: 'Save credit as given',
                    onTap: () {
                      HapticFeedback.mediumImpact();
                      Navigator.pop(sheetContext, 'credit');
                    },
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _MilkCustomerRoleButton(
                    label: 'Taken',
                    icon: Icons.remove_rounded,
                    color: appleRed,
                    semanticLabel: 'Save credit as taken',
                    onTap: () {
                      HapticFeedback.mediumImpact();
                      Navigator.pop(sheetContext, 'debit');
                    },
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
    if (type == null || !context.mounted) {
      date.dispose();
      amount.dispose();
      return;
    }
    final String entryDate = date.text.trim();
    final double entryAmount = double.tryParse(amount.text) ?? 0;
    date.dispose();
    amount.dispose();
    if (LedgerMath.strictDate(entryDate) == null || entryAmount <= 0) {
      _toast(context, 'Enter a valid date and positive amount.', error: true);
      return;
    }
    final String id = _newId('udh');
    await _runMutation(
      context,
      () => sync.write(
        'udharDB/$id',
        <String, dynamic>{
          'id': id,
          'date': entryDate,
          'name': personName,
          'amount': entryAmount,
          'type': type,
        },
        reason: 'credit-entry-save',
      ),
      type == 'credit' ? 'Given entry saved!' : 'Taken entry saved!',
    );
  }

'''

code = code[:method_start] + new_method + code[method_end:]

# Scope guarantees: only the CreditDetail add method changes.
if code.count('class CreditDetailScreen extends StatelessWidget {') != 1:
    raise SystemExit('SAFETY STOP: unexpected CreditDetailScreen count')

path.write_text(code, encoding='utf-8')
print('Credit detail modal now uses direct premium Given/Taken actions.')
