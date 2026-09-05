import 'package:flutter_test/flutter_test.dart';
import 'package:voice_ludo_masti/game/ludo_engine.dart';

void main() {
  group('Ludo state-machine invariants', () {
    test('commitRoll is ignored unless a roll transaction is active', () {
      final engine = LudoEngine(playerCount: 2);

      engine.commitRoll(6);

      expect(engine.currentRoll, isNull);
      expect(engine.awaitingMove, isFalse);
      expect(engine.currentColor, LudoColor.red);
      expect(engine.canRoll, isTrue);
    });

    test('invalid token selection cannot mutate an awaiting move', () {
      final engine = LudoEngine(playerCount: 2);
      engine.beginRolling();
      engine.commitRoll(6);

      final before = engine.players.first.tokens
          .map((token) => token.progress)
          .toList(growable: false);
      final outcome = engine.moveToken(99);

      expect(outcome, isNull);
      expect(
        engine.players.first.tokens.map((token) => token.progress).toList(),
        before,
      );
      expect(engine.awaitingMove, isTrue);
      expect(engine.currentRoll, 6);
      expect(engine.currentColor, LudoColor.red);
    });

    test('restart clears an in-flight token choice atomically', () {
      final engine = LudoEngine(playerCount: 2);
      engine.beginRolling();
      engine.commitRoll(6);
      expect(engine.awaitingMove, isTrue);

      engine.reset(2);

      expect(engine.awaitingMove, isFalse);
      expect(engine.isRolling, isFalse);
      expect(engine.currentRoll, isNull);
      expect(engine.movableTokenIds, isEmpty);
      expect(engine.winnerOrder, isEmpty);
      expect(engine.turnNumber, 1);
      expect(engine.currentColor, LudoColor.red);
      expect(engine.canRoll, isTrue);
      for (final player in engine.players) {
        expect(player.tokens.every((token) => token.inYard), isTrue);
      }
    });

    test('a token in a home lane cannot capture a track token', () {
      final engine = LudoEngine(playerCount: 2);
      final red = engine.players.first;
      final yellow = engine.players.last;

      red.tokens[0].progress = 51;
      yellow.tokens[0].progress = 25;

      engine.beginRolling();
      engine.commitRoll(1);
      final outcome = engine.moveToken(0);

      expect(red.tokens[0].progress, 52);
      expect(outcome?.captures, 0);
      expect(yellow.tokens[0].progress, 25);
    });

    test('two-player winner atomically completes final ranking', () {
      final engine = LudoEngine(playerCount: 2);
      final red = engine.players.first;
      for (var index = 0; index < 3; index++) {
        red.tokens[index].progress = LudoEngine.finishProgress;
      }
      red.tokens[3].progress = 55;

      engine.beginRolling();
      engine.commitRoll(2);
      final outcome = engine.moveToken(3);

      expect(outcome?.finishedToken, isTrue);
      expect(engine.gameOver, isTrue);
      expect(engine.awaitingMove, isFalse);
      expect(engine.currentRoll, isNull);
      expect(engine.movableTokenIds, isEmpty);
      expect(
        engine.winnerOrder,
        <LudoColor>[LudoColor.red, LudoColor.yellow],
      );
      expect(engine.canRoll, isFalse);
    });

    test('finished players are never selected as the next active turn', () {
      final engine = LudoEngine(playerCount: 4);
      final green = engine.players[1];
      for (final token in green.tokens) {
        token.progress = LudoEngine.finishProgress;
      }
      engine.winnerOrder.add(LudoColor.green);

      engine.beginRolling();
      engine.commitRoll(5);

      expect(engine.currentColor, LudoColor.yellow);
      expect(engine.currentColor, isNot(LudoColor.green));
    });
  });
}
