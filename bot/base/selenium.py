import os
import pdb
import platform
import time

from selenium import webdriver
from selenium.common.exceptions import (
    TimeoutException, WebDriverException
)
from selenium.webdriver.common.action_chains import ActionChains

import config
from logger import Logger


class BaseSelenium:
    def __init__(self, *args, **kwargs):
        self.logger = Logger()

    def get_driver(self):
        if hasattr(self, 'driver') and self.driver:
            return self.driver
        elif platform.system() == 'Windows':
            driver = webdriver.Chrome(
                executable_path=os.path.join(config.BASE_DIR, 'chromedriver')
            )
        else:
            driver = webdriver.Chrome()

        while len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[1])
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            self._wait(2)

        return driver

    def quit_driver(self):
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
                    if isinstance(selector, (list, tuple)):
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
                    else:
                        self.logger(data={
                            'action': func.__name__,
                            'selector': selector,
                            'args': args,
                            'retry': retry,
                        })
                        response = func(self, by, selector, *args, **kwargs)
                        success = True
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
    def get_element(self, by, selector, source=None, *args, **kwargs):
        source = source or self.driver
        element = source.find_element(by, selector)
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
        if config.PDB_DEBUG:
            pdb.set_trace()
