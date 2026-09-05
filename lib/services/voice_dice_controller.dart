import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart';
import 'package:vosk_flutter_service/vosk_flutter_service.dart';

/// Offline, command-focused voice recognizer for the Ludo dice.
class VoiceDiceController extends ChangeNotifier with WidgetsBindingObserver {
  VoiceDiceController() {
    WidgetsBinding.instance.addObserver(this);
  }

  static const MethodChannel _nativeModelChannel =
      MethodChannel('voice_ludo/native_model');
  static const int sampleRate = 16000;
  static const Duration candidateFreshness = Duration(milliseconds: 1400);

  static const List<String> commandGrammar = <String>[
    '[unk]',
    'एक', 'इक', 'वन',
    'दो', 'टू',
    'तीन', 'थ्री',
    'चार', 'फोर',
    'पांच', 'पाँच', 'पाच', 'फाइव', 'फाईव',
    'छह', 'छः', 'छे', 'छक्का', 'छका', 'चक्का', 'सिक्स',
    'एक नंबर', 'दो नंबर', 'तीन नंबर', 'चार नंबर',
    'पांच नंबर', 'पाँच नंबर', 'छह नंबर', 'छक्का नंबर',
  ];

  // vosk_flutter_service keeps Android Model objects in a plugin-level map and
  // Model.dispose() does not release that Android object. Creating a fresh
  // Model every time GameScreen is opened therefore leaks a large native model.
  // Keep exactly one process-wide model load and create lightweight recognizers
  // per controller instead.
  static Model? _sharedModel;
  static String? _sharedModelPath;
  static Future<Model>? _sharedModelFuture;

  // The Android plugin owns exactly one SpeechService. Destruction is async, so
  // a quick back -> Play sequence must not initialize the next service while
  // the previous controller is still tearing the native service down.
  static Future<void> _globalServiceRelease = Future<void>.value();

  final VoskFlutterPlugin _vosk = VoskFlutterPlugin.instance();

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
  int _generation = 0;

  int? _pendingValue;
  DateTime? _pendingAt;
  int? _candidateValue;
  DateTime? _candidateAt;
  int? _lastPartialValue;
  int _partialHits = 0;
  String _lastHeard = '';
  double? _lastConfidence;
  String? _errorMessage;

  bool get initialized => _initialized && !_initializing;
  bool get initializing => _initializing;
  bool get available => _available;
  bool get enabled => _enabled;
  bool get listening => _listening;
  bool get offlineReady => initialized && _available;
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
      await _ensureRecognizer();
      if (_disposed || _recognizer == null) return;

      if (_enabled && !_lifecyclePaused) {
        await _ensureSpeechService();
      }
      if (_disposed) return;

      _available = true;
      _errorMessage = null;
      _safeNotify();

      if (_enabled && !_rollSuspended && !_lifecyclePaused) {
        await _startListening();
      }
    } on MicrophoneAccessDeniedException {
      await _markPermissionFailure();
    } catch (error) {
      _available = false;
      _enabled = false;
      _listening = false;
      await _releaseSpeechService();
      _errorMessage = _friendlyInitError(error);
      _safeNotify();
    } finally {
      _initializing = false;
      _safeNotify();
    }
  }

  Future<String> _prepareModelPath() async {
    final path = await _nativeModelChannel.invokeMethod<String>(
      'prepareOfflineVoskModel',
    );
    if (path == null || path.trim().isEmpty) {
      throw StateError('Android did not return an offline Vosk model path.');
    }
    return path;
  }

  Future<Model> _obtainSharedModel(String modelPath) async {
    final cached = _sharedModel;
    if (cached != null && _sharedModelPath == modelPath) return cached;

    final inFlight = _sharedModelFuture;
    if (inFlight != null) return inFlight;

    final load = _vosk.createModel(modelPath);
    _sharedModelFuture = load;
    try {
      final model = await load;
      _sharedModel = model;
      _sharedModelPath = modelPath;
      return model;
    } finally {
      if (identical(_sharedModelFuture, load)) {
        _sharedModelFuture = null;
      }
    }
  }

  Future<void> _ensureRecognizer() async {
    if (_model == null) {
      final cached = _sharedModel;
      if (cached != null) {
        _model = cached;
      } else {
        // Do NOT use vosk_flutter_service ModelLoader here. Its asset loader
        // reads and decodes the whole ZIP in Dart memory. Android streams the
        // ZIP directly to disk instead, which avoids a large first-play spike.
        final modelPath = await _prepareModelPath();
        if (_disposed) return;
        final model = await _obtainSharedModel(modelPath);
        if (_disposed) {
          // The process-wide model intentionally remains cached. On Android the
          // plugin itself owns that native Model until engine detach, so trying
          // to create/dispose another copy here would only increase leak risk.
          return;
        }
        _model = model;
      }
    }
    if (_disposed || _model == null) return;

    if (_recognizer == null) {
      final recognizer = await _vosk.createRecognizer(
        model: _model!,
        sampleRate: sampleRate,
        grammar: commandGrammar,
      );
      if (_disposed) {
        try {
          await recognizer.dispose();
        } catch (_) {}
        return;
      }

      await recognizer.setMaxAlternatives(1);
      if (_disposed) {
        try {
          await recognizer.dispose();
        } catch (_) {}
        return;
      }
      _recognizer = recognizer;
    }
  }

  Future<void> _ensureSpeechService() async {
    if (_disposed || _speechService != null) return;

    // Wait for the previous GameScreen's native SpeechService destruction. The
    // upstream plugin rejects a second service while the first still exists.
    try {
      await _globalServiceRelease;
    } catch (_) {}
    if (_disposed || _speechService != null) return;

    final recognizer = _recognizer;
    if (recognizer == null) return;

    final service = await _vosk.initSpeechService(recognizer);
    if (_disposed) {
      try {
        await service.dispose();
      } catch (_) {}
      return;
    }

    _speechService = service;
    _serviceStarted = false;
    _servicePaused = false;
    _attachStreams(service);
  }

  void _attachStreams(SpeechService service) {
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
      if (value && !_available && !_initializing) {
        await retry();
      }
      return;
    }

    _enabled = value;
    _errorMessage = null;

    if (!value) {
      _generation += 1;
      _listening = false;
      _clearAllCommands();
      await _releaseSpeechService();
      _safeNotify();
      return;
    }

    _safeNotify();
    if (_initializing) return;

    if (!_available) {
      await retry();
      return;
    }

    if (!_rollSuspended && !_lifecyclePaused) {
      await _startListening();
    }
  }

  Future<void> retry() async {
    if (_disposed) return;

    _enabled = true;
    _errorMessage = null;
    _generation += 1;
    _listening = false;
    _clearAllCommands();

    if (_initializing) {
      _safeNotify();
      return;
    }

    await _releaseSpeechService();

    if (_model == null || _recognizer == null) {
      _available = false;
      _initialized = false;
      _safeNotify();
      await initialize();
      return;
    }

    try {
      if (!_lifecyclePaused) {
        await _ensureSpeechService();
      }
      _available = true;
      _initialized = true;
      _safeNotify();

      if (!_rollSuspended && !_lifecyclePaused) {
        await _startListening();
      }
    } on MicrophoneAccessDeniedException {
      await _markPermissionFailure();
    } catch (_) {
      _available = false;
      _enabled = false;
      await _releaseSpeechService();
      _errorMessage = 'Could not reopen the offline microphone.';
      _safeNotify();
    }
  }

  Future<int?> suspendForRoll() async {
    if (_disposed) return null;

    final value = resolveNewestDiceCommand(
      pendingValue: _pendingValue,
      pendingAt: _pendingAt,
      candidateValue: _candidateValue,
      candidateAt: _candidateAt,
      now: DateTime.now(),
    );

    _rollSuspended = true;
    _generation += 1;
    _listening = false;
    _clearAllCommands();

    await _pauseServiceIfNeeded();
    _safeNotify();
    return value;
  }

  Future<void> resumeAfterRoll() async {
    if (_disposed) return;

    _rollSuspended = false;
    _clearCandidate();

    try {
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

    final generation = ++_generation;

    try {
      await _ensureSpeechService();
      final service = _speechService;
      if (service == null ||
          _disposed ||
          generation != _generation ||
          _rollSuspended ||
          _lifecyclePaused) {
        return;
      }

      if (_serviceStarted) {
        if (_servicePaused) {
          await service.setPause(paused: false);
          if (!identical(service, _speechService)) return;
          _servicePaused = false;
        }
      } else {
        await service.start(onRecognitionError: _handleRecognitionError);
        if (!identical(service, _speechService) || _disposed) return;
        _serviceStarted = true;
        _servicePaused = false;
      }

      if (generation != _generation || _rollSuspended || _lifecyclePaused) {
        await _pauseServiceIfNeeded();
        return;
      }

      _listening = true;
      _errorMessage = null;
      _safeNotify();
    } on MicrophoneAccessDeniedException {
      if (_disposed || generation != _generation) return;
      await _markPermissionFailure();
    } catch (_) {
      if (_disposed || generation != _generation) return;
      _enabled = false;
      _listening = false;
      await _releaseSpeechService();
      _errorMessage = 'Could not start the offline microphone recognizer.';
      _safeNotify();
    }
  }

  Future<void> _pauseServiceIfNeeded() async {
    final service = _speechService;
    if (service == null || !_serviceStarted || _servicePaused) return;

    try {
      await service.setPause(paused: true);
      if (identical(service, _speechService)) {
        _servicePaused = true;
      }
    } catch (_) {}
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    unawaited(_handleLifecycleState(state));
  }

  Future<void> _handleLifecycleState(AppLifecycleState state) async {
    if (_disposed) return;

    if (state == AppLifecycleState.resumed) {
      _lifecyclePaused = false;
      if (_enabled && _available && !_rollSuspended) {
        try {
          await _speechService?.reset();
        } catch (_) {}
        await _startListening();
      } else {
        _safeNotify();
      }
      return;
    }

    _lifecyclePaused = true;
    _generation += 1;
    _listening = false;
    _clearAllCommands();
    await _pauseServiceIfNeeded();
    _safeNotify();
  }

  void _handleRecognitionError(Object error, [StackTrace? stackTrace]) {
    if (_disposed || _lifecyclePaused || _rollSuspended) return;
    _runtimeVoiceFailure('Offline voice paused. Tap the mic to retry.');
  }

  void _handleStreamError(Object error, [StackTrace? stackTrace]) {
    if (_disposed || _lifecyclePaused || _rollSuspended) return;
    _runtimeVoiceFailure('Offline voice stream paused. Tap the mic to retry.');
  }

  void _runtimeVoiceFailure(String message) {
    _generation += 1;
    _listening = false;
    _enabled = false;
    _errorMessage = message;
    _safeNotify();
    unawaited(_releaseSpeechService());
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

    final confidence = hypothesis.confidence;
    final normalizedVeryWeak = isFinal &&
        confidence != null &&
        confidence >= 0 &&
        confidence <= 1 &&
        confidence < .18;
    if (normalizedVeryWeak) {
      _safeNotify();
      return;
    }

    final heardAt = DateTime.now();
    _candidateValue = value;
    _candidateAt = heardAt;

    if (isFinal) {
      _commitCandidate(value, heardAt);
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

    if (_partialHits >= 2) {
      _commitCandidate(value, heardAt);
    } else {
      _safeNotify();
    }
  }

  void _commitCandidate(int value, DateTime heardAt) {
    _pendingValue = value;
    _pendingAt = heardAt;
    _errorMessage = null;
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

  static int? resolveNewestDiceCommand({
    required int? pendingValue,
    required DateTime? pendingAt,
    required int? candidateValue,
    required DateTime? candidateAt,
    required DateTime now,
  }) {
    final pendingFresh = pendingValue != null &&
        pendingAt != null &&
        !pendingAt.isAfter(now) &&
        now.difference(pendingAt) <= candidateFreshness;
    final candidateFresh = candidateValue != null &&
        candidateAt != null &&
        !candidateAt.isAfter(now) &&
        now.difference(candidateAt) <= candidateFreshness;

    if (!candidateFresh) return pendingFresh ? pendingValue : null;
    if (!pendingFresh) return candidateValue;

    return candidateAt!.isBefore(pendingAt!) ? pendingValue : candidateValue;
  }

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
          final score = decoded['confidence'];
          return (
            text: text.trim(),
            confidence: score is num ? score.toDouble() : null,
          );
        }

        final alternatives = decoded['alternatives'];
        if (alternatives is List) {
          for (final item in alternatives) {
            if (item is! Map) continue;
            final text = item['text'];
            if (text is! String || text.trim().isEmpty) continue;
            final score = item['confidence'];
            return (
              text: text.trim(),
              confidence: score is num ? score.toDouble() : null,
            );
          }
        }
      }
    } catch (_) {
      // Some platform versions already return plain recognized text.
    }

    return (text: trimmed, confidence: null);
  }

  static int? parseLastDiceValue(String input) {
    final normalized = input
        .toLowerCase()
        .replaceAll('।', ' ')
        .replaceAll(RegExp(r'[^a-z0-9\u0900-\u097F]+'), ' ')
        .trim();
    if (normalized.isEmpty) return null;

    const aliases = <String, int>{
      '1': 1, '१': 1, 'one': 1, 'एक': 1, 'इक': 1, 'ek': 1, 'वन': 1,
      '2': 2, '२': 2, 'two': 2, 'दो': 2, 'do': 2, 'टू': 2,
      '3': 3, '३': 3, 'three': 3, 'तीन': 3, 'teen': 3, 'थ्री': 3,
      '4': 4, '४': 4, 'four': 4, 'चार': 4, 'char': 4, 'chaar': 4,
      'फोर': 4,
      '5': 5, '५': 5, 'five': 5, 'पांच': 5, 'पाँच': 5, 'पाच': 5,
      'paanch': 5, 'panch': 5, 'फाइव': 5, 'फाईव': 5,
      '6': 6, '६': 6, 'six': 6, 'छह': 6, 'छः': 6, 'छे': 6,
      'छक्का': 6, 'छका': 6, 'चक्का': 6, 'chakka': 6, 'chhakka': 6,
      'सिक्स': 6,
    };

    int? latest;
    for (final token in normalized.split(RegExp(r'\s+'))) {
      final value = aliases[token];
      if (value != null) latest = value;
    }
    return latest;
  }

  Future<void> _markPermissionFailure() async {
    _available = false;
    _enabled = false;
    _listening = false;
    await _releaseSpeechService();
    _errorMessage = 'Microphone permission is required for offline voice dice.';
    _safeNotify();
  }

  String _friendlyInitError(Object error) {
    final lower = error.toString().toLowerCase();
    if (lower.contains('ram') || lower.contains('memory')) {
      return 'Not enough free memory for offline voice. Random dice still works.';
    }
    if (lower.contains('storage') || lower.contains('space')) {
      return 'Not enough free storage for offline voice. Random dice still works.';
    }
    if (lower.contains('asset') ||
        lower.contains('model') ||
        lower.contains('prepare') ||
        lower.contains('corrupt') ||
        lower.contains('incomplete')) {
      return 'Offline Hindi voice model could not be prepared. Random dice still works.';
    }
    return 'Offline voice setup failed. You can still use random dice.';
  }

  Future<void> _releaseSpeechServiceNow() async {
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

  Future<void> _releaseSpeechService() {
    final release = _releaseSpeechServiceNow();
    _globalServiceRelease = release.catchError((_) {});
    return release;
  }

  void _safeNotify() {
    if (!_disposed) notifyListeners();
  }

  Future<void> _shutdown() async {
    await _releaseSpeechService();

    final recognizer = _recognizer;
    _recognizer = null;
    _model = null;
    if (recognizer != null) {
      try {
        await recognizer.dispose();
      } catch (_) {}
    }
    // Do not dispose _sharedModel here. On Android the upstream plugin owns the
    // native Model for the FlutterEngine lifetime, and its Dart Model.dispose()
    // does not release that Android object. Reusing one process-wide model is
    // the leak-safe lifecycle for repeated GameScreen entries.
  }

  @override
  void dispose() {
    if (_disposed) return;
    _disposed = true;
    _generation += 1;
    WidgetsBinding.instance.removeObserver(this);
    unawaited(_shutdown());
    super.dispose();
  }
}
