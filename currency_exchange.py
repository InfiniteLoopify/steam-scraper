import requests
import utils
from datetime import datetime, timedelta
from enum import Flag, auto

"""
https://manage.exchangeratesapi.io/
hjm16398@omeie.com
hjm16398@omeie.com
"""


class CurrencyType(Flag):
    pk = auto()
    ar = auto()
    tr = auto()

    @classmethod
    def ALL(cls):
        ret_val = None
        for index, member in enumerate(cls.__members__.values()):
            if index == 0:
                ret_val = member
            else:
                ret_val |= member
        return ret_val

    @classmethod
    def get_list(cls):
        ret_val = []
        for member in cls.__members__.values():
            ret_val.append(member)
        return ret_val


class CurrencyExchange:
    API_KEY = "40690a658bad20bd71e8453ecc4226b8"
    URL = f"http://api.exchangeratesapi.io/v1/latest?access_key={API_KEY}&base=EUR&symbols=PKR,ARS,TRY,USD"
    FILE = "files/rates.json"

    def _exchange_rate_api(self):
        response = requests.get(self.URL, verify=False)
        if response.status_code == 200:
            utils.write_file(self.FILE, response.json())
            return response.json()
        return {}

    def convert_to_usd(self, _from):
        data = utils.read_file(self.FILE)
        data_timestamp = data.get("timestamp", "")
        if data and data_timestamp:
            run_time_exceeded = utils.has_time_exceeded(data_timestamp, hours=48)
            if run_time_exceeded:
                data = self._exchange_rate_api()
        if not data:
            data = self._exchange_rate_api()
        if not data:
            return

        rates = data.get("rates", {})
        usd_rate = rates.get("USD")
        from_rate = rates.get(_from)
        if not usd_rate:
            return
        if not from_rate:
            return

        exchange_rate = usd_rate / from_rate
        return exchange_rate
