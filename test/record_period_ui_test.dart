import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('record-backed selectors stay wired to every dated ledger detail', () {
    final String source = File('lib/main.dart').readAsStringSync();

    expect(source, contains('required this.availablePeriods'));
    expect(
      RegExp(r'availablePeriods: availablePeriods').allMatches(source),
      hasLength(4),
      reason: 'Milk, Salary, Credit and Expense must share the same picker.',
    );
    expect(source, contains('class CreditDetailScreen extends StatefulWidget'));
    expect(source, isNot(contains('currentYear + 2 - index')));
    expect(
      source,
      isNot(
        contains(
          'if (!LedgerMath.inMonth(row, now.month, now.year)) continue;',
        ),
      ),
      reason: 'Historical-only expense categories must remain reachable.',
    );
  });
}
