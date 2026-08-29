#!/usr/bin/env python3
from pathlib import Path

path = Path('lib/main.dart')
code = path.read_text(encoding='utf-8')

old = """    String flow = 'given';
    final bool? save = await _openSheet<bool>(
      context,
      StatefulBuilder(
        builder: (BuildContext sheetContext, StateSetter setSheetState) =>
            _SheetFrame(
          title: 'Daily Milk Entry',
          children: <Widget>[
            _DateField(controller: date),
            const SizedBox(height: 13),
            Row(
              children: <Widget>[
                Expanded(
                  child: TextField(
                    controller: morning,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: <TextInputFormatter>[
                      FilteringTextInputFormatter.allow(RegExp(r'[0-9.]')),
                    ],
                    decoration: const InputDecoration(labelText: 'Morning KG'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: TextField(
                    controller: evening,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: <TextInputFormatter>[
                      FilteringTextInputFormatter.allow(RegExp(r'[0-9.]')),
                    ],
                    decoration: const InputDecoration(labelText: 'Evening KG'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 13),
            SegmentedButton<String>(
              segments: const <ButtonSegment<String>>[
                ButtonSegment<String>(
                  value: 'given',
                  label: Text('Given'),
                  icon: Icon(Icons.add_rounded),
                ),
                ButtonSegment<String>(
                  value: 'taken',
                  label: Text('Taken'),
                  icon: Icon(Icons.remove_rounded),
                ),
              ],
              selected: <String>{flow},
              onSelectionChanged: (Set<String> values) {
                HapticFeedback.selectionClick();
                setSheetState(() => flow = values.first);
              },
            ),
            const SizedBox(height: 20),
            _PrimaryButton(
              label: 'Save Entry',
              color: flow == 'given' ? appleGreen : appleRed,
              onTap: () => Navigator.pop(sheetContext, true),
            ),
          ],
        ),
      ),
    );
    if (save != true || !mounted) {
"""

new = """    final String? flow = await _openSheet<String>(
      context,
      Builder(
        builder: (BuildContext sheetContext) => _SheetFrame(
          title: 'Daily Milk Entry',
          children: <Widget>[
            _DateField(controller: date),
            const SizedBox(height: 13),
            Row(
              children: <Widget>[
                Expanded(
                  child: TextField(
                    controller: morning,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: <TextInputFormatter>[
                      FilteringTextInputFormatter.allow(RegExp(r'[0-9.]')),
                    ],
                    decoration: const InputDecoration(labelText: 'Morning KG'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: TextField(
                    controller: evening,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: <TextInputFormatter>[
                      FilteringTextInputFormatter.allow(RegExp(r'[0-9.]')),
                    ],
                    decoration: const InputDecoration(labelText: 'Evening KG'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 22),
            Row(
              children: <Widget>[
                Expanded(
                  child: _MilkCustomerRoleButton(
                    label: 'Given',
                    icon: Icons.add_rounded,
                    color: appleGreen,
                    semanticLabel: 'Save milk as given',
                    onTap: () {
                      HapticFeedback.mediumImpact();
                      Navigator.pop(sheetContext, 'given');
                    },
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _MilkCustomerRoleButton(
                    label: 'Taken',
                    icon: Icons.remove_rounded,
                    color: appleRed,
                    semanticLabel: 'Save milk as taken',
                    onTap: () {
                      HapticFeedback.mediumImpact();
                      Navigator.pop(sheetContext, 'taken');
                    },
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
    if (flow == null || !mounted) {
"""

count = code.count(old)
if count != 1:
    raise SystemExit(f'SAFETY STOP: Daily Milk Entry selector block expected once, found {count}')

code = code.replace(old, new, 1)

# Guardrails: this specific modal must no longer contain the old selection/save controls.
start = code.index('  Future<void> _addEntry(Map<String, dynamic> profile) async {')
end = code.index('\n  Future<void> _deleteEntry(String id) async {', start)
method = code[start:end]
for dead in ('SegmentedButton<String>', "label: 'Save Entry'", 'setSheetState(() => flow'):
    if dead in method:
        raise SystemExit(f'SAFETY STOP: old Daily Milk Entry control still present: {dead}')
for required in ("label: 'Given'", "label: 'Taken'", "Navigator.pop(sheetContext, 'given')", "Navigator.pop(sheetContext, 'taken')"):
    if required not in method:
        raise SystemExit(f'SAFETY STOP: expected direct flow action missing: {required}')

path.write_text(code, encoding='utf-8')
print('Daily Milk Entry now saves directly from colorful Given/Taken buttons.')
