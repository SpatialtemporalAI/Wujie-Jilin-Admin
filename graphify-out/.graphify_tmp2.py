import json
from pathlib import Path

result = json.loads(Path('graphify-out/.graphify_incremental.json').read_text(encoding='utf-8'))
new_files = result.get('new_files', {})
code_exts = {'.py','.ts','.js','.go','.rs','.java','.cpp','.c','.rb','.swift','.kt','.cs','.scala','.php','.cc','.cxx','.hpp','.h','.kts','.lua','.toc'}
all_changed = [f for files in new_files.values() for f in files]
code_only = all(Path(f).suffix.lower() in code_exts for f in all_changed)
print('code_only:', code_only)
