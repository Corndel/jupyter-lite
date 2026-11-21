"""
Checks for the Topsify exercises, in place of the repository's bash tests.

Each bash test ran an exercise's SQL with the sqlite3 command-line tool and
compared (diffed) the output with tests/<id>.txt. These checks do the same
comparison in Python: they print rows the way sqlite3 prints them (columns
joined by "|") and compare them, line by line, with the expected file.
Decimal numbers are compared to 13 significant figures, because SQLite
versions can print the 15th digit differently.
"""

import math
import sqlite3
from pathlib import Path

TESTS = Path(__file__).parent / "tests"

# The query each write exercise's test ran after the exercise, and the rows it
# inserted first (9a and 9b insert sample rows to check the new tables work).
WRITE_CHECKS = {
    "7a": ([], "SELECT username, email, password FROM users WHERE first_name IN ('Vincenza', 'Lionel');"),
    "7b": ([], "SELECT email FROM users WHERE username = 'Sally_Kunde';"),
    "8a": ([], "SELECT COUNT(*) FROM artists;"),
    "8b": ([], "SELECT COUNT(*) FROM albums;"),
    "9a": (
        ["INSERT INTO genres (name) VALUES ('Pop'), ('Rock'), ('Classical'), ('Hip Hop');"],
        "SELECT * FROM genres;",
    ),
    "9b": (
        [
            "INSERT INTO genres (name) VALUES ('Pop'), ('Rock'), ('Classical'), ('Hip Hop');",
            "INSERT INTO track_genres (track_id, genre_id) VALUES "
            "('1MpCaOeUWhox2Fgigbe1cL', 1), ('1MpCaOeUWhox2Fgigbe1cL', 2), "
            "('0mKGwFMHzTprtS2vpR3b6s', 1), ('0mKGwFMHzTprtS2vpR3b6s', 2);",
        ],
        "SELECT * FROM track_genres;",
    ),
}


def format_value(value):
    """Format one value as the sqlite3 command-line tool prints it."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(int(value))
    if isinstance(value, float):
        if math.isinf(value):
            return "Inf" if value > 0 else "-Inf"
        text = "%.15g" % value
        if "e" in text:
            mantissa, exponent = text.split("e")
            if "." not in mantissa:
                mantissa += ".0"
            return mantissa + "e" + exponent
        if "." not in text:
            text += ".0"
        return text
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def format_rows(rows):
    return ["|".join(format_value(v) for v in row) for row in rows]


def _same_line(a, e):
    """Compare two output lines. Decimal numbers may differ in the 15th significant
    digit between SQLite versions, so those are compared as numbers."""
    if a == e:
        return True
    a_fields, e_fields = a.split("|"), e.split("|")
    if len(a_fields) != len(e_fields):
        return False
    for x, y in zip(a_fields, e_fields):
        if x == y:
            continue
        try:
            if not ("." in x and "." in y and math.isclose(float(x), float(y), rel_tol=1e-13)):
                return False
        except ValueError:
            return False
    return True


def _compare(exercise, actual):
    expected = (TESTS / f"{exercise}.txt").read_text(encoding="utf-8").splitlines()
    if len(actual) == len(expected) and all(_same_line(a, e) for a, e in zip(actual, expected)):
        print(f"Exercise {exercise} Pass ✅")
        return True
    print(f"Exercise {exercise} Fail ❌")
    print(f"  Your result has {len(actual)} row(s); the expected result has {len(expected)}.")
    for i, (a, e) in enumerate(zip(actual, expected), start=1):
        if not _same_line(a, e):
            print(f"  First difference, row {i}:")
            print(f"    yours:    {a}")
            print(f"    expected: {e}")
            break
    return False


def check(exercise, result=None, con=None):
    """Check an exercise.

    For a query exercise (1a to 6b), pass the saved result:   check("1a", result_1a)
    For a write exercise (7a to 9b), pass the connection:     check("7a", con=con)
    """
    if exercise in WRITE_CHECKS:
        if con is None:
            raise ValueError(f"Exercise {exercise} changes the database: call check('{exercise}', con=con)")
        # Work on a copy, so the sample rows the check inserts do not stay in your database
        copy = sqlite3.connect(":memory:")
        con.backup(copy)
        inserts, query = WRITE_CHECKS[exercise]
        try:
            for statement in inserts:
                copy.execute(statement)
            rows = copy.execute(query).fetchall()
        except sqlite3.Error as error:
            print(f"Exercise {exercise} Fail ❌")
            print(f"  The check could not run: {error}")
            return False
        finally:
            copy.close()
        return _compare(exercise, format_rows(rows))

    if result is None:
        raise ValueError(f"Pass your saved result: check('{exercise}', result_{exercise})")
    passed = _compare(exercise, format_rows(tuple(row) for row in result))
    try:
        from IPython.display import display
        display(result)  # show the result table under the check
    except ImportError:
        pass
    return passed
