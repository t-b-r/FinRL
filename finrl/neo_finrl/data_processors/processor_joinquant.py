import copy
import os
from typing import List
import jqdatasdk as jq
import numpy as np
import pandas as pd
from finrl.neo_finrl.data_processors.func import calc_all_filenames, date2str, remove_all_files
from finrl.neo_finrl.data_processors.basic_processor import BasicProcessor

class JoinquantProcessor(BasicProcessor):
    def __init__(self, data_source: str, **kwargs):
        BasicProcessor.__init__(self, data_source, **kwargs)
        if 'username' in kwargs.keys() and 'password' in kwargs.keys():
            jq.auth(kwargs['username'], kwargs['password'])


    def download_data(self, ticker_list: List[str], start_date: str, end_date: str, time_interval: str
    ) -> pd.DataFrame:
        unit = None
        # joinquant supports: '1m', '5m', '15m', '30m', '60m', '120m', '1d', '1w', '1M'。'1w' 表示一周，‘1M' 表示一月。
        if time_interval == '1D':
            unit = '1d'
        elif time_interval == '1Min':
            unit = '1m'
        else:
            raise ValueError('not supported currently')
        count = len(self.calc_trade_days_by_joinquant(start_date, end_date))
        df = jq.get_bars(
            security=ticker_list,
            count=count,
            unit=unit,
            fields=["date", "open", "high", "low", "close", "volume"],
            end_dt=end_date,
        )

        return df

    # def download_data(
    #     self, ticker_list, start_date, end_date, time_interval
    # ) -> pd.DataFrame:
    #     self.start = start_date
    #     self.end = end_date
    #     self.time_interval = time_interval
    #
    #     dfs = []
    #     if read_data_from_local == 1:
    #         dfs = self.read_data_from_csv(path_of_data, start_day, end_day)
    #     else:
    #         if os.path.exists(path_of_data) is False:
    #             os.makedirs(path_of_data)
    #         for stockname in stocknames:
    #             df = jq.get_price(
    #                 stockname,
    #                 start_date=start_day,
    #                 end_date=end_day,
    #                 frequency="daily",
    #                 fields=["open", "close", "high", "low", "volume"],
    #             )
    #             dfs.append(df)
    #             df.to_csv(path_of_data + "/" + stockname + ".csv", float_format="%.4f")
    #     return dfs


    def preprocess(df, stock_list):
        n = len(stock_list)
        N = df.shape[0]
        assert N % n == 0
        d = int(N / n)
        stock1_ary = df.iloc[0:d, 1:].values
        temp_ary = stock1_ary
        for j in range(1, n):
            stocki_ary = df.iloc[j * d : (j + 1) * d, 1:].values
            temp_ary = np.hstack((temp_ary, stocki_ary))
        return temp_ary

    # start_day: str
    # end_day: str
    # output: list of str_of_trade_day, e.g., ['2021-09-01', '2021-09-02']
    def calc_trade_days_by_joinquant(self, start_day: str, end_day: str) -> List[str]:
        dates = jq.get_trade_days(start_day, end_day)
        str_dates = [date2str(dt) for dt in dates]
        return str_dates

    # start_day: str
    # end_day: str
    # output: list of dataframes, e.g., [df1, df2]
    def read_data_from_csv(self, path_of_data, start_day, end_day):
        datasets = []
        selected_days = self.calc_trade_days_by_joinquant(start_day, end_day)
        filenames = calc_all_filenames(path_of_data)
        for filename in filenames:
            dataset_orig = pd.read_csv(filename)
            dataset = copy.deepcopy(dataset_orig)
            days = dataset.iloc[:, 0].values.tolist()
            indices_of_rows_to_drop = [d for d in days if d not in selected_days]
            dataset.drop(index=indices_of_rows_to_drop, inplace=True)
            datasets.append(dataset)
        return datasets

    # start_day: str
    # end_day: str
    # read_data_from_local: if it is true, read_data_from_csv, and fetch data from joinquant otherwise.
    # output: list of dataframes, e.g., [df1, df2]
    def download_data_for_stocks(
        self, stocknames, start_day, end_day, read_data_from_local, path_of_data
    ):
        assert read_data_from_local in [0, 1]
        if read_data_from_local == 1:
            remove = 0
        else:
            remove = 1
        remove_all_files(remove, path_of_data)
        dfs = []
        if read_data_from_local == 1:
            dfs = self.read_data_from_csv(path_of_data, start_day, end_day)
        else:
            if os.path.exists(path_of_data) is False:
                os.makedirs(path_of_data)
            for stockname in stocknames:
                df = jq.get_price(
                    stockname,
                    start_date=start_day,
                    end_date=end_day,
                    frequency="daily",
                    fields=["open", "close", "high", "low", "volume"],
                )
                dfs.append(df)
                df.to_csv(path_of_data + "/" + stockname + ".csv", float_format="%.4f")
        return dfs


if __name__ == "__main__":
    import sys

    sys.path.append("..")
    # from finrl.neo_finrl.neofinrl_config import TRADE_START_DATE
    # from finrl.neo_finrl.neofinrl_config import TRADE_END_DATE
    # from finrl.neo_finrl.neofinrl_config import READ_DATA_FROM_LOCAL
    # from finrl.neo_finrl.neofinrl_config import PATH_OF_DATA

    # read_data_from_local = READ_DATA_FROM_LOCAL
    # path_of_data = '../' + PATH_OF_DATA

    path_of_data = "../" + "data"

    TRADE_START_DATE = "20210901"
    TRADE_END_DATE = "20210911"
    READ_DATA_FROM_LOCAL = 1

    e = JoinquantProcessor()
    username = "xxx"  # should input your username
    password = "xxx"  # should input your password
    e.auth(username, password)

    trade_days = e.calc_trade_days_by_joinquant(TRADE_START_DATE, TRADE_END_DATE)
    stocknames = ["000612.XSHE", "601808.XSHG"]
    data = e.download_data_for_stocks(
        stocknames, trade_days[0], trade_days[-1], READ_DATA_FROM_LOCAL, path_of_data
    )
