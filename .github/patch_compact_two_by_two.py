from pathlib import Path

path = Path('lib/main.dart')
src = path.read_text(encoding='utf-8')

helper_anchor = 'class _MetricCard extends StatelessWidget {'
helper = '''class _CompactTwoByTwoGrid extends StatelessWidget {
  const _CompactTwoByTwoGrid({
    required this.children,
    this.gap = 8,
  }) : assert(children.length == 4);

  final List<Widget> children;
  final double gap;

  @override
  Widget build(BuildContext context) => LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final double cardSize = (constraints.maxWidth - gap) / 2;

          Widget row(Widget left, Widget right) => Row(
                children: <Widget>[
                  SizedBox(
                    width: cardSize,
                    height: cardSize,
                    child: left,
                  ),
                  SizedBox(width: gap),
                  SizedBox(
                    width: cardSize,
                    height: cardSize,
                    child: right,
                  ),
                ],
              );

          return SizedBox(
            height: (cardSize * 2) + gap,
            child: Column(
              children: <Widget>[
                row(children[0], children[1]),
                SizedBox(height: gap),
                row(children[2], children[3]),
              ],
            ),
          );
        },
      );
}

'''
if helper_anchor not in src:
    raise SystemExit('Metric card anchor missing')
if 'class _CompactTwoByTwoGrid' not in src:
    src = src.replace(helper_anchor, helper + helper_anchor, 1)

old_dashboard = '''                GridView.count(
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
                ),'''
new_dashboard = '''                _CompactTwoByTwoGrid(
                  gap: 8,
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
                ),'''
if src.count(old_dashboard) != 1:
    raise SystemExit(f'Dashboard grid block count={src.count(old_dashboard)}')
src = src.replace(old_dashboard, new_dashboard, 1)

old_business = '''                      GridView.count(
                        crossAxisCount: 2,
                        crossAxisSpacing: 11,
                        mainAxisSpacing: 11,
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        childAspectRatio: 1.55,
                        children:
                            totals.entries.map((MapEntry<String, double> item) {
                          final _BusinessTone tone = _businessTones[item.key]!;
                          return _GlassCard(
                            padding: const EdgeInsets.all(13),
                            borderRadius: 19,
                            borderColor: tone.color.withAlpha(60),
                            shadowColor: tone.color.withAlpha(20),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: <Widget>[
                                Text(
                                  tone.label,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: TextStyle(
                                    color: tone.color,
                                    fontSize: 9,
                                    fontWeight: FontWeight.w900,
                                  ),
                                ),
                                const SizedBox(height: 5),
                                Text(
                                  _money(item.value),
                                  style: TextStyle(
                                    color: tone.color,
                                    fontSize: 19,
                                    fontWeight: FontWeight.w900,
                                    fontFeatures: AppStyles.tabularFigures,
                                  ),
                                ),
                              ],
                            ),
                          );
                        }).toList(),
                      ),'''
new_business = '''                      _CompactTwoByTwoGrid(
                        gap: 8,
                        children:
                            totals.entries.map((MapEntry<String, double> item) {
                          final _BusinessTone tone = _businessTones[item.key]!;
                          return _GlassCard(
                            padding: const EdgeInsets.all(13),
                            borderRadius: 19,
                            borderColor: tone.color.withAlpha(60),
                            shadowColor: tone.color.withAlpha(20),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: <Widget>[
                                Text(
                                  tone.label,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: TextStyle(
                                    color: tone.color,
                                    fontSize: 9,
                                    fontWeight: FontWeight.w900,
                                  ),
                                ),
                                const SizedBox(height: 5),
                                Text(
                                  _money(item.value),
                                  style: TextStyle(
                                    color: tone.color,
                                    fontSize: 19,
                                    fontWeight: FontWeight.w900,
                                    fontFeatures: AppStyles.tabularFigures,
                                  ),
                                ),
                              ],
                            ),
                          );
                        }).toList(),
                      ),'''
if src.count(old_business) != 1:
    raise SystemExit(f'Business grid block count={src.count(old_business)}')
src = src.replace(old_business, new_business, 1)

path.write_text(src, encoding='utf-8')
print('PATCH_OK compact square 2x2 layouts installed')
