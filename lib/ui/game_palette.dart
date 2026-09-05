import 'package:flutter/material.dart';

import '../game/ludo_engine.dart';

abstract final class GamePalette {
  static const Color background = Color(0xFF0C0E1A);
  static const Color backgroundSoft = Color(0xFF14172A);
  static const Color surface = Color(0xFF1B1F36);
  static const Color surfaceRaised = Color(0xFF252A46);
  static const Color cream = Color(0xFFFFFDF6);
  static const Color textPrimary = Color(0xFFF7F8FF);
  static const Color textMuted = Color(0xFFAEB4CC);
  static const Color violet = Color(0xFF8A6CFF);
  static const Color cyan = Color(0xFF55D7FF);

  static const Color red = Color(0xFFFF5A64);
  static const Color green = Color(0xFF2FC58D);
  static const Color yellow = Color(0xFFFFC84A);
  static const Color blue = Color(0xFF4C8DFF);

  static Color player(LudoColor color) => switch (color) {
        LudoColor.red => red,
        LudoColor.green => green,
        LudoColor.yellow => yellow,
        LudoColor.blue => blue,
      };

  static LinearGradient get appBackground => const LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: <Color>[
          Color(0xFF0B0D18),
          Color(0xFF11152A),
          Color(0xFF151328),
        ],
      );
}
