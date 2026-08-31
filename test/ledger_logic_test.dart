import 'package:flutter_test/flutter_test.dart';

import 'package:aarish_diary/firebase_sync.dart';

void main() {
  group('Firebase schema compatibility', () {
    test('compact delta paths round-trip without duplicate ambiguity', () {
      final String? encoded = DeltaPathCodec.encode(<String>[
        'diaryDB/dia_1',
        'expenseDB/exp_1',
      ]);

      expect(encoded, isNotNull);
      expect(DeltaPathCodec.decode(encoded), <String>[
        'diaryDB/dia_1',
        'expenseDB/exp_1',
      ]);
      expect(
        DeltaPathCodec.decode('["diaryDB/dia_1","diaryDB/dia_1"]'),
        isEmpty,
      );
      expect(DeltaPathCodec.decode('not-json'), isEmpty);
      expect(
        DeltaPathCodec.encode(
          List<String>.generate(
            DeltaPathCodec.maxPaths + 1,
            (int index) => 'diaryDB/dia_$index',
          ),
        ),
        isNull,
      );
    });

    test('canonicalizes Firebase maps into stable ID lists', () {
      final Map<String, dynamic> state = LedgerCodec.normalizeState(
        <String, dynamic>{
          'udharDB': <String, dynamic>{
            'udh_1': <String, dynamic>{
              'date': '2026-08-01',
              'name': 'Ali',
              'amount': 100,
              'type': 'credit',
            },
          },
          'milkDB': <String, dynamic>{
            'Shop': <String, dynamic>{
              'rate': 60,
              'records': <String, dynamic>{
                'mlk_1': <String, dynamic>{
                  'date': '2026-08-01',
                  'morning': 2,
                  'evening': 1,
                },
              },
            },
          },
        },
      );

      final List<Map<String, dynamic>> credit =
          LedgerCodec.canonicalList(state['udharDB']);
      final Map<String, dynamic> milk = LedgerCodec.objectMap(state['milkDB']);
      final List<Map<String, dynamic>> milkRows = LedgerCodec.canonicalList(
        LedgerCodec.objectMap(milk['Shop'])['records'],
      );

      expect(credit.single['id'], 'udh_1');
      expect(milkRows.single['id'], 'mlk_1');
    });

    test('monthly diary projection is fail-closed by schema and revision', () {
      final DiaryProjectionMetadata ready =
          DiaryProjectionMetadata.fromValue(<String, dynamic>{
        'schemaVersion': 1,
        'ready': true,
        'sourceRevision': 42,
      });
      expect(ready.matchesSourceRevision(42), isTrue);
      expect(ready.matchesSourceRevision(41), isFalse);
      expect(
        DiaryProjectionMetadata.fromValue(<String, dynamic>{
          'schemaVersion': 2,
          'ready': true,
          'sourceRevision': 42,
        }).matchesSourceRevision(42),
        isFalse,
      );
      expect(
        DiaryProjectionMetadata.fromValue(<String, dynamic>{
          'schemaVersion': 1,
          'ready': false,
          'sourceRevision': 42,
        }).matchesSourceRevision(42),
        isFalse,
      );
    });

    test('monthly diary codec replaces only the requested month', () {
      final List<Map<String, dynamic>> august =
          DiaryMonthCodec.decodeMonthEntries(
        <String, dynamic>{
          'aug': <String, dynamic>{
            'id': 'aug',
            'date': '2026-08-05',
            'title': 'Projected August',
            'content': 'new',
            '_period': '2026-08',
            '_sourceHash': 'private',
            '_version': 8,
          },
          'wrong_month': <String, dynamic>{
            'date': '2026-07-01',
            '_period': '2026-07',
          },
          'deleted': <String, dynamic>{
            'date': '2026-08-02',
            '_period': '2026-08',
            '_deleted': true,
          },
          'invalid_projected': <String, dynamic>{
            'date': 'not-a-date',
            'title': 'Projected invalid date',
            '_period': '_invalid',
          },
        },
        year: 2026,
        month: 8,
      );
      expect(august, hasLength(1));
      expect(august.single['title'], 'Projected August');
      expect(august.single.containsKey('_sourceHash'), isFalse);
      final List<Map<String, dynamic>> invalidProjected =
          DiaryMonthCodec.decodeInvalidEntries(<String, dynamic>{
        'invalid_projected': <String, dynamic>{
          'date': 'not-a-date',
          'title': 'Projected invalid date',
          '_period': '_invalid',
        },
      });
      expect(invalidProjected, hasLength(1));

      final Map<String, dynamic> state = LedgerCodec.normalizeState(
        <String, dynamic>{
          'diaryDB': <String, dynamic>{
            'old_aug': <String, dynamic>{
              'date': '2026-08-01',
              'title': 'Stale August',
            },
            'july': <String, dynamic>{
              'date': '2026-07-01',
              'title': 'Keep July',
            },
            'invalid': <String, dynamic>{
              'date': 'not-a-date',
              'title': 'Keep legacy invalid date',
            },
          },
        },
      );
      DiaryMonthCodec.replaceMonth(
        state,
        year: 2026,
        month: 8,
        entries: august,
      );
      final List<Map<String, dynamic>> rows =
          LedgerCodec.canonicalList(state['diaryDB']);
      expect(rows.map((Map<String, dynamic> row) => row['id']),
          containsAll(<String>['aug', 'july', 'invalid']));
      expect(
        rows.any((Map<String, dynamic> row) => row['id'] == 'old_aug'),
        isFalse,
      );
      DiaryMonthCodec.replaceInvalidEntries(state, invalidProjected);
      final List<Map<String, dynamic>> afterInvalidReplacement =
          LedgerCodec.canonicalList(state['diaryDB']);
      expect(
        afterInvalidReplacement
            .map((Map<String, dynamic> row) => row['id']),
        containsAll(<String>['aug', 'july', 'invalid_projected']),
      );
      expect(
        afterInvalidReplacement
            .any((Map<String, dynamic> row) => row['id'] == 'invalid'),
        isFalse,
      );
      expect(
        DiaryMonthCodec.periodsFromIndex(<String, dynamic>{
          'aug': <String, dynamic>{'p': '2026-08', 'v': 4},
          'july': '2026-07',
          'deleted': <String, dynamic>{'p': null, 'v': 8},
          'invalid': '2026-13',
        }),
        <DateTime>[DateTime(2026, 8), DateTime(2026, 7)],
      );
    });

    test('pending delete replay prevents stale cloud resurrection', () {
      final Map<String, dynamic> staleCloud = LedgerCodec.normalizeState(
        <String, dynamic>{
          'diaryDB': <String, dynamic>{
            'dia_1': <String, dynamic>{
              'id': 'dia_1',
              'date': '2026-08-01',
              'title': 'Delete me',
              'content': 'Old remote copy',
            },
          },
        },
      );

      expect(LedgerCodec.applyPath(staleCloud, 'diaryDB/dia_1', null), isTrue);
      expect(LedgerCodec.canonicalList(staleCloud['diaryDB']), isEmpty);

      final Map<String, dynamic> staleLoginCopy = LedgerCodec.normalizeState(
        <String, dynamic>{
          'diaryDB': <String, dynamic>{
            'dia_1': <String, dynamic>{
              'id': 'dia_1',
              'date': '2026-08-01',
              'title': 'Delete me',
              'content': 'Old remote copy',
            },
          },
        },
      );
      LedgerCodec.applyPath(staleLoginCopy, 'diaryDB/dia_1', null);
      expect(LedgerCodec.canonicalList(staleLoginCopy['diaryDB']), isEmpty);
    });

    test('parent and child writes are separated into ordered batches', () {
      final List<PendingWrite> queue = <PendingWrite>[
        const PendingWrite(
          id: '1',
          path: 'milkDB/Ali/records/mlk_1',
          value: <String, dynamic>{'id': 'mlk_1'},
          createdAt: 1,
          reason: 'add',
        ),
        const PendingWrite(
          id: '2',
          path: 'expenseDB/exp_1',
          value: null,
          createdAt: 2,
          reason: 'delete',
        ),
        const PendingWrite(
          id: '3',
          path: 'milkDB/Ali',
          value: null,
          createdAt: 3,
          reason: 'profile-delete',
        ),
      ];

      final List<PendingWrite> first = OutboxPlanner.nextCompatibleBatch(queue);
      expect(first.map((PendingWrite item) => item.id), <String>['1', '2']);
      expect(
        OutboxPlanner.overlaps('milkDB/Ali', 'milkDB/Ali/records/mlk_1'),
        isTrue,
      );
    });

    test('vector clocks detect a same-revision multi-device race', () {
      const String writerA = 'writer_device_alpha';
      const String writerB = 'writer_device_bravo';
      final Map<String, Map<String, String>> localClocks =
          <String, Map<String, String>>{
        'diaryDB': <String, String>{writerA: 'a0', writerB: 'b0'},
      };
      final Map<String, Map<String, String>> remoteClocks =
          <String, Map<String, String>>{
        'diaryDB': <String, String>{writerA: 'a1', writerB: 'b1'},
      };

      final Set<String> changed = LedgerDeltaPolicy.changedRoots(
        remoteRevisions: const <String, int>{'diaryDB': 10},
        localRevisions: const <String, int>{'diaryDB': 10},
        remoteClocks: remoteClocks,
        localClocks: localClocks,
      );

      expect(changed, <String>{'diaryDB'});
      expect(
        LedgerDeltaPolicy.canApplyDelta(
          remoteWriterId: writerB,
          predecessorToken: 'global-0',
          localToken: 'global-0',
          changedRoots: changed,
          deltaRoots: <String>{'diaryDB'},
          remoteClocks: remoteClocks,
          localClocks: localClocks,
        ),
        isFalse,
        reason: 'two changed writers require a changed-root fetch',
      );
    });

    test('vector delta is accepted only for one proven writer', () {
      const String writer = 'writer_device_alpha';
      final Map<String, Map<String, String>> localClocks =
          <String, Map<String, String>>{
        'expenseDB': <String, String>{writer: 'a0'},
      };
      final Map<String, Map<String, String>> remoteClocks =
          <String, Map<String, String>>{
        'expenseDB': <String, String>{writer: 'a1'},
      };
      final Set<String> changed = LedgerDeltaPolicy.changedRoots(
        remoteRevisions: const <String, int>{'expenseDB': 11},
        localRevisions: const <String, int>{'expenseDB': 10},
        remoteClocks: remoteClocks,
        localClocks: localClocks,
      );

      expect(
        LedgerDeltaPolicy.canApplyDelta(
          remoteWriterId: writer,
          predecessorToken: 'global-0',
          localToken: 'global-0',
          changedRoots: changed,
          deltaRoots: <String>{'expenseDB'},
          remoteClocks: remoteClocks,
          localClocks: localClocks,
        ),
        isTrue,
      );
    });
  });

  group('Ledger calculations', () {
    test('record periods contain only months with data in newest-first order', () {
      final List<DateTime> periods = LedgerMath.recordPeriods(
        <String, dynamic>{
          'jan': <String, dynamic>{'date': '2026-01-05'},
          'mar-a': <String, dynamic>{'date': '2026-03-01'},
          'mar-b': <String, dynamic>{'date': '2026-03-29'},
          'future': <String, dynamic>{'date': '2035-06-14'},
          'invalid': <String, dynamic>{'date': 'not-a-date'},
        },
      );

      expect(periods, <DateTime>[
        DateTime(2035, 6),
        DateTime(2026, 3),
        DateTime(2026, 1),
      ]);
    });

    test('record period selection keeps data periods and falls back safely', () {
      final List<DateTime> periods = <DateTime>[
        DateTime(2035, 6),
        DateTime(2026, 3),
        DateTime(2026, 1),
      ];

      expect(
        LedgerMath.resolveRecordPeriod(periods, month: 3, year: 2026),
        DateTime(2026, 3),
      );
      expect(
        LedgerMath.resolveRecordPeriod(periods, month: 2, year: 2026),
        DateTime(2026, 3),
      );
      expect(
        LedgerMath.resolveRecordPeriod(periods, month: 8, year: 2030),
        DateTime(2035, 6),
      );
      expect(
        LedgerMath.resolveRecordPeriod(
          const <DateTime>[],
          month: 8,
          year: 2026,
        ),
        isNull,
      );
    });

    test('strict input dates reject normalized impossible dates', () {
      expect(LedgerMath.strictDate('2024-02-29'), DateTime(2024, 2, 29));
      expect(LedgerMath.strictDate('2026-02-29'), isNull);
      expect(LedgerMath.strictDate('2026-02-30'), isNull);
      expect(LedgerMath.strictDate('2026-2-03'), isNull);
      expect(LedgerMath.strictDate('not-a-date'), isNull);
    });

    test('milk entry rate overrides profile rate consistently', () {
      final MilkTotals totals = LedgerMath.milkTotals(
        <String, dynamic>{
          'rate': 50,
          'records': <String, dynamic>{
            'new_rate': <String, dynamic>{
              'morning': 2,
              'rate': 70,
              'flow': 'given',
            },
            'profile_rate': <String, dynamic>{
              'evening': 1,
              'flow': 'taken',
            },
          },
        },
      );

      expect(totals.givenAmount, 140);
      expect(totals.takenAmount, 50);
      expect(totals.netAmount, 90);
      expect(
        LedgerMath.milkRate(<String, dynamic>{}, <String, dynamic>{}),
        55,
      );
    });

    test('dashboard matches web receive, expense and profit rules', () {
      final Map<String, dynamic> state = LedgerCodec.normalizeState(
        <String, dynamic>{
          'milkDB': <String, dynamic>{
            'Dairy': <String, dynamic>{
              'rate': 50,
              'type': 'lene_wala',
              'records': <String, dynamic>{
                'mlk_1': <String, dynamic>{
                  'id': 'mlk_1',
                  'date': '2026-08-02',
                  'morning': 2,
                  'evening': 0,
                  'flow': 'given',
                },
              },
            },
          },
          'udharDB': <String, dynamic>{
            'udh_1': <String, dynamic>{
              'id': 'udh_1',
              'date': '2026-08-03',
              'name': 'Ali',
              'amount': 500,
              'type': 'credit',
            },
            'udh_2': <String, dynamic>{
              'id': 'udh_2',
              'date': '2026-08-04',
              'name': 'Ali',
              'amount': 200,
              'type': 'debit',
            },
          },
          'expenseDB': <String, dynamic>{
            'exp_1': <String, dynamic>{
              'id': 'exp_1',
              'date': '2026-08-05',
              'category': 'Fuel',
              'amount': 30,
            },
          },
          'salaryDB': <String, dynamic>{
            'Worker': <String, dynamic>{
              'type': 'lene_wala',
              'records': <String, dynamic>{
                'sal_1': <String, dynamic>{
                  'id': 'sal_1',
                  'date': '2026-08-06',
                  'amount': 200,
                },
              },
            },
          },
        },
      );

      final DashboardTotals totals = LedgerMath.dashboard(
        state,
        month: 8,
        year: 2026,
      );

      expect(totals.toReceive, 400);
      expect(totals.toPay, 0);
      expect(totals.monthExpense, 30);
      expect(totals.monthProfit, 270);
      expect(totals.creditReceive, 300);
    });

    test('party ledger combines lifetime milk and credit by name', () {
      final Map<String, dynamic> state = LedgerCodec.normalizeState(
        <String, dynamic>{
          'milkDB': <String, dynamic>{
            'Ali': <String, dynamic>{
              'rate': 50,
              'records': <String, dynamic>{
                'm': <String, dynamic>{
                  'id': 'm',
                  'date': '2026-01-01',
                  'morning': 2,
                  'flow': 'given',
                },
              },
            },
          },
          'udharDB': <String, dynamic>{
            'u': <String, dynamic>{
              'id': 'u',
              'name': 'Ali',
              'amount': 40,
              'type': 'debit',
            },
          },
        },
      );

      final PartyBalance ali = LedgerMath.partyBalances(state).single;
      expect(ali.milk, 100);
      expect(ali.credit, -40);
      expect(ali.net, 60);
    });

    test('materialized projection preserves every legacy dashboard invariant', () {
      final Map<String, dynamic> state = LedgerCodec.normalizeState(
        <String, dynamic>{
          'milkDB': <String, dynamic>{
            'Ali': <String, dynamic>{
              'rate': 50,
              'records': <String, dynamic>{
                'old': <String, dynamic>{
                  'date': '2025-12-01',
                  'morning': 2,
                  'flow': 'given',
                },
                'current': <String, dynamic>{
                  'date': '2026-08-01',
                  'morning': 1,
                  'flow': 'taken',
                },
              },
            },
            'Buyer': <String, dynamic>{
              'rate': 60,
              'type': 'dene_wala',
              'records': <String, dynamic>{
                'current': <String, dynamic>{
                  'date': '2026-08-02',
                  'morning': 2,
                },
              },
            },
            'Seller': <String, dynamic>{
              'rate': 40,
              'type': 'lene_wala',
              'records': <String, dynamic>{
                'old': <String, dynamic>{
                  'date': '2025-12-03',
                  'morning': 1,
                  'flow': 'taken',
                },
                'current': <String, dynamic>{
                  'date': '2026-08-03',
                  'morning': 3,
                },
              },
            },
          },
          'udharDB': <String, dynamic>{
            'ali_credit': <String, dynamic>{
              'date': '2026-07-01',
              'name': 'Ali',
              'amount': 200,
              'type': 'credit',
            },
            'ali_debit': <String, dynamic>{
              'date': '2026-08-04',
              'name': 'Ali',
              'amount': 250,
              'type': 'debit',
            },
            'bob_credit': <String, dynamic>{
              'date': '2026-08-05',
              'name': 'Bob',
              'amount': 300,
              'type': 'credit',
            },
            'bob_debit': <String, dynamic>{
              'date': '2026-08-06',
              'name': 'Bob',
              'amount': 100,
              'type': 'debit',
            },
            'legacy_unnamed': <String, dynamic>{
              'date': '2026-08-07',
              'amount': 999,
              'type': 'credit',
            },
          },
          'expenseDB': <String, dynamic>{
            'fuel': <String, dynamic>{
              'date': '2026-08-08',
              'category': 'Fuel',
              'amount': 30,
            },
            'old_fuel': <String, dynamic>{
              'date': '2026-07-08',
              'category': 'Fuel',
              'amount': 10,
            },
            'travel': <String, dynamic>{
              'date': '2026-08-12',
              'category': ' Travel/Taxi ',
              'amount': 20,
            },
            'invalid_date': <String, dynamic>{
              'date': '',
              'category': 'Misc',
              'amount': 500,
            },
          },
          'salaryDB': <String, dynamic>{
            'Receiver': <String, dynamic>{
              'type': 'lene_wala',
              'records': <String, dynamic>{
                'current': <String, dynamic>{
                  'date': '2026-08-09',
                  'amount': 200,
                },
              },
            },
            'Payer': <String, dynamic>{
              'type': 'dene_wala',
              'records': <String, dynamic>{
                'current': <String, dynamic>{
                  'date': '2026-08-10',
                  'amount': 80,
                },
              },
            },
          },
          'projectDB': <String, dynamic>{
            'Shop': <String, dynamic>{
              'records': <String, dynamic>{
                'one': <String, dynamic>{'date': '2026-08-01'},
                'two': <String, dynamic>{'date': '2026-08-02'},
              },
            },
          },
        },
      );

      final LedgerProjection projection = LedgerProjection.fromState(
        state,
        month: 8,
        year: 2026,
      );
      final DashboardTotals legacy = LedgerMath.dashboard(
        state,
        month: 8,
        year: 2026,
      );

      expect(projection.dashboard.toReceive, legacy.toReceive);
      expect(projection.dashboard.toPay, legacy.toPay);
      expect(projection.dashboard.monthExpense, legacy.monthExpense);
      expect(projection.dashboard.monthProfit, legacy.monthProfit);
      expect(projection.dashboard.creditReceive, legacy.creditReceive);
      expect(projection.dashboard.creditPay, legacy.creditPay);
      expect(projection.dashboard.toReceive, 330);
      expect(projection.dashboard.toPay, 170);
      expect(projection.dashboard.monthExpense, 300);
      expect(projection.dashboard.monthProfit, 20);
      expect(projection.milkLifetimeNet, 10);
      expect(projection.creditLifetimeNet, 1149);
      expect(projection.salaryMonthNet, 120);
      expect(projection.expenseMonthTotal, 50);
      expect(projection.businessRecordCounts['Shop'], 2);
      expect(
        projection.expenseCategories
            .map((ExpenseCategorySummary item) => item.category),
        containsAll(<String>['Fuel', 'Travel Taxi', 'Misc']),
      );

      final List<PartyBalance> legacyParties = LedgerMath.partyBalances(state);
      expect(projection.partyBalances.length, legacyParties.length);
      for (int index = 0; index < legacyParties.length; index++) {
        expect(projection.partyBalances[index].name, legacyParties[index].name);
        expect(projection.partyBalances[index].milk, legacyParties[index].milk);
        expect(
          projection.partyBalances[index].credit,
          legacyParties[index].credit,
        );
        expect(projection.partyBalances[index].net, legacyParties[index].net);
      }
    });

    test('projection handles sign crossing, deletion, and month moves', () {
      final Map<String, dynamic> state = LedgerCodec.normalizeState(
        <String, dynamic>{
          'udharDB': <String, dynamic>{
            'credit': <String, dynamic>{
              'date': '2026-08-01',
              'name': 'Ali',
              'amount': 100,
              'type': 'credit',
            },
          },
          'expenseDB': <String, dynamic>{
            'expense': <String, dynamic>{
              'date': '2026-08-02',
              'category': 'Fuel',
              'amount': 40,
            },
          },
        },
      );

      LedgerProjection projection = LedgerProjection.fromState(
        state,
        month: 8,
        year: 2026,
      );
      expect(projection.dashboard.creditReceive, 100);
      expect(projection.dashboard.creditPay, 0);
      expect(projection.expenseMonthTotal, 40);

      expect(
        LedgerCodec.applyPath(
          state,
          'udharDB/debit',
          <String, dynamic>{
            'date': '2026-08-03',
            'name': 'Ali',
            'amount': 150,
            'type': 'debit',
          },
        ),
        isTrue,
      );
      projection = LedgerProjection.fromState(state, month: 8, year: 2026);
      expect(projection.dashboard.creditReceive, 0);
      expect(projection.dashboard.creditPay, 50);

      expect(
        LedgerCodec.applyPath(
          state,
          'expenseDB/expense',
          <String, dynamic>{
            'id': 'expense',
            'date': '2026-07-02',
            'category': 'Fuel',
            'amount': 40,
          },
        ),
        isTrue,
      );
      expect(LedgerCodec.applyPath(state, 'udharDB/debit', null), isTrue);
      projection = LedgerProjection.fromState(state, month: 8, year: 2026);
      expect(projection.dashboard.creditReceive, 100);
      expect(projection.dashboard.creditPay, 0);
      expect(projection.expenseMonthTotal, 0);
      expect(projection.expenseCategories.single.monthTotal, 0);
    });
  });
}
