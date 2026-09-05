import 'package:flutter/material.dart';

import 'ui/setup_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const VoiceLudoApp());
}

class VoiceLudoApp extends StatelessWidget {
  const VoiceLudoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Voice Ludo Masti',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF6C4DFF),
          brightness: Brightness.light,
        ),
        scaffoldBackgroundColor: const Color(0xFFF7F7FC),
        fontFamily: 'Roboto',
      ),
      home: const SetupScreen(),
    );
  }
}
