from unittest import TestCase
from unittest.mock import MagicMock, patch

from redash_parameter_supported_query_results_query_runner.parameter_supported_query_results import (
    _collect_tokens,
    _extract_child_queries,
    _tmp_table_name,
    get_default_params,
)


class TestResultsWithParams(TestCase):
    def test_extract_child_queries(self):
        query = """
select
    *
from
    query_1('{"foo": "bar"}') a
left join
    query_2 b on a.id = b.user_id
left join
    (select * from query_3('{"hoge": "fuga", "n": 42}')) c on b.id = c.item_id
;
"""
        child_queries = _extract_child_queries(query)
        expected = [
            {
                "query_id": 1,
                "params": {"foo": "bar"},
                "table": "tmp_query1_c8ec23248b6b5d300cdc3108a231b8741a6dc829510e0711c795f812bfaae087",
                "token": 'query_1(\'{"foo": "bar"}\')',
            },
            {
                "query_id": 2,
                "params": {},
                "table": "tmp_query2_876f9a03213a59cdd00e70552c2c7eb33f1b9264b2a61211435b19b80842710c",
                "token": "query_2",
            },
            {
                "query_id": 3,
                "params": {"hoge": "fuga", "n": 42},
                "table": "tmp_query3_e482858d67788c606c7c71e0e84f0b1226bb524f2728c7dc9e0b04557b10c11d",
                "token": 'query_3(\'{"hoge": "fuga", "n": 42}\')',
            },
        ]

        self.assertEqual(expected, [q.__dict__ for q in child_queries])

    def test_collect_tokens(self):
        query = """
select
    *
from
    query_1('{"foo": "bar"}') a
left join
    query_2 b on a.id = b.user_id
left join
    (select * from query_3('{"hoge": "fuga", "n": 42}')) c on b.id = c.item_id
;
"""
        actual = _collect_tokens(query)
        expected = [
            ('query_1(\'{"foo": "bar"}\')', 1, '{"foo": "bar"}'),
            ("query_2", 2, ""),
            ('query_3(\'{"hoge": "fuga", "n": 42}\')', 3, '{"hoge": "fuga", "n": 42}'),
        ]
        self.assertEqual(expected, actual)

    def test_tmp_table_name(self):
        actual = _tmp_table_name(1, 'query_1(\'{"foo": "bar"}\')')
        expected = "tmp_query1_c8ec23248b6b5d300cdc3108a231b8741a6dc829510e0711c795f812bfaae087"
        self.assertEqual(expected, actual)

    def test_get_default_params(self):
        m = MagicMock()
        m.options = {
            "parameters": [
                {"name": "foo", "value": "bar"},
                {"name": "hoge", "value": "fuga"},
            ]
        }
        actual = get_default_params(m)
        expected = {"foo": "bar", "hoge": "fuga"}
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
