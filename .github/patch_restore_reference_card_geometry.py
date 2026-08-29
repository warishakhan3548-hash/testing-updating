from pathlib import Path

path = Path('lib/main.dart')
src = path.read_text(encoding='utf-8')

# Remove the temporary compact-square helper introduced later.
helper_start = src.find('class _CompactTwoByTwoGrid extends StatelessWidget {')
if helper_start == -1:
    raise SystemExit('Expected _CompactTwoByTwoGrid helper not found')
metric_anchor = src.find('class _MetricCard extends StatelessWidget {', helper_start)
if metric_anchor == -1:
    raise SystemExit('Metric card anchor not found')
src = src[:helper_start] + src[metric_anchor:]

# Restore Dashboard geometry from the user-provided reference main.dart:
# 2 columns, 13dp gaps, square cells (aspect ratio 1.0).
old_dashboard = '''                _CompactTwoByTwoGrid(
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
new_dashboard = '''                GridView.count(
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
if src.count(old_dashboard) != 1:
    raise SystemExit(f'Dashboard compact block count={src.count(old_dashboard)}')
src = src.replace(old_dashboard, new_dashboard, 1)

# Restore Business-detail geometry from the reference file while preserving
# the current behavior of rendering all four summary categories, including 0.
old_business = '''                      _CompactTwoByTwoGrid(
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
new_business = '''                      GridView.count(
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
if src.count(old_business) != 1:
    raise SystemExit(f'Business compact block count={src.count(old_business)}')
src = src.replace(old_business, new_business, 1)

path.write_text(src, encoding='utf-8')
print('PATCH_OK reference card geometry restored')
