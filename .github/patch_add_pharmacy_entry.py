from pathlib import Path

path = Path('lib/main.dart')
src = path.read_text(encoding='utf-8')

if "'Enter in Pharmacy'" in src or 'class PharmacyDashboardPlaceholderScreen' in src:
    raise SystemExit('Pharmacy dashboard entry already exists')

party_block = """                _Pressable(
                  onTap: () => Navigator.of(context).push(
                    _premiumRoute<void>(PartyLedgerScreen(sync: sync)),
                  ),
                  borderRadius: BorderRadius.circular(24),
                  child: const _GlassCard(
                    child: Row(
                      children: <Widget>[
                        _LedgerIcon(
                          icon: Icons.contact_page_rounded,
                          color: Color(0xFF9333EA),
                        ),
                        SizedBox(width: 15),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: <Widget>[
                              Text(
                                'Party Ledger',
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.w900,
                                ),
                              ),
                              SizedBox(height: 3),
                              Text(
                                'COMBINED MILK & CREDIT',
                                style: TextStyle(
                                  color: systemGray,
                                  fontSize: 10,
                                  fontWeight: FontWeight.w900,
                                  letterSpacing: .8,
                                ),
                              ),
                            ],
                          ),
                        ),
                        Icon(Icons.chevron_right_rounded, color: systemGray),
                      ],
                    ),
                  ),
                ),
"""

if src.count(party_block) != 1:
    raise SystemExit(f'Expected exactly one Party Ledger dashboard block, found {src.count(party_block)}')

pharmacy_card = party_block + """                const SizedBox(height: 16),
                _Pressable(
                  onTap: () => Navigator.of(context).push(
                    _premiumRoute<void>(
                      const PharmacyDashboardPlaceholderScreen(),
                    ),
                  ),
                  borderRadius: BorderRadius.circular(24),
                  semanticLabel: 'Enter in Pharmacy',
                  child: const _GlassCard(
                    child: Row(
                      children: <Widget>[
                        _LedgerIcon(
                          icon: Icons.medication_rounded,
                          color: salaryGreen,
                        ),
                        SizedBox(width: 15),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: <Widget>[
                              Text(
                                'Enter in Pharmacy',
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.w900,
                                ),
                              ),
                              SizedBox(height: 3),
                              Text(
                                'PHARMACY MEDICATIONS',
                                style: TextStyle(
                                  color: systemGray,
                                  fontSize: 10,
                                  fontWeight: FontWeight.w900,
                                  letterSpacing: .8,
                                ),
                              ),
                            ],
                          ),
                        ),
                        Icon(Icons.chevron_right_rounded, color: systemGray),
                      ],
                    ),
                  ),
                ),
"""

src = src.replace(party_block, pharmacy_card, 1)

screen_marker = "class PartyLedgerScreen extends StatefulWidget {"
if src.count(screen_marker) != 1:
    raise SystemExit('PartyLedgerScreen insertion marker is not unique')

placeholder = """class PharmacyDashboardPlaceholderScreen extends StatelessWidget {
  const PharmacyDashboardPlaceholderScreen({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(
        body: Column(
          children: <Widget>[
            const _ScreenHeader(
              leading: _BackCircle(),
              title: 'Dashboard',
              subtitle: 'PHARMACY MEDICATIONS',
              color: salaryGreen,
            ),
            Expanded(
              child: Center(
                child: Text(
                  'Dashboard',
                  style: TextStyle(
                    color: salaryGreen,
                    fontSize: 32,
                    fontWeight: FontWeight.w900,
                    letterSpacing: -.5,
                    shadows: AppStyles.inkGlow(salaryGreen, strong: true),
                  ),
                ),
              ),
            ),
          ],
        ),
      );
}

"""

src = src.replace(screen_marker, placeholder + screen_marker, 1)

# Guard requested scope and behavior.
dash = src[src.index('class DashboardScreen'):src.index('class _SyncPill')]
required = [
    "'Party Ledger'",
    "'Enter in Pharmacy'",
    "'PHARMACY MEDICATIONS'",
    'Icons.medication_rounded',
    'PharmacyDashboardPlaceholderScreen',
    'childAspectRatio: 1.0',
]
for token in required:
    if token not in dash:
        raise SystemExit(f'Missing dashboard token after patch: {token}')

if src.count('class PharmacyDashboardPlaceholderScreen') != 1:
    raise SystemExit('Placeholder screen count is not exactly one')

path.write_text(src, encoding='utf-8')
print('PATCH_OK pharmacy entry card added below Party Ledger with Dashboard placeholder')
