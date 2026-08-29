import pathlib

# Fix 1: IDEIAS_VIABILIDADE_V4.md - correct indentation
f2 = pathlib.Path('docs/IDEIAS_VIABILIDADE_V4.md')
content2 = f2.read_text(encoding='utf-8')
content2 = content2.replace(
    "                return usar_modelo('qwen3.5:4b')  # modelo legado opcional",
    "        return usar_modelo('qwen3.5:4b')  # modelo legado opcional"
)
f2.write_text(content2, encoding='utf-8')
print('IDEIAS_VIABILIDADE_V4.md: indentation fixed')

# Fix 2: GUIA_DESENVOLVIMENTO.md - remaining qwen3.5:4b on line 117 (box chars)
f = pathlib.Path('docs/GUIA_DESENVOLVIMENTO.md')
content = f.read_text(encoding='utf-8')
# Replace any remaining qwen3.5:4b that don't have (legado) next to them
import re
content = re.sub(r'qwen3\.5:4b(?!\s*\(legado)', 'qwen3.5:4b (legado)', content)
f.write_text(content, encoding='utf-8')
print('GUIA_DESENVOLVIMENTO.md: all qwen3.5:4b updated')

# Fix 3: GUIA_DESENVOLVIMENTO_FASE3.md - qwen3.5:4b in box drawing
f3 = pathlib.Path('docs/GUIA_DESENVOLVIMENTO_FASE3.md')
content3 = f3.read_text(encoding='utf-8')
content3 = re.sub(r'qwen3\.5:4b(?!\s*-\s*legado)', 'qwen3.5:4b - legado', content3)
f3.write_text(content3, encoding='utf-8')
print('GUIA_DESENVOLVIMENTO_FASE3.md: qwen3.5:4b updated')

# Verify no remaining unqualified mentions
for df in pathlib.Path('docs').rglob('*.md'):
    text = df.read_text(encoding='utf-8')
    for i, line in enumerate(text.splitlines(), 1):
        if 'qwen3.5:4b' in line and 'legado' not in line.lower() and 'opcional' not in line.lower():
            print(f'  WARNING: {df} line {i}: {line.strip()[:80]}')

print('Verification complete')
