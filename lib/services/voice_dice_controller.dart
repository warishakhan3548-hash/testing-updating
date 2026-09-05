import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:speech_to_text/speech_recognition_error.dart';
import 'package:speech_to_text/speech_recognition_result.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

class VoiceDiceController extends ChangeNotifier {
  final stt.SpeechToText _speech = stt.SpeechToText();

  bool _initialized = false;
  bool _available = false;
  bool _enabled = true;
  bool _listening = false;
  bool _rollSuspended = false;
  bool _disposed = false;
  int? _pendingValue;
  String _lastHeard = '';
  String? _errorMessage;
  String? _preferredLocaleId;
  int _listenGeneration = 0;
  Timer? _restartTimer;

  bool get initialized => _initialized;
  bool get available => _available;
  bool get enabled => _enabled;
  bool get listening => _listening;
  int? get pendingValue => _pendingValue;
  String get lastHeard => _lastHeard;
  String? get errorMessage => _errorMessage;

  @override
  void notifyListeners() {
    if (!_disposed) super.notifyListeners();
  }

  Future<void> initialize() async {
    if (_initialized || _disposed) return;
    _initialized = true;

    try {
      _available = await _speech.initialize(
        onStatus: _handleStatus,
        onError: _handleError,
        debugLogging: false,
      );

      if (_disposed) return;
      if (_available) {
        await _chooseBestLocale();
        await _startListening();
      } else {
        _errorMessage = 'Speech recognition is unavailable on this device.';
      }
    } catch (error) {
      if (_disposed) return;
      _available = false;
      _errorMessage = 'Voice setup failed: $error';
    }
    notifyListeners();
  }

  Future<void> setEnabled(bool value) async {
    if (_disposed) return;
    _enabled = value;
    _errorMessage = null;
    notifyListeners();

    if (!value) {
      _restartTimer?.cancel();
      _listenGeneration += 1;
      try {
        await _speech.stop();
      } catch (_) {}
      if (_disposed) return;
      _listening = false;
      notifyListeners();
      return;
    }

    if (!_initialized) {
      await initialize();
    } else if (_available && !_rollSuspended) {
      await _startListening();
    }
  }

  Future<int?> suspendForRoll() async {
    if (_disposed) return null;
    final value = _pendingValue;
    _pendingValue = null;
    _rollSuspended = true;
    _restartTimer?.cancel();

    // Invalidate callbacks from the pre-roll listening session. Late speech
    // results can never overwrite the next roll's command.
    _listenGeneration += 1;
    try {
      if (_speech.isListening) await _speech.stop();
    } catch (_) {}
    if (_disposed) return value;
    _listening = false;
    notifyListeners();
    return value;
  }

  Future<void> resumeAfterRoll() async {
    if (_disposed) return;
    _rollSuspended = false;
    notifyListeners();
    if (_enabled && _available) await _startListening();
  }

  void clearPending() {
    if (_disposed) return;
    _pendingValue = null;
    notifyListeners();
  }

  Future<void> _chooseBestLocale() async {
    if (_disposed) return;
    try {
      final locales = await _speech.locales();
      if (_disposed || locales.isEmpty) return;

      stt.LocaleName? hindi;
      stt.LocaleName? englishIndia;
      for (final locale in locales) {
        final id = locale.localeId.toLowerCase().replaceAll('-', '_');
        if (hindi == null && id.startsWith('hi')) hindi = locale;
        if (englishIndia == null && id.startsWith('en_in')) {
          englishIndia = locale;
        }
      }

      final systemLocale = await _speech.systemLocale();
      if (_disposed) return;
      _preferredLocaleId =
          hindi?.localeId ?? englishIndia?.localeId ?? systemLocale?.localeId;
    } catch (_) {
      if (!_disposed) _preferredLocaleId = null;
    }
  }

  Future<void> _startListening() async {
    if (_disposed ||
        !_enabled ||
        !_available ||
        _rollSuspended ||
        _speech.isListening) {
      return;
    }

    _restartTimer?.cancel();
    final generation = ++_listenGeneration;

    try {
      await _speech.listen(
        onResult: (SpeechRecognitionResult result) {
          if (_disposed ||
              generation != _listenGeneration ||
              _rollSuspended) {
            return;
          }
          _onSpeechResult(result);
        },
        listenOptions: stt.SpeechListenOptions(
          partialResults: true,
          cancelOnError: false,
          listenMode: stt.ListenMode.confirmation,
          pauseFor: const Duration(seconds: 2),
          listenFor: const Duration(seconds: 30),
          localeId: _preferredLocaleId,
          enableHapticFeedback: false,
        ),
      );
      if (_disposed) return;
      if (generation == _listenGeneration) {
        _listening = _speech.isListening;
        _errorMessage = null;
        notifyListeners();
      }
    } catch (_) {
      if (_disposed || generation != _listenGeneration) return;
      _listening = false;
      _errorMessage = 'Could not start listening.';
      _scheduleRestart();
      notifyListeners();
    }
  }

  void _onSpeechResult(SpeechRecognitionResult result) {
    if (_disposed) return;
    final words = result.recognizedWords.trim();
    if (words.isEmpty) return;

    _lastHeard = words;
    final parsed = parseLastDiceValue(words);
    if (parsed != null) {
      _pendingValue = parsed;
      _errorMessage = null;
    }
    notifyListeners();
  }

  void _handleStatus(String status) {
    if (_disposed) return;
    _listening = status == stt.SpeechToText.listeningStatus;
    notifyListeners();

    if (status == stt.SpeechToText.notListeningStatus ||
        status == stt.SpeechToText.doneStatus) {
      _scheduleRestart();
    }
  }

  void _handleError(SpeechRecognitionError error) {
    if (_disposed) return;
    _listening = false;
    final message = error.errorMsg.toLowerCase();
    final permissionProblem = message.contains('permission') ||
        message.contains('not_allowed') ||
        message.contains('denied');

    _errorMessage = permissionProblem
        ? 'Microphone permission is required for voice dice.'
        : 'Voice paused. Tap the mic if it does not restart.';

    if (!permissionProblem) _scheduleRestart();
    notifyListeners();
  }

  void _scheduleRestart() {
    if (_disposed || !_enabled || !_available || _rollSuspended) return;
    _restartTimer?.cancel();
    _restartTimer = Timer(const Duration(milliseconds: 550), () {
      if (!_disposed && _enabled && _available && !_rollSuspended) {
        _startListening();
      }
    });
  }

  static int? parseLastDiceValue(String input) {
    var normalized = input.toLowerCase();
    normalized = normalized
        .replaceAll('।', ' ')
        .replaceAll(RegExp(r'[^a-z0-9\u0900-\u097F]+'), ' ')
        .trim();
    if (normalized.isEmpty) return null;

    const aliases = <String, int>{
      '1': 1, '१': 1, 'one': 1, 'एक': 1, 'ek': 1, 'वन': 1,
      '2': 2, '२': 2, 'two': 2, 'दो': 2, 'do': 2, 'टू': 2,
      '3': 3, '३': 3, 'three': 3, 'तीन': 3, 'teen': 3, 'थ्री': 3,
      '4': 4, '४': 4, 'four': 4, 'चार': 4, 'char': 4, 'chaar': 4,
      'फोर': 4,
      '5': 5, '५': 5, 'five': 5, 'पांच': 5, 'पाँच': 5, 'paanch': 5,
      'panch': 5, 'फाइव': 5,
      '6': 6, '६': 6, 'six': 6, 'छह': 6, 'छक्का': 6, 'छक्क': 6,
      'chakka': 6, 'chhakka': 6, 'सिक्स': 6,
    };

    int? latest;
    for (final token in normalized.split(RegExp(r'\s+'))) {
      final value = aliases[token];
      if (value != null) latest = value;
    }
    return latest;
  }

  @override
  void dispose() {
    if (_disposed) return;
    _disposed = true;
    _restartTimer?.cancel();
    _listenGeneration += 1;
    _speech.cancel();
    super.dispose();
  }
}
