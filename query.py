"""Running queries against the flight database."""
import math

from validator import parse_datetime

RECORD_KEYS = (
    "flight_id",
    "origin",
    "destination",
    "departure_datetime",
    "arrival_datetime",
    "price",
)
STRING_KEYS = ("flight_id", "origin", "destination")
DATETIME_KEYS = ("departure_datetime", "arrival_datetime")
NUMBER_KEYS = ("price", "min_price")
ALLOWED_KEYS = set(STRING_KEYS) | set(DATETIME_KEYS) | set(NUMBER_KEYS) | {
    "sort_by",
    "order",
    "limit",
}


def _is_number(value) -> bool:
    # bool is a subclass of int, but booleans are not numbers here.
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _is_valid_query(query) -> bool:
    if not isinstance(query, dict):
        return False
    if not set(query) <= ALLOWED_KEYS:
        return False

    for key in STRING_KEYS:
        if key in query and not isinstance(query[key], str):
            return False
    for key in DATETIME_KEYS:
        if key in query and parse_datetime(query[key]) is None:
            return False
    for key in NUMBER_KEYS:
        if key in query and not _is_number(query[key]):
            return False

    if "sort_by" in query:
        sort_by = query["sort_by"]
        if not isinstance(sort_by, str) or sort_by not in RECORD_KEYS:
            return False
    if "order" in query:
        if "sort_by" not in query:
            return False
        order = query["order"]
        if not isinstance(order, str) or order not in ("asc", "desc"):
            return False
    if "limit" in query:
        limit = query["limit"]
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
            return False
    return True


def _matches(flight: dict, query: dict) -> bool:
    for key in STRING_KEYS:
        if key in query and flight.get(key) != query[key]:
            return False
    # 'YYYY-MM-DD HH:MM' is zero-padded, so text order equals time order.
    if "departure_datetime" in query:
        if not flight["departure_datetime"] >= query["departure_datetime"]:
            return False
    if "arrival_datetime" in query:
        if not flight["arrival_datetime"] <= query["arrival_datetime"]:
            return False
    if "price" in query and not flight["price"] <= query["price"]:
        return False
    if "min_price" in query and not flight["price"] >= query["min_price"]:
        return False
    return True


def run_query(db: list[dict], query: dict) -> dict:
    """Return one response entry for one query object.

    Valid query:   {"query": query, "matches": [...]}
    Invalid query: {"query": query, "error": "INVALID_QUERY", "matches": []}
    """
    if not _is_valid_query(query):
        return {"query": query, "error": "INVALID_QUERY", "matches": []}

    matches = [dict(flight) for flight in db if _matches(flight, query)]

    if "sort_by" in query:
        key = query["sort_by"]
        # sorted() is stable, also with reverse=True, so ties keep db order.
        matches = sorted(
            matches,
            key=lambda f: f[key],
            reverse=query.get("order", "asc") == "desc",
        )
    if "limit" in query:
        matches = matches[: query["limit"]]

    return {"query": query, "matches": matches}


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    """Accept one query object or a list of them; always return a list."""
    if isinstance(queries, dict):
        queries = [queries]
    elif not isinstance(queries, list):
        raise TypeError("queries must be an object or a list of objects")
    return [run_query(db, q) for q in queries]
