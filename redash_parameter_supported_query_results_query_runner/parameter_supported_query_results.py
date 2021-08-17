import hashlib
import json
import logging
import re
import sqlite3
from typing import List, Optional, Tuple

import pystache

from redash.models import Query, User
from redash.query_runner import TYPE_STRING, guess_type, register
from redash.query_runner.query_results import Results, _load_query, create_table
from redash.utils import json_dumps

logger = logging.getLogger(__name__)


class ChildQueryExecutionError(Exception):
    pass


class ChildQuery:
    query_id: int
    params: dict
    table: str
    token: str

    def __init__(self, query_id: int, params: dict, table: str, token: str) -> None:
        super().__init__()
        self.query_id = query_id
        self.params = params
        self.table = table
        self.token = token


def _extract_child_queries(query: str) -> List[ChildQuery]:
    tokens_list = _collect_tokens(query)

    child_queries = []
    for tokens in tokens_list:
        child_query_token = tokens[0]
        query_id = tokens[1]
        params = json.loads(tokens[2]) if tokens[2] else {}
        table = _tmp_table_name(query_id, child_query_token)

        child_queries.append(ChildQuery(query_id, params, table, child_query_token))

    return child_queries


def _collect_tokens(query: str) -> list:
    pattern = re.compile(r"\s(query_(\d+)(?:\(\s*'({.+})'\s*\))?)", re.IGNORECASE)
    matches = pattern.findall(query)
    return [(m[0], int(m[1]), m[2]) for m in list(matches)]


def _tmp_table_name(query_id: int, child_query_token: str):
    return f"tmp_query{query_id}_{hashlib.sha256(child_query_token.encode('utf-8')).hexdigest()}"


def _create_tables_from_child_queries(
    user: User,
    connection: sqlite3.Connection,
    query: str,
    child_queries: List[ChildQuery],
) -> str:
    for i, child_query in enumerate(child_queries):
        loaded_child_query = _load_query(user, child_query.query_id)

        params = (
            child_query.params
            if child_query.params
            else get_default_params(loaded_child_query)
        )

        _rendered_child_query = pystache.render(loaded_child_query.query_text, params)
        logger.debug(
            f"ResultsWithParams child_queries[{i}], query_id={child_query.query_id} : {_rendered_child_query}"
        )
        results, error = loaded_child_query.data_source.query_runner.run_query(
            _rendered_child_query, user
        )
        if error:
            raise ChildQueryExecutionError(
                f"Failed loading results for query id {loaded_child_query.id}."
            )

        results = json.loads(results)
        table_name = child_query.table
        create_table(connection, table_name, results)
        query = query.replace(child_query.token, table_name, 1)

    return query


def get_default_params(query: Query) -> dict:
    return {p["name"]: p["value"] for p in query.options.get("parameters", {})}


class ParameterSupportedResults(Results):
    @classmethod
    def name(cls):
        return "Parameter Supported Query Results(PoC)"

    def run_query(
        self, query: Query, user: User
    ) -> Tuple[Optional[str], Optional[str]]:
        child_queries = _extract_child_queries(query)

        connection = None
        cursor = None

        try:
            connection = sqlite3.connect(":memory:")
            query = _create_tables_from_child_queries(
                user, connection, query, child_queries
            )

            cursor = connection.cursor()
            cursor.execute(query)

            if cursor.description is None:
                return None, "Query completed but it returned no data."

            columns = self.fetch_columns([(d[0], None) for d in cursor.description])

            rows = []
            column_names = [c["name"] for c in columns]

            for i, row in enumerate(cursor):
                if i == 0:
                    for j, col in enumerate(row):
                        guess = guess_type(col)

                        if columns[j]["type"] is None:
                            columns[j]["type"] = guess
                        elif columns[j]["type"] != guess:
                            columns[j]["type"] = TYPE_STRING

                rows.append(dict(zip(column_names, row)))

            return json_dumps({"columns": columns, "rows": rows}), None
        except KeyboardInterrupt:
            if connection:
                connection.interrupt()
            return None, "Query cancelled by user."
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()


register(ParameterSupportedResults)
