import 'package:flutter_test/flutter_test.dart';
import 'package:voice_ludo_masti/services/voice_dice_controller.dart';

void main() {
  group('Bounded six-command voice grammar', () {
    test('required Hindi English and digit commands resolve deterministically', () {
      expect(VoiceDiceController.parseLastDiceValue('एक'), 1);
      expect(VoiceDiceController.parseLastDiceValue('two'), 2);
      expect(VoiceDiceController.parseLastDiceValue('तीन'), 3);
      expect(VoiceDiceController.parseLastDiceValue('four'), 4);
      expect(VoiceDiceController.parseLastDiceValue('पाँच'), 5);
      expect(VoiceDiceController.parseLastDiceValue('छक्का'), 6);
      expect(VoiceDiceController.parseLastDiceValue('६'), 6);
    });

    test('common short and Hinglish ASR variants stay in the tiny vocabulary', () {
      expect(VoiceDiceController.parseLastDiceValue('छक्क'), 6);
      expect(VoiceDiceController.parseLastDiceValue('छक'), 6);
      expect(VoiceDiceController.parseLastDiceValue('शक्का'), 6);
      expect(VoiceDiceController.parseLastDiceValue('chhakka'), 6);
      expect(VoiceDiceController.parseLastDiceValue('फौर'), 4);
      expect(VoiceDiceController.parseLastDiceValue('पान्च'), 5);
    });

    test('repeated copies of one value are accepted for fast partials', () {
      expect(DiceVoiceIntentParser.isDiceOnlyPhrase('छक्का छक्का'), isTrue);
      expect(DiceVoiceIntentParser.isDiceOnlyPhrase('six six'), isTrue);
      expect(DiceVoiceIntentParser.isDiceOnlyPhrase('पाँच पाँच'), isTrue);
      expect(VoiceDiceController.parseLastDiceValue('छक्का छक्का'), 6);
    });

    test('mixed dice values are ambiguous and never guessed', () {
      expect(DiceVoiceIntentParser.isDiceOnlyPhrase('six five'), isFalse);
      expect(DiceVoiceIntentParser.isDiceOnlyPhrase('छक्का पाँच'), isFalse);
      expect(VoiceDiceController.parseLastDiceValue('six five'), isNull);
      expect(VoiceDiceController.parseLastDiceValue('छक्का पाँच'), isNull);
    });

    test('command phrases work while unrelated conversation is rejected', () {
      expect(VoiceDiceController.parseLastDiceValue('छक्का दे दो'), 6);
      expect(VoiceDiceController.parseLastDiceValue('give me six'), 6);
      expect(VoiceDiceController.parseLastDiceValue('चार आना चाहिए'), 4);
      expect(VoiceDiceController.parseLastDiceValue('we have six players'), isNull);
      expect(VoiceDiceController.parseLastDiceValue('six o clock'), isNull);
    });
  });
}
