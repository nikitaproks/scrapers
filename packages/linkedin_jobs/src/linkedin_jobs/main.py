import os
import time
from selenium import webdriver
from pathlib import Path
from enum import Enum
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement
from pydantic import BaseModel


class GeoId(Enum):
    Munich = 100477049


class Thumbnail(BaseModel):
    job_id: str
    title: str
    company: str
    place: str
    format: str


class JobSearch:
    url_base = Path("https://www.linkedin.com/jobs/search/?")

    def __init__(
        self, driver: webdriver.Chrome, keywords: str, city: GeoId, distance: int = 10
    ):
        self.driver = driver
        self.parameters = {
            "distance": distance,
            "geoId": city.value,
            "origin": "JOB_SEARCH_PAGE_JOB_FILTER",
            "refresh": "true",
            "f_TPR": "r86400",
            "keywords": keywords,
        }
        self._open_search()
        time.sleep(3)

    def scrape(self):
        self._load_all_cards()
        jobs = self._read_job_thumbnail()
        print(jobs)

    def _open_search(self):
        url = self.url_base / "&".join(
            [f"{key}={value}" for key, value in self.parameters.items()]
        )
        self.driver.get(str(url))

    def _load_all_cards(self):
        previous_count = 0
        while True:
            cards = self.driver.find_elements(By.CSS_SELECTOR, "div.job-card-container")
            if len(cards) == previous_count:
                break
            previous_count = len(cards)

            # Scroll the last card into view
            last_card = cards[-1]
            self.driver.execute_script("arguments[0].scrollIntoView(true);", last_card)
            time.sleep(1)

    def _read_job_thumbnail(self) -> list[Thumbnail]:
        jobs: list[Thumbnail] = []
        for card in self.driver.find_elements(By.XPATH, "//div[@data-job-id]"):
            if job_id := card.get_attribute("data-job-id"):
                title_block = card.find_elements(
                    By.XPATH,
                    ".//a[contains(@class, 'job-card-list__title--link')]/span[@aria-hidden='true']",
                ).pop()
                company_block = card.find_elements(
                    By.XPATH,
                    ".//span[@class='EkSbRKxoEDInamyWLVvMrOoyFWbvRyaAStjo ']",
                ).pop()
                place_format_block = card.find_elements(
                    By.XPATH,
                    ".//li[@class='kcDwsQoAbFUGaVAIZfOdIgdPTAzFKEceDOys ']",
                ).pop()
                place, format = place_format_block.text[:-1].split(" (")
                jobs.append(
                    Thumbnail(
                        job_id=job_id,
                        title=title_block.text,
                        company=company_block.text,
                        place=place,
                        format=format,
                    )
                )
        return jobs


def main():
    project_temp_profile = os.path.join(os.getcwd(), "tmp")
    if not os.path.exists(project_temp_profile):
        os.makedirs(project_temp_profile)

    options = Options()
    options.add_argument(f"--user-data-dir={project_temp_profile}")
    options.add_argument("--profile-directory=Profile 1")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)
    driver.get("https://www.linkedin.com/jobs/")
    time.sleep(2)

    if "linkedin.com/login" in driver.current_url:
        input("Press Enter to continue...")

    job_search = JobSearch(driver, "Software", GeoId.Munich)
    job_search.scrape()
    input("Press Enter to continue...")


if __name__ == "__main__":
    main()
