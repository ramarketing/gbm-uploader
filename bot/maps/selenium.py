import csv
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from ..base.selenium import BaseSelenium


class MapsSelenium(BaseSelenium):
    def __init__(self, file, search, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file = file
        self.search = search

        try:
            self.handle()
        finally:
            self.quit_driver()

    def handle(self):
        self.driver = self.get_driver(size=(1200, 700))
        self.driver.get('https://maps.google.com/')
        self.do_search()

        results = self.get_results()
        names = self.get_names(results)
        response = []

        for index, name in enumerate(names):
            result = self.get_result(name)
            link = self.get_share_link_for_result(result)
            gs360 = self.get_360_link_for_result(result)
            obj = {
                'name': name,
                'link': link,
                'gs360': gs360,
            }
            response.append(obj)

        for place in response:
            mid = self.get_mid_for_result(place['link'])
            place['mid'] = mid

        writer = csv.DictWriter(self.file, fieldnames=response[0].keys())
        for place in response:
            writer.writerow(place)

    def do_search(self):
        self._wait(3)
        self.fill_input(
            By.ID,
            'searchboxinput',
            self.search + Keys.RETURN
        )
        self._wait(3)

    def get_result(self, name):
        results = self.get_results()
        names = self.get_names(results)
        position = names.index(name)
        return results[position]

    def get_results(self):
        return self.get_elements(
            By.CLASS_NAME,
            'section-result'
        )

    def get_name_for_result(self, result):
        return self.get_text(
            By.CLASS_NAME,
            'section-result-title',
            source=result
        )

    def get_names(self, results):
        return [self.get_name_for_result(r) for r in results]

    def get_mid_for_result(self, link=None):
        source = self.get_source(link=link)
        mid = re.search(r'"\/?(g|m)\/.{5,10}"', source)
        if mid:
            mid = mid.group(0)[1:-1]
        return mid

    def get_share_link_for_result(self, result):
        result.click()
        self._wait(3)

        self.click_element(
            By.CSS_SELECTOR,
            '[jsaction="pane.placeActions.share"]'
        )
        self._wait(3)
        input_ = self.get_element(
            By.CSS_SELECTOR,
            '[jsaction="pane.copyLink.clickInput"]'
        )
        link = input_.get_attribute('value')
        self.click_element(
            By.CSS_SELECTOR,
            '[jsaction="modal.close"]'
        )

        return link

    def get_360_link_for_result(self, result):
        button = self.click_element(
            By.CSS_SELECTOR,
            '[aria-label="Street View"][jsaction="pane.imagepack.button"]',
            raise_exception=False
        )
        link = None

        if button:
            self._wait(5)
            self.click_element(
                By.CSS_SELECTOR,
                '[jsaction="titlecard.settings"]'
            )
            elements = self.get_elements(
                By.CLASS_NAME,
                'goog-menuitem'
            )
            elements[-1].click()
            input_ = self.get_element(
                By.CSS_SELECTOR,
                '[jsaction="pane.copyLink.clickInput"]'
            )
            link = input_.get_attribute('value')
            self.click_element(
                By.CSS_SELECTOR,
                '[jsaction="modal.close"]'
            )
            self.click_element(
                By.CSS_SELECTOR,
                (
                    '[jsaction="pane.topappbar.back;'
                    'focus:pane.focusTooltip;blur:pane.blurTooltip"]'
                )
            )
        self.click_element(
            By.CSS_SELECTOR,
            '[jsaction="pane.place.backToList"]'
        )

        self._wait(3)
        return link

    def get_source(self, link=None):
        if link:
            self.driver.get(link)
            self._wait(3)
        element = self.get_element(By.TAG_NAME, 'html')
        return element.get_attribute('innerHTML')
