import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import '../game/dice_roll_models.dart';

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

/// Deterministic Hindi + English + Hinglish parser for dice commands.
///
/// This deliberately rejects phrases containing unrelated vocabulary instead of
/// treating every occurrence of "six" (or another number) as a game command.
class DiceVoiceIntentParser {
  static const Map<String, int> _aliases = <String, int>{
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
    'छक्के': 6,
    'chakka': 6,
    'chhakka': 6,
    'chakkaa': 6,
    'सिक्स': 6,
    'सिक्सर': 6,
    'sixer': 6,
  };

  static const Set<String> _contextTokens = <String>{
    'a',
    'ab',
    'aa',
    'aana',
    'aaye',
    'again',
    'आ',
    'अब',
    'आए',
    'आना',
    'आना',
    'bhai',
    'भाई',
    'bolo',
    'बोलो',
    'bring',
    'chahiye',
    'चाहिए',
    'de',
    'दे',
    'dice',
    'फिर',
    'give',
    'i',
    'lao',
    'लाओ',
    'me',
    'mujhe',
    'मुझे',
    'na',
    'need',
    'now',
    'number',
    'please',
    'roll',
    'set',
    'should',
    'the',
    'to',
    'want',
    'यार',
    'yaar',
    'ना',
    'फिर',
    'चाहिये',
    'कर',
    'करो',
    'doit',
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

  static DiceVoiceParseResult? parse(
    String input, {
    double? recognitionConfidence,
  }) {
    final normalized = input
        .toLowerCase()
        .replaceAll('\u200c', '')
        .replaceAll('\u200d', '')
        .replaceAll('।', ' ')
        .replaceAll(RegExp(r'[^a-z0-9\u0900-\u097F]+'), ' ')
        .trim();
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

      if (!_contextTokens.contains(token)) {
        return null;
      }
      if (_strongCommandTokens.contains(token)) {
        strongContext = true;
      }
    }

    if (values.isEmpty) return null;

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
      value: values.last,
      confidence: confidence,
      strongContext: strongContext,
    );
  }
}

/// Match-scoped Android speech controller.
///
/// Platform speech callbacks never decide a dice result. They only emit a
/// turn-bound [PendingVoiceDiceIntent], which the authoritative Ludo engine can
/// accept or reject. Native callbacks carry the binding captured by the speech
/// cycle, so stale results cannot silently attach themselves to a newer turn.
class VoiceDiceController extends ChangeNotifier {
  VoiceDiceController({
    required bool Function(PendingVoiceDiceIntent intent) onIntent,
    VoidCallback? onClearPending,
    this.intentTtl = const Duration(minutes: 2),
  })  : _onIntent = onIntent,
        _onClearPending = onClearPending;

  static const MethodChannel _voiceChannel = MethodChannel('voice_ludo/speech');
  static const EventChannel _voiceEvents = EventChannel('voice_ludo/speech_events');

  final bool Function(PendingVoiceDiceIntent intent) _onIntent;
  final VoidCallback? _onClearPending;
  final Duration intentTtl;

  StreamSubscription<dynamic>? _eventSub;
  TurnBinding? _binding;
  bool _initialized = false;
  bool _initializing = false;
  bool _starting = false;
  bool _available = false;
  bool _enabled = true;
  bool _listening = false;
  bool _rollSuspended = false;
  bool _matchSessionActive = false;
  bool _lifecycleActive = true;
  bool _disposed = false;
  int _acceptedIntentSerial = 0;
  int? _lastAcceptedValue;

  VoiceSessionState _state = VoiceSessionState.idle;
  String _lastHeard = '';
  double? _lastConfidence;
  String? _errorMessage;

  bool get initialized => _initialized && !_initializing;
  bool get initializing => _initializing;
  bool get available => _available;
  bool get enabled => _enabled;
  bool get listening => _listening;
  bool get offlineReady => initialized && _available;
  String get engineName => 'Android SpeechRecognizer';
  String get lastHeard => _lastHeard;
  double? get lastConfidence => _lastConfidence;
  String? get errorMessage => _errorMessage;
  VoiceSessionState get state => _state;
  int get acceptedIntentSerial => _acceptedIntentSerial;
  int? get lastAcceptedValue => _lastAcceptedValue;
  TurnBinding? get binding => _binding;

  Future<void> initialize() async {
    if (_disposed || _initializing || _initialized) return;

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
      _errorMessage = _available
          ? null
          : 'Voice recognition is not available on this device.';
      _state = _available ? VoiceSessionState.idle : VoiceSessionState.error;
    } on PlatformException catch (error) {
      _initialized = true;
      _available = false;
      _listening = false;
      _state = VoiceSessionState.error;
      _errorMessage = error.message ?? 'Could not initialize voice recognition.';
    } catch (_) {
      _initialized = true;
      _available = false;
      _listening = false;
      _state = VoiceSessionState.error;
      _errorMessage = 'Could not initialize voice recognition.';
    } finally {
      _initializing = false;
      _safeNotify();
    }
  }

  Future<void> startMatchSession(TurnBinding binding) async {
    if (_disposed) return;
    _matchSessionActive = true;
    _binding = binding;
    _rollSuspended = false;

    if (!_initialized) {
      await initialize();
    }
    if (_disposed || !_enabled || !_available || !_lifecycleActive) return;
    await _startListening();
  }

  Future<void> bindTurn(TurnBinding binding) async {
    if (_disposed) return;
    if (_binding == binding) return;
    _binding = binding;
    _safeNotify();

    if (!_matchSessionActive || !_initialized || !_available) return;
    try {
      await _voiceChannel.invokeMethod<void>('updateContext', _bindingMap(binding));
    } catch (_) {
      // A failed context push is fail-safe: speech events without the exact new
      // binding are rejected in Dart, and manual gameplay continues normally.
    }
  }

  Future<void> setLifecycleActive(bool active) async {
    if (_disposed || _lifecycleActive == active) return;
    _lifecycleActive = active;

    if (!active) {
      _listening = false;
      _state = VoiceSessionState.paused;
      _onClearPending?.call();
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
          !_listening) {
        await _startListening();
      }
      return;
    }

    _enabled = value;
    _errorMessage = null;

    if (!value) {
      _listening = false;
      _rollSuspended = false;
      _state = VoiceSessionState.stopped;
      _onClearPending?.call();
      _safeNotify();
      try {
        await _voiceChannel.invokeMethod<void>('stopListening');
      } catch (_) {}
      return;
    }

    if (!_initialized) {
      await initialize();
    }
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
        _listening = false;
        _state = VoiceSessionState.error;
        _errorMessage = 'Voice recognition is not available on this device.';
        _safeNotify();
        return;
      }

      if (_matchSessionActive && _lifecycleActive && !_rollSuspended) {
        await _startListening();
      } else {
        _state = VoiceSessionState.idle;
        _safeNotify();
      }
    } on PlatformException catch (error) {
      _listening = false;
      _state = VoiceSessionState.error;
      _errorMessage = error.message ?? 'Could not restart voice recognition.';
      _safeNotify();
    } catch (_) {
      _listening = false;
      _state = VoiceSessionState.error;
      _errorMessage = 'Could not restart voice recognition.';
      _safeNotify();
    }
  }

  Future<void> suspendForRoll() async {
    if (_disposed) return;
    _rollSuspended = true;
    _listening = false;
    _state = VoiceSessionState.paused;
    _safeNotify();

    if (_available && _enabled) {
      try {
        await _voiceChannel.invokeMethod<void>('pauseListening');
      } catch (_) {}
    }
  }

  Future<void> resumeAfterRoll() async {
    if (_disposed) return;

    _rollSuspended = false;
    if (_matchSessionActive && _enabled && _available && _lifecycleActive) {
      await _startListening();
    } else {
      _safeNotify();
    }
  }

  Future<void> endMatchSession() async {
    if (_disposed) return;
    _matchSessionActive = false;
    _rollSuspended = false;
    _listening = false;
    _binding = null;
    _state = VoiceSessionState.stopped;
    _onClearPending?.call();
    _safeNotify();
    try {
      await _voiceChannel.invokeMethod<void>('stopListening');
    } catch (_) {}
  }

  Future<void> _startListening() async {
    final binding = _binding;
    if (_disposed ||
        _starting ||
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
    } on PlatformException catch (error) {
      _listening = false;
      _state = VoiceSessionState.error;
      _errorMessage = error.message ?? 'Could not start the microphone.';
    } catch (_) {
      _listening = false;
      _state = VoiceSessionState.error;
      _errorMessage = 'Could not start the microphone.';
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
            _listening = false;
            _state = VoiceSessionState.error;
            _errorMessage = 'Voice recognition is not available on this device.';
          }
          _safeNotify();
        }
        return;
      case 'listening':
        final active = event['active'];
        if (active is bool) {
          _listening = active &&
              _enabled &&
              _matchSessionActive &&
              _lifecycleActive &&
              !_rollSuspended;
          _state = _listening
              ? VoiceSessionState.listening
              : (_rollSuspended || !_lifecycleActive
                  ? VoiceSessionState.paused
                  : VoiceSessionState.restarting);
          _safeNotify();
        }
        return;
      case 'permission':
        final granted = event['granted'];
        if (granted == false) {
          _enabled = false;
          _listening = false;
          _state = VoiceSessionState.error;
          _onClearPending?.call();
          _errorMessage = 'Microphone permission is required for voice dice.';
          _safeNotify();
        } else if (granted == true) {
          _state = VoiceSessionState.starting;
          _safeNotify();
        }
        return;
      case 'unavailable':
        _available = false;
        _listening = false;
        _state = VoiceSessionState.error;
        _onClearPending?.call();
        _errorMessage = _eventMessage(event) ??
            'Voice recognition is not available on this device.';
        _safeNotify();
        return;
      case 'error':
        _listening = false;
        final recoverable = event['recoverable'] == true;
        _state = recoverable ? VoiceSessionState.restarting : VoiceSessionState.error;
        if (!recoverable) {
          _errorMessage = _eventMessage(event) ?? 'Voice recognition failed.';
        }
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

    final finalResult = event['final'] == true;
    final confidenceValues = event['confidences'];
    String? firstHeard;
    DiceVoiceParseResult? parsed;

    for (var i = 0; i < rawTexts.length; i++) {
      final item = rawTexts[i];
      if (item is! String) continue;
      final heard = item.trim();
      if (heard.isEmpty) continue;
      firstHeard ??= heard;

      final candidate = DiceVoiceIntentParser.parse(
        heard,
        recognitionConfidence: _confidenceAt(confidenceValues, i),
      );
      if (candidate == null) continue;

      // Bare partial words are intentionally not armed. Waiting for the final
      // callback prevents unrelated speech such as "six players" from briefly
      // forcing a six when its first partial result was only "six".
      if (!finalResult && !candidate.strongContext) continue;
      parsed = candidate;
      break;
    }

    if (firstHeard != null) {
      _lastHeard = firstHeard;
    }
    if (parsed == null) {
      _safeNotify();
      return;
    }

    final recognizedAt = _recognizedAt(event);
    final intent = PendingVoiceDiceIntent(
      matchId: eventBinding.matchId,
      playerId: eventBinding.playerId,
      turnId: eventBinding.turnId,
      requestedValue: parsed.value,
      recognizedAt: recognizedAt,
      expiresAt: recognizedAt.add(intentTtl),
    );

    if (_onIntent(intent)) {
      _lastConfidence = parsed.confidence;
      _lastAcceptedValue = parsed.value;
      _acceptedIntentSerial += 1;
      _errorMessage = null;
    }
    _safeNotify();
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

  String? _eventMessage(Map event) {
    final message = event['message'];
    return message is String && message.trim().isNotEmpty ? message.trim() : null;
  }

  void _handleEventStreamError(Object error, [StackTrace? stackTrace]) {
    if (_disposed) return;
    _listening = false;
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
    _disposed = true;
    _matchSessionActive = false;
    _listening = false;
    unawaited(_eventSub?.cancel());
    unawaited(_voiceChannel.invokeMethod<void>('stopListening').catchError((_) {}));
    super.dispose();
  }
}
