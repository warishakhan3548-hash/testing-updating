from pathlib import Path

path = Path('lib/main.dart')
src = path.read_text(encoding='utf-8')

# 1) Dashboard metric cards already live in a strict 2x2 GridView. Give every
# card the same visible semantic hairline so equal bounds remain visually clear
# against the ambient background at different display scales.
old_metric = '''        tintColor: color,
        shadowColor: color,
        child: Column('''
new_metric = '''        tintColor: color,
        shadowColor: color,
        borderColor: color.withAlpha(60),
        child: Column('''
if src.count(old_metric) != 1:
    raise SystemExit(f'Expected exactly one _MetricCard surface block, found {src.count(old_metric)}')
src = src.replace(old_metric, new_metric, 1)

# 2) Business detail must always retain a deterministic 2x2 summary matrix.
# Previously zero-value categories were filtered out, which could collapse the
# grid and shift the remaining cards into different positions.
old_business = '''                      if (totals.values.any((double value) => value > 0))
                        GridView.count(
                          crossAxisCount: 2,
                          crossAxisSpacing: 11,
                          mainAxisSpacing: 11,
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          childAspectRatio: 1.55,
                          children: totals.entries
                              .where((MapEntry<String, double> item) =>
                                  item.value > 0)
                              .map((MapEntry<String, double> item) {'''
new_business = '''                      GridView.count(
                        crossAxisCount: 2,
                        crossAxisSpacing: 11,
                        mainAxisSpacing: 11,
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        childAspectRatio: 1.55,
                        children: totals.entries
                            .map((MapEntry<String, double> item) {'''
if src.count(old_business) != 1:
    raise SystemExit(f'Expected exactly one business summary grid block, found {src.count(old_business)}')
src = src.replace(old_business, new_business, 1)

path.write_text(src, encoding='utf-8')
