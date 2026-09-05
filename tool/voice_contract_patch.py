#!/usr/bin/env python3
from pathlib import Path

path = Path("test/android_build_contract_test.dart")
text = path.read_text(encoding="utf-8")

old_permission = "      expect(controller, contains('_enabled = false'));\n"
new_permission = """      expect(controller, contains('bool _permissionDenied = false;'));\n      expect(controller, contains('_permissionDenied = true;'));\n      expect(controller, isNot(contains('_enabled = false;')));\n"""
count = text.count(old_permission)
if count != 1:
    raise SystemExit(
        f"{path}: expected exactly one legacy permission contract, found {count}"
    )
text = text.replace(old_permission, new_permission, 1)

old_conflict = (
    "      expect(controller, contains('conflicting dice values are rejected'));\n"
)
new_conflict = """      expect(\n        controller,\n        contains('if (values.any((value) => value != requestedValue))'),\n      );\n"""
count = text.count(old_conflict)
if count != 1:
    raise SystemExit(
        f"{path}: expected exactly one prose-only conflict contract, found {count}"
    )
text = text.replace(old_conflict, new_conflict, 1)

path.write_text(text, encoding="utf-8")
print("Updated Android voice contracts to assert executable invariants.")
