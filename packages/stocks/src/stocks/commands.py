import json
import time
from enum import Enum

from browser.lib import Browser
from pydantic.main import BaseModel
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from tqdm import tqdm


class Element(str, Enum):
    ShowMoreButton = ".//div[@id='allHoldingsTable_wrapper']//div[@class='show-all']//a[@class='toggle-records']"
    TickerListElement = ".//table[@id='allHoldingsTable']/tbody/tr"


class Ticker(BaseModel):
    symbol: str
    name: str
    sector: str
    market_value: float
    weight: float


# allHoldingsTable_wrapper > div.datatables-utilities.ui-helper-clearfix > div.show-all
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
