import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

import 'package:aarish_diary/ai_bridge.dart';
import 'package:aarish_diary/firebase_sync.dart';

void main() {
  group('External AI package', () {
    test('exports every ledger module without sync metadata', () {
      final AiBridgePackage package = AiBridgeProtocol.buildPackage(
        state: _completeState(),
        generatedAt: DateTime.utc(2026, 8, 30, 9, 15),
        snapshotId: 'aip_snapshot_1',
      );

      expect(package.fileName, 'AarishAI_Database_State_2026-08-30.txt');
      expect(package.recordCount, 6);
      for (final String root in <String>[
        'milkDB',
        'udharDB',
        'expenseDB',
        'salaryDB',
        'diaryDB',
        'projectDB',
      ]) {
        expect(package.fileContent, contains('"$root"'));
      }
      expect(package.fileContent, contains('aip_snapshot_1'));
      expect(package.fileContent, contains('STATE_FINGERPRINT'));
      expect(package.fileContent, isNot(contains('firebase-secret')));
      expect(package.fileContent, isNot(contains('_syncMeta')));
    });

    test('prompt preserves contextual conversation and clarification rules',
        () {
      final AiBridgePackage package = AiBridgeProtocol.buildPackage(
        state: LedgerCodec.emptyState(),
        generatedAt: DateTime.utc(2026, 8, 30),
        snapshotId: 'aip_context',
      );

      expect(package.prompt, contains('does not need to say "JSON"'));
      expect(package.prompt, contains('whole conversation'));
      expect(package.prompt, contains('every still-pending real ledger entry'));
      expect(package.prompt, contains('ask one short focused question'));
      expect(package.prompt, contains('from whom, morning or evening'));
      expect(package.prompt, contains('groups of 25'));
      expect(package.prompt, contains('"snapshotId": "aip_context"'));
    });

    test('state fingerprint is stable across map insertion order', () {
      final Map<String, dynamic> first = LedgerCodec.emptyState();
      first['expenseDB'] = <String, dynamic>{
        'exp_1': <String, dynamic>{
          'id': 'exp_1',
          'date': '2026-08-30',
          'category': 'Fuel',
          'amount': 100,
        },
      };
      final Map<String, dynamic> second = <String, dynamic>{
        'projectDB': <String, dynamic>{},
        'diaryDB': <dynamic>[],
        'salaryDB': <String, dynamic>{},
        'expenseDB': <String, dynamic>{
          'exp_1': <String, dynamic>{
            'amount': 100,
            'category': 'Fuel',
            'date': '2026-08-30',
            'id': 'exp_1',
          },
        },
        'udharDB': <dynamic>[],
        'milkDB': <String, dynamic>{},
      };

      expect(
        AiBridgeProtocol.stateFingerprint(first),
        AiBridgeProtocol.stateFingerprint(second),
      );
    });
  });

  group('AI envelope parser', () {
    test('extracts fenced JSON surrounded by normal AI prose', () {
      final AiBridgeEnvelope envelope = AiBridgeProtocol.parseEnvelope('''
Here is the reviewed result:
```json
{
  "protocol": "aarish.ai.bridge.v1",
  "snapshotId": "aip_1",
  "stateFingerprint": "state_1",
  "reply": "Ho gaya",
  "actions": [
    {
      "path": "expenseDB/__NEW__",
      "data": {
        "id": "__NEW__",
        "date": "2026-08-30",
        "category": "Fuel",
        "amount": 500
      }
    }
  ]
}
```
''');

      expect(envelope.protocol, AiBridgeProtocol.version);
      expect(envelope.snapshotId, 'aip_1');
      expect(envelope.actions, hasLength(1));
      expect(envelope.actions.single['path'], 'expenseDB/__NEW__');
      expect(envelope.envelopeFingerprint, hasLength(64));
    });

    test('canonical envelope fingerprint ignores object key order', () {
      final AiBridgeEnvelope first = AiBridgeProtocol.parseEnvelope(
        '{"reply":"ok","actions":[]}',
      );
      final AiBridgeEnvelope second = AiBridgeProtocol.parseEnvelope(
        '{"actions":[],"reply":"ok"}',
      );

      expect(first.envelopeFingerprint, second.envelopeFingerprint);
    });

    test('uses the final complete JSON object when prose contains an example',
        () {
      final AiBridgeEnvelope envelope = AiBridgeProtocol.parseEnvelope(
        'Example: {"reply":"example","actions":[]}\n'
        'Final: {"reply":"final","actions":[]}',
      );

      expect(envelope.reply, 'final');
    });

    test('rejects more than the reviewed-job limit', () {
      final String response = jsonEncode(<String, dynamic>{
        'actions': List<Map<String, dynamic>>.generate(
          AiBridgeProtocol.maxActionCount + 1,
          (int index) => <String, dynamic>{
            'path': 'expenseDB/__NEW__',
            'data': <String, dynamic>{
              'id': '__NEW__',
              'date': '2026-08-30',
              'category': 'Item $index',
              'amount': index + 1,
            },
          },
        ),
      });

      expect(
        () => AiBridgeProtocol.parseEnvelope(response),
        throwsA(isA<AiBridgeException>()),
      );
    });
  });

  group('AI action validation and batching', () {
    test('normalizes 100 entries into four unique 25-action chunks', () {
      int sequence = 0;
      final AiActionPlan plan = AiBridgeProtocol.validateAndNormalize(
        rawActions: List<Map<String, dynamic>>.generate(
          100,
          (int index) => <String, dynamic>{
            'path': 'udharDB/__NEW__',
            'data': <String, dynamic>{
              'id': '__NEW__',
              'date': '2026-08-30',
              'name': 'Person $index',
              'amount': index + 1,
              'type': 'credit',
            },
          },
        ),
        state: LedgerCodec.emptyState(),
        newId: (String prefix) => '${prefix}_${sequence++}',
      );

      expect(plan.actions, hasLength(100));
      expect(plan.batchCount, 4);
      expect(plan.chunks.map((List<Map<String, dynamic>> c) => c.length),
          <int>[25, 25, 25, 25]);
      expect(
        plan.actions
            .map((Map<String, dynamic> action) => action['path'])
            .toSet(),
        hasLength(100),
      );
    });

    test('accepts AI-stripped NEW aliases for safe record creation', () {
      int sequence = 0;
      final AiActionPlan plan = AiBridgeProtocol.validateAndNormalize(
        rawActions: <Map<String, dynamic>>[
          <String, dynamic>{
            'path': 'milkDB/Aaris',
            'data': <String, dynamic>{
              'rate': 80,
              'type': 'lene_wala',
              'records': <Map<String, dynamic>>[
                <String, dynamic>{
                  'id': 'NEW',
                  'date': '2026-08-30',
                  'morning': 5,
                  'evening': 0,
                  'flow': 'taken',
                },
              ],
            },
          },
          <String, dynamic>{
            'path': 'udharDB/NEW',
            'data': <String, dynamic>{
              'id': 'NEW',
              'date': '2026-08-30',
              'name': 'Kollu',
              'amount': 400,
              'type': 'credit',
            },
          },
        ],
        state: LedgerCodec.emptyState(),
        newId: (String prefix) => '${prefix}_${sequence++}',
      );

      expect(plan.actions, hasLength(2));
      final Map<String, dynamic> milkProfile =
          LedgerCodec.objectMap(plan.actions.first['data']);
      expect(
        LedgerCodec.canonicalList(milkProfile['records']).single['id'],
        'mlk_0',
      );
      expect(plan.actions.last['path'], 'udharDB/udh_1');
      expect(
        LedgerCodec.objectMap(plan.actions.last['data'])['id'],
        'udh_1',
      );
    });

    test('an existing record literally named NEW is edited, not duplicated',
        () {
      final Map<String, dynamic> state = LedgerCodec.emptyState();
      state['udharDB'] = <String, dynamic>{
        'NEW': <String, dynamic>{
          'id': 'NEW',
          'date': '2026-08-29',
          'name': 'Existing',
          'amount': 100,
          'type': 'credit',
        },
      };
      final AiActionPlan plan = AiBridgeProtocol.validateAndNormalize(
        rawActions: <Map<String, dynamic>>[
          <String, dynamic>{
            'path': 'udharDB/NEW',
            'data': <String, dynamic>{'amount': 150},
          },
        ],
        state: state,
        newId: (String prefix) => fail('Must not create a new ID.'),
      );

      expect(plan.actions.single['path'], 'udharDB/NEW');
      expect(
        LedgerCodec.objectMap(plan.actions.single['data'])['amount'],
        150,
      );
    });

    test('rejects a whole-root overwrite and a duplicate target', () {
      expect(
        () => AiBridgeProtocol.validateAndNormalize(
          rawActions: <Map<String, dynamic>>[
            <String, dynamic>{'path': 'expenseDB', 'data': <dynamic>[]},
          ],
          state: _completeState(),
          newId: (String prefix) => '${prefix}_new',
        ),
        throwsA(isA<AiBridgeException>()),
      );

      expect(
        () => AiBridgeProtocol.validateAndNormalize(
          rawActions: <Map<String, dynamic>>[
            <String, dynamic>{
              'path': 'expenseDB/exp_1',
              'data': <String, dynamic>{'amount': 200},
            },
            <String, dynamic>{
              'path': 'expenseDB/exp_1',
              'data': <String, dynamic>{'amount': 300},
            },
          ],
          state: _completeState(),
          newId: (String prefix) => '${prefix}_new',
        ),
        throwsA(isA<AiBridgeException>()),
      );
    });

    test('rejects incomplete milk data instead of inventing it', () {
      expect(
        () => AiBridgeProtocol.validateAndNormalize(
          rawActions: <Map<String, dynamic>>[
            <String, dynamic>{
              'path': 'milkDB/Kabir/records/__NEW__',
              'data': <String, dynamic>{
                'id': '__NEW__',
                'date': '2026-08-30',
                'morning': 5,
                'evening': 0,
              },
            },
          ],
          state: _completeState(),
          newId: (String prefix) => '${prefix}_new',
        ),
        throwsA(isA<AiBridgeException>()),
      );
    });

    test('preserves existing profile records during metadata edits', () {
      final AiActionPlan plan = AiBridgeProtocol.validateAndNormalize(
        rawActions: <Map<String, dynamic>>[
          <String, dynamic>{
            'path': 'milkDB/Kabir',
            'data': <String, dynamic>{
              'rate': 65,
              'type': 'lene_wala',
            },
          },
        ],
        state: _completeState(),
        newId: (String prefix) => '${prefix}_new',
      );

      final Map<String, dynamic> profile = LedgerCodec.objectMap(
        plan.actions.single['data'],
      );
      expect(profile['rate'], 65);
      expect(profile['canonicalNameV18'], 'kabir');
      expect(LedgerCodec.canonicalList(profile['records']), hasLength(1));
    });

    test('new grouped profile cannot hide many writes in one action', () {
      expect(
        () => AiBridgeProtocol.validateAndNormalize(
          rawActions: <Map<String, dynamic>>[
            <String, dynamic>{
              'path': 'projectDB/Bulk',
              'data': <String, dynamic>{
                'records': <Map<String, dynamic>>[
                  _businessRecord('__NEW__', 1),
                  _businessRecord('__NEW__', 2),
                ],
              },
            },
          ],
          state: LedgerCodec.emptyState(),
          newId: (String prefix) => '${prefix}_new',
        ),
        throwsA(isA<AiBridgeException>()),
      );
    });
  });

  test('persisted batch keeps account, progress and conflict fingerprint', () {
    final AiBatchJob original = AiBatchJob(
      id: 'batch_1',
      ownerUid: 'user_a',
      fingerprint: 'response_hash',
      expectedStateFingerprint: 'state_hash',
      actions: List<Map<String, dynamic>>.generate(
        30,
        (int index) => <String, dynamic>{
          'path': 'expenseDB/exp_$index',
          'data': <String, dynamic>{'id': 'exp_$index'},
        },
      ),
      nextIndex: 25,
      nextRunAtMillis: 2000,
      createdAtMillis: 1000,
      snapshotId: 'aip_1',
    );

    final AiBatchJob? restored = AiBatchJob.tryDecode(
      jsonEncode(original.toJson()),
    );

    expect(restored, isNotNull);
    expect(restored!.ownerUid, 'user_a');
    expect(restored.completed, 25);
    expect(restored.remaining, 5);
    expect(restored.nextChunkSize, 5);
    expect(restored.expectedStateFingerprint, 'state_hash');
    expect(
      restored
          .copyWith(
            paused: true,
            lastError:
                'Ledger changed after approval. Cancel and review again.',
          )
          .hasStateConflict,
      isTrue,
    );
  });

  test('AI setup exposes native external-AI share and review controls', () {
    final String source = File('lib/main.dart').readAsStringSync();

    expect(source, contains("'Connect with Other AI'"));
    expect(source, contains("'Use any AI without an API key'"));
    expect(source, contains("'OR'"));
    expect(source, contains('SharePlus.instance.share('));
    expect(source, contains("mimeType: 'text/plain'"));
    expect(source, contains("'Paste & Review'"));
    expect(source, contains("'Apply All'"));
    expect(source, contains("'Cancel'"));
  });
}

Map<String, dynamic> _completeState() => LedgerCodec.normalizeState(
      <String, dynamic>{
        '_syncMeta': <String, dynamic>{'uid': 'firebase-secret'},
        'milkDB': <String, dynamic>{
          'Kabir': <String, dynamic>{
            'rate': 60,
            'type': 'lene_wala',
            'canonicalNameV18': 'kabir',
            'records': <String, dynamic>{
              'mlk_1': <String, dynamic>{
                'id': 'mlk_1',
                'date': '2026-08-29',
                'morning': 5,
                'evening': 0,
                'flow': 'taken',
                'type': 'taken',
              },
            },
          },
        },
        'udharDB': <String, dynamic>{
          'udh_1': <String, dynamic>{
            'id': 'udh_1',
            'date': '2026-08-29',
            'name': 'Sameer',
            'amount': 500,
            'type': 'credit',
          },
        },
        'expenseDB': <String, dynamic>{
          'exp_1': <String, dynamic>{
            'id': 'exp_1',
            'date': '2026-08-29',
            'category': 'Fuel',
            'amount': 100,
          },
        },
        'salaryDB': <String, dynamic>{
          'Worker': <String, dynamic>{
            'company': 'Dairy',
            'type': 'dene_wala',
            'records': <String, dynamic>{
              'sal_1': <String, dynamic>{
                'id': 'sal_1',
                'date': '2026-08-29',
                'amount': 1000,
              },
            },
          },
        },
        'diaryDB': <String, dynamic>{
          'dia_1': <String, dynamic>{
            'id': 'dia_1',
            'date': '2026-08-29',
            'title': 'Reminder',
            'content': 'Call supplier',
            'updated': 1,
          },
        },
        'projectDB': <String, dynamic>{
          'Shop': <String, dynamic>{
            'records': <String, dynamic>{
              'prj_1': _businessRecord('prj_1', 500),
            },
          },
        },
      },
    );

Map<String, dynamic> _businessRecord(String id, num amount) =>
    <String, dynamic>{
      'id': id,
      'date': '2026-08-29',
      'title': 'Sale',
      'amount': amount,
      'color': 'green',
    };
