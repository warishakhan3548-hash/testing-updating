import 'package:flutter/cupertino.dart';
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
    final baseScheme = ColorScheme.fromSeed(
      seedColor: GamePalette.violet,
      brightness: Brightness.dark,
      surface: GamePalette.surface,
    );
    final colorScheme = baseScheme.copyWith(
      primary: GamePalette.violet,
      secondary: GamePalette.cyan,
      surface: GamePalette.surface,
      surfaceContainerHighest: GamePalette.surfaceRaised,
      onSurface: GamePalette.textPrimary,
      outline: GamePalette.textMuted.withValues(alpha: .34),
    );

    final baseText = ThemeData.dark(useMaterial3: true).textTheme;
    final textTheme = baseText.copyWith(
      headlineSmall: baseText.headlineSmall?.copyWith(
        color: GamePalette.textPrimary,
        fontWeight: FontWeight.w900,
        letterSpacing: -.45,
      ),
      titleLarge: baseText.titleLarge?.copyWith(
        color: GamePalette.textPrimary,
        fontWeight: FontWeight.w900,
        letterSpacing: -.25,
      ),
      titleMedium: baseText.titleMedium?.copyWith(
        color: GamePalette.textPrimary,
        fontWeight: FontWeight.w800,
      ),
      bodyLarge: baseText.bodyLarge?.copyWith(
        color: GamePalette.textPrimary,
        height: 1.32,
      ),
      bodyMedium: baseText.bodyMedium?.copyWith(
        color: GamePalette.textMuted,
        height: 1.32,
      ),
    );

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Aarish Kingdom',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: colorScheme,
        scaffoldBackgroundColor: GamePalette.background,
        fontFamily: 'Roboto',
        textTheme: textTheme,
        splashFactory: InkSparkle.splashFactory,
        visualDensity: VisualDensity.standard,
        pageTransitionsTheme: const PageTransitionsTheme(
          builders: <TargetPlatform, PageTransitionsBuilder>{
            TargetPlatform.android: PredictiveBackPageTransitionsBuilder(),
            TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
          },
        ),
        appBarTheme: const AppBarTheme(
          elevation: 0,
          scrolledUnderElevation: 0,
          centerTitle: true,
          backgroundColor: Colors.transparent,
          surfaceTintColor: Colors.transparent,
          foregroundColor: GamePalette.textPrimary,
        ),
        cardTheme: CardThemeData(
          elevation: 0,
          color: GamePalette.surface,
          surfaceTintColor: Colors.transparent,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(24),
            side: BorderSide(color: Colors.white.withValues(alpha: .055)),
          ),
        ),
        dialogTheme: DialogThemeData(
          elevation: 0,
          backgroundColor: GamePalette.surface,
          surfaceTintColor: Colors.transparent,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(28),
            side: BorderSide(color: Colors.white.withValues(alpha: .075)),
          ),
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            backgroundColor: GamePalette.violet,
            foregroundColor: Colors.white,
            disabledBackgroundColor: GamePalette.surfaceRaised,
            disabledForegroundColor: GamePalette.textMuted,
            elevation: 0,
            minimumSize: const Size(48, 52),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
            textStyle: const TextStyle(
              fontWeight: FontWeight.w900,
              letterSpacing: .15,
            ),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(18),
            ),
          ),
        ),
        textButtonTheme: TextButtonThemeData(
          style: TextButton.styleFrom(
            foregroundColor: GamePalette.cyan,
            textStyle: const TextStyle(fontWeight: FontWeight.w800),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
            ),
          ),
        ),
        iconButtonTheme: IconButtonThemeData(
          style: IconButton.styleFrom(
            foregroundColor: GamePalette.textPrimary,
            highlightColor: Colors.white.withValues(alpha: .06),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: GamePalette.surfaceRaised.withValues(alpha: .82),
          contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
          hintStyle: const TextStyle(color: GamePalette.textMuted),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(18),
            borderSide: BorderSide.none,
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(18),
            borderSide: BorderSide(color: Colors.white.withValues(alpha: .055)),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(18),
            borderSide: const BorderSide(color: GamePalette.violet, width: 1.4),
          ),
        ),
      ),
      home: const SetupScreen(),
    );
  }
}
