import pathlib

f = pathlib.Path('frontend-tauri/src-tauri/src/main.rs')
lines = f.read_text(encoding='utf-8').splitlines(keepends=True)

# Fix 1: get_chat_history - add PRAGMA after conn.execute and change SQL
# Line 133 (0-indexed: 132): "    let conn = Connection::open(&db_path)\n"
# We need to insert PRAGMA line after line 134 (the .map_err line)
# And change the SQL query on lines 136-138

# Find the get_chat_history SQL query
for i, line in enumerate(lines):
    if 'SELECT id, role, content, timestamp FROM messages' in line:
        # This is line 136 (0-indexed: 136)
        # Insert PRAGMA before "let mut stmt" - which is on line 135 (0-indexed: 134 after 0-based)
        # Actually let's find the exact pattern and fix
        
        # The "let mut stmt" line is right before the SQL
        stmt_line_idx = i - 1  # the "let mut stmt" line
        conn_line_idx = stmt_line_idx - 2  # skip blank line
        
        # Insert PRAGMA after the conn line's map_err line
        map_err_line_idx = conn_line_idx + 1  # the .map_err line
        
        # Insert PRAGMA lines after map_err
        pragma_lines = [
            '    conn.execute("PRAGMA foreign_keys = ON", [])\n',
            '        .map_err(|e| e.to_string())?;\n',
        ]
        
        # Insert into lines list
        for j, pline in enumerate(pragma_lines):
            lines.insert(map_err_line_idx + 1 + j, pline)
        
        print(f'PRAGMA inserted at lines {map_err_line_idx + 2}-{map_err_line_idx + 3}')
        break

# Now fix the SQL query
for i, line in enumerate(lines):
    if 'SELECT id, role, content, timestamp FROM messages' in line:
        lines[i] = line.replace(
            '"SELECT id, role, content, timestamp FROM messages \\',
            '"SELECT id, role, conteudo AS content, criado_em AS timestamp \\'
        )
        print(f'SQL SELECT line fixed at line {i+1}')
    if 'WHERE conversation_id = ? ORDER BY timestamp ASC' in line:
        lines[i] = line.replace(
            'WHERE conversation_id = ? ORDER BY timestamp ASC',
            'FROM mensagens WHERE conversa_id = ?1 ORDER BY criado_em ASC'
        )
        print(f'SQL WHERE line fixed at line {i+1}')

# Fix 2: save_message - fix indentation
for i, line in enumerate(lines):
    if '                let conn = Connection::open(&db_path)' in line:
        lines[i] = '    let conn = Connection::open(&db_path)\n'
        print(f'save_message indentation fixed at line {i+1}')

# Fix 3: Remove trailing whitespace issues in save_message (the line after .join)
for i, line in enumerate(lines):
    if 'save_message' in lines[i-2] if i >= 2 else False:
        pass

f.write_text(''.join(lines), encoding='utf-8')
print('File saved')