# Susu savings

A Python program for managing one rotating savings group. Development is in progress.

## Setup

Run these commands from the project root on Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The application currently uses only the Python standard library. `requirements.txt`
includes pytest for automated tests.

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
