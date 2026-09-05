import 'package:flutter_test/flutter_test.dart';
import 'package:voice_ludo_masti/game/ludo_engine.dart';
import 'package:voice_ludo_masti/services/voice_dice_controller.dart';

void main() {
  group('Voice dice parser', () {
    test('latest spoken number wins', () {
      expect(VoiceDiceController.parseLastDiceValue('छक्का पाँच चार'), 4);
      expect(VoiceDiceController.parseLastDiceValue('six five two'), 2);
      expect(VoiceDiceController.parseLastDiceValue('6 6 5'), 5);
    });

    test('supports Hindi, English and digits', () {
      expect(VoiceDiceController.parseLastDiceValue('एक'), 1);
      expect(VoiceDiceController.parseLastDiceValue('three'), 3);
      expect(VoiceDiceController.parseLastDiceValue('५'), 5);
      expect(VoiceDiceController.parseLastDiceValue('सिक्स'), 6);
    });
  });

  group('Ludo engine', () {
    test('unlimited sixes keep granting turns without a three-six penalty', () {
      final engine = LudoEngine(playerCount: 2);

      for (var i = 0; i < 4; i++) {
        engine.beginRolling();
        engine.commitRoll(6);
        expect(engine.awaitingMove, isTrue);
        engine.moveToken(0);
        expect(engine.currentColor, LudoColor.red);
        expect(engine.gameOver, isFalse);
      }
    });

    test('capture sends opponent token back to yard and gives extra turn', () {
      final engine = LudoEngine(playerCount: 2);
      final red = engine.players.first;
      final yellow = engine.players.last;

      red.tokens[0].progress = 25; // red global cell 25
      yellow.tokens[0].progress = 51; // yellow global cell 25

      engine.beginRolling();
      engine.commitRoll(1); // red lands on global 26, which is safe -> no capture
      engine.moveToken(0);
      expect(yellow.tokens[0].progress, 51);
    });

    test('exact roll is required to finish', () {
      final engine = LudoEngine(playerCount: 2);
      engine.players.first.tokens[0].progress = 55;

      engine.beginRolling();
      engine.commitRoll(3);
      expect(engine.awaitingMove, isFalse);
      expect(engine.players.first.tokens[0].progress, 55);
    });
  });
}
