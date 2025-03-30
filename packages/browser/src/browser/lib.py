import os

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class Tab:
    def __init__(
        self, driver: webdriver.Chrome, name: str, handle: str | None = None
    ):
        self.driver = driver
        self.name = name
        self.handle = handle

    def spawn(self):
        self.driver.switch_to.new_window("tab")
        self.driver.execute_script(f"window.name = '{self.name}';")
        self.handle = self.driver.current_window_handle

    def focus(self):
        try:
            self.driver.switch_to.window(self.name)
            return True
        except Exception:
            return False

    def open(
        self, url: str, tab: str = "main", control_xpath: str | None = None
    ):
        self.focus()
        self.driver.get(url)
        if control_xpath:
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, control_xpath))
                )
            except TimeoutException:
                print(f"Element not found within 10 seconds: {control_xpath}")

    def close(self, tab: str = "main"):
        self.focus()
        self.driver.close()


class Browser:
    def __init__(self, headless: bool = False, profile_name: str | None = None):
        options = Options()
        if profile_name:
            project_temp_profile = os.path.join(
                os.getcwd(), "profiles", profile_name
            )
            if not os.path.exists(project_temp_profile):
                os.makedirs(project_temp_profile)

            options.add_argument(f"--user-data-dir=profiles/{profile_name}")

        options.add_argument("--profile-directory=Profile 1")
        if headless:
            options.add_argument("--headless")
        options.add_experimental_option(
            "excludeSwitches", ["enable-automation"]
        )
        options.add_experimental_option("useAutomationExtension", False)

        self.driver = webdriver.Chrome(options=options)
        self.driver.get("https://www.google.com")
        self.driver.execute_script("window.name = 'main';")
        self.driver.switch_to.window("main")
        self.main_tab = Tab(
            self.driver, "main", handle=self.driver.current_window_handle
        )

    def new_tab(self, name: str) -> Tab:
        tab = Tab(self.driver, name)
        tab.spawn()
        return tab

    def switch_tab(self, tab: Tab):
        tab.focus()
