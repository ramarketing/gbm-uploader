import os
import pdb
import platform
import time

from selenium import webdriver
from selenium.common.exceptions import (
    TimeoutException, WebDriverException
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

from ..base.exceptions import (
    CaptchaError, CredentialInvalid, EntityInvalid
)
from ..captcha import HttpClient, AccessDeniedException
from .. import config
from ..logger import Logger
from ..utils import save_image_from_url


class BaseSelenium:
    def __init__(self, *args, **kwargs):
        self.logger = Logger()

    def get_driver(self, size=None):
        if hasattr(self, 'driver') and self.driver:
            return self.driver

        options = Options()
        options.add_argument('disable-infobars')
        options.add_argument('disable-extensions')
        options.add_argument('profile-directory=Default')
        options.add_argument('incognito')
        options.add_argument('disable-plugins-discovery')
        # options.add_argument('headless')
        # options.add_argument(f'user-agent={user_agent}')

        if platform.system() == 'Windows':
            driver = webdriver.Chrome(
                chrome_options=options,
                executable_path=os.path.join(config.BASE_DIR, 'chromedriver')
            )
        else:
            driver = webdriver.Chrome(
                chrome_options=options
            )

        if size:
            try:
                width, height = size
                driver.set_window_size(int(width), int(height))
            except (TypeError, ValueError):
                pass

        while len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[1])
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            self._wait(2)

        return driver

    def quit_driver(self):
        self.driver.switch_to.window(self.driver.window_handles[0])
        self.logger(data="Closing at {}.".format(self.driver.current_url))
        self.driver.quit()

    def perform_action(func):
        def wrapper(self, by, selector, *args, **kwargs):
            retry = 0
            success = False

            try:
                max_retries = int(kwargs.get('max_retries', 5))
            except ValueError:
                max_retries = 5

            try:
                timeout = int(kwargs.get('timeout', 0))
            except ValueError:
                timeout = 0

            return_method = func.__name__.startswith('get_')
            raise_exception = kwargs.get('raise_exception', True)

            if timeout:
                self._wait(timeout)

            while not success:
                retry += 1

                if retry > max_retries:
                    if raise_exception:
                        self._start_debug()
                        raise TimeoutException
                    else:
                        return success

                try:
                    if not isinstance(selector, (list, tuple)):
                        selector = [selector]

                    for s in selector:
                        try:
                            self.logger(data={
                                'action': func.__name__,
                                'selector': s,
                                'args': args,
                                'retry': retry,
                            })
                            response = func(self, by, s, *args, **kwargs)
                            success = True
                            break
                        except Exception:
                            pass
                    if not success:
                        raise TimeoutException
                except (TimeoutException, WebDriverException):
                    self._wait(1)

            return response if return_method else success

        return wrapper

    @perform_action
    def click_element(
        self, by, selector, source=None, move=False, *args, **kwargs
    ):
        final_source = source or self.driver
        element = final_source.find_element(by, selector)

        if move:
            ActionChains(self.driver) \
                .move_to_element(source or element) \
                .perform()

        disabled = element.get_attribute('aria-disabled')
        if disabled == 'true':
            self._wait(5)
            raise WebDriverException
        element.click()

    @perform_action
    def clear_input(self, by, selector, source=None, *args, **kwargs):
        source = source or self.driver
        element = source.find_element(by, selector)
        element.clear()

    def do_login(self, credential=None):
        credential = credential or self.entity

        self.driver.get('https://accounts.google.com/ServiceLogin')
        self.fill_input(
            By.ID,
            ('identifierId', 'Email'),
            credential.username + Keys.RETURN
        )
        self.fill_input(
            By.NAME,
            ('password', 'Passwd'),
            credential.password + Keys.RETURN,
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
                            credential.password
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
            credential.report_fail()
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
            credential.report_fail()
            raise EntityInvalid(
                msg="Phone number is required", logger=self.logger
            )

        self._wait(3)
        success = self.driver.current_url.startswith(
            'https://myaccount.google'
        )
        if not success:
            credential.report_fail()
            raise CredentialInvalid(
                msg="Login failed", logger=self.logger
            )

    @perform_action
    def fill_input(self, by, selector, content, source=None, *args, **kwargs):
        source = source or self.driver
        element = source.find_element(by, selector)
        element.send_keys(content)

    @perform_action
    def get_text(self, by, selector, source=None, *args, **kwargs):
        source = source or self.driver
        element = source.find_element(by, selector)
        return element.text

    @perform_action
    def get_element(
        self, by, selector, source=None, move=False, *args, **kwargs
    ):
        source = source or self.driver
        element = source.find_element(by, selector)

        if move:
            ActionChains(self.driver) \
                .move_to_element(source or element) \
                .perform()

        return element

    @perform_action
    def get_elements(self, by, selector, source=None, *args, **kwargs):
        source = source or self.driver
        elements = source.find_elements(by, selector)
        if len(elements) == 0:
            raise WebDriverException
        return elements

    def handle(self):
        raise NotImplementedError("`handle` nor implemented in the Base.")

    def _wait(self, seconds):
        for second in range(seconds):
            print('Wait: {:d}/{:d}'.format(second + 1, seconds))
            time.sleep(1)

    def _start_debug(self, *args, **kwargs):
        if 'message' in kwargs:
            print(kwargs['message'])
        if config.PDB_DEBUG:
            pdb.set_trace()
