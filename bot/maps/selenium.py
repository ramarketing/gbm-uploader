import csv
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from ..base.selenium import BaseSelenium


class MapsSelenium(BaseSelenium):
    def __init__(self, cid, file=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cid = cid
        self.file = file
        self.city = None
        self.state = None
        self.zip_code = None

        if cid.get('address', None):
            address_parts = cid['address'].split(', ')
            self.state, self.zip_code = address_parts[-2].split()
            self.city = address_parts[-3].strip()

    def __call__(self):
        try:
            return self.handle()
        finally:
            self.quit_driver()

    def handle(self):
        self.driver = self.get_driver(size=(1200, 700))
        if not self.cid.get('mid', None):
            self.driver.get(self.cid['cid'])
            self._wait(5)
            return {
                'cid': self.cid['cid'],
                'metro area': self.cid['metro area'],
                'state': self.cid['state'],
                'name': self.get_cid_name(),
                'address': self.get_cid_address(),
                'mid': self.get_mid_for_result(),
            }
        else:
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
                    'neighborhood name': name,
                    'city section': '',
                    'map neighborhood url': link,
                    'streetview url': gs360,
                    'search string url': ''
                }
                response.append(obj)
                break

            for place in response:
                link = place['map neighborhood url']
                mid = self.get_mid_for_result(link)
                driving = self.get_driving_directions_for_result(link)
                place['machine id'] = mid
                place['driving directions url'] = driving

            writer = csv.DictWriter(self.file, fieldnames=response[0].keys())
            writer.writeheader()
            for place in response:
                writer.writerow(place)

    def get_cid_name(self):
        return self.get_text(
            By.CSS_SELECTOR, '.section-hero-header-title-title'
        )

    def get_cid_address(self):
        value = self.get_text(
            By.CSS_SELECTOR,
            '.section-info-text > span.widget-pane-link'
        )
        if not value:
            self._start_debug()
        return value

    def do_search(self):
        metro_area = self.cid['metro area']
        state = self.cid['state']

        self._wait(3)
        self.fill_input(
            By.ID,
            'searchboxinput',
            f'neighborhoods in {metro_area} {state}' + Keys.RETURN
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
        mid = re.search(r'"\/?(g|m)\/.{8,12}"', source)
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

    def get_driving_directions_for_result(self, link=None):
        if link:
            self.driver.get(link)
        self.click_element(
            By.CSS_SELECTOR,
            '[jsaction="pane.placeActions.directions"]'
        )
        self.fill_input(
            By.CSS_SELECTOR,
            '#directions-searchbox-0 input',
            self.cid['address']
        )
        self.click_element(
            By.CSS_SELECTOR,
            'button.widget-directions-reverse'
        )
        self._wait(5)
        self.click_element(
            By.CSS_SELECTOR,
            (
                '[jsaction="settings.open;mouseover:omnibox.showTooltip;'
                'mouseout:omnibox.hideTooltip;focus:omnibox.showTooltip;'
                'blur:omnibox.hideTooltip"]'
            )
        )
        self._wait(2)
        self.click_element(
            By.CSS_SELECTOR,
            'button[jsaction="settings.share"]'
        )
        element = self.get_element(
            By.CSS_SELECTOR,
            '[jsaction="pane.copyLink.clickInput"]'
        )
        return element.get_attribute('value')

    def get_source(self, link=None):
        if link:
            self.driver.get(link)
            self._wait(3)
        element = self.get_element(By.TAG_NAME, 'html')
        return element.get_attribute('innerHTML')
