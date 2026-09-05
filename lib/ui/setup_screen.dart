import 'package:flutter/material.dart';

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
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 520),
              child: Column(
                children: [
                  Container(
                    width: 100,
                    height: 100,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [scheme.primary, scheme.tertiary],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(28),
                      boxShadow: [
                        BoxShadow(
                          color: scheme.primary.withValues(alpha: .22),
                          blurRadius: 28,
                          offset: const Offset(0, 12),
                        ),
                      ],
                    ),
                    child: const Icon(Icons.casino_rounded,
                        size: 58, color: Colors.white),
                  ),
                  const SizedBox(height: 22),
                  Text(
                    'Voice Ludo Masti',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                          fontWeight: FontWeight.w900,
                          letterSpacing: -.8,
                        ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'बोलो नंबर • Dice दबाओ • वही नंबर पाओ 🎲',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          color: scheme.onSurfaceVariant,
                          fontWeight: FontWeight.w600,
                        ),
                  ),
                  const SizedBox(height: 28),
                  Card(
                    elevation: 0,
                    color: scheme.surfaceContainerHighest.withValues(alpha: .55),
                    child: Padding(
                      padding: const EdgeInsets.all(18),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Text(
                            'Players',
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                  fontWeight: FontWeight.w800,
                                ),
                          ),
                          const SizedBox(height: 14),
                          Row(
                            children: [2, 3, 4].map((count) {
                              final selected = _players == count;
                              return Expanded(
                                child: Padding(
                                  padding: EdgeInsets.only(right: count == 4 ? 0 : 10),
                                  child: ChoiceChip(
                                    selected: selected,
                                    showCheckmark: false,
                                    label: SizedBox(
                                      height: 38,
                                      child: Center(
                                        child: Text(
                                          '$count Player',
                                          style: TextStyle(
                                            fontWeight: FontWeight.w800,
                                            color: selected
                                                ? scheme.onPrimary
                                                : scheme.onSurface,
                                          ),
                                        ),
                                      ),
                                    ),
                                    selectedColor: scheme.primary,
                                    onSelected: (_) => setState(() => _players = count),
                                  ),
                                ),
                              );
                            }).toList(),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  const _FeatureRow(
                    icon: Icons.mic_rounded,
                    title: 'Latest voice wins',
                    subtitle: 'छक्का → पाँच → चार, then roll = 4',
                  ),
                  const _FeatureRow(
                    icon: Icons.all_inclusive_rounded,
                    title: 'Unlimited sixes',
                    subtitle: 'No three-six penalty. Take as many as you want.',
                  ),
                  const _FeatureRow(
                    icon: Icons.groups_rounded,
                    title: 'Local multiplayer',
                    subtitle: '2, 3 or 4 players on one phone.',
                  ),
                  const SizedBox(height: 22),
                  SizedBox(
                    width: double.infinity,
                    height: 58,
                    child: FilledButton.icon(
                      icon: const Icon(Icons.play_arrow_rounded, size: 30),
                      label: const Text(
                        'START GAME',
                        style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: .6),
                      ),
                      onPressed: () {
                        Navigator.of(context).push(
                          MaterialPageRoute<void>(
                            builder: (_) => GameScreen(playerCount: _players),
                          ),
                        );
                      },
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Tip: If you do not say a number, the dice rolls normally at random.',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: scheme.onSurfaceVariant,
                        ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _FeatureRow extends StatelessWidget {
  const _FeatureRow({
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  final IconData icon;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: scheme.primaryContainer,
              borderRadius: BorderRadius.circular(14),
            ),
            child: Icon(icon, color: scheme.onPrimaryContainer),
          ),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
                const SizedBox(height: 2),
                Text(
                  subtitle,
                  style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12.5),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
