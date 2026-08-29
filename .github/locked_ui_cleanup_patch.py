#!/usr/bin/env python3
from pathlib import Path

path = Path('lib/main.dart')
code = path.read_text(encoding='utf-8')


def remove_class(class_name: str) -> None:
    global code
    marker = f'class {class_name}'
    start = code.find(marker)
    if start < 0:
        raise SystemExit(f'SAFETY STOP: class not found: {class_name}')
    next_start = code.find('\nclass ', start + len(marker))
    if next_start < 0:
        raise SystemExit(f'SAFETY STOP: next class not found after {class_name}')
    code = code[:start] + code[next_start + 1:]


# The locked table system replaces these two legacy stick renderers everywhere.
remove_class('_RecordsCard')
remove_class('_RecordTile')

if '_RecordsCard(' in code or '_RecordTile(' in code:
    raise SystemExit('SAFETY STOP: legacy record renderer is still referenced')

path.write_text(code, encoding='utf-8')
print('Removed obsolete stick-based record renderer classes.')
