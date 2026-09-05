#!/usr/bin/env python3
from pathlib import Path

path = Path("test/android_build_contract_test.dart")
text = path.read_text(encoding="utf-8")
old = "      expect(controller, contains('_enabled = false'));\n"
new = """      expect(controller, contains('bool _permissionDenied = false;'));\n      expect(controller, contains('_permissionDenied = true;'));\n      expect(controller, isNot(contains('_enabled = false;')));\n"""
count = text.count(old)
if count != 1:
    raise SystemExit(
        f"{path}: expected exactly one legacy permission contract, found {count}"
    )
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Updated Android voice permission contract.")
