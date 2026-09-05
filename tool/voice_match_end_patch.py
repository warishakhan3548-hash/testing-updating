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


path = "lib/services/voice_dice_controller.dart"

replace_once(
    path,
    """  bool _rollSuspended = false;\n  bool _matchSessionActive = false;\n  bool _lifecycleActive = true;\n""",
    """  bool _rollSuspended = false;\n  bool _matchSessionActive = false;\n  bool _matchSessionExplicitlyEnded = false;\n  bool _lifecycleActive = true;\n""",
)

replace_once(
    path,
    """    if (engine != null && !engine.gameOver) {\n      _binding = engine.voiceTurnBinding;\n""",
    """    if (engine != null &&\n        !engine.gameOver &&\n        !_matchSessionExplicitlyEnded) {\n      _binding = engine.voiceTurnBinding;\n""",
)

replace_once(
    path,
    """  Future<void> startMatchSession(TurnBinding binding) async {\n    if (_disposed) return;\n    _matchSessionActive = true;\n""",
    """  Future<void> startMatchSession(TurnBinding binding) async {\n    if (_disposed) return;\n    _matchSessionExplicitlyEnded = false;\n    _matchSessionActive = true;\n""",
)

replace_once(
    path,
    """    final engine = _engine;\n    if (engine == null) return;\n\n    final nowGameOver = engine.gameOver;\n""",
    """    final engine = _engine;\n    if (engine == null) return;\n\n    // endMatchSession() is an explicit ownership boundary. Clearing a pending\n    // engine intent emits a synchronous engine notification; without this guard\n    // that notification can accidentally reactivate and rebind voice after the\n    // match has already been stopped. Only startMatchSession() may clear this\n    // terminal match-session latch.\n    if (_matchSessionExplicitlyEnded) {\n      _engineWasGameOver = engine.gameOver;\n      _lastObservedEngineBinding = engine.voiceTurnBinding;\n      return;\n    }\n\n    final nowGameOver = engine.gameOver;\n""",
)

replace_once(
    path,
    """  Future<void> endMatchSession() async {\n    if (_disposed) return;\n    _matchSessionActive = false;\n""",
    """  Future<void> endMatchSession() async {\n    if (_disposed) return;\n    _matchSessionExplicitlyEnded = true;\n    _matchSessionActive = false;\n""",
)

print("Explicit match-end voice ownership race fixed.")
