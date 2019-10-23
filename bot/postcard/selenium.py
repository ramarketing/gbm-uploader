from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from ..base.selenium import BaseSelenium
from ..utils import permute_characters


class PostcardSelenium(BaseSelenium):
    def __init__(self, postcard, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.postcard = postcard
        self.handle()
        self.quit_driver()

    def handle(self):
        self.driver = self.get_driver(size=(1200, 700))
        self.do_login(
            self.postcard.account, url='https://business.google.com/create'
        )
        self.do_name()
        self.do_can_visit()
        self.do_address_country()
        self.do_address_state()
        self.do_address_state()
        self.do_address_zip_code()
        self.do_address_city()
        self.do_address_street()

        import pdb
        pdb.set_trace()

    def do_name(self):
        name = 'For: {recipient} {address}'.format(**self.postcard.raw_data)

        xpath_input = (
            'input[aria-label="Type your business name"]',
        )
        self.clear_input(By.CSS_SELECTOR, xpath_input)
        self.fill_input(
            By.CSS_SELECTOR,
            xpath_input,
            name + Keys.RETURN
        )

        xpath = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[2]/div/div[2]/div/'
            'div/div[2]/div/div/div[1]'
        )
        self.click_element(By.XPATH, xpath, raise_exception=False)

        xpath = '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[3]/div[1]'
        self.click_element(By.XPATH, xpath)

    def do_can_visit(self):
        xpath = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[2]/div/div[1]/div'
        )
        self.click_element(By.XPATH, xpath)

        xpath = '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[3]/div[1]'
        self.click_element(By.XPATH, xpath)

    def do_address_state(self):
        self.click_element(By.CSS_SELECTOR, 'div[aria-label="State"]')
        xpath_state_options = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[2]/div/div/div[1]/'
            'div/div/c-wiz/c-wiz/div/div/div[6]/div[1]/div[2]/div',
        )
        state_options = self.get_elements(
            By.XPATH, xpath_state_options, timeout=3
        )
        for option in state_options:
            code = option.get_attribute('data-value')
            if code.upper() != self.postcard.state.upper():
                continue
            option.click()

    def do_address_city(self):
        # City
        self.fill_input(
            By.CSS_SELECTOR,
            'input[aria-label="City"]',
            self.postcard.city
        )

    def do_address_street(self):
        # Street
        street = permute_characters(self.postcard.address, replaces=5)
        print(street)
        try:
            self.fill_input(
                By.CSS_SELECTOR,
                'input[aria-label="Street address"]',
                street
            )
        except TimeoutException:
            self.fill_input(
                By.XPATH,
                (
                    '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[2]/div/div/'
                    'div[1]/div/div/c-wiz/c-wiz/div/div/div[4]/div/div[1]/div/'
                    'div[1]/input'
                ),
                street
            )
        xpath_next = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[3]/div[1]',
        )
        self.click_element(By.XPATH, xpath_next, timeout=3)

    def do_address_zip_code(self):
        # ZIP
        self.fill_input(
            By.CSS_SELECTOR,
            'input[aria-label="ZIP code"]',
            self.postcard.zip_code.split('-')[0]
        )

    def do_address_country(self):
        # Country
        self.click_element(
            By.CSS_SELECTOR, 'div[aria-label="Country / Region"]'
        )
        xpath_country_options = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[2]/div/div/'
            'div[1]/div/div/c-wiz/c-wiz/div/div/div[1]/div[1]/div[2]/div',
        )
        country_options = self.get_elements(By.XPATH, xpath_country_options)
        for option in country_options:
            code = option.get_attribute('data-value')
            if code.upper() != self.postcard.country.code.upper():
                continue
            option.click()

        self._wait(3)
