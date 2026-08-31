import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('record-backed selectors stay wired to every dated ledger detail', () {
    final String source = File('lib/main.dart').readAsStringSync();

    expect(source, contains('required this.availablePeriods'));
    expect(
      RegExp(r'availablePeriods: availablePeriods').allMatches(source),
      hasLength(5),
      reason:
          'Milk, Salary, Credit, Expense and Diary must share the same picker.',
    );
    expect(source, contains('class CreditDetailScreen extends StatefulWidget'));
    expect(source, contains('class _DiaryEditorSheet extends StatefulWidget'));
    expect(source, contains('color: diaryOrange'));
    expect(source, contains('LengthLimitingTextInputFormatter'));
    expect(source, contains('This page changed on another device.'));
    final int diaryStart = source.indexOf('class DiaryScreen');
    final int diaryEnd = source.indexOf('class DiaryDetailScreen');
    expect(diaryStart, greaterThanOrEqualTo(0));
    expect(diaryEnd, greaterThan(diaryStart));
    final String diarySource = source.substring(diaryStart, diaryEnd);
    expect(diarySource, contains('ListView.builder('));
    expect(diarySource, contains('LedgerMath.inMonth('));
    expect(diarySource, isNot(contains('...entries.map(')));
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
