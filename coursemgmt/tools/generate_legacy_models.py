import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','training_management.settings')
import django
django.setup()
from django.db import connection
from pathlib import Path

DB = connection.settings_dict['NAME']
CUR = connection.cursor()

CUR.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s", [DB])
rows = [r[0] for r in CUR.fetchall()]

out_dir = Path(os.getcwd()) / 'legacy_models'
out_dir.mkdir(parents=True, exist_ok=True)

model_lines = [
    'from django.db import models\n\n',
]

def camel_case(name):
    parts = [p for p in name.replace('-', '_').split('_') if p]
    return ''.join(p.title() for p in parts)

seen = set()
for table in rows:
    CUR.execute("SELECT column_name, column_type, is_nullable, column_key, extra, character_maximum_length, numeric_precision, numeric_scale FROM information_schema.columns WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position", [DB, table])
    cols = CUR.fetchall()
    base_name = camel_case(table)
    class_name = base_name
    suffix = 1
    while class_name.lower() in seen:
        class_name = f"{base_name}{suffix}"
        suffix += 1
    seen.add(class_name.lower())
    model_lines.append(f'class {class_name}(models.Model):\n')
    if not cols:
        model_lines.append('    pass\n\n')
        continue
    for col in cols:
        name, coltype, is_nullable, colkey, extra, char_max, num_prec, num_scale = col
        # determine field
        field = 'models.TextField()'
        params = []
        if colkey == 'PRI' and extra and 'auto_increment' in extra:
            # primary auto
            field = 'models.BigAutoField(primary_key=True)'
            model_lines.append(f'    {name} = {field}\n')
            continue
        if colkey == 'PRI':
            params.append('primary_key=True')
        if coltype.startswith('varchar') or coltype.startswith('char'):
            mlen = char_max or 255
            field = f'models.CharField(max_length={mlen})'
        elif 'int' in coltype and not coltype.startswith('tinyint'):
            field = 'models.IntegerField()'
        elif coltype.startswith('bigint'):
            field = 'models.BigIntegerField()'
        elif coltype.startswith('decimal') or coltype.startswith('numeric'):
            p = num_prec or 10
            s = num_scale or 2
            field = f'models.DecimalField(max_digits={p}, decimal_places={s})'
        elif coltype.startswith('datetime') or 'timestamp' in coltype:
            field = 'models.DateTimeField()'
        elif coltype.startswith('date'):
            field = 'models.DateField()'
        elif coltype.startswith('time'):
            field = 'models.TimeField()'
        elif 'text' in coltype:
            field = 'models.TextField()'
        elif coltype.startswith('tinyint(1)') or coltype == 'tinyint(1)':
            field = 'models.BooleanField()'
        else:
            field = 'models.TextField()'
        # nullable
        if is_nullable == 'YES':
            open_paren = field.find('(')
            close_paren = field.rfind(')')
            inside = field[open_paren+1:close_paren].strip()
            if inside:
                # there are existing args
                field = field[:-1] + ', null=True, blank=True)'
            else:
                # no args
                field = field[:open_paren+1] + 'null=True, blank=True)'
        # primary_key param
        if params and 'primary_key=True' in params and 'primary_key=True' not in field:
            open_paren = field.find('(')
            close_paren = field.rfind(')')
            inside = field[open_paren+1:close_paren].strip()
            if inside:
                field = field[:-1] + ', primary_key=True)'
            else:
                field = field[:open_paren+1] + 'primary_key=True)'
        model_lines.append(f'    {name} = {field}\n')
    model_lines.append('\n    class Meta:\n')
    model_lines.append(f"        db_table = '{table}'\n")
    model_lines.append('        managed = False\n\n')

# write models.py
models_path = out_dir / 'models.py'
models_path.write_text(''.join(model_lines))

# write __init__.py
(init_path := out_dir / '__init__.py').write_text('from .models import *\n')
print('Generated models for', len(rows), 'tables in', models_path)
