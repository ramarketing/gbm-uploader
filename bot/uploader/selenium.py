import platform
import traceback

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import config
from base.exceptions import (
    CaptchaError, CredentialInvalid, EmptyList, EntityInvalid,
    EntityIsSuccess, InvalidValidationMethod, NotFound, MaxRetries,
    TerminatedByUser
)
from base.selenium import BaseSelenium
from captcha import HttpClient, AccessDeniedException
from utils import save_image_from_url


class UploaderSelenium(BaseSelenium):
    active_list = []

    def __init__(self, entity, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entity = entity
        try:
            self.handle()
        except TerminatedByUser:
            self.quit_driver()
        except (
            CredentialInvalid, EntityInvalid, EmptyList, NotFound, MaxRetries,
            InvalidValidationMethod
        ):
            self.entity.report_fail()
            self.quit_driver()
        except EntityIsSuccess:
            self.quit_driver()
        except Exception as err:
            print(err)
            print(traceback.format_exc())
            self._start_debug()
            self.quit_driver()

    def handle(self):
        self.driver = self.get_driver(size=(1200, 700))
        self.do_login()
        self.wait_for_upload()
        self.do_pagination()
        self.verify_rows()
        self._start_debug()  # DEBUG

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

        while captcha_element and captcha_element.get_attribute('src'):
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
                        captcha_element = self.get_element(
                            By.ID,
                            'captchaimg',
                            timeout=5,
                            raise_exception=False
                        )
            except AccessDeniedException:
                raise CaptchaError(
                    data=(
                        'Access to DBC API denied, check '
                        'your credentials and/or balance'
                    ),
                    logger=self.logger
                )

        element = self.get_element(
            By.CSS_SELECTOR,
            'input[type="password"]',
            raise_exception=False
        )
        if element:
            raise CredentialInvalid("Wrong password.")

        success = self.click_element(
            By.CSS_SELECTOR,
            'div[data-challengetype="12"]',
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

    def go_to_manager(self):
        url = 'https://business.google.com/locations'
        if not self.driver.current_url.startswith(url):
            self.driver.get(url)

    def get_rows(self, raise_exception=True):
        self.go_to_manager()
        rows = self.get_elements(
            By.XPATH,
            '//table/tbody/tr',
            raise_exception=raise_exception
        )
        return rows or []

    def do_delete_all(self):
        rows = self.get_rows()

        if not rows:
            return

        self.click_element(
            By.XPATH,
            (
                '/html/body/div[4]/c-wiz/div[2]/div[1]/c-wiz/div/c-wiz[3]/'
                'div/content/c-wiz[2]/div[2]/table/thead/tr/th[1]/span/div'
            ),
            move=True
        )
        self.click_element(
            By.XPATH,
            (
                '/html/body/div[4]/c-wiz/div[2]/div[1]/c-wiz/div/c-wiz[3]/'
                'div/content/div/div[2]/div[2]/span/div'
            ),
            timeout=3
        )
        self.click_element(
            By.XPATH,
            (
                '/html/body/div[5]/div/div/content[8]'
            ),
            timeout=3
        )
        self.click_element(
            By.XPATH,
            (
                '/html/body/div[5]/div/div[2]/content/div/div[2]/'
                'div[3]/div[2]',
                '/html/body/div[4]/div[4]/div/div[2]/content/div/'
                'div[2]/div[3]/div[2]',
            ),
            timeout=3
        )
        self._wait(20)

    def wait_for_upload(self):
        rows = self.get_rows(raise_exception=False)
        action_list = ['r', 'c', 'q']

        if rows:
            self.logger(instance=self.entity, data=(
                "This credential has businesses inside.\n\n"
            ))

            action = None
            while not action:
                action = input(
                    "(r) To remove them.\n"
                    "(c) To continue.\n"
                    "(q) To use the next credential.\n"
                )
                if action not in action_list:
                    action = None
                    print('Invalid action. Try again.\n')

            if action == 'q':
                raise TerminatedByUser
            elif action == 'r':
                self.do_delete_all()
        else:
            action = None
            while action != "c":
                action = input(
                    (
                        'Please upload the data. Press "c" after '
                        'is displayed on your screen.'
                    )
                )

    def verify_rows(self):
        rows = self.get_rows()
        if not rows:
            return

        for row in rows:
            self.verify_row(row)

    def verify_row(self, row):
        columns = self.get_elements(
            By.XPATH,
            'td',
            source=row
        )
        column = columns[-1]

        if column.text != 'Verify now':
            return

        element = self.get_element(
            By.XPATH,
            'content/div/div',
            source=column,
            move=True
        )

        before_length = len(self.driver.window_handles)

        if platform.system() == 'Darwin':
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

        after_length = len(self.driver.window_handles)

        if before_length != after_length:
            self.active_list.append(
                (row, self.driver.window_handles[1])
            )

    def verify_tabs(self):
        index = 0
        for tab in self.driver.window_handles:
            index += 1

            if index == 1:
                continue

            self.verify_tab(tab)

    def verify_tab(self, tab):
        text = self.get_element(By.XPATH, '//body').text.strip()

        if 'Is this your business' in text:
            elements = self.get_elements(
                By.XPATH,
                (
                    '//*[@id="main_viewpane"]/c-wiz[1]/div/div[2]/div/div/'
                    'div[1]/div/content/label[2]'
                )
            )
            self.click_element(
                By.XPATH,
                'div[1]',
                source=elements[-1],
                timeout=5
            )
            self.click_element(
                By.XPATH,
                (
                    '//*[@id="main_viewpane"]/c-wiz[1]/div/div[2]/div/div/'
                    'div[2]/button'
                )
            )

            text = self.get_element(
                By.XPATH, '//body', timeout=5
            ).text.strip()

        if (
            'Enter the code' not in text and
            'Get your code at this number now by automated call' not in text
        ):
            raise EntityInvalid(
                "Cannot validate by phone.", logger=self.logger
            )

    def do_pagination(self):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="yDmH0d"]/c-wiz/div[2]/div[1]/c-wiz/div/c-wiz[3]/'
                'div/content/c-wiz[2]/div[4]/div/span[1]/div[2]/div[1]/'
                'div[1]/div[4]',
                '//*[@id="yDmH0d"]/c-wiz[2]/div[2]/div[1]/c-wiz/div/c-wiz[3]/'
                'div/content/c-wiz[2]/div[4]/div/span[1]/div[2]/div[1]/'
                'div[1]/div[1]',
                '//*[@id="yDmH0d"]/c-wiz[3]/div[2]/div[1]/c-wiz/div/c-wiz[3]/'
                'div/content/c-wiz[2]/div[4]/div/span[1]/div[2]/div[1]/'
                'div[1]/div[4]'

            ),
            move=True
        )
        self.click_element(
            By.XPATH,
            (
                '/html/body/div[4]/c-wiz/div[2]/div[1]/c-wiz/div/c-wiz[3]/'
                'div/content/c-wiz[2]/div[4]/div/span[1]/div[2]/div[2]/div[4]',
                '/html/body/div[4]/c-wiz[2]/div[2]/div[1]/c-wiz/div/c-wiz[3]/'
                'div/content/c-wiz[2]/div[4]/div/span[1]/div[2]/div[2]/div[4]',
                '/html/body/div[4]/c-wiz[3]/div[2]/div[1]/c-wiz/div/c-wiz[3]/'
                'div/content/c-wiz[2]/div[4]/div/span[1]/div[2]/div[2]/div[4]',
            ),
            timeout=3
        )
        self._wait(5)
