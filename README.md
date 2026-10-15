# Susu savings

A command-line Python program for managing one rotating savings group.

## Setup

Run these commands from the project root on Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The application currently uses only the Python standard library. `requirements.txt`
includes pytest for automated tests.

## Run the program

From the project root with your virtual environment activated:

```bash
python -m susu create 50.00
python -m susu add Ama
python -m susu add Kofi
python -m susu add Esi
python -m susu pay Ama 1 50.00
python -m susu pay Kofi 1 50.00
python -m susu pay Esi 1 30.00
python -m susu close
```

The last command reports `Esi owes 20.00 GHS` and leaves week 1 open.
Finish her payment and close again:

```bash
python -m susu pay Esi 1 20.00
python -m susu close
python -m susu report
```

Ama receives 150.00 GHS. The report shows week 2, Kofi as the next recipient,
each member's outstanding balance, and the payout history.

Data is saved in `susu.json` in the current directory. Creating a group refuses
to overwrite an existing file. For another file, put `--file` before the command:

```bash
python -m susu --file another-group.json create 50.00
python -m susu --file another-group.json report
```

Quote names containing spaces. Use `python -m susu --help` for commands.
Commands return exit code 0 on success, 1 for validation/storage errors or an
unpaid week, and 2 for invalid command syntax. Run one command at a time.
The default `susu.json` is ignored by Git; keep other saved group files out of
your commits too.

## Use the group API

Run this example from the project root:

```bash
python - <<'PY'
from susu.group import SusuGroup

group = SusuGroup("50.00")
for name in ("Ama", "Kofi", "Esi"):
    group.add_member(name)

group.record_contribution("Ama", 1, "50")
group.record_contribution("Kofi", 1, "50")
group.record_contribution("Esi", 1, "30")
print(group.close_week())  # No payout; Esi owes 20.00.

group.record_contribution("Esi", 1, "20")
print(group.close_week())  # Ama receives 150.00.
print(group.report())     # Week 2; Kofi is next.
PY
```

`record_contribution(member, week, amount)` accepts GHS amounts as text,
integers, or Decimal values. `close_week()` returns `closed`, `owing`, and
`payout`. `report()` includes the current week, members paid in full,
outstanding balances, next recipient, and payout history. Monetary report
values are GHS strings. Validation failures raise subclasses of `SusuError`
from `susu.errors`.

Direct API objects keep data in memory; the CLI saves accepted actions to disk.
See [NOTES.md](NOTES.md) for membership, cycle completion, and other assumptions.

## Tests

Run the tests from the project root:

```bash
python -m pytest
```

Alternatively, run the tests with Python's built-in test runner (no pytest installation required):

```bash
python -m unittest discover -v
```

Money inputs accept positive GHS amounts with up to 12 whole digits and two
decimal places. Extra decimal places are rejected, including trailing zeros
such as `10.000`. Money is stored as integer pesewas.

To leave the virtual environment:

```bash
deactivate
```
