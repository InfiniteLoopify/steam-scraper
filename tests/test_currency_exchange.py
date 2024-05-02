import pytest
from datetime import datetime

from steam_scraper.currency_exchange import CurrencyExchange
from steam_scraper.utils import write_file, has_time_exceeded


def test_has_time_exceeded():
    timestamp = int(datetime.now().timestamp())
    assert has_time_exceeded(timestamp) == False
    assert has_time_exceeded(timestamp, hours=0) == True
    with pytest.raises(ValueError):
        has_time_exceeded("XYZ")


@pytest.fixture
def currency_exchange_obj(tmp_path):
    rates = {
        "success": True,
        "timestamp": int(datetime.now().timestamp()),
        "base": "EUR",
        "date": "2023-07-19",
        "rates": {
            "PKR": 318.515334,
            "ARS": 300.087049,
            "TRY": 30.211956,
            "USD": 1.121762,
        },
    }
    ce = CurrencyExchange()
    ce.FILE = tmp_path / ce.FILE
    ce.FILE.parent.mkdir()
    write_file(ce.FILE, rates)
    return ce, rates


def test_convert_to_usd(currency_exchange_obj):
    ce, rates = currency_exchange_obj
    assert ce.convert_to_usd("xyz") is None
    assert ce.convert_to_usd("TRY") == rates["rates"]["USD"] / rates["rates"]["TRY"]
