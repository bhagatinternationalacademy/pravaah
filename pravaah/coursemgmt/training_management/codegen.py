from secrets import choice
from string import ascii_uppercase, digits
import re


def generate_unique_code(model, field_name, prefix, length=6):
    alphabet = ascii_uppercase + digits
    while True:
        suffix = "".join(choice(alphabet) for _ in range(length))
        code = f"{prefix}{suffix}"
        if not model.objects.filter(**{field_name: code}).exists():
            return code


def generate_batch_code(model, program_initials, client_code, year, subject_code):
    base = f"{program_initials}_{client_code}_{year}_{subject_code}"
    existing = model.objects.filter(batch_code__startswith=f"{base}_").values_list("batch_code", flat=True)
    max_number = 0
    pattern = re.compile(rf"^{re.escape(base)}_(\d+)$")
    for batch_code in existing:
        match = pattern.match(batch_code or "")
        if match:
            max_number = max(max_number, int(match.group(1)))
    return f"{base}_{max_number + 1}"
