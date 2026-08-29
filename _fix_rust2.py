import pathlib

# Fix main.rs: line 273 should have 8 spaces before .run
f1 = pathlib.Path('frontend-tauri/src-tauri/src/main.rs')
content1 = f1.read_text(encoding='utf-8')
content1 = content1.replace(
    '                        .run(tauri::generate_context!())',
    '        .run(tauri::generate_context!())'
)
f1.write_text(content1, encoding='utf-8')
print('main.rs fixed')

# Fix Cargo.toml: remove the chrono line (just whitespace)
f2 = pathlib.Path('frontend-tauri/src-tauri/Cargo.toml')
lines = f2.read_text(encoding='utf-8').splitlines(keepends=True)
new_lines = []
for line in lines:
    # Skip the chrono line (now just whitespace) and the extra blank line
    if line.strip() == '' and new_lines and new_lines[-1].strip() == '':
        continue
    new_lines.append(line)
# Remove the chrono line (whitespace only)
filtered = [l for l in new_lines if l.strip() != '' or l.strip() == '' and new_lines.index(l) < 22]
# Actually, let's just rebuild it properly
with open(f2, 'w', encoding='utf-8') as f:
    for line in lines:
        stripped = line.strip()
        if stripped == '' and len(new_lines) > 0 and new_lines[-1].strip() == '':
            # Skip consecutive blank lines
            new_lines.pop()
            new_lines.append(line)
        elif stripped == '':
            new_lines.append(line)
        else:
            new_lines.append(line)
    f.write(''.join(new_lines))
print('Cargo.toml fixed')

# Actually, let's just do simple replacements
lines = f2.read_text(encoding='utf-8').splitlines(keepends=True)
result = []
prev_blank = False
for line in lines:
    if line.strip() == '':
        if prev_blank:
            continue
        prev_blank = True
    else:
        prev_blank = False
    result.append(line)
# Ensure single blank line between sections
f2.write_text(''.join(result), encoding='utf-8')
print('Cargo.toml cleaned')

