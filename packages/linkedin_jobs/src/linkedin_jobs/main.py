import math
import random
import re
import time
from enum import Enum

from pydantic import BaseModel
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from linkedin_jobs.classes import Browser, Tab
from linkedin_jobs.db import Job, session

CAPTION_RE = re.compile(r"(.*)\s\((.*)\)")


def find_element(object: WebElement | Chrome, xpath: str) -> WebElement | None:
    elements = object.find_elements(
        By.XPATH,
        xpath,
    )
    if elements:
        return elements.pop()
    return None


def parse_thumbnail_caption(
    element: WebElement,
) -> tuple[str, str | None]:
    match = re.match(CAPTION_RE, element.text)
    if match:
        return match.groups()
    return element.text, None


class Element(str, Enum):
    JobCardContainer = ".//div[contains(@class, 'job-card-container')]"
    JobCardTitle = ".//a[contains(@class, 'job-card-list__title--link')]/span[@aria-hidden='true']"
    JobCardCompany = (
        ".//div[contains(@class, 'artdeco-entity-lockup__subtitle')]/span"
    )
    JobCardPlaceFormat = (
        ".//div[contains(@class, 'artdeco-entity-lockup__caption')]/ul/li/span"
    )
    JobNumber = (
        ".//div[contains(@class, 'jobs-search-results-list__subtitle')]/span"
    )
    JobDescription = ".//div[contains(@id, 'job-details')]/div/p"


class GeoId(Enum):
    Munich = 100477049


class JobPosting(BaseModel):
    linkedin_id: str
    title: str
    company: str
    place: str | None
    format: str | None
    description: str


class JobSearch:
    url_base = "https://www.linkedin.com/jobs/search/?"

    def __init__(
        self,
        tab: Tab,
        keywords: str,
        city: GeoId,
        distance: int = 10,
    ):
        self.driver = tab.driver
        self.parameters = {
            "distance": distance,
            "f_TPR": "r86400",
            "geoId": city.value,
            "keywords": keywords,
            "origin": "JOB_SEARCH_PAGE_JOB_FILTER",
            "refresh": "true",
        }
        self.jobs_number = 25

    def _open_search(self, page: int = 0):
        temp_parameters = self.parameters.copy()
        if page > 0:
            temp_parameters["start"] = page * 25
        url = self.url_base + "&".join(
            [f"{key}={value}" for key, value in temp_parameters.items()]
        )
        self.driver.get(str(url))
        time.sleep(2)

    def _parse_jobs_number(self):
        if number_element := find_element(self.driver, Element.JobNumber):
            self.jobs_number = int(number_element.text.split()[0])

    def _load_all_cards(self):
        previous_count = 0
        while True:
            cards = self.driver.find_elements(
                By.XPATH, Element.JobCardContainer
            )
            if len(cards) == previous_count:
                break
            previous_count = len(cards)

            # Scroll the last card into view
            last_card = cards[-1]
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", last_card
            )
            time.sleep(1)

    def _read_job(self, card: WebElement) -> JobPosting | None:
        if not (linkedin_id := card.get_attribute("data-job-id")):
            return None

        time.sleep(random.randrange(5, 20) / 10)

        # Read thumbnail
        title_block = find_element(
            card,
            Element.JobCardTitle,
        )
        company_block = find_element(
            card,
            Element.JobCardCompany,
        )
        place_format_block = find_element(
            card,
            Element.JobCardPlaceFormat,
        )
        place, format = (
            parse_thumbnail_caption(place_format_block)
            if place_format_block
            else (None, None)
        )

        # Open job card and read details
        self.driver.execute_script("arguments[0].scrollIntoView(true);", card)
        card.click()
        job_description = find_element(self.driver, Element.JobDescription)

        return JobPosting(
            linkedin_id=linkedin_id,
            title=title_block.text if title_block else "",
            company=company_block.text if company_block else "",
            place=place,
            format=format,
            description=job_description.text if job_description else "",
        )

    def _read_jobs(self) -> list[JobPosting]:
        self._load_all_cards()
        job_postings = [
            self._read_job(card)
            for card in self.driver.find_elements(
                By.XPATH, Element.JobCardContainer
            )
        ]
        return [job for job in job_postings if job]

    def _save_to_db(self, jobs: list[JobPosting]):
        new_jobs: list[Job] = []
        for job in jobs:
            existing = (
                session.query(Job)
                .filter_by(linkedin_id=job.linkedin_id)
                .first()
            )
            if not existing:
                new_jobs.append(Job(**job.model_dump()))
        session.add_all(new_jobs)
        session.commit()

    def scrape(self):
        job_postings: list[JobPosting] = []
        i = 0
        while i < math.ceil(self.jobs_number / 25):
            self._open_search(page=i)
            self._parse_jobs_number()
            job_postings += self._read_jobs()
            i += 1

        self._save_to_db(job_postings)


def main():
    browser = Browser()

    browser.main_tab.open("https://www.linkedin.com/login")
    time.sleep(2)

    if "linkedin.com/login" in browser.driver.current_url:
        input("Press Enter to continue...")

    job_search = JobSearch(browser.main_tab, "Software", GeoId.Munich)
    job_search.scrape()
    input("Press Enter to continue...")


if __name__ == "__main__":
    main()
