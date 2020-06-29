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
    CredentialInvalid
)
from .. import config
from ..logger import Logger


class BaseSelenium:
    WAIT_BEFORE_NEXT = 3

    def __init__(self, *args, **kwargs):
        self.logger = Logger()

    def get_driver(self, size=None):
        if hasattr(self, 'driver') and self.driver:
            return self.driver

        if platform.system() == 'Windows':
            options = Options()
            options.add_argument('disable-infobars')
            options.add_argument('disable-extensions')
            options.add_argument('profile-directory=Default')
            options.add_argument('incognito')
            options.add_argument('disable-plugins-discovery')
            options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Safari/605.1.15')

            driver = webdriver.Chrome(
                chrome_options=options,
                executable_path=os.path.join(os.path.normpath(os.getcwd()), 'chromedriver.exe')
            )

        else:
            options = Options()
            # options.add_argument('--headless')
            options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Safari/605.1.15')

            driver = webdriver.Chrome(chrome_options=options)

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
        try:
            self.driver.switch_to.window(self.driver.window_handles[0])
            self.logger(data="Closing at {}.".format(self.driver.current_url))
            self.driver.quit()
        except AttributeError:
            pass

    def perform_action(func):
        def wrapper(self, by, selector, *args, **kwargs):
            retry = 0
            success = False

            try:
                max_retries = int(
                    kwargs.get('max_retries', config.MAX_RETRIES)
                )
            except ValueError:
                max_retries = config.MAX_RETRIES

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

    def do_login(self, credential, url=None):
        url = url or 'https://business.google.com/locations'
        final_url = url.split('.com')[0]

        self.driver.get(url)
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
            url.split('.com')[0]
        )
        if success:
            return

        element = self.get_element(
            By.CSS_SELECTOR,
            'input[type="password"]',
            max_retries=2,
            raise_exception=False
        )
        if element:
            credential.report_fail()
            raise CredentialInvalid("Wrong password.")

        by_recovery_email = self.click_element(
            By.CSS_SELECTOR,
            'div[data-challengetype="12"]',
            raise_exception=False,
            max_retries=2,
            timeout=3
        )
        if by_recovery_email:
            self.fill_input(
                By.NAME,
                'knowledgePreregisteredEmailResponse',
                credential.recovery_email + Keys.RETURN,
                timeout=3
            )

        by_recovery_phone = self.click_element(
            By.CSS_SELECTOR,
            'div[data-challengetype="13"]',
            raise_exception=False,
            max_retries=2,
            timeout=3
        )
        if by_recovery_phone:
            self.fill_input(
                By.ID,
                'phoneNumberId',
                credential.recovery_phone + Keys.RETURN,
                timeout=3
            )

        self._wait(3)
        success = self.driver.current_url.startswith(
            final_url
        )
        if not success:
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
            if config.DEBUG:
                print('Wait: {:d}/{:d}'.format(second + 1, seconds))
            time.sleep(1)

    def _start_debug(self, *args, **kwargs):
        if 'message' in kwargs:
            print(kwargs['message'])
        if config.PDB_DEBUG:
            pdb.set_trace()
