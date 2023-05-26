# -*- coding: utf-8 -*-
"""
Created on May 21 2022
@author: Victor Feitosa Lourenco

This is the main python file for ... It is responsible for ...
"""

""" --------- LIBRARIES --------- """
# External Libraries
import os
import time
import ratelimit
from schedule import repeat, every, run_pending
import requests
import datetime
import json
from typing import Union, List
from abc import ABC, abstractmethod
from backoff import expo, on_exception

# Internal Modules
import structlogger

""" ----------------------------- """

structlogger.init_logger()
logger = structlogger.get_logger()
ingestor = None

# ---------------------------- Classes -------------------------------

class MercadoBitcoinApi(ABC):
    def __init__(self, coin:str) -> None:
        self.coin = coin
        self.base_endpoint = "https://www.mercadobitcoin.net/api"
    
    @abstractmethod
    def _get_endpoint(self, **kwargs) -> str:
        pass
        #return f"{self.base_endpoint}{self.coin}/day-summary/2022/5/20"
    
    @on_exception(expo, ratelimit.exception.RateLimitException, max_tries=10)
    @ratelimit.limits(calls=29, period=30)
    @on_exception(expo, requests.exceptions.HTTPError, max_tries=10)
    def get_data(self, **kwargs) -> dict:
        endpoint = self._get_endpoint(**kwargs)
        logger.info(f"Getting date from endpoint {endpoint}")
        response = requests.get(endpoint)
        response.raise_for_status()
        return response.json()


class DaySummaryApi(MercadoBitcoinApi):
    type = "day-summary"

    def _get_endpoint(self, date: datetime.date) -> str:
        return f"{self.base_endpoint}/{self.coin}/{self.type}/{date.year}/{date.month}/{date.day}"


class TradesApi(MercadoBitcoinApi):
    type = "trades"

    def _get_unix_epoch(self, date: datetime.datetime) -> int:
        return int(date.timestamp())

    def _get_endpoint(self,
        date_from: datetime.datetime = None,
        date_to: datetime.datetime = None
    ) -> str:
        if date_from and not date_to:
            unix_date_from = self._get_unix_epoch(date_from)
            endpoint = f"{self.base_endpoint}/{self.coin}/{self.type}/{unix_date_from}"
        elif date_from and date_to:
            unix_date_from = self._get_unix_epoch(date_from)
            unix_date_to = self._get_unix_epoch(date_to)
            endpoint = f"{self.base_endpoint}/{self.coin}/{self.type}/{unix_date_from}/{unix_date_to}"
        else:
            endpoint = f"{self.base_endpoint}/{self.coin}/{self.type}"
        
        return endpoint


class DataTypeNotSupportedForIngestionException(Exception):
    def __init__(self, data) -> None:
        self.data = data
        self.message = f"Data type {type(data)} is not supported for ingestion"
        super().__init__(self.message)


class DataWriter:
    def __init__(self, coin: str, api: str) -> None:
        self.coin = coin
        self.api = api
        now = datetime.datetime.now().strftime('%Y-%m-%d %H.%M.%S')
        self.filename = f"{self.api}/{self.coin}/{now}.json"

    def _write_row(self, row: str) -> None:
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        with open(self.filename, "a") as f:
            f.write(row)
    
    def write(self, data: Union[List, dict]):
        if isinstance(data, dict):
            self._write_row(json.dumps(data) + "\n")

        elif isinstance(data, List):
            for element in data:
                self.write(element)
        
        else:
            raise DataTypeNotSupportedForIngestionException(data)
 

class DataIngestor(ABC):
    def __init__(self,
        coins: List[str],
        default_start_date: datetime.date,
        writer
    ) -> None:
        self.coins = coins
        self.default_start_date = default_start_date
        self.writer = writer
        self._checkpoint = self._load_checkpoint()
    
    @property
    def _checkpoint_filename(self) -> str:
        return f"{self.__class__.__name__}.checkpoint"
    
    def _load_checkpoint(self) -> datetime:
        try:
            with open(self._checkpoint_filename, "r") as f:
                return datetime.datetime.strptime(f.read(), "%Y-%m-%d").date()
        except FileNotFoundError:
            return None
    
    def _get_checkpoint(self):
        if not self._checkpoint:
            return self.default_start_date
        else:
            return self._checkpoint
    
    def _update_checkpoint(self, value):
        self._checkpoint = value
        self._write_checkpoint()
    
    def _write_checkpoint(self):
        with open(self._checkpoint_filename, "w") as f:
            f.write(f"{self._checkpoint}")

    @abstractmethod
    def ingest(self) -> None:
        pass


class DaySummaryIngestor(DataIngestor):
    def __init__(self,
                 coins: List[str],
                 default_start_date: datetime.date,
                 writer: DataWriter
    ) -> None:
        super().__init__(coins, default_start_date, writer)
        self.writer = writer

    def ingest(self) -> None:
        date = self._get_checkpoint()
        if date < datetime.date.today():
            for coin in self.coins:
                api = DaySummaryApi(coin=coin)
                data = api.get_data(date=date)
                self.writer(coin=coin, api=api.type).write(data)
            self._update_checkpoint(date + datetime.timedelta(days=1))

# --------------------------------------------------------------------


# --------------------------- Functions ------------------------------

@repeat(every(1).seconds)
def job():
    if ingestor:
        ingestor.ingest()

# --------------------------------------------------------------------


def main():
    global ingestor
    ingestor = DaySummaryIngestor(writer=DataWriter,
                                  coins=["BTC", "ETH", "LTC"],
                                  default_start_date=datetime.date(2022, 5, 1)
    )

    while True:
        run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()
