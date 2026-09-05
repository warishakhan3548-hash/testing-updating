import 'package:flutter_test/flutter_test.dart';
import 'package:voice_ludo_masti/services/voice_dice_controller.dart';

void main() {
  group('Low-confidence bounded dice grammar', () {
    test('precise dice-only commands survive quiet ASR confidence', () {
      expect(
        DiceVoiceIntentParser.parse(
          'छक्का',
          recognitionConfidence: 0.08,
        )?.value,
        6,
      );
      expect(
        DiceVoiceIntentParser.parse(
          'six',
          recognitionConfidence: 0.05,
        )?.value,
        6,
      );
      expect(
        DiceVoiceIntentParser.parse(
          'पाँच पाँच',
          recognitionConfidence: 0.10,
        )?.value,
        5,
      );
      expect(
        DiceVoiceIntentParser.parse(
          '४',
          recognitionConfidence: 0.01,
        )?.value,
        4,
      );
    });

    test('low-confidence short or noisy aliases still fail closed', () {
      expect(
        DiceVoiceIntentParser.parse(
          'छ',
          recognitionConfidence: 0.08,
        ),
        isNull,
      );
      expect(
        DiceVoiceIntentParser.parse(
          'सिक',
          recognitionConfidence: 0.08,
        ),
        isNull,
      );
      expect(
        DiceVoiceIntentParser.parse(
          'tin',
          recognitionConfidence: 0.08,
        ),
        isNull,
      );
      expect(
        DiceVoiceIntentParser.parse(
          'char',
          recognitionConfidence: 0.08,
        ),
        isNull,
      );
    });

    test('low-confidence contextual speech does not bypass the safety floor', () {
      expect(
        DiceVoiceIntentParser.parse(
          'give me six',
          recognitionConfidence: 0.08,
        ),
        isNull,
      );
      expect(
        DiceVoiceIntentParser.parse(
          'छक्का दे',
          recognitionConfidence: 0.08,
        ),
        isNull,
      );
    });

    test('conflicting exact numbers remain rejected regardless of confidence', () {
      expect(
        DiceVoiceIntentParser.parse(
          'six five',
          recognitionConfidence: 0.95,
        ),
        isNull,
      );
      expect(
        DiceVoiceIntentParser.parse(
          'छक्का पाँच',
          recognitionConfidence: 0.05,
        ),
        isNull,
      );
    });
  });
}
