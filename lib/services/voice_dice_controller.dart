import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

/// A one-shot latch: the latest spoken value stays armed until a roll consumes it.
class VoiceDiceLatch {
  int? _value;

  int? get value => _value;

  void setValue(int value) {
    if (value < 1 || value > 6) {
      throw RangeError.range(value, 1, 6, 'value');
    }
    _value = value;
  }

  int? take() {
    final value = _value;
    _value = null;
    return value;
  }

  void clear() => _value = null;
}

/// Android-system speech recognition controller for instant voice-controlled dice.
///
/// A recognized number is latched with no timeout. The next roll consumes that
/// value exactly once. Recognition is paused only during the dice animation and
/// resumes immediately afterwards, even while a token is waiting to be moved.
class VoiceDiceController extends ChangeNotifier {
  static const MethodChannel _voiceChannel = MethodChannel('voice_ludo/speech');
  static const EventChannel _voiceEvents = EventChannel('voice_ludo/speech_events');

  final VoiceDiceLatch _latch = VoiceDiceLatch();

  StreamSubscription<dynamic>? _eventSub;
  bool _initialized = false;
  bool _initializing = false;
  bool _available = false;
  bool _enabled = true;
  bool _listening = false;
  bool _rollSuspended = false;
  bool _disposed = false;

  String _lastHeard = '';
  String? _errorMessage;

  bool get initialized => _initialized && !_initializing;
  bool get initializing => _initializing;
  bool get available => _available;
  bool get enabled => _enabled;
  bool get listening => _listening;
  bool get offlineReady => initialized && _available;
  String get engineName => 'Android Voice Recognition';
  int? get pendingValue => _latch.value;
  String get lastHeard => _lastHeard;
  double? get lastConfidence => null;
  String? get errorMessage => _errorMessage;

  Future<void> initialize() async {
    if (_disposed || _initializing || _initialized) return;

    _initializing = true;
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
          : 'Android voice recognition is not available on this device.';

      if (_enabled && _available) {
        await _startListening();
      }
    } on PlatformException catch (error) {
      _initialized = true;
      _available = false;
      _enabled = false;
      _listening = false;
      _errorMessage = error.message ?? 'Could not start voice recognition.';
    } catch (_) {
      _initialized = true;
      _available = false;
      _enabled = false;
      _listening = false;
      _errorMessage = 'Could not start voice recognition.';
    } finally {
      _initializing = false;
      _safeNotify();
    }
  }

  Future<void> setEnabled(bool value) async {
    if (_disposed) return;

    if (_enabled == value) {
      if (value && _available && !_rollSuspended && !_listening) {
        await _startListening();
      }
      return;
    }

    _enabled = value;
    _errorMessage = null;

    if (!value) {
      _listening = false;
      _rollSuspended = false;
      _latch.clear();
      _safeNotify();
      try {
        await _voiceChannel.invokeMethod<void>('stopListening');
      } catch (_) {}
      return;
    }

    if (!_initialized) {
      await initialize();
      return;
    }

    if (!_available) {
      await retry();
      return;
    }

    _safeNotify();
    if (!_rollSuspended) {
      await _startListening();
    }
  }

  Future<void> retry() async {
    if (_disposed) return;

    _enabled = true;
    _errorMessage = null;

    try {
      _available = await _voiceChannel.invokeMethod<bool>('isAvailable') ?? false;
      _initialized = true;
      if (!_available) {
        _enabled = false;
        _listening = false;
        _errorMessage = 'Android voice recognition is not available on this device.';
        _safeNotify();
        return;
      }

      _safeNotify();
      if (!_rollSuspended) {
        await _startListening();
      }
    } on PlatformException catch (error) {
      _enabled = false;
      _listening = false;
      _errorMessage = error.message ?? 'Could not restart voice recognition.';
      _safeNotify();
    } catch (_) {
      _enabled = false;
      _listening = false;
      _errorMessage = 'Could not restart voice recognition.';
      _safeNotify();
    }
  }

  Future<int?> suspendForRoll() async {
    if (_disposed) return null;

    final value = _latch.take();
    _rollSuspended = true;
    _listening = false;
    _safeNotify();

    if (_available && _enabled) {
      try {
        await _voiceChannel.invokeMethod<void>('pauseListening');
      } catch (_) {}
    }
    return value;
  }

  Future<void> resumeAfterRoll() async {
    if (_disposed) return;

    _rollSuspended = false;
    if (_enabled && _available) {
      await _startListening();
    } else {
      _safeNotify();
    }
  }

  void clearPending() {
    _latch.clear();
    _safeNotify();
  }

  Future<void> _startListening() async {
    if (_disposed || !_enabled || !_available || _rollSuspended) return;

    try {
      await _voiceChannel.invokeMethod<void>('startListening');
      _errorMessage = null;
    } on PlatformException catch (error) {
      _listening = false;
      _errorMessage = error.message ?? 'Could not start the microphone.';
    } catch (_) {
      _listening = false;
      _errorMessage = 'Could not start the microphone.';
    }
    _safeNotify();
  }

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
            _errorMessage = 'Android voice recognition is not available on this device.';
          }
          _safeNotify();
        }
        return;
      case 'listening':
        final active = event['active'];
        if (active is bool) {
          _listening = active && _enabled && !_rollSuspended;
          _safeNotify();
        }
        return;
      case 'permission':
        final granted = event['granted'];
        if (granted == false) {
          _enabled = false;
          _listening = false;
          _errorMessage = 'Microphone permission is required for voice dice.';
          _safeNotify();
        }
        return;
      case 'unavailable':
        _available = false;
        _enabled = false;
        _listening = false;
        _errorMessage = _eventMessage(event) ??
            'Android voice recognition is not available on this device.';
        _safeNotify();
        return;
      case 'error':
        _listening = false;
        final recoverable = event['recoverable'] == true;
        if (!recoverable) {
          _errorMessage = _eventMessage(event) ?? 'Voice recognition failed.';
        }
        _safeNotify();
        return;
      case 'speech':
        if (!_enabled || _rollSuspended) return;
        _handleSpeechAlternatives(event['texts']);
        return;
      default:
        return;
    }
  }

  void _handleSpeechAlternatives(dynamic rawTexts) {
    if (rawTexts is! List) return;

    String? firstHeard;
    int? value;
    for (final item in rawTexts) {
      if (item is! String) continue;
      final heard = item.trim();
      if (heard.isEmpty) continue;
      firstHeard ??= heard;
      value ??= parseLastDiceValue(heard);
      if (value != null) break;
    }

    if (firstHeard != null) {
      _lastHeard = firstHeard;
    }
    if (value != null) {
      _latch.setValue(value);
      _errorMessage = null;
    }
    _safeNotify();
  }

  String? _eventMessage(Map event) {
    final message = event['message'];
    return message is String && message.trim().isNotEmpty ? message.trim() : null;
  }

  void _handleEventStreamError(Object error, [StackTrace? stackTrace]) {
    if (_disposed) return;
    _listening = false;
    _errorMessage = 'Voice connection was interrupted. Tap the mic to retry.';
    _safeNotify();
  }

  static int? parseLastDiceValue(String input) {
    final normalized = input
        .toLowerCase()
        .replaceAll('\u200c', '')
        .replaceAll('\u200d', '')
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
      'छक्का': 6, 'छका': 6, 'चक्का': 6, 'छक्के': 6, 'chakka': 6,
      'chhakka': 6, 'chakkaa': 6, 'सिक्स': 6, 'सिक्सर': 6, 'sixer': 6,
    };

    int? latest;
    for (final token in normalized.split(RegExp(r'\s+'))) {
      final value = aliases[token];
      if (value != null) latest = value;
    }
    return latest;
  }

  void _safeNotify() {
    if (!_disposed) notifyListeners();
  }

  @override
  void dispose() {
    if (_disposed) return;
    _disposed = true;
    _listening = false;
    unawaited(_eventSub?.cancel());
    unawaited(_voiceChannel.invokeMethod<void>('stopListening').catchError((_) {}));
    super.dispose();
  }
}
