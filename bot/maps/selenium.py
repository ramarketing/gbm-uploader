import traceback

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from base.selenium import BaseSelenium


class MapsSelenium(BaseSelenium):
    WAIT_BEFORE_NEXT = 5
    WAIT_BEFORE_INPUT = 10

    def __init__(self, entity, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entity = entity
        try:
            self.handle()
        except Exception as err:
            print(err)
            print(traceback.format_exc())
            self._start_debug()
        self.quit_driver()

    def handle(self):
        self.driver = self.get_driver(size=(1200, 700))
        self.go_to_maps()
        self.click_directions()
        self.fill_points()
        self.click_by_car()
        self.navigate_share()
        self.get_link()

    def go_to_maps(self):
        self.driver.get('https://www.google.com/maps/')

    def click_directions(self):
        self.click_element(By.ID, 'searchbox-directions')

    def click_by_car(self):
        self.click_element(By.CLASS_NAME, 'directions-drive-icon')

    def fill_points(self):
        self.fill_input(
            By.XPATH,
            '//*[@id="directions-searchbox-0"]/div/div/input',
            self.entity.location + Keys.RETURN,
            timeout=5
        )
        self.fill_input(
            By.XPATH,
            '//*[@id="directions-searchbox-1"]/div/div/input',
            self.entity.address.replace('\n', ' ') + Keys.RETURN,
            timeout=5
        )

    def navigate_share(self):
        self.click_element(
            By.XPATH,
            '//*[@id="omnibox-directions"]/div/div[1]/button'
        )
        self.click_element(
            By.CSS_SELECTOR,
            'button[jsaction="settings.share"]',
            timeout=5
        )

    def get_link(self):
        element = self.get_element(
            By.CSS_SELECTOR,
            'input[jsaction="pane.copyLink.clickInput"]',
            move=False
        )
        value = element.get_attribute('value')
        self.entity.update(directions=value)
