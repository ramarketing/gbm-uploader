from selenium.webdriver.common.by import By

from ..base.selenium import BaseSelenium
from ..base.exceptions import MaxRetries
from ..utils import permute_characters, remove_words_with_numbers


class PostcardSelenium(BaseSelenium):
    def __init__(self, postcard, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.postcard = postcard
        try:
            self.handle()
        except Exception:
            self.quit_driver()
            raise

    def handle(self):
        self.driver = self.get_driver(size=(1200, 700))
        self.do_login(
            self.postcard.account, url='https://business.google.com/create'
        )
        self.do_name()
        self.do_can_visit()
        self.do_address_country()
        try:
            self.do_address_state()
            self.do_address_state(raise_exception=False)
        except Exception:
            pass
        self.do_address_zip_code()
        self.do_address_city()
        self.do_address_street()
        self.do_map()
        self.do_can_visit()
        self.do_service_area()
        self.do_category()
        self.do_phone()
        self.do_finish()
        self.do_contact_name()

    def do_name(self):
        if self.postcard.recipient:
            address = '{street} {city} {state} {zip_code}'.format(
                **self.postcard.verification_address.raw_data
            )
            name = 'For: {recipient} {address}'.format(
                recipient=self.postcard.recipient,
                address=address,
                special_id=self.postcard.special_id
            )
        else:
            name = self.postcard.name

        self.click_element(
            By.XPATH,
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[2]/div/div[4]/div'
        )

        xpath_input = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[2]/div/div/div/'
            'div/div/div[1]/div[2]/div[1]/div/div[1]/input'
        )

        while not self.fill_input(
            By.XPATH,
            xpath_input,
            (
                permute_characters(name)
                if self.postcard.recipient else name
            ),
            max_retries=1,
            raise_exception=False
        ):
            pass

        xpath = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[3]/div[1]'
        )
        self.click_element(By.XPATH, xpath, timeout=3)

    def do_can_visit(self):
        content = self.get_text(By.TAG_NAME, 'body')

        if 'Is this your business' in content:
            import pdb
            pdb.set_trace()
        else:
            xpath = (
                '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[2]/div/'
                'div[1]/div'
            )
        self.click_element(By.XPATH, xpath, timeout=3)

        xpath = '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[3]/div[1]'
        self.click_element(By.XPATH, xpath, timeout=3)

    def do_address_city(self):
        # City
        self.fill_input(
            By.CSS_SELECTOR,
            'input[aria-label="City"]',
            self.postcard.city
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

    def do_address_state(self, **kwargs):
        self.click_element(By.CSS_SELECTOR, 'div[aria-label="State"]')
        xpath_state_options = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[2]/div/div/div[1]/'
            'div/div/c-wiz/c-wiz/div/div/div[6]/div[1]/div[2]/div',
        )
        state_options = self.get_elements(
            By.XPATH, xpath_state_options, timeout=3, **kwargs
        )
        if state_options:
            for option in state_options:
                code = option.get_attribute('data-value')
                if code.upper() != self.postcard.state.upper():
                    continue
                option.click()

    def do_address_street(self):
        # Street
        if self.postcard.recipient:
            street = '{street} {city} {state} {zip_code}'.format(
                **self.postcard.verification_address.raw_data
            )
        else:
            street = self.postcard.address

        while not self.fill_input(
            By.CSS_SELECTOR,
            'input[aria-label="Street address"]',
            permute_characters(street) if self.postcard.recipient else street,
            max_retries=1,
            raise_exception=False
        ):
            pass

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

    def do_map(self):
        content = 'Where are you located'
        retries = 0

        while 'Where are you located' in content:
            if retries == 4:
                self.postcard.update(status='not-created')
                raise MaxRetries

            self.click_element(
                By.XPATH,
                '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[3]/div[1]',
                timeout=3
            )
            content = self.get_text(By.TAG_NAME, 'body')
            retries += 1

    def do_service_area(self):
        sa = '{}, {}'.format(self.postcard.city, self.postcard.state)
        self.fill_input(
            By.XPATH,
            (
                '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[2]/div/div/div/'
                'div/div/div/div[1]/div[2]/div[1]/div/div[1]/input'
            ),
            sa,
            timeout=3
        )

        self.click_element(
            By.XPATH,
            (
                '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[2]/div/div/'
                'div/div/div/div/div[3]/div/div/div[1]'
            ),
            timeout=3
        )
        self.click_element(
            By.XPATH,
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[3]/div[1]',
            timeout=3
        )

    def do_category(self):
        xpath_input = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[2]/div/div/div/'
            'div/div/div[1]/div[2]/div[1]/div/div[1]/input'
        )
        self.fill_input(
            By.XPATH, xpath_input, self.postcard.category, timeout=3
        )
        xpath_option = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[2]/div/div/div/'
            'div/div/div[2]/div/div'
        )
        self.click_element(By.XPATH, xpath_option, timeout=3)
        xpath_next = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[3]/div[1]',
        )
        self.click_element(By.XPATH, xpath_next, timeout=3)

    def do_phone(self):
        xpath_phone = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[2]/div/form/'
            'div[1]/div/div/div/div/div[2]/div[1]/div/div[1]/input',
        )
        self.clear_input(
            By.XPATH, xpath_phone, timeout=3
        )
        self.fill_input(By.XPATH, xpath_phone, self.postcard.phone)

        xpath_option = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[2]/div/form/'
            'div[2]/div/span/div[2]/div'
        )
        self.click_element(By.XPATH, xpath_option)

        xpath_next = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[3]/div[1]'
        )
        self.click_element(By.XPATH, xpath_next)

    def do_finish(self):
        self.click_element(
            By.XPATH, '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[3]/div[1]'
        )

    def do_contact_name(self):
        if not self.postcard.recipient:
            return

        name = remove_words_with_numbers(
            '{special_id} to:{first_name} Addr:{street} {state}'.format(
                special_id=self.postcard.special_id,
                first_name=self.postcard.recipient.split(' ')[0],
                street=self.postcard.verification_address.street,
                state=self.postcard.verification_address.state
            )
        )

        xpath_input = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div/div[2]/div/div/div/'
            'div[1]/div/div[1]/div/div/div[1]/div/div[1]/div/div[1]/input'
        )
        self.fill_input(
            By.XPATH,
            xpath_input,
            name[0:30],
            timeout=10
        )

        xpath_input = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div/div[2]/div/div/div/'
            'div[1]/div/div[2]/button'
        )
        self.click_element(By.XPATH, xpath_input)

        xpath_input = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div/div[2]/div/div/'
            'div[3]/button'
        )
        self.click_element(By.XPATH, xpath_input, timeout=3)
