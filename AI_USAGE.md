# AI Usage Disclosure

## Tools used

- Claude (Anthropic), Claude Sonnet 5.5, via the claude.ai chat interface

## Conversation links

- Link 1: TODO - paste the share link of the Claude conversation here

## What I used them for

- Writing the first complete version of the program from the assignment text and the starter skeleton
- Checking the code against the public test script and extra edge cases (non-ASCII letters, non-padded dates, `inf`/`nan` prices, CRLF line endings)

## Which parts of the code were AI-generated or substantially AI-assisted

| File | Function or part | How (generated / modified / explained) |
| --- | --- | --- |
| `validator.py` | `load_airports`, `validate_row`, `to_record`, `parse_datetime` | generated |
| `csv_loader.py` | `parse_files` | generated |
| `query.py` | `run_query`, `run_queries` and the query validation helpers | generated |
| `flight_parser.py` | `main`, argparse setup, logging setup, JSON reading/writing, response file | generated |

## Key prompts

1. I uploaded the assignment text and the starter zip and asked Claude to write the whole lab and give me the finished project as a zip.

## What I changed or verified myself

TODO - write here, in your own words, what you personally changed or checked (for example: set my student details, ran `python tests/run_public_tests.py`, read through each function, tried my own test files).
