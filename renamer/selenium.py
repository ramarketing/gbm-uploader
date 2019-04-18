from datetime import datetime
import platform
from random import randint

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from base.exceptions import (
    CaptchaError, CredentialInvalid, EmptyList, EntityInvalid, NotFound
)
from base.selenium import BaseSelenium
from captcha import HttpClient, AccessDeniedException

import config
from utils import save_image_from_url


class RenamerSelenium(BaseSelenium):
    def __init__(self, entity, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entity = entity
        self.handle()

    def handle(self):
        self.driver = self.get_driver()
        self.do_login()
        self.do_open_verification_tab()
        self.go_to_edit()
        self.do_final_name()
        self.do_final_category()
        self.do_service_area()
        self.do_hours()
        self.do_special_hours()
        self.do_website()
        self.do_description()
        self.do_opening_date()

        self.do_code_fill()

        self.do_address()
        self.do_phone()

        self.driver.close()
        self.driver.switch_to_window(self.driver.window_handles[0])

        self.do_code_send()

    def go_to_edit(self):
        row = self.get_business_row()
        self.click_element(
            By.XPATH,
            'td[3]/content/a',
            source=row
        )
        current_url = self.driver.current_url
        self.driver.get(current_url.replace('/dashboard/', '/edit/'))

    def get_business_row(self):
        if self.driver.current_url == 'https://business.google.com/locations':
            self.driver.get('https://business.google.com/locations')

        rows = self.get_elements(
            By.XPATH,
            (
                '/html/body/div[4]/c-wiz/div[2]/div[1]/c-wiz/div/c-wiz[3]'
                '/div/content/c-wiz[2]/div[2]/table/tbody/tr'
            ),
            raise_exception=False
        )
        if not rows:
            raise EmptyList(
                msg="There aren't any business", logger=self.logger
            )

        row = None
        for r in rows:
            if self.entity.name in r.text:
                row = r
                break

        if not row:
            raise NotFound(msg="Business not found.", logger=self.logger)

        return row

    def do_login(self):
        self.driver.get('https://accounts.google.com/ServiceLogin')
        self.fill_input(
            By.ID,
            'identifierId',
            self.entity.email + Keys.RETURN
        )
        self.fill_input(
            By.NAME,
            'password',
            self.entity.password + Keys.RETURN,
            timeout=3
        )

        self._wait(3)
        success = self.driver.current_url.startswith(
            'https://myaccount.google'
        )
        if success:
            return

        captcha_client = HttpClient(
            config.CAPTCHA_USERNAME, config.CAPTCHA_PASSWORD
        )
        captcha_element = self.get_element(
            By.ID,
            'captchaimg',
            timeout=3,
            raise_exception=False
        )
        captcha_solution = None

        while captcha_element:
            if captcha_solution:
                captcha_client.report(captcha_solution["captcha"])

            url = captcha_element.get_attribute('src')
            image_path = save_image_from_url(url, 'captcha.jpg')

            try:
                captcha_client.get_balance()
                captcha_solution = captcha_client.decode(image_path)
                if captcha_solution:
                    self.logger(
                        instance=captcha_client,
                        data="CAPTCHA %s solved: %s" % (
                            captcha_solution["captcha"],
                            captcha_solution["text"]
                        )
                    )

                    if '':
                        captcha_client.report(captcha_solution["captcha"])
                    else:
                        self.fill_input(
                            By.NAME,
                            'password',
                            self.entity.password
                        )
                        self.fill_input(
                            By.CSS_SELECTOR,
                            'input[type="text"]',
                            captcha_solution["text"] + Keys.RETURN
                        )
            except AccessDeniedException:
                raise CaptchaError(
                    data=(
                        'Access to DBC API denied, check '
                        'your credentials and/or balance'
                    ),
                    logger=self.logger
                )

        success = self.click_element(
            By.ID,
            'knowledgePreregisteredEmailResponse',
            raise_exception=False,
            timeout=3
        )
        if success:
            self.fill_input(
                By.NAME,
                'knowledgePreregisteredEmailResponse',
                self.entity.recovery_email + Keys.RETURN,
                timeout=3
            )

        phone = self.get_text(
            By.ID,
            'deviceAddress',
            timeout=3,
            raise_exception=False
        )
        if phone:
            raise EntityInvalid(
                msg="Phone number is required", logger=self.logger
            )

        self._wait(3)
        success = self.driver.current_url.startswith(
            'https://myaccount.google'
        )
        if not success:
            raise CredentialInvalid(
                msg="Login failed", logger=self.logger
            )

    def do_open_verification_tab(self):
        row = self.get_business_row()
        element = self.get_element(
            By.XPATH,
            'td[5]/content/div/div',
            source=row
        )

        if platform.system() == 'Windows':
            ActionChains(self.driver) \
                .key_down(Keys.COMMAND) \
                .click(element) \
                .key_up(Keys.COMMAND) \
                .perform()
        else:
            ActionChains(self.driver) \
                .key_down(Keys.CONTROL) \
                .click(element) \
                .key_up(Keys.CONTROL) \
                .perform()

        self.driver.switch_to_window(self.driver.window_handles[1])

        text = self.get_element('//body').text.strip()
        if (
            'Enter the code' not in text and
            'Get your code at this number now by automated call' not in text
        ):
            raise EntityInvalid(
                "Cannot validate by phone.", logger=self.logger
            )

        self.driver.switch_to_window(self.driver.window_handles[0])

    def do_final_name(self):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[1]/div[2]/'
                'content/div[2]'
            )
        )

        xpath_input = (
            '//*[@id="js"]/div[9]/div/div[2]/content/div/div[4]/'
            'div/div[1]/div/div[1]/input'
        )

        self.clear_input(By.XPATH, xpath_input)
        self.fill_input(By.XPATH, xpath_input, self.entity.final_name)
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[9]/div/div[2]/content/div/div[5]/div[2]'
            ),
        )

    def do_final_category_1(self):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[1]/div[2]/'
                'content/div[3]'
            )
        )

        xpath_input = (
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
            'div/div[1]/div/div[1]/div[1]/input[2]'
        )

        self.clear_input(By.XPATH, xpath_input)
        self.fill_input(By.XPATH, xpath_input, self.entity.final_category_1)

        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
                'div/div[1]/div/div[1]/div[2]/div/div'
            )
        )
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[5]/div[2]',
            ),
        )

    def do_service_area(self):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[1]/div[2]/'
                'content/div[5]'
            )
        )

        xpath_input = (
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div/div[1]/'
            'div/div/div/div/div/div/div[1]/div[2]/div[1]/div/div[1]/input'
        )
        self.clear_input(By.XPATH, xpath_input)
        self.fill_input(By.XPATH, xpath_input, self.entity.final_name)

        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
                'div/div[1]/div/div/div/div/div/div/div[2]/div/div/div[1]'
            )
        )
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[5]/div[2]'
            )
        )

    def do_hours(self):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[1]/div[2]/'
                'content/div[6]'
            )
        )
        elements = self.get_elements(
            By.XPATH,
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[3]/div/div'
        )
        for element in elements:
            self.click_element(
                By.XPATH,
                'label/div',
                source=element
            )
            self.click_element(
                By.XPATH,
                'div[2]/div[1]/div/div[1]/div[1]/input[2]',
                source=element
            )
            self.click_element(
                By.XPATH,
                'div[2]/div[1]/div/div[1]/div[2]/div/div/div[1]',
                source=element
            )

        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div[2]'
        )

    def do_special_hours(self):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[1]/div[2]/'
                'content/div[7]'
            )
        )
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
                'div[2]/div[1]/span[1]/div'
            )
        )
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
                'div[2]/div[3]/span[1]/div'
            )
        )
        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[5]/div[2]'
        )

    def do_website(self):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[1]/div[2]/'
                'content/div[9]'
            )
        )

        xpath_input = (
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div[1]/'
            'div[1]/div/div[1]/input'
        )
        self.clear_input(By.XPATH, xpath_input)
        self.fill_input(By.XPATH, xpath_input, self.entity.final_website)

        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[5]/div[2]'
        )

    def do_attributes(self):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[1]/div[2]/'
                'content/div[10]'
            )
        )
        source = self.get_elements(
            By.XPATH,
            '//*[@id="attr-dialog-content"]/div'
        )
        to_clic = randint(1, 2)
        source = source[to_clic]
        self.click_element(
            By.XPATH,
            'div',
            source=source
        )
        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[5]/div[2]'
        )

    def do_description(self):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[1]/div[2]/'
                'content/div[11]'
            )
        )

        xpath_input = (
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
            'div/div[1]/div[1]/textarea'
        )
        self.clear_input(By.XPATH, xpath_input)
        self.fill_input(By.XPATH, xpath_input, self.entity.final_description)
        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[11]/div/div[2]/content/div/div[5]/div[2]'
        )

    def do_opening_date(self):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[1]/div[2]/'
                'content/div[12]'
            )
        )

        date_start = int(datetime(2011, 1, 1).timestamp())
        date_end = int(datetime(2018, 12, 31).timestamp())
        date_final = randint(date_start, date_end)
        date_final = datetime.fromtimestamp(date_final)

        # Year
        self.fill_input(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
                'div[1]/span[1]/div/div[1]/div/div[1]/input'
            ),
            date_final.year
        )
        # Month
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
                'div[1]/span[2]/span/div'
            )
        )
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
                'div[1]/span[2]/span/div/div[2]/div[{}]'
            ).format(date_final.month + 2)
        )
        # Day
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
                'div[1]/span[3]/div'
            )
        )
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
                'div[1]/span[3]/div/div[2]/div[{}]'
            ).format(date_final.day + 2)
        )

        # Apply
        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[5]/div[2]'
        )

    def do_code_fill(self):
        self.driver.switch_to_window(self.driver.window_handles[1])

        success = self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[2]/div/div/div/'
                'div[1]/div/div[2]/button[2]'
            ),
            raise_exception=False
        )

        if not success:
            self.click_element(
                By.XPATH,
                (
                    '//*[@id="main_viewpane"]/c-wiz[1]/div/div[2]/div/div/'
                    'div[2]/div/div[1]/button'
                ),
            )

        code = self.entity.get_code()
        self.fill_input(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[2]/div/div/'
                'div[1]/div[2]/div[1]/div/div[1]/input'
            ),
            code
        )

        self.driver.switch_to_window(self.driver.window_handles[0])

    def do_address(self):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[1]/div[2]/'
                'content/div[4]'
            )
        )
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
                'div/div[3]/div[4]/div'
            )
        )

        xpath_input_address = (
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div/div[3]/'
            'div[1]/div/div/div[2]/div/div/div[2]/input'
        )
        self.fill_input(
            By.XPATH,
            xpath_input_address,
            (
                '{address} {city} {state} {zip_code}'.format(
                    address=self.entity.final_address,
                    city=self.entity.final_city,
                    state=self.entity.final_state,
                    zip_code=self.entity.final_zip_code
                )
            )
        )

        # Zip Code
        self.fill_input(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div/div[3]/'
                'div[1]/div/div/div[2]/div/div/div[6]/input'
            ),
            self.entity.final_zip_code
        )

        # State
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div/'
                'div[3]/div[1]/div/div/div[2]/div/div/div[5]/div[2]'
            )
        )
        elements = self.get_elements(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div/'
                'div[3]/div[1]/div/div/div[2]/div/div/div[5]/div[3]/div'
            )
        )

        for element in elements:
            if element.text == self.entity.final_state:
                self.click(
                    By.XPATH,
                    'div',
                    source=element
                )
                break

        self.fill_input(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div/'
                'div[3]/div[1]/div/div/div[2]/div/div/div[4]/input'
            ),
            self.entity.final_city
        )

        self.clear_input(By.XPATH, xpath_input_address)
        self.fill_input(
            By.XPATH,
            xpath_input_address,
            self.entity.final_address
        )

        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[5]/div[2]'
        )

    def do_phone(self):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[1]/div[2]/'
                'content/div[8]'
            )
        )
        xpath_input = (
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[3]/div[1]/'
            'div/div/div[2]/div[1]/div/div[1]/input'
        )
        self.clear_input(By.XPATH, xpath_input)
        self.fill_input(By.XPATH, xpath_input, self.final_phone_number)
        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div[2]'
        )

    def do_code_send(self):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[2]/div/div/'
                'div[1]/div[3]/button'
            )
        )

    def get_final_data(self):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[1]/div[1]/div/header/div[2]/div[1]/'
                'div[4]/div/a'
            )
        )
        self._start_debug()
