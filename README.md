# Parameter supported QRDS for Redash

This is one of the PoC of parameter supported QRDS for Redash.

## Disclaimer

THIS REPOSITORY IS UNOFFICIAL AND STILL UNDER DEVELOPMENT. USE IT AT YOUR OWN RISK.

This feature is still in [discussion](https://discuss.redash.io/t/thoughts-on-adding-support-for-queries-with-parameters-in-query-results-data-source/1709).

## Prerequisites

- It will works on Redash v10.0.0-beta
- You need to run Redash with Docker Compose

## Installation

First, Clone it.

```shell
$ cd /path/to/somewhere
$ git clone https://github.com/ariarijp/redash-parameter-supported-query-results-query-runner.git
```

Then, add `volumes` lines to your Redash's docker-compose.yml.

```yaml
x-redash-service: &redash-service
  # ...snip...
  restart: always
  volumes:
    - /path/to/somewhere/redash-parameter-supported-query-results-query-runner/redash_parameter_supported_query_results_query_runner/parameter_supported_query_results.py:/app/redash/query_runner/parameter_supported_query_results.py
    - /path/to/somewhere/redash-parameter-supported-query-results-query-runner/images/parametersupportedresults.png:/app/client/dist/images/db-logos/parametersupportedresults.png
services:
  server:
# ...snip...
```

Finally, add `REDASH_ADDITIONAL_QUERY_RUNNERS` environment variable in env file like below, and up or restart your Redash services via `docker-compose` command.

```sh
REDASH_ADDITIONAL_QUERY_RUNNERS="redash.query_runner.parameter_supported_query_results"
```

## Syntax

You can pass query parameters like this.

```sql
-- Query 1
SELECT '{{ a }}' a, '{{ b }}' b;

-- Query 2
SELECT * FROM query_1('{"a": "Hello", "b": "Redash"}');
```

## License

BSD-2-Clause

## Author

[ariarijp / Takuya Arita](https://github.com/ariarijp)
