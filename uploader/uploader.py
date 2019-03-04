import os
import platform
import time
import traceback

from selenium import webdriver
from selenium.common.exceptions import (
    ElementNotVisibleException, TimeoutException, WebDriverException
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from exceptions import CredentialInvalid
from services import BusinessService, CredentialService
from config import BASE_DIR, PER_CREDENTIAL, WAIT_TIME
from constants import TEXT_PHONE_VERIFICATION
from logger import UploaderLogger


logger = UploaderLogger()
success_logger = UploaderLogger('success')


class BaseManager:
    def perform_action(func):
        def wrapper(*args, **kwargs):
            retry = 0
            success = False

            try:
                max_retries = int(kwargs.get('max_retries', 10))
            except ValueError:
                max_retries = 10

            try:
                timeout = int(kwargs.get('timeout', 0))
            except ValueError:
                timeout = 0

            if timeout:
                time.sleep(timeout)

            while not success:
                retry += 1
                logger(data={
                    'action': func,
                    'args': args,
                    'retry': retry,
                })

                if retry == max_retries:
                    raise TimeoutException

                try:
                    func(*args, **kwargs)
                    success = True
                except (TimeoutException, WebDriverException):
                    time.sleep(1)

            return success

        return wrapper

    @perform_action
    def fill_input(self, by, selector, content, timeout=0, max_retries=10):
        element = self.driver.find_element(by, selector)
        element.send_keys(content)

    @perform_action
    def click_element(self, by, selectors, timeout=0, max_retries=10):
        def execute(selector):
            element = self.wait.until(
                EC.element_to_be_clickable(
                    (by, selector)
                )
            )
            element.click()

        if isinstance(selectors, (list, tuple)):
            for selector in selectors:
                try:
                    return execute(selector)
                except Exception:
                    pass
        else:
            return execute(selectors)


class Uploader(BaseManager):
    service_cred = CredentialService()
    service_biz = BusinessService()
    biz_list = None

    def __init__(self, *args):
        pass

    def do_login(self, credential):
        logger(instance=credential)

        element = self.driver.find_element_by_id('identifierId')
        element.send_keys(credential.email + Keys.RETURN)
        time.sleep(1)

        element = self.wait.until(
            EC.presence_of_element_located((By.NAME, 'password'))
        )
        element.send_keys(credential.password + Keys.RETURN)
        time.sleep(1)

        try:
            self.wait.until(
                EC.url_contains('https://myaccount.google.com/')
            )
            return
        except Exception:
            pass

        try:
            element = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[@data-challengetype="12"]')
                )
            )
            element.click()
            element = self.wait.until(
                EC.presence_of_element_located(
                    (By.NAME, 'knowledgePreregisteredEmailResponse')
                )
            )
            element.send_keys(credential.recovery_email + Keys.RETURN)
        except Exception:
            pass

        try:
            phone = self.wait.until(
                EC.presence_of_element_located(
                    (By.ID, 'deviceAddress')
                )
            )
        except Exception as e:
            phone = None

        if phone:
            raise CredentialInvalid("Requires cellphone.")

        self.wait.until(
            EC.url_contains('https://myaccount.google.com/')
        )

    def do_upload(self, file):
        self.driver.get('https://www.google.com/')

        try:
            alert = self.driver.switch_to_alert()
            alert.accept()
        except Exception:
            pass

        self.driver.get(
            'https://business.google.com/locations'
            #'https://business.google.com/manage/?noredirect=1#/upload'
        )

        self.click_element(
            By.XPATH,
            '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/c-wiz[3]/div/content/div/div/div/div/div/content/span/span[2]'
        )

        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div/content[2]/div[2]',
                '//*[@id="js"]/div[11]/div/div/content[2]/div[2]'
            ),
            timeout=3
        )

        self.fill_input(By.NAME, 'Filedata', file, timeout=5)

        self.click_element(
            By.XPATH,
            '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/div[1]/c-wiz/div/div[2]/div[2]',
            timeout=20
        )
        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[2]/div[3]/div[2]/div[2]',
            timeout=5
        )
        self.click_element(
            By.XPATH,
            '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/div[1]/c-wiz/div/div[2]/div',
            timeout=20
        )
        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[2]/div[3]/div[2]/div',
            timeout=5
        )

        self.driver.get('https://business.google.com/locations')

    def do_verification(self, credential):
        self.active_list = []
        rows = self.driver.find_elements_by_xpath('//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/c-wiz[3]/div/content/c-wiz[2]/div[2]/table/tbody/tr')

        ActionChains(self.driver) \
            .move_to_element(rows[-1]) \
            .perform()

        for row in rows:
            self.do_verification_row(row)

        if len(self.active_list) == 0:
            return

        tab_index = len(self.active_list)

        for item in self.active_list:
            element = item['element'].find_element_by_xpath('content/div/div')
            if platform.system() == 'Windows':
                ActionChains(self.driver).key_down(Keys.CONTROL).click(element).key_up(Keys.CONTROL).perform()
            else:
                ActionChains(self.driver).key_down(Keys.COMMAND).click(element).key_up(Keys.COMMAND).perform()
            item['tab_index'] = tab_index
            tab_index -= 1

        has_success = False

        for i in range(1, len(self.driver.window_handles)):
            self.driver.switch_to_window(self.driver.window_handles[i])

            item = self.get_item_by_tab_index(i)
            biz = item['biz']
            title = self.driver.title

            logger(instance=biz, data='Title: "{}"'.format(title))

            if (
                'Choose a way to verify' not in title and
                'Success' not in title and
                'Is this your business' not in title
            ):
                biz.report_fail()
                continue

            text = self.driver.find_element_by_xpath('//body').text.strip()

            try:
                if TEXT_PHONE_VERIFICATION in text:
                    logger(instance=biz, data='Success')
                    success_line = [
                        credential.email,
                        credential.password,
                        credential.recovery_email,
                        biz.phone_friendly,
                        biz.address,
                        biz.city,
                        biz.state,
                        biz.zip_code,
                    ]
                    success_logger(instance=biz, data=','.join(success_line))

                    biz.report_success(credential)
                    has_success = True
                else:
                    biz.report_fail()
            except Exception:
                logger(
                    instance=biz,
                    data='Couldn\'t report "{}" back to server.'.format(
                        'success' if has_success else 'fail'
                    )
                )

        for i in reversed(range(1, len(self.driver.window_handles))):
            self.driver.switch_to_window(self.driver.window_handles[i])
            self.driver.close()

        return has_success

    def do_verification_row(self, row):
        ActionChains(self.driver) \
            .move_to_element(row) \
            .perform()

        try:
            got_it = self.driver.find_element_by_id('lm-tip-got-it-btn')
            self.driver.execute_script("arguments[0].click();", got_it)
        except Exception:
            pass

        columns = row.find_elements(By.XPATH, 'td')
        empty, index, name_address, status, action = [c.text for c in columns]
        name, address = name_address.split('\n')

        if status.upper() == 'PUBLISHED':
            return

        element = columns[-1]
        biz = self.biz_list.get_by_name(name)

        if action == 'Verify now' and not self.in_active_list(biz):
            logger(instance=biz, data={'action': action, 'status': status})
            self.active_list.append(dict(
                biz=biz,
                element=element,
                row=row,
            ))
        else:
            biz.report_fail()
            logger(instance=biz, data='OUT')

    def get_item_by_tab_index(self, tab_index):
        for item in self.active_list:
            if item['tab_index'] == tab_index:
                return item

    def in_active_list(self, biz):
        for item in self.active_list:
            if biz == item['biz']:
                return True
        return False

    def can_continue(self, max_success, **kwargs):
        new_kwargs = kwargs.copy()
        if 'can_use' in new_kwargs:
            new_kwargs.pop('can_use')
        new_kwargs['is_success'] = True
        success_count = self.service_biz.get_list(**new_kwargs)
        return success_count.total_count < max_success

    def clean_kwargs(self, **kwargs):
        if 'limit' not in kwargs:
            kwargs['limit'] = 9
        if 'can_use' not in kwargs:
            kwargs['can_use'] = 1
        return kwargs

    def delete_all(self):
        self.driver.get('https://business.google.com/locations')
        rows = self.driver.find_elements_by_xpath('//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/c-wiz[3]/div/content/c-wiz[2]/div[2]/table/tbody/tr')

        if not rows:
            return

        selected = 0

        for row in rows:
            columns = row.find_elements(By.XPATH, 'td')
            empty, index, name_address, status, action = [c.text for c in columns]
            name, address = name_address.split('\n')

            biz = self.biz_list.get_by_name(name)

            if biz.date_success:
                continue

            column = columns[0]

            element = column.find_element_by_xpath('content/div')
            element.click()
            selected += 1

        if not selected:
            return

        self.click_element(
            By.XPATH,
            '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/c-wiz[3]/div/content/div/div[2]/div[2]/span'
        )
        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[10]/div/div/content[8]',
            timeout=3
        )
        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[2]/div[3]/div[2]',
            timeout=5
        )
        time.sleep(30)

    def handle(self, *args, **kwargs):
        kwargs = self.clean_kwargs(**kwargs)

        if 'max' in kwargs:
            try:
                max_success = int(kwargs.pop('max'))
            except ValueError:
                max_success = 0
        else:
            max_success = 0

        if max_success and not self.can_continue(max_success, **kwargs):
            logger(data="Completed.")
            return

        file_index = 0
        credential_list = self.service_cred.get_list(**kwargs)

        for credential in credential_list:
            if platform.system() == 'Windows':
                self.driver = webdriver.Chrome(
                    executable_path=os.path.join(BASE_DIR, 'chromedriver'),
                )
            else:
                self.driver = webdriver.Chrome()

            self.wait = WebDriverWait(self.driver, WAIT_TIME)
            self.driver.get('https://accounts.google.com/ServiceLogin')

            try:
                self.do_login(credential)
            except CredentialInvalid:
                logger(instance=credential, data='Reported fail')
                credential.report_fail()
                self.driver.quit()
                continue
            except Exception as e:
                text = self.driver.find_element_by_xpath('//body').text.strip()

                if (
                    "t find your Google Account" in text or
                    "Account disabled" in text
                ):
                    logger(instance=credential, data="Account doesn't exists.")
                    logger(instance=credential, data='Reported fail')
                    credential.report_fail()
                    continue
                else:
                    self.driver.get(
                        'https://business.google.com/manage/?noredirect=1#/upload'
                    )
                    if not self.driver.current_url.startswith(
                        'https://business.google.com/'
                    ):
                        logger(instance=credential, data='Pass')
                        self.driver.quit()
                        continue

            self.biz_list = self.biz_list or self.service_biz.get_list(**kwargs)

            if max_success and not self.can_continue(max_success, **kwargs):
                logger(data="Completed.")
                return

            for index in range(PER_CREDENTIAL):
                if file_index > 0:
                    self.biz_list.get_next_page()

                file = self.biz_list.create_csv()
                logger(instance=self.biz_list, data={'file': file})

                try:
                    self.do_upload(file)
                    has_success = self.do_verification(credential)
                    self.driver.switch_to_window(self.driver.window_handles[0])

                    if has_success:
                        self.delete_all()
                        break
                    else:
                        self.delete_all()
                except Exception as err:
                    logger(instance=err, data=err)
                    print(traceback.format_exc())
                    self.delete_all()

                file_index += 1

            credential.report_success()
            self.driver.quit()
