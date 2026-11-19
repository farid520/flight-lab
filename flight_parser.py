"""Flight Schedule Parser and Query Tool - command-line entry point.

Run from the project folder, for example:
    python flight_parser.py -i data/db.csv -a data/airports.txt
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime

from csv_loader import parse_files
from query import run_queries
from validator import load_airports

# TODO: fill in your details: plain ASCII, no spaces or underscores.
STUDENT_ID = "251ADB132"
FIRST_NAME = "Farid"
LAST_NAME = "Hajiyev"


class RuntimeProblem(Exception):
    """An expected runtime problem; reported as 'Error: ...' with exit code 1."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flight_parser.py",
        description="Validate flight schedule CSV files, store the valid "
        "flights as a JSON database and answer queries against it.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-i", metavar="FILE", help="parse a single CSV file")
    source.add_argument(
        "-d", metavar="FOLDER", help="parse every .csv file in a folder (sorted by name)"
    )
    source.add_argument(
        "-j", metavar="FILE", help="load an existing JSON database instead of parsing CSVs"
    )
    parser.add_argument("-a", metavar="FILE", help="airport list file (required with -i and -d)")
    parser.add_argument(
        "-o", metavar="FILE", help="output path of the JSON database (default: db.json); only with -i or -d"
    )
    parser.add_argument("-q", metavar="FILE", help="JSON file with the queries to run")
    parser.add_argument(
        "-r", metavar="FOLDER", default=".", help="folder for the query response file (default: current directory)"
    )
    return parser


def parse_arguments(argv):
    """Parse and check the command line. Usage errors raise SystemExit(2)."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.j is None and args.a is None:
        parser.error("-a is required with -i and -d")
    if args.j is not None and args.o is not None:
        parser.error("-o can only be used with -i or -d")
    if args.o is None:
        args.o = "db.json"
    return args


def read_json(path: str, what: str):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except FileNotFoundError:
        raise RuntimeProblem(f"{what} not found: {path}")
    except json.JSONDecodeError as exc:
        raise RuntimeProblem(f"{what} is not valid JSON ({path}): {exc}")
    except (OSError, UnicodeDecodeError) as exc:
        raise RuntimeProblem(f"cannot read {what} {path}: {exc}")


def write_json(path: str, data, what: str) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
    except OSError as exc:
        raise RuntimeProblem(f"cannot write {what} {path}: {exc}")


def find_csv_files(folder: str) -> list[str]:
    if not os.path.isdir(folder):
        raise RuntimeProblem(f"folder not found: {folder}")
    try:
        names = sorted(os.listdir(folder))
    except OSError as exc:
        raise RuntimeProblem(f"cannot read folder {folder}: {exc}")
    paths = [
        os.path.join(folder, n)
        for n in names
        if n.endswith(".csv") and os.path.isfile(os.path.join(folder, n))
    ]
    if not paths:
        raise RuntimeProblem(f"no .csv files found in {folder}")
    return paths


def parse_csv_sources(args) -> list[dict]:
    """Handle -i / -d: parse, then write the database and errors.log."""
    paths = [args.i] if args.i is not None else find_csv_files(args.d)
    for path in paths:
        if not os.path.isfile(path):
            raise RuntimeProblem(f"file not found: {path}")

    try:
        airports = load_airports(args.a)
    except FileNotFoundError:
        raise RuntimeProblem(f"airport file not found: {args.a}")
    except (OSError, UnicodeDecodeError) as exc:
        raise RuntimeProblem(f"cannot read airport file {args.a}: {exc}")

    try:
        records, errors = parse_files(paths, airports)
    except (OSError, UnicodeDecodeError) as exc:
        raise RuntimeProblem(f"cannot read CSV file: {exc}")

    write_json(args.o, records, "database")

    log_path = os.path.join(os.path.dirname(os.path.abspath(args.o)), "errors.log")
    logger = logging.getLogger("flight_parser")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    handler = None
    try:
        try:
            handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
        except OSError as exc:
            raise RuntimeProblem(f"cannot write log file {log_path}: {exc}")
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
        )
        logger.addHandler(handler)
        logger.info(
            "Processed %d file(s): %d valid row(s), %d invalid row(s)",
            len(paths), len(records), len(errors),
        )
        for message in errors:
            logger.warning(message)
    finally:
        if handler is not None:
            logger.removeHandler(handler)
            handler.close()

    print(f"Valid flights: {len(records)}, invalid rows: {len(errors)}")
    return records


def load_database(path: str) -> list[dict]:
    """Handle -j."""
    data = read_json(path, "database")
    if not isinstance(data, list) or not all(isinstance(r, dict) for r in data):
        raise RuntimeProblem(f"database {path} must be a JSON array of objects")
    return data


def run_query_file(db: list[dict], query_path: str, response_dir: str) -> None:
    queries = read_json(query_path, "query file")
    ok_shape = isinstance(queries, dict) or (
        isinstance(queries, list) and all(isinstance(q, dict) for q in queries)
    )
    if not ok_shape:
        raise RuntimeProblem(
            f"query file {query_path} must be a JSON object or an array of objects"
        )
    responses = run_queries(db, queries)

    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    name = f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_{stamp}.json"
    write_json(os.path.join(response_dir, name), responses, "response file")
    print(f"Wrote {len(responses)} query response(s) to {os.path.join(response_dir, name)}")


def main(argv: list[str] | None = None) -> int:
    """Run the whole program and return the exit code (0, 1 or 2).

    argv is the argument list without the program name.
    None means use sys.argv[1:] (argparse does this for you).
    Do not call sys.exit() inside main(); return the code instead.
    """
    try:
        args = parse_arguments(argv)
    except SystemExit as exc:  # argparse: -h (0) or a usage error (2)
        return exc.code if isinstance(exc.code, int) else 0

    try:
        if args.j is not None:
            db = load_database(args.j)
        else:
            db = parse_csv_sources(args)
        if args.q is not None:
            run_query_file(db, args.q, args.r)
    except RuntimeProblem as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # last line of defence: never show a traceback
        print(f"Error: unexpected problem: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
