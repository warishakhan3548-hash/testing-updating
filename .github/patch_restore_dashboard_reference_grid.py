from pathlib import Path

path = Path('lib/main.dart')
src = path.read_text(encoding='utf-8')

start_marker = """                LayoutBuilder(
                  builder: (BuildContext context, BoxConstraints constraints) {
                    const double gap = 13;
                    const double minimumCardHeight = 156;
"""
end_marker = """                const SizedBox(height: 16),
"""

start = src.find(start_marker)
if start < 0:
    raise SystemExit('Dashboard geometry start marker not found')
end = src.find(end_marker, start)
if end < 0:
    raise SystemExit('Dashboard geometry end marker not found')

old = src[start:end]
required_old = [
    'final double cardHeight = math.max(',
    'Widget lockedCard(Widget child) => SizedBox(',
    "label: 'To Receive (+)'",
    "label: 'To Pay (-)'",
    "label: 'Month Expense'",
    "label: 'Month Profit'",
]
for token in required_old:
    if token not in old:
        raise SystemExit(f'Expected current dashboard geometry token missing: {token}')

new = """                GridView.count(
                  crossAxisCount: 2,
                  crossAxisSpacing: 13,
                  mainAxisSpacing: 13,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  childAspectRatio: 1.0,
                  children: <Widget>[
                    _MetricCard(
                      icon: Icons.volunteer_activism_rounded,
                      label: 'To Receive (+)',
                      value: _money(totals.toReceive),
                      color: appleGreen,
                    ),
                    _MetricCard(
                      icon: Icons.request_quote_rounded,
                      label: 'To Pay (-)',
                      value: _money(totals.toPay),
                      color: appleRed,
                    ),
                    _MetricCard(
                      icon: Icons.receipt_long_rounded,
                      label: 'Month Expense',
                      value: _money(totals.monthExpense),
                      color: diaryOrange,
                    ),
                    _MetricCard(
                      icon: Icons.trending_up_rounded,
                      label: 'Month Profit',
                      value: _signedMoney(totals.monthProfit),
                      color: appleBlue,
                    ),
                  ],
                ),
"""

src = src[:start] + new + src[end:]

# Guard the exact requested scope/behavior.
dash = src[src.index('class DashboardScreen'):src.index('class _SyncPill')]
required_new = [
    'GridView.count(',
    'crossAxisCount: 2',
    'crossAxisSpacing: 13',
    'mainAxisSpacing: 13',
    'childAspectRatio: 1.0',
]
for token in required_new:
    if token not in dash:
        raise SystemExit(f'Restored dashboard grid token missing: {token}')
for forbidden in [
    'minimumCardHeight',
    'cardHeight = math.max',
    'Widget lockedCard',
]:
    if forbidden in dash:
        raise SystemExit(f'Old dashboard sizing logic still present: {forbidden}')

path.write_text(src, encoding='utf-8')
print('PATCH_OK dashboard four-card geometry restored to reference 1:1 GridView logic')
