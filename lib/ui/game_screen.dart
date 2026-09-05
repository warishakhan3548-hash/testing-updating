import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../game/ludo_engine.dart';
import '../services/voice_dice_controller.dart';
import 'ludo_board.dart';

class GameScreen extends StatefulWidget {
  const GameScreen({super.key, required this.playerCount});

  final int playerCount;

  @override
  State<GameScreen> createState() => _GameScreenState();
}

class _GameScreenState extends State<GameScreen>
    with SingleTickerProviderStateMixin {
  late final LudoEngine _engine;
  late final VoiceDiceController _voice;
  late final AnimationController _diceController;
  final math.Random _random = math.Random();

  int _targetDice = 1;
  int _animationSeed = 1;
  bool _winnerDialogShown = false;

  @override
  void initState() {
    super.initState();
    _engine = LudoEngine(playerCount: widget.playerCount);
    _voice = VoiceDiceController();
    _diceController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 780),
    );
    _voice.initialize();
  }

  @override
  void dispose() {
    _diceController.dispose();
    _engine.dispose();
    _voice.dispose();
    super.dispose();
  }

  Future<void> _rollDice() async {
    if (!_engine.canRoll) return;

    final forcedValue = await _voice.suspendForRoll();
    if (!mounted || !_engine.canRoll) {
      await _voice.resumeAfterRoll();
      return;
    }

    final target = forcedValue ?? (_random.nextInt(6) + 1);
    _targetDice = target;
    _animationSeed = _random.nextInt(5000);
    _engine.beginRolling();
    HapticFeedback.selectionClick();

    try {
      await _diceController.forward(from: 0);
      if (!mounted) return;
      _engine.commitRoll(target);
      HapticFeedback.mediumImpact();

      // Keep recognition suspended while the current move is unresolved.
      // Speech during token selection must not leak into the next player's roll.
      if (!_engine.awaitingMove) {
        await _voice.resumeAfterRoll();
      }
    } catch (_) {
      _engine.cancelRolling();
      await _voice.resumeAfterRoll();
    }
  }

  Future<void> _moveToken(int tokenId) async {
    final outcome = _engine.moveToken(tokenId);
    if (outcome == null) return;

    if (outcome.captures > 0) {
      HapticFeedback.heavyImpact();
    } else {
      HapticFeedback.lightImpact();
    }

    await Future<void>.delayed(const Duration(milliseconds: 180));
    if (!mounted) return;

    if (_engine.gameOver) {
      _showWinnerDialog();
    } else {
      await _voice.resumeAfterRoll();
    }
  }

  void _showWinnerDialog() {
    if (_winnerDialogShown || !mounted) return;
    _winnerDialogShown = true;
    final ranking = _engine.winnerOrder;

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      showDialog<void>(
        context: context,
        barrierDismissible: false,
        builder: (dialogContext) {
          return AlertDialog(
            icon: const Text('🏆', style: TextStyle(fontSize: 54)),
            title: Text('${ranking.first.label} wins!'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  'Final ranking',
                  style: TextStyle(fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 12),
                for (var i = 0; i < ranking.length; i++)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Row(
                      children: [
                        Text(i == 0
                            ? '🥇'
                            : i == 1
                                ? '🥈'
                                : i == 2
                                    ? '🥉'
                                    : '🏁'),
                        const SizedBox(width: 10),
                        Container(
                          width: 14,
                          height: 14,
                          decoration: BoxDecoration(
                            color: _playerColor(ranking[i]),
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          ranking[i].label,
                          style: const TextStyle(fontWeight: FontWeight.w800),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () {
                  Navigator.of(dialogContext).pop();
                  Navigator.of(context).pop();
                },
                child: const Text('EXIT'),
              ),
              FilledButton(
                onPressed: () {
                  Navigator.of(dialogContext).pop();
                  setState(() {
                    _winnerDialogShown = false;
                    _targetDice = 1;
                  });
                  _engine.reset(widget.playerCount);
                  _voice.clearPending();
                  _voice.resumeAfterRoll();
                },
                child: const Text('PLAY AGAIN'),
              ),
            ],
          );
        },
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _engine,
      builder: (context, _) {
        return AnimatedBuilder(
          animation: _voice,
          builder: (context, _) {
            return Scaffold(
              appBar: AppBar(
                title: const Text(
                  'Voice Ludo Masti',
                  style: TextStyle(fontWeight: FontWeight.w900),
                ),
                centerTitle: true,
                actions: [
                  IconButton(
                    tooltip: 'Restart game',
                    onPressed:
                        _engine.isRolling ? null : () => _confirmRestart(context),
                    icon: const Icon(Icons.refresh_rounded),
                  ),
                ],
              ),
              body: SafeArea(
                top: false,
                child: LayoutBuilder(
                  builder: (context, constraints) {
                    final boardSize = math.min(
                      constraints.maxWidth - 24,
                      560.0,
                    );
                    return SingleChildScrollView(
                      padding: const EdgeInsets.fromLTRB(12, 8, 12, 28),
                      child: Center(
                        child: ConstrainedBox(
                          constraints: const BoxConstraints(maxWidth: 620),
                          child: Column(
                            children: [
                              _buildTurnHeader(context),
                              const SizedBox(height: 10),
                              SizedBox(
                                width: boardSize,
                                height: boardSize,
                                child: LudoBoard(
                                  engine: _engine,
                                  onTokenTap: _moveToken,
                                ),
                              ),
                              const SizedBox(height: 14),
                              _buildPlayersStrip(context),
                              const SizedBox(height: 12),
                              _buildVoicePanel(context),
                              const SizedBox(height: 12),
                              _buildDicePanel(context),
                            ],
                          ),
                        ),
                      ),
                    );
                  },
                ),
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildTurnHeader(BuildContext context) {
    final color = _playerColor(_engine.currentColor);
    return AnimatedContainer(
      duration: const Duration(milliseconds: 250),
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: .10),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: color.withValues(alpha: .28)),
      ),
      child: Row(
        children: [
          Container(
            width: 14,
            height: 14,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${_engine.currentColor.label} • Turn ${_engine.turnNumber}',
                  style: const TextStyle(fontWeight: FontWeight.w900),
                ),
                const SizedBox(height: 2),
                Text(
                  _engine.lastEvent,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 12.5,
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          ),
          if (_engine.currentRoll != null)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 6),
              decoration: BoxDecoration(
                color: color,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                '${_engine.currentRoll}',
                style: TextStyle(
                  color: _engine.currentColor == LudoColor.yellow
                      ? Colors.black87
                      : Colors.white,
                  fontWeight: FontWeight.w900,
                  fontSize: 18,
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildPlayersStrip(BuildContext context) {
    return SizedBox(
      height: 58,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: _engine.players.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final player = _engine.players[index];
          final active = index == _engine.currentPlayerIndex && !_engine.gameOver;
          final color = _playerColor(player.color);
          final homeCount = player.tokens.where((t) => t.finished).length;
          return AnimatedContainer(
            duration: const Duration(milliseconds: 220),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: active ? color.withValues(alpha: .13) : Colors.white,
              borderRadius: BorderRadius.circular(15),
              border: Border.all(
                color: active ? color : Colors.black.withValues(alpha: .08),
                width: active ? 1.5 : 1,
              ),
            ),
            child: Row(
              children: [
                Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(color: color, shape: BoxShape.circle),
                ),
                const SizedBox(width: 7),
                Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      player.color.label,
                      style: const TextStyle(fontWeight: FontWeight.w800),
                    ),
                    Text(
                      '$homeCount/4 home',
                      style: TextStyle(
                        fontSize: 11,
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildVoicePanel(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final pending = _voice.pendingValue;
    final status = !_voice.initialized
        ? 'Starting voice…'
        : !_voice.available
            ? 'Voice unavailable'
            : !_voice.enabled
                ? 'Voice off'
                : _voice.listening
                    ? 'Listening… बोलो 1 से 6'
                    : 'Voice restarting…';

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            scheme.primaryContainer.withValues(alpha: .8),
            scheme.secondaryContainer.withValues(alpha: .45),
          ],
        ),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        children: [
          Material(
            color: _voice.enabled && _voice.available
                ? scheme.primary
                : scheme.surfaceContainerHighest,
            shape: const CircleBorder(),
            child: InkWell(
              customBorder: const CircleBorder(),
              onTap: () => _voice.setEnabled(!_voice.enabled),
              child: Padding(
                padding: const EdgeInsets.all(13),
                child: Icon(
                  _voice.enabled ? Icons.mic_rounded : Icons.mic_off_rounded,
                  color: _voice.enabled && _voice.available
                      ? scheme.onPrimary
                      : scheme.onSurfaceVariant,
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(status, style: const TextStyle(fontWeight: FontWeight.w900)),
                const SizedBox(height: 3),
                Text(
                  _voice.errorMessage ??
                      (_voice.lastHeard.isEmpty
                          ? 'Hindi/English: एक, दो, तीन… / one, two, three…'
                          : 'Heard: “${_voice.lastHeard}”'),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 11.5,
                    color: scheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          AnimatedContainer(
            duration: const Duration(milliseconds: 180),
            width: 54,
            height: 54,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: pending == null ? Colors.white70 : scheme.primary,
              borderRadius: BorderRadius.circular(16),
              boxShadow: pending == null
                  ? null
                  : [
                      BoxShadow(
                        color: scheme.primary.withValues(alpha: .28),
                        blurRadius: 12,
                      ),
                    ],
            ),
            child: Text(
              pending?.toString() ?? '?',
              style: TextStyle(
                fontSize: 25,
                fontWeight: FontWeight.w900,
                color: pending == null
                    ? scheme.onSurfaceVariant
                    : scheme.onPrimary,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDicePanel(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final canRoll = _engine.canRoll;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: Colors.black.withValues(alpha: .06)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: .05),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Row(
        children: [
          AnimatedBuilder(
            animation: _diceController,
            builder: (context, child) {
              final t = _diceController.value;
              final displayValue = _engine.isRolling && t < .9
                  ? ((_animationSeed + (t * 41).floor()) % 6) + 1
                  : (_engine.currentRoll ?? _targetDice);
              final angle = _engine.isRolling ? t * math.pi * 5 : 0.0;
              return Transform.rotate(
                angle: angle,
                child: _DiceFace(value: displayValue),
              );
            },
          ),
          const SizedBox(width: 15),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _engine.awaitingMove
                      ? 'Choose your token'
                      : _voice.pendingValue != null
                          ? 'Voice locked: ${_voice.pendingValue}'
                          : 'Normal random roll',
                  style: const TextStyle(
                    fontWeight: FontWeight.w900,
                    fontSize: 15,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  _engine.awaitingMove
                      ? 'Tap any glowing token on the board.'
                      : _voice.pendingValue != null
                          ? 'Tap roll — ${_voice.pendingValue} will come.'
                          : 'Say a number first if you want to control the dice.',
                  style: TextStyle(
                    fontSize: 11.5,
                    color: scheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 10),
          SizedBox(
            height: 52,
            child: FilledButton.icon(
              onPressed: canRoll ? _rollDice : null,
              icon: _engine.isRolling
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2.2),
                    )
                  : const Icon(Icons.casino_rounded),
              label: Text(_engine.isRolling ? 'ROLLING' : 'ROLL'),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _confirmRestart(BuildContext context) async {
    final restart = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Restart game?'),
        content: const Text(
          'All token positions and the current ranking will reset.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('CANCEL'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('RESTART'),
          ),
        ],
      ),
    );
    if (restart != true || !mounted) return;
    _engine.reset(widget.playerCount);
    _voice.clearPending();
    await _voice.resumeAfterRoll();
  }

  Color _playerColor(LudoColor color) => switch (color) {
        LudoColor.red => const Color(0xFFE84343),
        LudoColor.green => const Color(0xFF2CB76F),
        LudoColor.yellow => const Color(0xFFF4C542),
        LudoColor.blue => const Color(0xFF3978E8),
      };
}

class _DiceFace extends StatelessWidget {
  const _DiceFace({required this.value});

  final int value;

  @override
  Widget build(BuildContext context) {
    const positions = <Alignment>[
      Alignment(-.58, -.58),
      Alignment(0, -.58),
      Alignment(.58, -.58),
      Alignment(-.58, 0),
      Alignment.center,
      Alignment(.58, 0),
      Alignment(-.58, .58),
      Alignment(0, .58),
      Alignment(.58, .58),
    ];

    final dots = switch (value) {
      1 => <int>[4],
      2 => <int>[0, 8],
      3 => <int>[0, 4, 8],
      4 => <int>[0, 2, 6, 8],
      5 => <int>[0, 2, 4, 6, 8],
      _ => <int>[0, 2, 3, 5, 6, 8],
    };

    return Container(
      width: 70,
      height: 70,
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.primary,
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
            color: Theme.of(context)
                .colorScheme
                .primary
                .withValues(alpha: .28),
            blurRadius: 16,
            offset: const Offset(0, 7),
          ),
        ],
      ),
      child: Stack(
        children: [
          for (final index in dots)
            Align(
              alignment: positions[index],
              child: Container(
                width: 10,
                height: 10,
                decoration: const BoxDecoration(
                  color: Colors.white,
                  shape: BoxShape.circle,
                ),
              ),
            ),
        ],
      ),
    );
  }
}
