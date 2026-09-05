import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:voice_ludo_masti/services/voice_dice_controller.dart';

void main() {
  group('Play-crash resilience', () {
    test('a stable voice command expires before a later unrelated roll', () {
      final heardAt = DateTime(2026, 9, 5, 12);

      final value = VoiceDiceController.resolveNewestDiceCommand(
        pendingValue: 6,
        pendingAt: heardAt,
        candidateValue: null,
        candidateAt: null,
        now: heardAt.add(const Duration(seconds: 2)),
      );

      expect(value, isNull);
    });

    test('future-dated recognition cannot force a dice result', () {
      final now = DateTime(2026, 9, 5, 12);

      final value = VoiceDiceController.resolveNewestDiceCommand(
        pendingValue: 4,
        pendingAt: now.add(const Duration(milliseconds: 1)),
        candidateValue: null,
        candidateAt: null,
        now: now,
      );

      expect(value, isNull);
    });

    test('native Hindi model validation covers the complete critical graph', () {
      final activity = File(
        'android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt',
      ).readAsStringSync();

      for (final required in <String>[
        'am/final.mdl',
        'conf/mfcc.conf',
        'conf/model.conf',
        'graph/Gr.fst',
        'graph/HCLr.fst',
        'graph/disambig_tid.int',
        'graph/phones/word_boundary.int',
        'ivector/final.dubm',
        'ivector/final.ie',
        'ivector/final.mat',
        'ivector/global_cmvn.stats',
        'ivector/online_cmvn.conf',
        'ivector/splice.conf',
      ]) {
        expect(activity, contains('"$required"'));
      }

      expect(activity, contains('MIN_EXTRACTED_MODEL_BYTES'));
      expect(activity, contains('MAX_EXTRACTED_MODEL_BYTES'));
      expect(activity, contains('MIN_VOSK_HEADROOM_MB'));
      expect(activity, contains('memoryInfo.lowMemory'));
      expect(activity, contains('MODEL_MARKER_FILE'));
      expect(activity, contains('MODEL_INSTALL_SCHEMA'));
      expect(activity, contains('hasCompleteModelStructure'));
    });

    test('voice controller reuses one Android Vosk model across game entries', () {
      final controller =
          File('lib/services/voice_dice_controller.dart').readAsStringSync();

      expect(controller, contains('static Model? _sharedModel;'));
      expect(controller, contains('static Future<Model>? _sharedModelFuture;'));
      expect(controller, contains('_obtainSharedModel'));
      expect(controller, contains('static Future<void> _globalServiceRelease'));
      expect(
        controller,
        isNot(
          contains(
            'await _recognizer?.dispose();\n'
            '    } catch (_) {}\n'
            '    try {\n'
            '      _model?.dispose();',
          ),
        ),
      );
    });
  });
}
