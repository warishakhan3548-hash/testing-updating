import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:vosk_flutter_service/vosk_flutter_service.dart';

/// Offline, command-focused voice recognizer for the Ludo dice.
///
/// The recognizer deliberately uses a tiny grammar instead of general
/// dictation. That makes short dice commands fast and reduces false matches
/// from room conversation. `[unk]` lets Vosk reject unrelated speech instead
/// of forcing every sound into one of the six numbers.
class VoiceDiceController extends ChangeNotifier with WidgetsBindingObserver {
  VoiceDiceController() {
    WidgetsBinding.instance.addObserver(this);
  }

  static const String modelAsset =
      'assets/models/vosk-model-small-hi-0.22.zip';
  static const int sampleRate = 16000;
  static const Duration candidateFreshness = Duration(milliseconds: 1400);

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
  bool _initializing = false;
  bool _available = false;
  bool _enabled = true;
  bool _listening = false;
  bool _serviceStarted = false;
  bool _servicePaused = false;
  bool _rollSuspended = false;
  bool _lifecyclePaused = false;
  bool _disposed = false;
  int _listenGeneration = 0;

  int? _pendingValue;
  DateTime? _pendingAt;
  int? _candidateValue;
  DateTime? _candidateAt;
  int? _lastPartialValue;
  int _partialHits = 0;
  String _lastHeard = '';
  double? _lastConfidence;
  String? _errorMessage;

  bool get initialized => _initialized;
  bool get initializing => _initializing;
  bool get available => _available;
  bool get enabled => _enabled;
  bool get listening => _listening;
  bool get offlineReady => _initialized && _available;
  String get engineName => 'Offline Vosk Hindi AI';
  int? get pendingValue => _pendingValue;
  String get lastHeard => _lastHeard;
  double? get lastConfidence => _lastConfidence;
  String? get errorMessage => _errorMessage;

  Future<void> initialize() async {
    if (_disposed || _initializing || _available) return;
    _initialized = true;
    _initializing = true;
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

      // Respect a user turning voice OFF while the model was still loading,
      // and never open the microphone while the app is backgrounded.
      if (_enabled && !_rollSuspended && !_lifecyclePaused) {
        await _startListening();
      }
    } on MicrophoneAccessDeniedException {
      _available = false;
      _enabled = false;
      _listening = false;
      _errorMessage = 'Microphone permission is required for offline voice dice.';
      _safeNotify();
    } catch (error) {
      _available = false;
      _enabled = false;
      _listening = false;
      _errorMessage = _friendlyInitError(error);
      _safeNotify();
    } finally {
      _initializing = false;
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
    if (_disposed) return;
    if (_enabled == value) {
      if (value && !_available && !_initializing) await retry();
      return;
    }

    _enabled = value;
    _errorMessage = null;

    if (!value) {
      _listenGeneration += 1;
      _listening = false;
      _clearAllCommands();
      await _releaseSpeechService();
      _safeNotify();
      return;
    }

    _safeNotify();

    // If initialization is already in flight, simply preserve the desired ON
    // state. initialize() will start listening when it finishes.
    if (_initializing) return;

    if (!_initialized) {
      await initialize();
      return;
    }

    if (!_available) {
      await retry();
      return;
    }

    if (!_rollSuspended && !_lifecyclePaused) {
      try {
        await _createSpeechService();
        await _startListening();
      } on MicrophoneAccessDeniedException {
        _available = false;
        _enabled = false;
        _errorMessage = 'Microphone permission is required for offline voice dice.';
        _safeNotify();
      } catch (_) {
        _enabled = false;
        _errorMessage = 'Could not reopen the offline microphone.';
        _safeNotify();
      }
    }
  }

  /// Rebuilds the offline voice stack after a permission or native-service
  /// failure. This lets the user recover without restarting the whole game.
  Future<void> retry() async {
    if (_disposed) return;

    _enabled = true;

    // Never tear down resources underneath an in-flight model initialization.
    // The current initialization will honor the desired enabled state.
    if (_initializing) {
      _safeNotify();
      return;
    }

    if (_available) {
      if (!_rollSuspended && !_lifecyclePaused) await _startListening();
      return;
    }

    _errorMessage = null;
    _listenGeneration += 1;
    _listening = false;
    _clearAllCommands();

    // IMPORTANT: preserve _rollSuspended and _lifecyclePaused. Retrying the
    // microphone during a move or while backgrounded must never reopen it.
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
  /// A fresh partial candidate can beat an older stable command. This is what
  /// makes the user's exact rule deterministic: say "six", then quickly say
  /// "five" and tap roll -> five wins even before Vosk emits a final result.
  Future<int?> suspendForRoll() async {
    if (_disposed) return null;

    final now = DateTime.now();
    final value = resolveNewestDiceCommand(
      pendingValue: _pendingValue,
      pendingAt: _pendingAt,
      candidateValue: _candidateValue,
      candidateAt: _candidateAt,
      now: now,
    );

    _rollSuspended = true;
    _clearAllCommands();
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

    if (_enabled && _available && !_lifecyclePaused) {
      await _startListening();
    } else {
      _safeNotify();
    }
  }

  void clearPending() {
    _clearAllCommands();
    _safeNotify();
  }

  Future<void> _startListening() async {
    if (_disposed ||
        !_enabled ||
        !_available ||
        _rollSuspended ||
        _lifecyclePaused ||
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
        if (_disposed ||
            generation != _listenGeneration ||
            _lifecyclePaused ||
            _rollSuspended) {
          return;
        }
        _listening = true;
        _errorMessage = null;
        _safeNotify();
        return;
      }

      await service.start(onRecognitionError: _handleRecognitionError);
      if (_disposed ||
          generation != _listenGeneration ||
          _lifecyclePaused ||
          _rollSuspended) {
        return;
      }

      _serviceStarted = true;
      _servicePaused = false;
      _listening = true;
      _errorMessage = null;
      _safeNotify();
    } catch (_) {
      if (_disposed || generation != _listenGeneration) return;
      _listening = false;
      _serviceStarted = false;
      _servicePaused = false;
      _enabled = false;
      _errorMessage = 'Could not start the offline microphone recognizer.';
      _safeNotify();
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    unawaited(_handleLifecycleState(state));
  }

  Future<void> _handleLifecycleState(AppLifecycleState state) async {
    if (_disposed) return;

    switch (state) {
      case AppLifecycleState.resumed:
        _lifecyclePaused = false;
        if (_enabled && _available && !_rollSuspended) {
          try {
            await _speechService?.reset();
          } catch (_) {}
          await _startListening();
        } else {
          _safeNotify();
        }
      case AppLifecycleState.inactive:
      case AppLifecycleState.hidden:
      case AppLifecycleState.paused:
      case AppLifecycleState.detached:
        _lifecyclePaused = true;
        _listenGeneration += 1;
        _listening = false;
        _clearAllCommands();
        if (_serviceStarted && !_servicePaused) {
          try {
            await _speechService?.setPause(paused: true);
            _servicePaused = true;
          } catch (_) {}
        }
        _safeNotify();
    }
  }

  void _handleRecognitionError(Object error, [StackTrace? stackTrace]) {
    if (_disposed) return;
    _listening = false;
    _enabled = false;
    _errorMessage = 'Offline voice paused. Tap the mic to retry.';
    _safeNotify();
  }

  void _handleRawRecognition(String raw, {required bool isFinal}) {
    if (_disposed || !_enabled || _rollSuspended || _lifecyclePaused) return;

    final hypothesis = parseRecognitionPayload(raw);
    final heard = hypothesis.text.trim();
    if (heard.isEmpty || heard == '[unk]') return;

    _lastHeard = heard;
    _lastConfidence = hypothesis.confidence;
    final value = parseLastDiceValue(heard);
    if (value == null) {
      _safeNotify();
      return;
    }

    // Some Vosk outputs expose a normalized 0..1 confidence, while others use
    // a different score scale. Only reject when it is clearly a normalized and
    // extremely weak final hypothesis.
    final confidence = hypothesis.confidence;
    if (isFinal &&
        confidence != null &&
        confidence >= 0 &&
        confidence <= 1 &&
        confidence < .18) {
      _safeNotify();
      return;
    }

    final heardAt = DateTime.now();
    _candidateValue = value;
    _candidateAt = heardAt;

    if (isFinal) {
      _commitCandidate(value, heardAt: heardAt);
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
      _commitCandidate(value, heardAt: heardAt);
    } else {
      _safeNotify();
    }
  }

  void _commitCandidate(int value, {required DateTime heardAt}) {
    // No queue: newest command always overwrites the old command.
    _pendingValue = value;
    _pendingAt = heardAt;
    _errorMessage = null;
    _safeNotify();
  }

  void _handleStreamError(Object error, [StackTrace? stackTrace]) {
    if (_disposed) return;
    _listening = false;
    _enabled = false;
    _errorMessage = 'Offline voice stream paused. Tap the mic to retry.';
    _safeNotify();
  }

  void _clearCandidate() {
    _candidateValue = null;
    _candidateAt = null;
    _lastPartialValue = null;
    _partialHits = 0;
  }

  void _clearAllCommands() {
    _pendingValue = null;
    _pendingAt = null;
    _clearCandidate();
  }

  /// Selects the newest usable command at the instant the user taps ROLL.
  /// This is public mainly so the arbitration rule can be regression-tested.
  static int? resolveNewestDiceCommand({
    required int? pendingValue,
    required DateTime? pendingAt,
    required int? candidateValue,
    required DateTime? candidateAt,
    required DateTime now,
  }) {
    final candidateIsFresh = candidateValue != null &&
        candidateAt != null &&
        !candidateAt.isAfter(now) &&
        now.difference(candidateAt) <= candidateFreshness;

    if (!candidateIsFresh) return pendingValue;
    if (pendingValue == null || pendingAt == null) return candidateValue;

    return candidateAt.isBefore(pendingAt) ? pendingValue : candidateValue;
  }

  /// Decodes both standard Vosk payloads (`text` / `partial`) and the
  /// `alternatives` payload produced when max alternatives is enabled.
  static ({String text, double? confidence}) parseRecognitionPayload(String raw) {
    final trimmed = raw.trim();
    if (trimmed.isEmpty) return (text: '', confidence: null);

    try {
      final decoded = jsonDecode(trimmed);
      if (decoded is Map<String, dynamic>) {
        final partial = decoded['partial'];
        if (partial is String && partial.trim().isNotEmpty) {
          return (text: partial.trim(), confidence: null);
        }

        final text = decoded['text'];
        if (text is String && text.trim().isNotEmpty) {
          final rawConfidence = decoded['confidence'];
          return (
            text: text.trim(),
            confidence: rawConfidence is num ? rawConfidence.toDouble() : null,
          );
        }

        final alternatives = decoded['alternatives'];
        if (alternatives is List) {
          for (final item in alternatives) {
            if (item is! Map) continue;
            final alternativeText = item['text'];
            if (alternativeText is! String || alternativeText.trim().isEmpty) {
              continue;
            }
            final rawConfidence = item['confidence'];
            return (
              text: alternativeText.trim(),
              confidence: rawConfidence is num ? rawConfidence.toDouble() : null,
            );
          }
        }
      }
    } catch (_) {
      // Some platform/plugin versions may already return plain recognized text.
    }

    return (text: trimmed, confidence: null);
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
    WidgetsBinding.instance.removeObserver(this);
    unawaited(_shutdown());
    super.dispose();
  }
}
