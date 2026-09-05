#!/usr/bin/env python3
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one patch target, found {count}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"patched {path}")


# 1) Keep permission state separate from the user's voice-enabled preference.
replace_once(
    "lib/services/voice_dice_controller.dart",
    """  bool _available = false;\n  bool _enabled = true;\n  bool _listening = false;\n""",
    """  bool _available = false;\n  bool _enabled = true;\n  bool _permissionDenied = false;\n  bool _listening = false;\n""",
)

replace_once(
    "lib/services/voice_dice_controller.dart",
    """  int _acceptedIntentSerial = 0;\n  int? _lastAcceptedValue;\n""",
    """  int _acceptedIntentSerial = 0;\n  int? _lastAcceptedValue;\n  int? _lastAcceptedNativeSessionEpoch;\n  TurnBinding? _lastAcceptedNativeSessionBinding;\n""",
)

replace_once(
    "lib/services/voice_dice_controller.dart",
    """    if (!_available) return 'Voice control is unavailable on this device.';\n    if (!_enabled) return 'Microphone access is needed for voice control.';\n    return 'Voice control needs attention. Tap the mic to retry.';\n""",
    """    if (!_available) return 'Voice control is unavailable on this device.';\n    if (_permissionDenied) return 'Microphone access is needed for voice control.';\n    if (!_enabled) return 'Voice control is turned off.';\n    return 'Voice control needs attention. Tap the mic to retry.';\n""",
)

replace_once(
    "lib/services/voice_dice_controller.dart",
    """        if ((token == 'दो' || token == 'do') &&\n            (previous == 'दे' || previous == 'de')) {\n          continue;\n        }\n""",
    """        if ((token == 'दो' || token == 'do') &&\n            (previous == 'दे' ||\n                previous == 'de' ||\n                previous == 'कर' ||\n                previous == 'करो')) {\n          continue;\n        }\n""",
)

replace_once(
    "lib/services/voice_dice_controller.dart",
    """    'छे': 6,\n    'छक्का': 6,\n""",
    """    'छे': 6,\n    'छ': 6,\n    'cheh': 6,\n    'chhe': 6,\n    'छक्का': 6,\n""",
)

replace_once(
    "lib/services/voice_dice_controller.dart",
    """      case 'listening':\n        final active = event['active'];\n        if (active is bool) {\n          _listening = active &&\n""",
    """      case 'listening':\n        final active = event['active'];\n        if (active is bool) {\n          if (active) _permissionDenied = false;\n          _listening = active &&\n""",
)

replace_once(
    "lib/services/voice_dice_controller.dart",
    """      case 'permission':\n        final granted = event['granted'];\n        if (granted == false) {\n          _enabled = false;\n          _listening = false;\n          _state = VoiceSessionState.error;\n          _clearPendingIntent();\n          _internalErrorMessage = 'Microphone permission denied.';\n          _safeNotify();\n        } else if (granted == true) {\n          _state = VoiceSessionState.starting;\n          _safeNotify();\n        }\n        return;\n""",
    """      case 'permission':\n        final granted = event['granted'];\n        if (granted == false) {\n          // Permission is an OS capability, not the user's voice preference.\n          // Keeping _enabled true means a later Settings permission restore can\n          // resume automatically on lifecycle/start without requiring a second\n          // in-app enable toggle.\n          _permissionDenied = true;\n          _listening = false;\n          _state = VoiceSessionState.error;\n          _clearPendingIntent();\n          _internalErrorMessage = 'Microphone permission denied.';\n          _safeNotify();\n        } else if (granted == true) {\n          _permissionDenied = false;\n          _state = VoiceSessionState.starting;\n          _safeNotify();\n        }\n        return;\n""",
)

# 2) Deduplicate accepted partial/final callbacks from one native utterance.
replace_once(
    "lib/services/voice_dice_controller.dart",
    """    if (currentBinding == null ||\n        eventBinding == null ||\n        eventBinding != currentBinding) {\n      return;\n    }\n\n    final finalResult = event['final'] == true;\n""",
    """    if (currentBinding == null ||\n        eventBinding == null ||\n        eventBinding != currentBinding) {\n      return;\n    }\n\n    final rawSessionEpoch = event['sessionEpoch'];\n    final sessionEpoch =\n        rawSessionEpoch is num ? rawSessionEpoch.toInt() : null;\n    if (sessionEpoch != null &&\n        _lastAcceptedNativeSessionEpoch == sessionEpoch &&\n        _lastAcceptedNativeSessionBinding == eventBinding) {\n      // One utterance can emit several partials plus a final result. Once one\n      // command from this exact native session is accepted, all later callbacks\n      // from that utterance are feedback duplicates, never new dice intents.\n      return;\n    }\n\n    final finalResult = event['final'] == true;\n""",
)

replace_once(
    "lib/services/voice_dice_controller.dart",
    """    if (_submitIntent(intent)) {\n      _lastConfidence = parsed.confidence;\n      _lastAcceptedValue = parsed.value;\n      _acceptedIntentSerial += 1;\n      _internalErrorMessage = null;\n    }\n""",
    """    if (_submitIntent(intent)) {\n      _lastConfidence = parsed.confidence;\n      _lastAcceptedValue = parsed.value;\n      if (sessionEpoch != null) {\n        _lastAcceptedNativeSessionEpoch = sessionEpoch;\n        _lastAcceptedNativeSessionBinding = eventBinding;\n      }\n      _acceptedIntentSerial += 1;\n      _internalErrorMessage = null;\n    }\n""",
)

# 3) Remove the artificial post-move blind window. The engine has already
# atomically transitioned the turn before this point, so voice can safely bind
# and listen for the next roll immediately.
replace_once(
    "lib/ui/game_screen.dart",
    """    await Future<void>.delayed(const Duration(milliseconds: 330));\n    if (!mounted) return;\n\n    if (_engine.gameOver) {\n      _showWinnerDialog();\n    } else {\n      await _voice.resumeAfterRoll();\n    }\n""",
    """    if (_engine.gameOver) {\n      _showWinnerDialog();\n      return;\n    }\n\n    // The move/turn transition above is already authoritative. Resume the\n    // recognizer immediately instead of creating a 330 ms blind window in\n    // which the next player can speak before Android is listening again.\n    await _voice.resumeAfterRoll();\n""",
)

# 4) Regression tests for the newly hardened grammar paths.
replace_once(
    "test/voice_turn_binding_test.dart",
    """      expect(VoiceDiceController.parseLastDiceValue('chhaka'), 6);\n      expect(VoiceDiceController.parseLastDiceValue('फौर'), 4);\n""",
    """      expect(VoiceDiceController.parseLastDiceValue('chhaka'), 6);\n      expect(VoiceDiceController.parseLastDiceValue('छ'), 6);\n      expect(VoiceDiceController.parseLastDiceValue('chhe'), 6);\n      expect(VoiceDiceController.parseLastDiceValue('फौर'), 4);\n""",
)

replace_once(
    "test/voice_turn_binding_test.dart",
    """      expect(VoiceDiceController.parseLastDiceValue('अरे पाँच'), 5);\n      expect(VoiceDiceController.parseLastDiceValue('we have six players'), isNull);\n""",
    """      expect(VoiceDiceController.parseLastDiceValue('अरे पाँच'), 5);\n      expect(VoiceDiceController.parseLastDiceValue('कर दो'), isNull);\n      expect(VoiceDiceController.parseLastDiceValue('करो दो'), isNull);\n      expect(VoiceDiceController.parseLastDiceValue('we have six players'), isNull);\n""",
)

replace_once(
    "pubspec.yaml",
    "version: 1.4.0+12\n",
    "version: 1.4.1+13\n",
)

print("Voice reliability hardening patch applied successfully.")
