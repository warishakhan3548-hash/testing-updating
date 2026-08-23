from pathlib import Path
import re
import subprocess
import tempfile

html = Path('index.html').read_text(encoding='utf-8')
pattern = re.compile(r'<script(?P<attrs>[^>]*)>(?P<body>.*?)</script>', re.IGNORECASE | re.DOTALL)
checked = 0
for index, match in enumerate(pattern.finditer(html), 1):
    attrs = match.group('attrs').lower()
    if 'src=' in attrs or 'application/ld+json' in attrs:
        continue
    with tempfile.NamedTemporaryFile('w', suffix='.js', encoding='utf-8', delete=False) as script_file:
        script_file.write(match.group('body'))
        script_path = script_file.name
    result = subprocess.run(['node', '--check', script_path], capture_output=True, text=True)
    if result.returncode:
        raise SystemExit(f'inline JavaScript block {index} failed:\n{result.stderr}')
    checked += 1

print(f'PASS: node syntax check for {checked} inline JavaScript blocks')
