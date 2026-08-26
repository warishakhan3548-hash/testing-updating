from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path('/home/ubuntu/testing-updating')
html = (ROOT / 'index.html').read_text(encoding='utf-8')

# Validate every inline JavaScript block except JSON-LD and ensure the AI handler is structurally present.
blocks = re.findall(r'<script(?:\s[^>]*)?>([\s\S]*?)</script>', html, flags=re.I)
js_count = 0
for index, block in enumerate(blocks):
    if not block.strip() or block.lstrip().startswith('{'):
        continue
    with tempfile.NamedTemporaryFile('w', suffix='.js', encoding='utf-8', delete=False) as handle:
        handle.write(block)
        temp_path = handle.name
    result = subprocess.run(['node', '--check', temp_path], text=True, capture_output=True)
    Path(temp_path).unlink(missing_ok=True)
    if result.returncode:
        raise SystemExit(f'inline script {index} syntax error:\n{result.stderr}')
    js_count += 1

handler_start = html.index('window.handleAIPaste = async function() {')
handler_end = html.index('\n};\n</script>\n<!-- AARISH_AI_PROMPT_AUTOPASTE_ENGINE_V1_END -->', handler_start)
handler = html[handler_start:handler_end]
assert 'fullFirebaseSyncCostV81' not in handler, 'destructive full sync still called by AI handler'
assert 'ai-full-state-delta' in handler, 'full-state delta reason missing'
assert "if (key === 'records') return;" in handler, 'group profile records are not protected from parent writes'
assert 'local-before-queue' in handler and 'local-after-queue' in handler, 'convergence-safe local replay missing'
assert 'for (let commandIndex = 0;' in handler, 'command index is not used for collision-safe IDs'
assert 'makeId(\'exp\', cmd, commandIndex' in handler, 'expense command IDs are not collision-safe'
print(f'PASS: {js_count} inline JavaScript blocks parse successfully')
print('PASS: AI handler uses surgical delta writes, avoids destructive full sync, and replays local state around queueing')
