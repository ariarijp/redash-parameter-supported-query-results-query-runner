import sys
from unittest.mock import MagicMock

sys.modules["redash"] = MagicMock()
sys.modules["redash.models"] = MagicMock()
sys.modules["redash.query_runner"] = MagicMock()
sys.modules["redash.query_runner.query_results"] = MagicMock()
sys.modules["redash.utils"] = MagicMock()
