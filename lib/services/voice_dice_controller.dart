import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:vosk_flutter_service/vosk_flutter_service.dart';

/// Offline, command-focused voice recognizer for the Ludo dice.
///
/// The recognizer deliberately uses a tiny grammar instead of general
/// dictation. That makes short dice commands fast and reduces false matches
/// from room conversation. `[unk]` lets Vosk reject unrelated speech instead
/// of forcing every sound into one of the six numbers.
class VoiceDiceController extends ChangeNotifier {
  static const String modelAsset =
      'assets/models/vosk-model-small-hi-0.22.zip';
  static const int sampleRate = 16000;

  static const List<String> commandGrammar = <String>[
    '[unk]',
    'एक',
    'इक',
    'वन',
    'दो',
    'टू',
    'तीन',
    'थ्री',
    'चार',
    'फोर',
    'पांच',
    'पाँच',
    'पाच',
    'फाइव',
    'फाईव',
    'छह',
    'छः',
    'छे',
    'छक्का',
    'छका',
    'चक्का',
    'सिक्स',
    'एक नंबर',
    'दो नंबर',
    'तीन नंबर',
    'चार नंबर',
    'पांच नंबर',
    'पाँच नंबर',
    'छह नंबर',
    'छक्का नंबर',
  ];

  final VoskFlutterPlugin _vosk = VoskFlutterPlugin.instance();
  final ModelLoader _modelLoader = ModelLoader();

  Model? _model;
  Recognizer? _recognizer;
  SpeechService? _speechService;
  StreamSubscription<String>? _partialSub;
  StreamSubscription<String>? _resultSub;

  bool _initialized = false;
  bool _available = false;
  bool _enabled = true;
  bool _listening = false;
  bool _serviceStarted = false;
  bool _servicePaused = false;
  bool _rollSuspended = false;
  bool _disposed = false;
  int _listenGeneration = 0;

  int? _pendingValue;
  int? _candidateValue;
  int? _lastPartialValue;
  int _partialHits = 0;
  DateTime? _candidateAt;
  String _lastHeard = '';
  String? _errorMessage;

  bool get initialized => _initialized;
  bool get available => _available;
  bool get enabled => _enabled;
  bool get listening => _listening;
  bool get offlineReady => _initialized && _available;
  String get engineName => 'Offline Vosk Hindi AI';
  int? get pendingValue => _pendingValue;
  String get lastHeard => _lastHeard;
  String? get errorMessage => _errorMessage;

  Future<void> initialize() async {
    if (_initialized || _disposed) return;
    _initialized = true;
    _safeNotify();

    try {
      final modelPath = await _modelLoader.loadFromAssets(modelAsset);
      if (_disposed) return;

      _model = await _vosk.createModel(modelPath);
      if (_disposed) return;

      _recognizer = await _vosk.createRecognizer(
        model: _model!,
        sampleRate: sampleRate,
        grammar: commandGrammar,
      );
      await _recognizer!.setMaxAlternatives(1);
      if (_disposed) return;

      await _createSpeechService();
      if (_disposed) return;

      _available = true;
      _errorMessage = null;
      _safeNotify();

      if (_enabled && !_rollSuspended) {
        await _startListening();
      }
    } on MicrophoneAccessDeniedException {
      _available = false;
      _errorMessage = 'Microphone permission is required for offline voice dice.';
      _safeNotify();
    } catch (error) {
      _available = false;
      _listening = false;
      _errorMessage = _friendlyInitError(error);
      _safeNotify();
    }
  }

  Future<void> _createSpeechService() async {
    if (_disposed || _recognizer == null || _speechService != null) return;
    _speechService = await _vosk.initSpeechService(_recognizer!);
    _serviceStarted = false;
    _servicePaused = false;
    _attachStreams();
  }

  void _attachStreams() {
    final service = _speechService;
    if (service == null) return;

    unawaited(_partialSub?.cancel());
    unawaited(_resultSub?.cancel());

    _partialSub = service.onPartial().listen(
      (raw) => _handleRawRecognition(raw, isFinal: false),
      onError: _handleStreamError,
    );
    _resultSub = service.onResult().listen(
      (raw) => _handleRawRecognition(raw, isFinal: true),
      onError: _handleStreamError,
    );
  }

  Future<void> setEnabled(bool value) async {
    if (_disposed || _enabled == value) return;
    _enabled = value;
    _errorMessage = null;

    if (!value) {
      _listenGeneration += 1;
      _listening = false;
      _clearCandidate();
      await _releaseSpeechService();
      _safeNotify();
      return;
    }

    _safeNotify();
    if (!_initialized) {
      await initialize();
      return;
    }

    if (_available && !_rollSuspended) {
      try {
        await _createSpeechService();
        await _startListening();
      } on MicrophoneAccessDeniedException {
        _available = false;
        _errorMessage = 'Microphone permission is required for offline voice dice.';
        _safeNotify();
      } catch (_) {
        _errorMessage = 'Could not reopen the offline microphone.';
        _safeNotify();
      }
    }
  }

  /// Rebuilds the offline voice stack after a permission or native-service
  /// failure. This lets the user recover without restarting the whole game.
  Future<void> retry() async {
    if (_disposed) return;

    if (_available) {
      if (!_enabled) {
        await setEnabled(true);
      } else if (!_rollSuspended) {
        await _startListening();
      }
      return;
    }

    _enabled = true;
    _errorMessage = null;
    _listenGeneration += 1;
    _listening = false;
    _rollSuspended = false;
    _pendingValue = null;
    _clearCandidate();

    await _releaseSpeechService();
    try {
      await _recognizer?.dispose();
    } catch (_) {}
    _recognizer = null;
    try {
      _model?.dispose();
    } catch (_) {}
    _model = null;

    _available = false;
    _initialized = false;
    _safeNotify();
    await initialize();
  }

  /// Atomically freezes voice input and returns the newest valid command.
  ///
  /// A very recent partial candidate is accepted even if it has not yet
  /// reached the normal two-frame stability threshold. This keeps a fast
  /// "say four → instantly tap roll" interaction deterministic.
  Future<int?> suspendForRoll() async {
    if (_disposed) return null;

    final now = DateTime.now();
    final candidateIsFresh = _candidateValue != null &&
        _candidateAt != null &&
        now.difference(_candidateAt!) <= const Duration(milliseconds: 1400);
    final value = _pendingValue ?? (candidateIsFresh ? _candidateValue : null);

    _rollSuspended = true;
    _pendingValue = null;
    _clearCandidate();
    _listenGeneration += 1;
    _listening = false;

    // Keep the native AudioRecord/recognizer pipeline warm while discarding
    // speech during dice animation and token selection. This is much faster
    // and safer than stop/start on every roll.
    if (_serviceStarted && !_servicePaused) {
      try {
        await _speechService?.setPause(paused: true);
        _servicePaused = true;
      } catch (_) {}
    }

    _safeNotify();
    return value;
  }

  Future<void> resumeAfterRoll() async {
    if (_disposed) return;
    _rollSuspended = false;
    _clearCandidate();

    try {
      // Clear any pre-roll acoustic state before accepting the next command.
      await _speechService?.reset();
    } catch (_) {}

    if (_enabled && _available) {
      await _startListening();
    } else {
      _safeNotify();
    }
  }

  void clearPending() {
    _pendingValue = null;
    _clearCandidate();
    _safeNotify();
  }

  Future<void> _startListening() async {
    if (_disposed ||
        !_enabled ||
        !_available ||
        _rollSuspended ||
        _listening) {
      return;
    }

    if (_speechService == null) {
      await _createSpeechService();
    }
    final service = _speechService;
    if (service == null) return;

    final generation = ++_listenGeneration;
    try {
      if (_serviceStarted) {
        if (_servicePaused) {
          await service.setPause(paused: false);
          _servicePaused = false;
        }
        if (_disposed || generation != _listenGeneration) return;
        _listening = true;
        _errorMessage = null;
        _safeNotify();
        return;
      }

      final started = await service.start(
        onRecognitionError: _handleRecognitionError,
      );
      if (_disposed || generation != _listenGeneration) return;

      // Native start returns false when it was already active; either way the
      // service is available for listening at this point.
      _serviceStarted = true;
      _servicePaused = false;
      _listening = started != false || _serviceStarted;
      _errorMessage = null;
      _safeNotify();
    } catch (_) {
      if (_disposed || generation != _listenGeneration) return;
      _listening = false;
      _serviceStarted = false;
      _servicePaused = false;
      _errorMessage = 'Could not start the offline microphone recognizer.';
      _safeNotify();
    }
  }

  void _handleRecognitionError(Object error, [StackTrace? stackTrace]) {
    if (_disposed) return;
    _listening = false;
    _errorMessage = 'Offline voice paused. Tap the mic to retry.';
    _safeNotify();
  }

  void _handleRawRecognition(String raw, {required bool isFinal}) {
    if (_disposed || !_enabled || _rollSuspended) return;

    final heard = _extractText(raw).trim();
    if (heard.isEmpty || heard == '[unk]') return;

    _lastHeard = heard;
    final value = parseLastDiceValue(heard);
    if (value == null) {
      _safeNotify();
      return;
    }

    _candidateValue = value;
    _candidateAt = DateTime.now();

    if (isFinal) {
      _commitCandidate(value);
      _lastPartialValue = null;
      _partialHits = 0;
      return;
    }

    if (_lastPartialValue == value) {
      _partialHits += 1;
    } else {
      _lastPartialValue = value;
      _partialHits = 1;
    }

    // Two matching partial frames reduce noise, while suspendForRoll can still
    // consume one very recent partial candidate for instant-tap responsiveness.
    if (_partialHits >= 2) {
      _commitCandidate(value);
    } else {
      _safeNotify();
    }
  }

  void _commitCandidate(int value) {
    // No queue: newest command always overwrites the old command.
    _pendingValue = value;
    _errorMessage = null;
    _safeNotify();
  }

  void _handleStreamError(Object error, [StackTrace? stackTrace]) {
    if (_disposed) return;
    _listening = false;
    _errorMessage = 'Offline voice stream paused. Tap the mic to retry.';
    _safeNotify();
  }

  void _clearCandidate() {
    _candidateValue = null;
    _candidateAt = null;
    _lastPartialValue = null;
    _partialHits = 0;
  }

  static String _extractText(String raw) {
    final trimmed = raw.trim();
    if (trimmed.isEmpty) return '';

    try {
      final decoded = jsonDecode(trimmed);
      if (decoded is Map<String, dynamic>) {
        for (final key in const <String>['partial', 'text']) {
          final value = decoded[key];
          if (value is String && value.trim().isNotEmpty) {
            return value.trim();
          }
        }
      }
    } catch (_) {
      // Some platform/plugin versions may already return plain recognized text.
    }

    return trimmed;
  }

  static int? parseLastDiceValue(String input) {
    var normalized = input.toLowerCase();
    normalized = normalized
        .replaceAll('।', ' ')
        .replaceAll(RegExp(r'[^a-z0-9\u0900-\u097F]+'), ' ')
        .trim();
    if (normalized.isEmpty) return null;

    const aliases = <String, int>{
      '1': 1,
      '१': 1,
      'one': 1,
      'एक': 1,
      'इक': 1,
      'ek': 1,
      'वन': 1,
      '2': 2,
      '२': 2,
      'two': 2,
      'दो': 2,
      'do': 2,
      'टू': 2,
      '3': 3,
      '३': 3,
      'three': 3,
      'तीन': 3,
      'teen': 3,
      'थ्री': 3,
      '4': 4,
      '४': 4,
      'four': 4,
      'चार': 4,
      'char': 4,
      'chaar': 4,
      'फोर': 4,
      '5': 5,
      '५': 5,
      'five': 5,
      'पांच': 5,
      'पाँच': 5,
      'पाच': 5,
      'paanch': 5,
      'panch': 5,
      'फाइव': 5,
      'फाईव': 5,
      '6': 6,
      '६': 6,
      'six': 6,
      'छह': 6,
      'छः': 6,
      'छे': 6,
      'छक्का': 6,
      'छका': 6,
      'चक्का': 6,
      'chakka': 6,
      'chhakka': 6,
      'सिक्स': 6,
    };

    int? latest;
    for (final token in normalized.split(RegExp(r'\s+'))) {
      final value = aliases[token];
      if (value != null) latest = value;
    }
    return latest;
  }

  String _friendlyInitError(Object error) {
    final lower = error.toString().toLowerCase();
    if (lower.contains('asset') || lower.contains('model')) {
      return 'Offline Hindi voice model is missing or could not be loaded.';
    }
    return 'Offline voice setup failed. You can still use random dice.';
  }

  Future<void> _releaseSpeechService() async {
    final service = _speechService;
    _speechService = null;
    _serviceStarted = false;
    _servicePaused = false;

    await _partialSub?.cancel();
    await _resultSub?.cancel();
    _partialSub = null;
    _resultSub = null;

    if (service != null) {
      try {
        await service.cancel();
      } catch (_) {}
      try {
        await service.dispose();
      } catch (_) {}
    }
  }

  void _safeNotify() {
    if (!_disposed) notifyListeners();
  }

  Future<void> _shutdown() async {
    try {
      await _releaseSpeechService();
      await _recognizer?.dispose();
      _model?.dispose();
    } catch (_) {}
  }

  @override
  void dispose() {
    if (_disposed) return;
    _disposed = true;
    _listenGeneration += 1;
    unawaited(_shutdown());
    super.dispose();
  }
}
