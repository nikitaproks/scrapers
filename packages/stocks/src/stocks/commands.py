import csv
import json
import time
from enum import Enum

from browser.lib import Browser
from pydantic.main import BaseModel
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from tqdm import tqdm


class ISharesElement(str, Enum):
    ShowMoreButton = ".//div[@id='allHoldingsTable_wrapper']//div[@class='show-all']//a[@class='toggle-records']"
    TickerListElement = ".//table[@id='allHoldingsTable']/tbody/tr"


class Ticker(BaseModel):
    symbol: str
    name: str
    sector: str
    market_value: float
    weight: float


def find_element(object: WebElement | Chrome, xpath: str) -> WebElement | None:
    elements = object.find_elements(
        By.XPATH,
        xpath,
    )
    if elements:
        return elements.pop()
    return None


def msci_world(out: str):
    browser = Browser(headless=False, profile_name="stocks")
    browser.main_tab.open("https://www.ishares.com/us/products/239696/")
    time.sleep(2)
    browser.driver.execute_script(
        "window.scrollTo(0, document.body.scrollHeight);"
    )
    time.sleep(1)
    # find show more button
    show_more_button = find_element(
        browser.driver,
        Element.ShowMoreButton,
    )
    if not show_more_button:
        print("Show more button not found")
        return

    # scroll to show more button
    browser.driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
        show_more_button,
    )
    time.sleep(1)
    browser.driver.execute_script("arguments[0].click();", show_more_button)
    time.sleep(2)
    # Get list of ticker elements
    ticker_elements = browser.driver.find_elements(
        By.XPATH,
        Element.TickerListElement,
    )

    tickers: list[Ticker] = []
    for el in tqdm(ticker_elements):
        cols = el.find_elements(By.XPATH, ".//td")
        tickers.append(
            Ticker(
                symbol=cols[0].text,
                name=cols[1].text,
                sector=cols[2].text,
                market_value=float(cols[6].text.replace(",", "")),
                weight=float(cols[5].text),
            )
        )

    with open(out, "w") as f:
        json.dump([ticker.model_dump() for ticker in tickers], f)


# TradeRepublic
class TRElement(str, Enum):
    spacer = "//tr[@aria-hidden='true' and contains(@class, 'instrumentTableWrapper__rowSpacer')]"


def get_spacer_height(spacer: WebElement):
    style = spacer.get_attribute("style")
    height_str = style.split("height:")[-1].split("px")[0].strip()
    return int(height_str)


def traderepublic(out: str):
    browser = Browser(headless=False, profile_name="stocks")
    browser.main_tab.open("https://app.traderepublic.com/browse/stock")
    time.sleep(2)

    collected_stocks = {}

    try:
        while True:
            # Capture currently visible rows in the table
            rows = browser.driver.find_elements(
                By.CSS_SELECTOR, "tr.tableRow.instrumentTableWrapper__row"
            )
            for row in rows:
                try:
                    # Locate the container that holds the name and ISIN details
                    info = row.find_element(
                        By.CSS_SELECTOR, "div.instrumentResult__info"
                    )
                    name = info.find_element(
                        By.CSS_SELECTOR, "span.instrumentResult__name"
                    ).text
                    isin = info.find_element(
                        By.CSS_SELECTOR, "span.instrumentResult__details"
                    ).text

                    # Use ISIN as a unique key to avoid duplicate entries
                    if isin not in collected_stocks:
                        collected_stocks[isin] = name
                except Exception as e:
                    # Skip rows that don't match the expected structure
                    print("Error extracting row:", e)

            # Scroll to the spacer element so new rows load
            browser.driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(0.5)
            spacers = browser.driver.find_elements(By.XPATH, TRElement.spacer)
            print(
                "Stocks collected:",
                len(collected_stocks),
                "Spacers:",
                [get_spacer_height(spacer) for spacer in spacers],
            )
    finally:
        with open(out, mode="w", newline="") as file:
            writer = csv.writer(file)
            # Write the header row
            writer.writerow(["Name", "ISIN"])

            # Write key-value pairs
            for key, value in collected_stocks.items():
                writer.writerow([value, key])
