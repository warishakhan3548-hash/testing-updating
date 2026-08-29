#!/usr/bin/env python3
from pathlib import Path

TARGET = Path('lib/main.dart')
code = TARGET.read_text(encoding='utf-8')
original = code

old = r'''  Future<void> _addCustomer() async {
    final TextEditingController name = TextEditingController();
    final TextEditingController rate = TextEditingController(
      text: LedgerMath.defaultMilkRate.toStringAsFixed(0),
    );
    String type = 'lene_wala';
    final bool? save = await _openSheet<bool>(
      context,
      StatefulBuilder(
        builder: (BuildContext sheetContext, StateSetter setSheetState) =>
            _SheetFrame(
          title: 'New Milk Customer',
          children: <Widget>[
            TextField(
              controller: name,
              autofocus: true,
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(
                labelText: 'Customer name',
                prefixIcon: Icon(Icons.person_rounded),
              ),
            ),
            const SizedBox(height: 13),
            TextField(
              controller: rate,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              inputFormatters: <TextInputFormatter>[
                FilteringTextInputFormatter.allow(RegExp(r'[0-9.]')),
              ],
              decoration: const InputDecoration(
                labelText: 'Rate per KG',
                prefixText: '₹ ',
              ),
            ),
            const SizedBox(height: 13),
            DropdownButtonFormField<String>(
              initialValue: type,
              decoration: const InputDecoration(labelText: 'Default direction'),
              items: const <DropdownMenuItem<String>>[
                DropdownMenuItem(
                  value: 'lene_wala',
                  child: Text('Given / To receive'),
                ),
                DropdownMenuItem(
                  value: 'dene_wala',
                  child: Text('Taken / To pay'),
                ),
              ],
              onChanged: (String? value) {
                if (value != null) {
                  HapticFeedback.selectionClick();
                  setSheetState(() => type = value);
                }
              },
            ),
            const SizedBox(height: 20),
            _PrimaryButton(
              label: 'Create Customer',
              color: appleGreen,
              onTap: () => Navigator.pop(sheetContext, true),
            ),
          ],
        ),
      ),
    );
    if (save != true || !mounted) {
      name.dispose();
      rate.dispose();
      return;
    }
'''

new = r'''  Future<void> _addCustomer() async {
    final TextEditingController name = TextEditingController();
    final TextEditingController rate = TextEditingController(
      text: LedgerMath.defaultMilkRate.toStringAsFixed(0),
    );
    final String? type = await _openSheet<String>(
      context,
      Builder(
        builder: (BuildContext sheetContext) => _SheetFrame(
          title: 'New Milk Customer',
          children: <Widget>[
            TextField(
              controller: name,
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(
                hintText: 'Customer Name',
                prefixIcon: Icon(Icons.person_rounded),
              ),
            ),
            const SizedBox(height: 14),
            TextField(
              controller: rate,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              inputFormatters: <TextInputFormatter>[
                FilteringTextInputFormatter.allow(RegExp(r'[0-9.]')),
              ],
              decoration: const InputDecoration(
                hintText: 'Rate per KG (₹)',
                prefixIcon: Icon(Icons.currency_rupee_rounded),
              ),
            ),
            const SizedBox(height: 22),
            Row(
              children: <Widget>[
                Expanded(
                  child: _MilkCustomerRoleButton(
                    label: 'Seller',
                    icon: Icons.add_rounded,
                    color: appleGreen,
                    semanticLabel: 'Create seller milk customer',
                    onTap: () {
                      HapticFeedback.mediumImpact();
                      Navigator.pop(sheetContext, 'lene_wala');
                    },
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _MilkCustomerRoleButton(
                    label: 'Buyer',
                    icon: Icons.remove_rounded,
                    color: appleRed,
                    semanticLabel: 'Create buyer milk customer',
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
      rate.dispose();
      return;
    }
'''

count = code.count(old)
if count != 1:
    raise SystemExit(f'SAFETY STOP: _addCustomer modal target expected exactly once, found {count}')
code = code.replace(old, new, 1)

anchor = '\nclass MilkDetailScreen extends StatefulWidget {'
if code.count(anchor) != 1:
    raise SystemExit(f'SAFETY STOP: MilkDetailScreen anchor expected once, found {code.count(anchor)}')

widget = r'''

class _MilkCustomerRoleButton extends StatelessWidget {
  const _MilkCustomerRoleButton({
    required this.label,
    required this.icon,
    required this.color,
    required this.semanticLabel,
    required this.onTap,
  });

  final String label;
  final IconData icon;
  final Color color;
  final String semanticLabel;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final bool dark = Theme.of(context).brightness == Brightness.dark;
    final Color companion = Color.lerp(color, Colors.black, .10)!;
    return _Pressable(
      onTap: onTap,
      semanticLabel: semanticLabel,
      borderRadius: BorderRadius.circular(22),
      child: Container(
        constraints: const BoxConstraints(
          minHeight: 62,
          minWidth: UIConstants.minTapTarget,
        ),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: <Color>[color, companion],
          ),
          borderRadius: BorderRadius.circular(22),
          border: Border.all(
            color: dark ? Colors.white.withAlpha(34) : color.withAlpha(95),
            width: .8,
          ),
          boxShadow: dark
              ? const <BoxShadow>[]
              : <BoxShadow>[
                  BoxShadow(
                    color: color.withAlpha(50),
                    blurRadius: 28,
                    spreadRadius: 1,
                    offset: const Offset(0, 12),
                  ),
                ],
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Icon(
              icon,
              color: Colors.white,
              size: 27,
              shadows: const <Shadow>[
                Shadow(color: Colors.black26, blurRadius: 8),
              ],
            ),
            const SizedBox(width: 9),
            Flexible(
              child: FittedBox(
                fit: BoxFit.scaleDown,
                child: Text(
                  label,
                  maxLines: 1,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 17,
                    fontWeight: FontWeight.w900,
                    letterSpacing: -.25,
                    shadows: <Shadow>[
                      Shadow(color: Colors.black26, blurRadius: 8),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
'''

code = code.replace(anchor, widget + anchor, 1)

if code == original:
    raise SystemExit('SAFETY STOP: no changes produced')

TARGET.write_text(code, encoding='utf-8')
print('New Milk Customer Seller/Buyer premium modal migration applied.')
