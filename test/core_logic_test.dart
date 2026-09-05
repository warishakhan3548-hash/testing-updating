import 'package:flutter_test/flutter_test.dart';
import 'package:voice_ludo_masti/game/ludo_engine.dart';
import 'package:voice_ludo_masti/services/voice_dice_controller.dart';

void main() {
  group('Voice dice parser', () {
    test('latest spoken number wins', () {
      expect(VoiceDiceController.parseLastDiceValue('छक्का पाँच चार'), 4);
      expect(VoiceDiceController.parseLastDiceValue('six five two'), 2);
      expect(VoiceDiceController.parseLastDiceValue('6 6 5'), 5);
      expect(VoiceDiceController.parseLastDiceValue('पाँच फिर छक्का'), 6);
      expect(VoiceDiceController.parseLastDiceValue('चार बोलो फिर दो'), 2);
    });

    test('supports Hindi, Hinglish-style outputs, English and digits', () {
      expect(VoiceDiceController.parseLastDiceValue('एक'), 1);
      expect(VoiceDiceController.parseLastDiceValue('three'), 3);
      expect(VoiceDiceController.parseLastDiceValue('५'), 5);
      expect(VoiceDiceController.parseLastDiceValue('फाइव'), 5);
      expect(VoiceDiceController.parseLastDiceValue('फाईव'), 5);
      expect(VoiceDiceController.parseLastDiceValue('सिक्स'), 6);
      expect(VoiceDiceController.parseLastDiceValue('चक्का'), 6);
    });

    test('unrelated speech does not invent a dice value', () {
      expect(VoiceDiceController.parseLastDiceValue('आज गेम बहुत मजेदार है'), isNull);
      expect(VoiceDiceController.parseLastDiceValue('[unk]'), isNull);
      expect(VoiceDiceController.parseLastDiceValue('चलो भाई शुरू करो'), isNull);
    });

    test('Vosk alternatives payload is decoded correctly', () {
      final payload = VoiceDiceController.parseRecognitionPayload(
        '{"alternatives":[{"confidence":0.84,"text":"पाँच"}]}',
      );
      expect(payload.text, 'पाँच');
      expect(payload.confidence, closeTo(.84, .0001));
      expect(VoiceDiceController.parseLastDiceValue(payload.text), 5);
    });

    test('standard Vosk partial and final payloads are decoded correctly', () {
      expect(
        VoiceDiceController.parseRecognitionPayload('{"partial":"छक्का"}').text,
        'छक्का',
      );
      expect(
        VoiceDiceController.parseRecognitionPayload('{"text":"चार"}').text,
        'चार',
      );
    });

    test('fresh newer partial beats older stable command at roll boundary', () {
      final base = DateTime(2026, 9, 5, 12);
      final value = VoiceDiceController.resolveNewestDiceCommand(
        pendingValue: 6,
        pendingAt: base,
        candidateValue: 5,
        candidateAt: base.add(const Duration(milliseconds: 420)),
        now: base.add(const Duration(milliseconds: 500)),
      );
      expect(value, 5);
    });

    test('stale partial cannot replace a stable command', () {
      final base = DateTime(2026, 9, 5, 12);
      final value = VoiceDiceController.resolveNewestDiceCommand(
        pendingValue: 4,
        pendingAt: base.add(const Duration(seconds: 2)),
        candidateValue: 2,
        candidateAt: base,
        now: base.add(const Duration(seconds: 3)),
      );
      expect(value, 4);
    });
  });

  group('Ludo engine', () {
    test('invalid player counts fail fast in release-safe logic', () {
      expect(() => LudoEngine(playerCount: 1), throwsRangeError);
      expect(() => LudoEngine(playerCount: 5), throwsRangeError);
    });

    test('two-player game uses opposite red and yellow sides', () {
      final engine = LudoEngine(playerCount: 2);
      expect(
        engine.players.map((player) => player.color).toList(),
        <LudoColor>[LudoColor.red, LudoColor.yellow],
      );
    });

    test('yard token cannot move without a six and turn advances', () {
      final engine = LudoEngine(playerCount: 2);

      engine.beginRolling();
      engine.commitRoll(5);

      expect(engine.awaitingMove, isFalse);
      expect(engine.currentColor, LudoColor.yellow);
      expect(engine.canRoll, isTrue);
    });

    test('unlimited sixes keep granting turns without a three-six penalty', () {
      final engine = LudoEngine(playerCount: 2);

      for (var i = 0; i < 8; i++) {
        engine.beginRolling();
        engine.commitRoll(6);
        expect(engine.awaitingMove, isTrue);
        engine.moveToken(0);
        expect(engine.currentColor, LudoColor.red);
        expect(engine.gameOver, isFalse);
      }
    });

    test('one hundred consecutive no-move sixes never force a turn switch', () {
      final engine = LudoEngine(playerCount: 2);
      for (final token in engine.players.first.tokens) {
        token.progress = 56;
      }

      for (var i = 0; i < 100; i++) {
        engine.beginRolling();
        engine.commitRoll(6);
        expect(engine.awaitingMove, isFalse);
        expect(engine.currentColor, LudoColor.red);
        expect(engine.canRoll, isTrue);
        expect(engine.gameOver, isFalse);
      }
      expect(engine.lastEvent, contains('Roll again'));
    });

    test('capture sends opponent token back to yard and gives extra turn', () {
      final engine = LudoEngine(playerCount: 2);
      final red = engine.players.first;
      final yellow = engine.players.last;

      red.tokens[0].progress = 13;
      yellow.tokens[0].progress = 40;

      engine.beginRolling();
      engine.commitRoll(1);
      final outcome = engine.moveToken(0);

      expect(outcome?.captures, 1);
      expect(yellow.tokens[0].progress, -1);
      expect(engine.currentColor, LudoColor.red);
    });

    test('safe-star cells do not capture opponent tokens', () {
      final engine = LudoEngine(playerCount: 2);
      final red = engine.players.first;
      final yellow = engine.players.last;

      red.tokens[0].progress = 7;
      yellow.tokens[0].progress = 34;

      engine.beginRolling();
      engine.commitRoll(1);
      final outcome = engine.moveToken(0);

      expect(outcome?.captures, 0);
      expect(yellow.tokens[0].progress, 34);
      expect(engine.currentColor, LudoColor.yellow);
    });

    test('exact roll is required to finish', () {
      final engine = LudoEngine(playerCount: 2);
      engine.players.first.tokens[0].progress = 55;

      engine.beginRolling();
      engine.commitRoll(3);
      expect(engine.awaitingMove, isFalse);
      expect(engine.players.first.tokens[0].progress, 55);
      expect(engine.currentColor, LudoColor.yellow);
    });

    test('exact roll reaches home', () {
      final engine = LudoEngine(playerCount: 2);
      engine.players.first.tokens[0].progress = 55;

      engine.beginRolling();
      engine.commitRoll(2);
      expect(engine.awaitingMove, isTrue);
      engine.moveToken(0);
      expect(engine.players.first.tokens[0].finished, isTrue);
    });

    test('finished player is ranked and skipped on following turns', () {
      final engine = LudoEngine(playerCount: 3);
      final red = engine.players.first;
      for (var i = 0; i < 3; i++) {
        red.tokens[i].progress = LudoEngine.finishProgress;
      }
      red.tokens[3].progress = 55;

      engine.beginRolling();
      engine.commitRoll(2);
      engine.moveToken(3);

      expect(red.finished, isTrue);
      expect(engine.winnerOrder, contains(LudoColor.red));
      expect(engine.currentColor, LudoColor.green);
    });
  });
}
