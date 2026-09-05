import 'package:flutter/material.dart';

import 'ui/game_palette.dart';
import 'ui/setup_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const VoiceLudoApp());
}

class VoiceLudoApp extends StatelessWidget {
  const VoiceLudoApp({super.key});

  @override
  Widget build(BuildContext context) {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: GamePalette.violet,
      brightness: Brightness.dark,
      surface: GamePalette.surface,
    );

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Voice Ludo Masti',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: colorScheme,
        scaffoldBackgroundColor: GamePalette.background,
        fontFamily: 'Roboto',
        splashFactory: InkSparkle.splashFactory,
        appBarTheme: const AppBarTheme(
          elevation: 0,
          centerTitle: true,
          backgroundColor: Colors.transparent,
          foregroundColor: GamePalette.textPrimary,
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            backgroundColor: GamePalette.violet,
            foregroundColor: Colors.white,
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(18),
            ),
          ),
        ),
        iconButtonTheme: IconButtonThemeData(
          style: IconButton.styleFrom(
            foregroundColor: GamePalette.textPrimary,
          ),
        ),
      ),
      home: const SetupScreen(),
    );
  }
}
