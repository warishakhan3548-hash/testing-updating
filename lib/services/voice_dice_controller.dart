import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import '../game/dice_roll_models.dart';
import '../game/ludo_engine.dart';

enum VoiceSessionState {
  idle,
  requestingPermission,
  starting,
  listening,
  processing,
  restarting,
  paused,
  stopped,
  error,
}

@immutable
class DiceVoiceParseResult {
  const DiceVoiceParseResult({
    required this.value,
    required this.confidence,
    required this.strongContext,
  });

  final int value;
  final double confidence;
  final bool strongContext;
}

@immutable
class _SpeechSessionKey {
  const _SpeechSessionKey({
    required this.binding,
    required this.recognizerEpoch,
    required this.sessionId,
  });

  final TurnBinding binding;
  final int recognizerEpoch;
  final int sessionId;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is _SpeechSessionKey &&
          other.binding == binding &&
          other.recognizerEpoch == recognizerEpoch &&
          other.sessionId == sessionId;

  @override
  int get hashCode => Object.hash(binding, recognizerEpoch, sessionId);
}

/// Deterministic Hindi + English + Hinglish parser for six dice commands.
///
/// This is intentionally a tiny grammar, not generic natural-language intent
/// detection. Exact/normalized vocabulary wins. Ambiguous multi-number phrases
/// are rejected instead of guessing, which prevents ordinary conversation from
/// accidentally mutating the game.
class DiceVoiceIntentParser {
  static const Map<String, int> _aliases = <String, int>{
    '1': 1,
    '१': 1,
    'one': 1,
    'एक': 1,
    'इक': 1,
    'ek': 1,
    'aik': 1,
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
    'tin': 3,
    'थ्री': 3,
    '4': 4,
    '४': 4,
    'four': 4,
    'चार': 4,
    'char': 4,
    'chaar': 4,
    'फोर': 4,
    'फौर': 4,
    '5': 5,
    '५': 5,
    'five': 5,
    'पांच': 5,
    'पाँच': 5,
    'पाच': 5,
    'पान्च': 5,
    'paanch': 5,
    'panch': 5,
    'panj': 5,
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
    'छक्क': 6,
    'छक': 6,
    'छको': 6,
    'चक्का': 6,
    'चका': 6,
    'चक्क': 6,
    'शक्का': 6,
    'छक्के': 6,
    'chakka': 6,
    'chaka': 6,
    'chhakka': 6,
    'chhaka': 6,
    'chakkaa': 6,
    'chhakkaa': 6,
    'shakka': 6,
    'सिक्स': 6,
    'सिक्सर': 6,
    'सिक': 6,
    'sixer': 6,
  };

  static const Set<String> _contextTokens = <String>{
    'a',
    'ab',
    'aa',
    'aana',
    'aaye',
    'aao',
    'again',
    'are',
    'आ',
    'अब',
    'आए',
    'आना',
    'आओ',
    'अरे',
    'bhai',
    'भाई',
    'bolo',
    'बोलो',
    'bring',
    'chahiye',
    'चाहिए',
    'chalo',
    'चलो',
    'de',
    'दे',
    'dice',
    'फिर',
    'give',
    'haan',
    'हाँ',
    'हां',
    'हा',
    'i',
    'ji',
    'जी',
    'lao',
    'लाओ',
    'me',
    'mujhe',
    'mujhko',
    'मुझे',
    'मुझको',
    'na',
    'need',
    'now',
    'number',
    'ok',
    'okay',
    'ओके',
    'please',
    'roll',
    'set',
    'should',
    'the',
    'to',
    'want',
    'yes',
    'यार',
    'yaar',
    'ना',
    'चाहिये',
    'कर',
    'करो',
  };

  static const Set<String> _strongCommandTokens = <String>{
    'give',
    'roll',
    'dice',
    'want',
    'need',
    'bring',
    'set',
    'de',
    'दे',
    'chahiye',
    'चाहिए',
    'चाहिये',
    'lao',
    'लाओ',
    'aana',
    'आना',
    'कर',
    'करो',
  };

  static String _normalize(String input) => input
      .toLowerCase()
      .replaceAll('\u200c', '')
      .replaceAll('\u200d', '')
      .replaceAll('।', ' ')
      .replaceAll(RegExp(r'[^a-z0-9\u0900-\u097F]+'), ' ')
      .trim();

  /// True when a partial hypothesis consists only of one repeated dice value.
  /// "छक्का छक्का" is safe; "six five" is deliberately ambiguous and false.
  static bool isDiceOnlyPhrase(String input) {
    final normalized = _normalize(input);
    if (normalized.isEmpty) return false;
    final tokens = normalized.split(RegExp(r'\s+'));
    final values = <int>[];
    for (final token in tokens) {
      final value = _aliases[token];
      if (value == null) return false;
      values.add(value);
    }
    return values.isNotEmpty && values.every((value) => value == values.first);
  }

  static DiceVoiceParseResult? parse(
    String input, {
    double? recognitionConfidence,
  }) {
    final normalized = _normalize(input);
    if (normalized.isEmpty) return null;

    if (recognitionConfidence != null &&
        recognitionConfidence >= 0 &&
        recognitionConfidence < .30) {
      return null;
    }

    final tokens = normalized.split(RegExp(r'\s+'));
    final values = <int>[];
    var strongContext = false;

    for (var i = 0; i < tokens.length; i++) {
      final token = tokens[i];
      final alias = _aliases[token];
      if (alias != null) {
        // "छक्का दे दो" / "chakka de do": the final "दो/do" is a verb,
        // not a request to replace six with two.
        final previous = i == 0 ? null : tokens[i - 1];
        if ((token == 'दो' || token == 'do') &&
            (previous == 'दे' || previous == 'de')) {
          continue;
        }
        values.add(alias);
        continue;
      }

      if (!_contextTokens.contains(token)) return null;
      if (_strongCommandTokens.contains(token)) strongContext = true;
    }

    if (values.isEmpty) return null;
    final requestedValue = values.first;
    if (!values.every((value) => value == requestedValue)) {
      // Never guess when one hypothesis contains two different dice values.
      return null;
    }

    final linguisticConfidence = tokens.length == 1
        ? 1.0
        : strongContext
            ? .98
            : .94;
    final confidence = recognitionConfidence != null && recognitionConfidence >= 0
        ? (linguisticConfidence * .72 + recognitionConfidence.clamp(0, 1) * .28)
            .clamp(0.0, 1.0)
            .toDouble()
        : linguisticConfidence;

    return DiceVoiceParseResult(
      value: requestedValue,
      confidence: confidence,
      strongContext: strongContext,
    );
  }
}

/// Match-scoped Android speech controller.
///
/// The native recognizer stays warm during dice animation/token movement while
/// Dart logically rejects speech outside a READY roll generation. This removes
/// an unnecessary cancel/recreate cycle from every roll without weakening turn
/// safety. Turn changes still hard-rotate the native recognizer epoch.
class VoiceDiceController extends ChangeNotifier {
  VoiceDiceController({
    LudoEngine? engine,
    bool Function(PendingVoiceDiceIntent intent)? onIntent,
    VoidCallback? onClearPending,
    int Function()? randomDice,
    this.intentTtl = const Duration(seconds: 5),
  })  : _engine = engine ?? LudoEngine.voiceRuntimeEngine,
        _externalOnIntent = onIntent,
        _externalClearPending = onClearPending {
    final rng = math.Random();
    _randomDice = randomDice ?? () => rng.nextInt(6) + 1;
    _binding = _engine?.voiceTurnBinding;
    _lastObservedEngineBinding = _binding;
    _engineWasGameOver = _engine?.gameOver ?? false;
    _engine?.addListener(_handleEngineStateChanged);
  }

  static const MethodChannel _voiceChannel = MethodChannel('voice_ludo/speech');
  static const EventChannel _voiceEvents = EventChannel('voice_ludo/speech_events');

  final LudoEngine? _engine;
  final bool Function(PendingVoiceDiceIntent intent)? _externalOnIntent;
  final VoidCallback? _externalClearPending;
  final Duration intentTtl;
  late final int Function() _randomDice;

  StreamSubscription<dynamic>? _eventSub;
  TurnBinding? _binding;
  TurnBinding? _lastObservedEngineBinding;
  _SpeechSessionKey? _lastAcceptedSpeechSession;

  bool _engineWasGameOver = false;
  bool _initialized = false;
  bool _initializing = false;
  bool _starting = false;
  bool _available = false;
  bool _enabled = true;
  bool _nativeListening = false;
  bool _rollSuspended = false;
  bool _matchSessionActive = false;
  bool _lifecycleActive = true;
  bool _disposed = false;
  int _acceptedIntentSerial = 0;
  int? _lastAcceptedValue;

  VoiceSessionState _state = VoiceSessionState.idle;
  String? _errorMessage;

  bool get initialized => _initialized && !_initializing;
  bool get initializing => _initializing;
  bool get available => _available;
  bool get enabled => _enabled;
  bool get listening =>
      _nativeListening &&
      _enabled &&
      _matchSessionActive &&
      _lifecycleActive &&
      !_rollSuspended;
  bool get offlineReady => initialized && _available;
  String get engineName => 'Android SpeechRecognizer';
  int? get pendingValue => _engine?.pendingVoiceDiceIntent?.requestedValue;

  // Intentionally do not expose raw transcript/confidence in production UI.
  // The game only needs the resolved bounded command value.
  String get lastHeard => '';
  double? get lastConfidence => null;

  String? get errorMessage => _errorMessage;
  VoiceSessionState get state => _state;
  int get acceptedIntentSerial => _acceptedIntentSerial;
  int? get lastAcceptedValue => _lastAcceptedValue;
  TurnBinding? get binding => _binding;

  bool _submitIntent(PendingVoiceDiceIntent intent) {
    final external = _externalOnIntent;
    if (external != null) return external(intent);
    return _engine?.acceptVoiceDiceIntent(intent) ?? false;
  }

  void _clearPendingIntent() {
    final external = _externalClearPending;
    if (external != null) {
      external();
    } else {
      _engine?.clearPendingVoiceIntent();
    }
  }

  Future<void> initialize() async {
    if (_disposed || _initializing || _initialized) return;

    final engine = _engine;
    if (engine != null && !engine.gameOver) {
      _binding = engine.voiceTurnBinding;
      _lastObservedEngineBinding = _binding;
      _matchSessionActive = true;
    }

    _initializing = true;
    _state = VoiceSessionState.starting;
    _safeNotify();

    _eventSub ??= _voiceEvents.receiveBroadcastStream().listen(
      _handleNativeEvent,
      onError: _handleEventStreamError,
    );

    try {
      _available = await _voiceChannel.invokeMethod<bool>('isAvailable') ?? false;
      _initialized = true;
      _errorMessage = _available ? null : 'Voice control is unavailable on this device.';
      _state = _available ? VoiceSessionState.idle : VoiceSessionState.error;

      if (_available &&
          _enabled &&
          _matchSessionActive &&
          _lifecycleActive &&
          _binding != null) {
        await _startListening();
      }
    } on PlatformException {
      _initialized = true;
      _available = false;
      _nativeListening = false;
      _state = VoiceSessionState.error;
      _errorMessage = 'Voice control could not start.';
    } catch (_) {
      _initialized = true;
      _available = false;
      _nativeListening = false;
      _state = VoiceSessionState.error;
      _errorMessage = 'Voice control could not start.';
    } finally {
      _initializing = false;
      _safeNotify();
    }
  }

  Future<void> startMatchSession(TurnBinding binding) async {
    if (_disposed) return;
    _matchSessionActive = true;
    _binding = binding;
    _lastObservedEngineBinding = binding;
    _lastAcceptedSpeechSession = null;
    _rollSuspended = false;

    if (!_initialized) await initialize();
    if (_disposed || !_enabled || !_available || !_lifecycleActive) return;
    await _startListening();
  }

  Future<void> bindTurn(TurnBinding binding) async {
    if (_disposed || _binding == binding) return;
    _binding = binding;
    _lastObservedEngineBinding = binding;
    _lastAcceptedSpeechSession = null;
    _safeNotify();

    if (!_matchSessionActive || !_initialized || !_available) return;
    try {
      await _voiceChannel.invokeMethod<void>('updateContext', _bindingMap(binding));
    } catch (_) {
      // Fail safe: any event without the exact current binding is rejected below.
    }
  }

  void _handleEngineStateChanged() {
    if (_disposed) return;
    final engine = _engine;
    if (engine == null) return;

    final nowGameOver = engine.gameOver;
    if (nowGameOver) {
      _engineWasGameOver = true;
      _lastObservedEngineBinding = engine.voiceTurnBinding;
      if (_matchSessionActive) {
        _matchSessionActive = false;
        _nativeListening = false;
        _lastAcceptedSpeechSession = null;
        _state = VoiceSessionState.stopped;
        _safeNotify();
        unawaited(_stopNativeOnly());
      }
      return;
    }

    final nextBinding = engine.voiceTurnBinding;
    final restartedMatch = _engineWasGameOver ||
        (_lastObservedEngineBinding != null &&
            _lastObservedEngineBinding!.matchId != nextBinding.matchId);
    _engineWasGameOver = false;

    if (!_matchSessionActive || restartedMatch) {
      _matchSessionActive = true;
      _binding = nextBinding;
      _lastObservedEngineBinding = nextBinding;
      _lastAcceptedSpeechSession = null;
      _rollSuspended = false;
      if (_initialized && _enabled && _available && _lifecycleActive) {
        unawaited(_startListening());
      }
      _safeNotify();
      return;
    }

    if (_binding != nextBinding) {
      _lastObservedEngineBinding = nextBinding;
      unawaited(bindTurn(nextBinding));
    }
  }

  Future<void> setLifecycleActive(bool active) async {
    if (_disposed || _lifecycleActive == active) return;
    _lifecycleActive = active;

    if (!active) {
      _nativeListening = false;
      _state = VoiceSessionState.paused;
      _clearPendingIntent();
      _safeNotify();
      try {
        await _voiceChannel.invokeMethod<void>('pauseListening');
      } catch (_) {}
      return;
    }

    if (_matchSessionActive && _enabled && _available && !_rollSuspended) {
      await _startListening();
    } else {
      _safeNotify();
    }
  }

  Future<void> setEnabled(bool value) async {
    if (_disposed) return;

    if (_enabled == value) {
      if (value &&
          _matchSessionActive &&
          _available &&
          _lifecycleActive &&
          !_rollSuspended &&
          !_nativeListening) {
        await _startListening();
      }
      return;
    }

    _enabled = value;
    _errorMessage = null;

    if (!value) {
      _nativeListening = false;
      _rollSuspended = false;
      _lastAcceptedSpeechSession = null;
      _state = VoiceSessionState.stopped;
      _clearPendingIntent();
      _safeNotify();
      try {
        await _voiceChannel.invokeMethod<void>('stopListening');
      } catch (_) {}
      return;
    }

    if (!_initialized) await initialize();
    if (!_available) {
      await retry();
      return;
    }

    if (_matchSessionActive && _lifecycleActive && !_rollSuspended) {
      await _startListening();
    }
  }

  Future<void> retry() async {
    if (_disposed) return;

    _enabled = true;
    _errorMessage = null;
    _state = VoiceSessionState.restarting;
    _safeNotify();

    try {
      _available = await _voiceChannel.invokeMethod<bool>('isAvailable') ?? false;
      _initialized = true;
      if (!_available) {
        _nativeListening = false;
        _state = VoiceSessionState.error;
        _errorMessage = 'Voice control is unavailable on this device.';
        _safeNotify();
        return;
      }

      if (_matchSessionActive && _lifecycleActive && !_rollSuspended) {
        await _startListening();
      } else {
        _state = VoiceSessionState.idle;
        _safeNotify();
      }
    } catch (_) {
      _nativeListening = false;
      _state = VoiceSessionState.error;
      _errorMessage = 'Voice control could not restart.';
      _safeNotify();
    }
  }

  /// Reserves the exact authoritative engine roll synchronously before the
  /// method reaches its first await. Speech remains physically warm in native
  /// code, but Dart rejects further speech until this roll generation finishes.
  /// That removes the old per-roll microphone cancel/restart gap.
  Future<int?> suspendForRoll() async {
    if (_disposed) return null;

    final engine = _engine;
    final reservation = engine?.reserveDiceRoll(randomDice: _randomDice);
    if (engine != null && reservation == null) return null;

    _rollSuspended = true;
    _state = VoiceSessionState.processing;
    _safeNotify();
    return reservation?.value;
  }

  Future<void> resumeAfterRoll() async {
    if (_disposed) return;

    _rollSuspended = false;
    final engine = _engine;
    if (engine != null && !engine.gameOver) {
      final nextBinding = engine.voiceTurnBinding;
      if (_binding != nextBinding) await bindTurn(nextBinding);
    }

    if (_matchSessionActive && _enabled && _available && _lifecycleActive) {
      if (_nativeListening) {
        _state = VoiceSessionState.listening;
        _safeNotify();
      } else {
        await _startListening();
      }
    } else {
      _safeNotify();
    }
  }

  void clearPending() {
    _clearPendingIntent();
    _safeNotify();
  }

  Future<void> endMatchSession() async {
    if (_disposed) return;
    _matchSessionActive = false;
    _rollSuspended = false;
    _nativeListening = false;
    _binding = null;
    _lastAcceptedSpeechSession = null;
    _state = VoiceSessionState.stopped;
    _clearPendingIntent();
    _safeNotify();
    await _stopNativeOnly();
  }

  Future<void> _stopNativeOnly() async {
    try {
      await _voiceChannel.invokeMethod<void>('stopListening');
    } catch (_) {}
  }

  Future<void> _startListening() async {
    final binding = _binding;
    if (_disposed ||
        _starting ||
        _nativeListening ||
        !_initialized ||
        !_enabled ||
        !_available ||
        !_matchSessionActive ||
        !_lifecycleActive ||
        _rollSuspended ||
        binding == null) {
      return;
    }

    _starting = true;
    _state = VoiceSessionState.starting;
    _safeNotify();
    try {
      await _voiceChannel.invokeMethod<void>('startListening', _bindingMap(binding));
      _errorMessage = null;
    } catch (_) {
      _nativeListening = false;
      _state = VoiceSessionState.error;
      _errorMessage = 'Microphone could not start.';
    } finally {
      _starting = false;
      _safeNotify();
    }
  }

  Map<String, Object> _bindingMap(TurnBinding binding) => <String, Object>{
        'matchId': binding.matchId,
        'playerId': binding.playerId,
        'turnId': binding.turnId,
      };

  void _handleNativeEvent(dynamic event) {
    if (_disposed || event is! Map) return;

    final type = event['type'];
    switch (type) {
      case 'availability':
        final available = event['available'];
        if (available is bool) {
          _available = available;
          if (!available) {
            _nativeListening = false;
            _state = VoiceSessionState.error;
            _errorMessage = 'Voice control is unavailable on this device.';
          }
          _safeNotify();
        }
        return;
      case 'lifecycle':
        final active = event['active'];
        if (active is bool) {
          _lifecycleActive = active;
          if (!active) {
            _nativeListening = false;
            _state = VoiceSessionState.paused;
            _clearPendingIntent();
          } else if (_matchSessionActive && _enabled && _available && !_rollSuspended) {
            unawaited(_startListening());
          }
          _safeNotify();
        }
        return;
      case 'listening':
        final active = event['active'];
        if (active is bool) {
          _nativeListening = active && _enabled && _matchSessionActive && _lifecycleActive;
          _state = listening
              ? VoiceSessionState.listening
              : _rollSuspended
                  ? VoiceSessionState.processing
                  : !_lifecycleActive
                      ? VoiceSessionState.paused
                      : VoiceSessionState.restarting;
          _safeNotify();
        }
        return;
      case 'permission':
        final granted = event['granted'];
        if (granted == false) {
          _enabled = false;
          _nativeListening = false;
          _state = VoiceSessionState.error;
          _clearPendingIntent();
          _errorMessage = 'Microphone permission is required for voice control.';
          _safeNotify();
        } else if (granted == true) {
          _state = VoiceSessionState.starting;
          _safeNotify();
        }
        return;
      case 'unavailable':
        _available = false;
        _nativeListening = false;
        _state = VoiceSessionState.error;
        _clearPendingIntent();
        _errorMessage = 'Voice control is unavailable on this device.';
        _safeNotify();
        return;
      case 'error':
        _nativeListening = false;
        final recoverable = event['recoverable'] == true;
        _state = recoverable ? VoiceSessionState.restarting : VoiceSessionState.error;
        if (!recoverable) _errorMessage = 'Voice control needs attention.';
        _safeNotify();
        return;
      case 'speech':
        if (!_enabled ||
            !_matchSessionActive ||
            !_lifecycleActive ||
            _rollSuspended) {
          return;
        }
        _handleSpeechAlternatives(event);
        return;
      default:
        return;
    }
  }

  void _handleSpeechAlternatives(Map event) {
    final rawTexts = event['texts'];
    if (rawTexts is! List) return;

    final currentBinding = _binding;
    final eventBinding = _bindingFromEvent(event);
    if (currentBinding == null || eventBinding == null || eventBinding != currentBinding) {
      return;
    }

    final speechSession = _speechSessionKey(event, eventBinding);
    if (speechSession == null || speechSession == _lastAcceptedSpeechSession) {
      return;
    }

    final finalResult = event['final'] == true;
    final confidenceValues = event['confidences'];
    DiceVoiceParseResult? parsed;

    for (var i = 0; i < rawTexts.length; i++) {
      final item = rawTexts[i];
      if (item is! String) continue;
      final heard = item.trim();
      if (heard.isEmpty) continue;

      final candidate = DiceVoiceIntentParser.parse(
        heard,
        recognitionConfidence: _confidenceAt(confidenceValues, i),
      );
      if (candidate == null) continue;

      // An unambiguous dice-only partial is the latency hot path. Longer natural
      // phrases are accepted from partials only with explicit command context.
      if (!finalResult &&
          !candidate.strongContext &&
          !DiceVoiceIntentParser.isDiceOnlyPhrase(heard)) {
        continue;
      }
      parsed = candidate;
      break;
    }

    if (parsed == null) return;

    final recognizedAt = _recognizedAt(event);
    final intent = PendingVoiceDiceIntent(
      matchId: eventBinding.matchId,
      playerId: eventBinding.playerId,
      turnId: eventBinding.turnId,
      requestedValue: parsed.value,
      recognizedAt: recognizedAt,
      expiresAt: recognizedAt.add(intentTtl),
    );

    if (_submitIntent(intent)) {
      _lastAcceptedSpeechSession = speechSession;
      _lastAcceptedValue = parsed.value;
      _acceptedIntentSerial += 1;
      _errorMessage = null;
      _safeNotify();
    }
  }

  _SpeechSessionKey? _speechSessionKey(Map event, TurnBinding binding) {
    final epoch = event['recognizerEpoch'];
    final sessionId = event['sessionId'];
    if (epoch is! num || sessionId is! num) return null;
    final parsedEpoch = epoch.toInt();
    final parsedSession = sessionId.toInt();
    if (parsedEpoch <= 0 || parsedSession <= 0) return null;
    return _SpeechSessionKey(
      binding: binding,
      recognizerEpoch: parsedEpoch,
      sessionId: parsedSession,
    );
  }

  TurnBinding? _bindingFromEvent(Map event) {
    final matchId = event['matchId'];
    final playerId = event['playerId'];
    final turnId = event['turnId'];
    if (matchId is! String || playerId is! String || turnId is! num) return null;
    return TurnBinding(
      matchId: matchId,
      playerId: playerId,
      turnId: turnId.toInt(),
    );
  }

  DateTime _recognizedAt(Map event) {
    final millis = event['recognizedAtMs'];
    if (millis is num && millis.toInt() > 0) {
      return DateTime.fromMillisecondsSinceEpoch(millis.toInt());
    }
    return DateTime.now();
  }

  double? _confidenceAt(dynamic raw, int index) {
    if (raw is! List || index >= raw.length) return null;
    final value = raw[index];
    if (value is! num) return null;
    final confidence = value.toDouble();
    return confidence < 0 ? null : confidence.clamp(0.0, 1.0).toDouble();
  }

  void _handleEventStreamError(Object error, [StackTrace? stackTrace]) {
    if (_disposed) return;
    _nativeListening = false;
    _state = VoiceSessionState.error;
    _errorMessage = 'Voice connection was interrupted. Tap the mic to retry.';
    _safeNotify();
  }

  static int? parseLastDiceValue(String input) =>
      DiceVoiceIntentParser.parse(input)?.value;

  void _safeNotify() {
    if (!_disposed) notifyListeners();
  }

  @override
  void dispose() {
    if (_disposed) return;
    _engine?.removeListener(_handleEngineStateChanged);
    _disposed = true;
    _matchSessionActive = false;
    _nativeListening = false;
    _lastAcceptedSpeechSession = null;
    unawaited(_eventSub?.cancel());
    unawaited(_voiceChannel.invokeMethod<void>('stopListening').catchError((_) {}));
    super.dispose();
  }
}
