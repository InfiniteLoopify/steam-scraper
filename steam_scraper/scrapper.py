import pandas as pd
import time
from pathlib import Path
from datetime import datetime
import os
import traceback

from fake_useragent import UserAgent

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium_stealth import stealth

from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

import steam_scraper.utils as utils
from steam_scraper.currency_exchange import CurrencyExchange, CurrencyType


class Scrapper:
    CSV_PATH = "files/data.csv"
    SETTING_PATH = "files/settings.json"

    def __init__(
        self,
        min_reviews=5000,
        max_reviews=None,
        min_rating=80,
        min_discount=0,
        cc=CurrencyType.ALL(),
    ):
        link = "https://steamdb.info/sales/?"
        params = self.add_params(
            min_reviews=min_reviews,
            max_reviews=max_reviews,
            min_rating=min_rating,
            min_discount=min_discount,
        )
        self.currencies = self.get_currencies(cc)
        link = "".join([link, params])

        self.links = ["".join([link, f"cc={cc.name}"]) for cc in self.currencies]
        print(self.links)

    def _get_driver(self):
        # ua = UserAgent()
        # random_agent = ua.random
        fixed_agent = """Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"""

        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        path = (
            Path(os.getenv("LOCALAPPDATA", "")) / "Google/Chrome/User Data"
        ).resolve()
        options.add_argument(f"--user-data-dir={path}")
        # options.add_argument('--profile-directory=Profile 2')

        options.add_argument(f"user-agent={fixed_agent}")
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        # options.add_argument("--headless")

        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # service = Service(ChromeDriverManager(version='114.0.5735.90').install())
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        # driver.execute_script("window.open('');")
        # driver.switch_to.window(driver.window_handles[1])

        stealth(
            driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )

        driver.implicitly_wait(4)
        driver.maximize_window()
        # print(f"version:[{manager.version}]")
        return driver

    def _get_table_info(self, driver):
        html = None
        try:
            driver.implicitly_wait(4)
            select = Select(
                driver.find_element(
                    By.XPATH, "//select[@name='DataTables_Table_0_length']"
                )
            )
            select.select_by_value("-1")
            driver.implicitly_wait(4)
            self._scroll_down_page(driver, delay=0.5)
            # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            html = driver.find_element(
                By.XPATH, "//table[@id='DataTables_Table_0']"
            ).get_attribute("innerHTML")
        except NoSuchElementException as e:
            pass
        return html

    def _scroll_down_page(self, driver, step=648, delay=0.0):
        max_height = driver.execute_script("return document.body.scrollHeight")
        for current_height in range(0, max_height, step):
            driver.execute_script(f"window.scrollTo(0, {current_height});")
            time.sleep(delay)
        driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight);")

    def _verify_human(self, driver):
        pass

    def _get_htmls(self):
        html_tables = []
        driver = None
        try:
            driver = self._get_driver()
            for link in self.links:
                driver.get(link)
                html = self._get_table_info(driver)
                if html:
                    html_tables.append(html)
        except Exception as e:
            print(traceback.format_exc())
        finally:
            if driver:
                driver.quit()
        return html_tables

    def _get_app_data(self, row):
        try:
            cols = row.find_all("td")

            app_link = cols[0].find("a").get("href")

            app_name = cols[2].find("a").text

            app_discount = cols[3].text
            app_discount_type = cols[3].get("class")
            app_discount_type = (
                app_discount_type[0]
                if app_discount_type and isinstance(app_discount_type, list)
                else ""
            )

            app_price = cols[4].text

            app_rating = cols[5].text

            app_ends_in_time = cols[6].text
            app_ends_in_date = cols[6].get("title")

            app_starts_in_time = cols[7].text
            app_starts_in_date = cols[7].get("title")

            app_release_date = cols[8].text

            return (
                app_name,
                app_discount,
                app_discount_type,
                app_price,
                app_rating,
                app_ends_in_time,
                app_ends_in_date,
                app_starts_in_time,
                app_starts_in_date,
                app_release_date,
                app_link,
            )
        except Exception as e:
            return

    def _html_to_table(self, htmls):
        data_frames = []
        soup = None
        for html in htmls:
            html_data = {}
            try:
                soup = BeautifulSoup(html, "html.parser")
                body = soup.find("tbody")
                rows = body.find_all("tr")
            except Exception as e:
                continue
            for row in rows:
                app_id = row.get("data-appid")
                app_data = self._get_app_data(row)
                if app_data:
                    html_data[app_id] = app_data

            columns_order = [
                "Name",
                "Discount",
                "Type",
                "Price",
                "Rating",
                "Ends In",
                "Ending Date",
                "Started",
                "Starting Date",
                "Release Date",
                "Steam Link",
            ]
            df = pd.DataFrame.from_dict(
                html_data, orient="index", columns=columns_order
            )
            data_frames.append(df)

        if isinstance(soup, BeautifulSoup):
            soup.decompose()

        return data_frames

    def _scrapping_fail_fallback(self, dfs):
        if isinstance(dfs, pd.DataFrame) and not dfs.empty:
            dfs.to_csv(self.CSV_PATH)
            utils.write_file(
                self.SETTING_PATH, {"last_modified": datetime.timestamp(datetime.now())}
            )
            return dfs

        try:
            dfs = pd.read_csv(self.CSV_PATH, index_col=0)
            return dfs
        except FileNotFoundError:
            return pd.DataFrame([])

    def _get_clean_dataframe(self, dfs):
        # def remove_non_numberics(s):
        #     return re.sub(r'[^0-9\.\-\,\+]+', '', str(s))
        if not dfs:
            return pd.DataFrame([])

        price = []
        ex_rate_arg = CurrencyExchange().convert_to_usd("ARS")
        ex_rate_tur = CurrencyExchange().convert_to_usd("TRY")

        for cc, df in zip(self.currencies, dfs):
            df = df[["Type", "Discount", "Price"]]
            numbers_only_regex = [r"[^0-9\.\-\+]+"]
            df.loc[:, "Type"] = df["Type"].apply(lambda x: " " if not x else "*")
            df.loc[:, "Price"] = df["Price"].replace(",", ".", regex=True)
            df.loc[:, "Price"] = (
                df["Price"].replace(regex=numbers_only_regex, value="").astype(float)
            )
            df.loc[:, "Discount"] = (
                df["Discount"].replace(regex=numbers_only_regex, value="").astype(int)
            )

            # df[["Discount", "Price"]] = df[["Discount", "Price"]].apply(remove_non_numberics)
            # df[["Discount", "Price"]] = df[["Discount", "Price"]].str.extract(r'(\d+)', expand=False)
            # df.loc[:, ["Discount", "Price"]] = df.loc[:, ["Discount", "Price"]].apply(pd.to_numeric)
            if cc == CurrencyType.pk:
                pass
            elif cc == CurrencyType.ar:
                df.loc[:, "Price"] = df["Price"].apply(lambda x: x * ex_rate_arg)
            elif cc == CurrencyType.tr:
                df.loc[:, "Price"] = df["Price"].apply(lambda x: x * ex_rate_tur)
            df.loc[:, "Price"] = df["Price"].astype(float).round(3)

            df.columns = [
                f"Type ({cc.name})",
                f"Discount ({cc.name})",
                f"Price ({cc.name})",
            ]
            price.append(df)

        clean_df = pd.concat(dfs)
        clean_df = clean_df.drop(columns=["Type", "Discount", "Price"])
        clean_df = clean_df[~clean_df.index.duplicated(keep="first")]

        clean_df = pd.concat([clean_df, *price], axis=1)
        clean_df = clean_df.drop(columns=["Starting Date", "Ending Date"])
        clean_df = clean_df.sort_values(by=["Rating"], ascending=False)

        cols = clean_df.columns.tolist()
        cols = cols[:2] + cols[-9:] + cols[2:-9]
        clean_df = clean_df[cols]

        return clean_df

    def run(self, delay_in_hours=4):
        last_run = utils.read_file(self.SETTING_PATH).get("last_modified")

        dfs = None
        run_time_exceeded = not last_run or utils.has_time_exceeded(
            last_run, hours=delay_in_hours
        )
        if run_time_exceeded:
            htmls = self._get_htmls()
            print(htmls)
            dfs = self._html_to_table(htmls)
            dfs = self._get_clean_dataframe(dfs)

        dfs = self._scrapping_fail_fallback(dfs)
        return dfs

    @staticmethod
    def add_params(**kwargs):
        param = ""
        for key in kwargs:
            param += f"{key}={kwargs[key]}&" if kwargs[key] is not None else ""
        return param

    @staticmethod
    def get_currencies(cc_list):
        currencies = [cc for cc in CurrencyType.get_list() if cc in cc_list]
        return currencies


if __name__ == "__main__":
    steam_scrapper = Scrapper()
    dfs = steam_scrapper.run(delay_in_hours=4)

    for df in dfs:
        print(df)
