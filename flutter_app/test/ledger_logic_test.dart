import 'package:flutter_test/flutter_test.dart';

import 'package:aarish_diary/firebase_sync.dart';

void main() {
  group('Firebase schema compatibility', () {
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
  });
}
