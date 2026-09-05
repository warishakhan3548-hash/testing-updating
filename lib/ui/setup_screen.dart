import 'package:flutter/material.dart';

import 'game_palette.dart';
import 'game_screen.dart';

class SetupScreen extends StatefulWidget {
  const SetupScreen({super.key});

  @override
  State<SetupScreen> createState() => _SetupScreenState();
}

class _SetupScreenState extends State<SetupScreen> {
  int _players = 2;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: DecoratedBox(
        decoration: const BoxDecoration(gradient: GamePalette.appBackground),
        child: Stack(
          children: [
            const Positioned(
              top: -80,
              right: -70,
              child: _GlowOrb(
                size: 230,
                color: Color(0x338A6CFF),
              ),
            ),
            const Positioned(
              bottom: 70,
              left: -90,
              child: _GlowOrb(
                size: 250,
                color: Color(0x224DD8FF),
              ),
            ),
            SafeArea(
              child: Center(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.fromLTRB(20, 26, 20, 26),
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 560),
                    child: Column(
                      children: [
                        const _GameLogo(),
                        const SizedBox(height: 22),
                        const Text(
                          'Voice Ludo Masti',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: GamePalette.textPrimary,
                            fontSize: 32,
                            fontWeight: FontWeight.w900,
                            letterSpacing: -1.1,
                          ),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'बोलो नंबर • Dice दबाओ • वही नंबर पाओ 🎲',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: GamePalette.textMuted,
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 14),
                        const _OfflineBadge(),
                        const SizedBox(height: 28),
                        _buildPlayerSelector(),
                        const SizedBox(height: 18),
                        const _HowItWorksCard(),
                        const SizedBox(height: 16),
                        const Wrap(
                          alignment: WrapAlignment.center,
                          spacing: 8,
                          runSpacing: 8,
                          children: [
                            _FeatureChip(
                              icon: Icons.graphic_eq_rounded,
                              label: 'Noise filtered',
                            ),
                            _FeatureChip(
                              icon: Icons.all_inclusive_rounded,
                              label: 'Unlimited sixes',
                            ),
                            _FeatureChip(
                              icon: Icons.groups_rounded,
                              label: 'Local multiplayer',
                            ),
                          ],
                        ),
                        const SizedBox(height: 24),
                        SizedBox(
                          width: double.infinity,
                          height: 62,
                          child: FilledButton(
                            onPressed: _startGame,
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                const Icon(Icons.play_arrow_rounded, size: 30),
                                const SizedBox(width: 9),
                                Text(
                                  'PLAY WITH $_players PLAYERS',
                                  style: const TextStyle(
                                    fontSize: 15,
                                    fontWeight: FontWeight.w900,
                                    letterSpacing: .5,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 12),
                        const Text(
                          'No internet needed while playing • No voice command = normal random roll',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: GamePalette.textMuted,
                            fontSize: 11.5,
                            height: 1.4,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPlayerSelector() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: GamePalette.surface.withValues(alpha: .92),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white.withValues(alpha: .07)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: .25),
            blurRadius: 28,
            offset: const Offset(0, 16),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.groups_2_rounded, color: GamePalette.cyan),
              SizedBox(width: 9),
              Text(
                'Choose Players',
                style: TextStyle(
                  color: GamePalette.textPrimary,
                  fontSize: 17,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [2, 3, 4].map((count) {
              final selected = _players == count;
              return Expanded(
                child: Padding(
                  padding: EdgeInsets.only(right: count == 4 ? 0 : 9),
                  child: _PlayerChoice(
                    count: count,
                    selected: selected,
                    onTap: () => setState(() => _players = count),
                  ),
                ),
              );
            }).toList(growable: false),
          ),
        ],
      ),
    );
  }

  void _startGame() {
    Navigator.of(context).push(
      PageRouteBuilder<void>(
        transitionDuration: const Duration(milliseconds: 360),
        reverseTransitionDuration: const Duration(milliseconds: 240),
        pageBuilder: (_, animation, __) => GameScreen(playerCount: _players),
        transitionsBuilder: (_, animation, __, child) {
          final curved = CurvedAnimation(
            parent: animation,
            curve: Curves.easeOutCubic,
          );
          return FadeTransition(
            opacity: curved,
            child: ScaleTransition(
              scale: Tween<double>(begin: .975, end: 1).animate(curved),
              child: child,
            ),
          );
        },
      ),
    );
  }
}

class _GameLogo extends StatelessWidget {
  const _GameLogo();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 116,
      height: 116,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(34),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [GamePalette.violet, Color(0xFF6749F5)],
        ),
        border: Border.all(color: Colors.white.withValues(alpha: .18)),
        boxShadow: const [
          BoxShadow(
            color: Color(0x558A6CFF),
            blurRadius: 38,
            offset: Offset(0, 18),
          ),
        ],
      ),
      child: const Stack(
        alignment: Alignment.center,
        children: [
          Icon(Icons.casino_rounded, color: Colors.white, size: 66),
          Positioned(
            right: 13,
            top: 13,
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: GamePalette.cyan,
                shape: BoxShape.circle,
              ),
              child: Padding(
                padding: EdgeInsets.all(6),
                child: Icon(Icons.mic_rounded, color: Color(0xFF07111A), size: 17),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _OfflineBadge extends StatelessWidget {
  const _OfflineBadge();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
      decoration: BoxDecoration(
        color: const Color(0x192FC58D),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: GamePalette.green.withValues(alpha: .35)),
      ),
      child: const Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.offline_bolt_rounded, size: 17, color: GamePalette.green),
          SizedBox(width: 6),
          Text(
            'OFFLINE VOICE AI',
            style: TextStyle(
              color: GamePalette.green,
              fontSize: 11.5,
              fontWeight: FontWeight.w900,
              letterSpacing: .6,
            ),
          ),
        ],
      ),
    );
  }
}

class _PlayerChoice extends StatelessWidget {
  const _PlayerChoice({
    required this.count,
    required this.selected,
    required this.onTap,
  });

  final int count;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    const colors = <Color>[
      GamePalette.red,
      GamePalette.green,
      GamePalette.yellow,
      GamePalette.blue,
    ];

    return Semantics(
      button: true,
      selected: selected,
      label: '$count players',
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(18),
          onTap: onTap,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 190),
            curve: Curves.easeOutCubic,
            height: 94,
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 12),
            decoration: BoxDecoration(
              color: selected
                  ? GamePalette.violet.withValues(alpha: .18)
                  : GamePalette.surfaceRaised.withValues(alpha: .72),
              borderRadius: BorderRadius.circular(18),
              border: Border.all(
                color: selected
                    ? GamePalette.violet
                    : Colors.white.withValues(alpha: .06),
                width: selected ? 1.8 : 1,
              ),
              boxShadow: selected
                  ? [
                      BoxShadow(
                        color: GamePalette.violet.withValues(alpha: .2),
                        blurRadius: 16,
                      ),
                    ]
                  : null,
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Wrap(
                  spacing: 3,
                  children: List<Widget>.generate(
                    count,
                    (index) => Container(
                      width: 11,
                      height: 11,
                      decoration: BoxDecoration(
                        color: colors[index],
                        shape: BoxShape.circle,
                        border: Border.all(color: Colors.white24),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 9),
                Text(
                  '$count PLAYERS',
                  style: TextStyle(
                    color: selected
                        ? GamePalette.textPrimary
                        : GamePalette.textMuted,
                    fontSize: 11.5,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _HowItWorksCard extends StatelessWidget {
  const _HowItWorksCard();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 15, 16, 16),
      decoration: BoxDecoration(
        color: GamePalette.surface.withValues(alpha: .76),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: Colors.white.withValues(alpha: .06)),
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'HOW IT WORKS',
            style: TextStyle(
              color: GamePalette.textMuted,
              fontSize: 10.5,
              fontWeight: FontWeight.w900,
              letterSpacing: 1.2,
            ),
          ),
          SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _Step(
                  icon: Icons.mic_rounded,
                  title: '1. बोलो',
                  subtitle: '“छक्का”',
                ),
              ),
              _Arrow(),
              Expanded(
                child: _Step(
                  icon: Icons.casino_rounded,
                  title: '2. Roll',
                  subtitle: 'Tap dice',
                ),
              ),
              _Arrow(),
              Expanded(
                child: _Step(
                  icon: Icons.auto_awesome_rounded,
                  title: '3. वही',
                  subtitle: 'Result = 6',
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _Step extends StatelessWidget {
  const _Step({required this.icon, required this.title, required this.subtitle});

  final IconData icon;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          width: 42,
          height: 42,
          decoration: BoxDecoration(
            color: GamePalette.surfaceRaised,
            borderRadius: BorderRadius.circular(13),
          ),
          child: Icon(icon, color: GamePalette.cyan, size: 22),
        ),
        const SizedBox(height: 7),
        Text(
          title,
          textAlign: TextAlign.center,
          style: const TextStyle(
            color: GamePalette.textPrimary,
            fontSize: 12,
            fontWeight: FontWeight.w900,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          subtitle,
          textAlign: TextAlign.center,
          style: const TextStyle(color: GamePalette.textMuted, fontSize: 10.5),
        ),
      ],
    );
  }
}

class _Arrow extends StatelessWidget {
  const _Arrow();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.only(bottom: 25),
      child: Icon(Icons.chevron_right_rounded, color: Colors.white24),
    );
  }
}

class _FeatureChip extends StatelessWidget {
  const _FeatureChip({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: .055),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: Colors.white.withValues(alpha: .07)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 15, color: GamePalette.textMuted),
          const SizedBox(width: 6),
          Text(
            label,
            style: const TextStyle(
              color: GamePalette.textMuted,
              fontSize: 11,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}

class _GlowOrb extends StatelessWidget {
  const _GlowOrb({required this.size, required this.color});

  final double size;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          color: color,
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(color: color, blurRadius: size * .5, spreadRadius: size * .08),
          ],
        ),
      ),
    );
  }
}
