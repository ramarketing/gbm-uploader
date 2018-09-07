import os
import platform
import time

from selenium import webdriver
from selenium.common.exceptions import ElementNotVisibleException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from services import BusinessService, CredentialService
from config import BASE_DIR, PER_CREDENTIAL, WAIT_TIME
from constants import TEXT_PHONE_VERIFICATION


class Uploader:
    service_cred = CredentialService()
    service_biz = BusinessService()

    def __init__(self, *args):
        pass

    def do_login(self, credential):
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
        except Exception:
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
            element.send_keys(credential.recovery + Keys.RETURN)

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
            'https://business.google.com/manage/?noredirect=1#/upload'
        )

        try:
            element = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//md-checkbox[@type="checkbox"]')
                )
            )
            element.click()
            element = self.driver.find_element_by_xpath(
                '//md-dialog-actions/button'
            )
            element.click()
        except Exception:
            pass

        try:
            element = self.wait.until(
                EC.presence_of_element_located(
                    (By.NAME, 'spreadsheet')
                )
            )
        except Exception:

            element = self.driver.find_element_by_name('spreadsheet')
        element.send_keys(file)

        try:
            element = self.wait.until(
                EC.visibility_of_element_located(
                    (By.ID, 'lm-conf-changes-btn-submit')
                )
            )
            element.click()
        except ElementNotVisibleException:
            try:
                element = self.wait.until(
                    EC.visibility_of_element_located(
                        (By.ID, 'lm-conf-changes-btn-got-it')
                    )
                )
                element.click()
                raise Exception('File uploaded already.')
            except ElementNotVisibleException:
                pass

            raise Exception('Submit button not found.')

    def do_preparation(self):

        try:
            element = self.wait.until(
                EC.visibility_of_element_located(
                    (By.ID, 'lm-tip-got-it-btn')
                )
            )
            self.driver.execute_script("arguments[0].click();", element)

        except Exception as e:
            pass

        try:
            element = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//button[@aria-label="List view"]')
                )
            )
            self.driver.execute_script("arguments[0].click();", element)
        except Exception as e:
            pass

        try:
            element = self.wait.until(
                EC.presence_of_element_located(
                    (By.ID, 'lm-list-view-promo-use-list-btn')
                )
            )
            element.click()
        except Exception:
            pass

        time.sleep(WAIT_TIME)

    def do_verification(self):
        self.active_list = []
        rows = self.driver.find_elements_by_css_selector(
            'div.lm-list-data-row'
        )

        ActionChains(self.driver) \
            .move_to_element(rows[-1]) \
            .perform()

        for row in rows:
            self.do_verification_row(row)

        if len(self.active_list) == 0:
            return self.driver.quit()

        for item in self.active_list:

            element = item['element'].find_element_by_css_selector(
                'div.lm-listing-data.lm-pointer'
            )
            self.driver.execute_script("arguments[0].click();", element)

        for i in reversed(range(1, len(self.driver.window_handles))):
            self.driver.switch_to_window(self.driver.window_handles[i])

            if 'Success' not in self.driver.title:
                self.driver.close()
                continue

            text = self.driver.find_element_by_xpath('//body').text.strip()

            if TEXT_PHONE_VERIFICATION not in text:
                self.driver.close()
                continue

            self.active_list[i - 1]['is_success'] = True
            self.driver.close()

    def do_verification_row(self, row):
        ActionChains(self.driver) \
            .move_to_element(row) \
            .perform()

        status = row.find_element_by_css_selector(
            'div.lm-statusColStatus'
        ).text.strip().upper()
        if status == 'PUBLISHED':
            return

        element = row.find_element_by_css_selector(
            'div.lm-action-col'
        )
        action = element.text.strip().upper()

        if action == 'GET VERIFIED':
            self.active_list.append(dict(
                row=row,
                element=element,
                is_success=False,
            ))

    def do_verify_validation_method(self, item, credential):
        name = item['row'].find_element_by_xpath(
            '//div[@flex-gt-sm="35"]/div[@class="lm-listing-data"]'
        ).find_element_by_css_selector(
            'div.lm-darkText'
        ).text.strip()

        biz = self.biz_list.get_by_name(name)

        if item['is_success']:
            biz.report_success(credential=credential)
        else:
            biz.report_fail()

    def do_cleanup(self):
        element = self.wait.until(
            EC.element_to_be_clickable(
                (By.ID, 'lm-title-bars-see-options-btn')
            )
        )
        self.driver.execute_script("arguments[0].click();", element)

        time.sleep(3)

        element = self.wait.until(
            EC.element_to_be_clickable(
                (By.ID, 'lm-title-bars-remove-btn')
            )
        )
        self.driver.execute_script("arguments[0].click();", element)

        element = self.wait.until(
            EC.element_to_be_clickable((
                By.ID,
                'lm-confirm-dialog-list-selection-remove-selected-2-btn'
            ))
        )
        self.driver.execute_script("arguments[0].click();", element)

    def handle(self, *args, **options):
        file_index = 0

        credential_list = self.service_cred.get_list()

        for credential in credential_list:
            if platform.system() == 'Windows':
                self.driver = webdriver.Chrome(
                    os.path.join(BASE_DIR, 'chromedriver')
                )
            else:
                self.driver = webdriver.Chrome()

            self.wait = WebDriverWait(self.driver, WAIT_TIME)
            self.driver.get('https://accounts.google.com/ServiceLogin')

            try:
                self.do_login(credential_list)
            except Exception:
                credential.report_fail()
                self.driver.quit()
                continue

            self.biz_list = self.service_biz.get_list()

            for index in range(PER_CREDENTIAL):
                if index > 0:
                    self.biz_list.get_next_page()

                file = self.biz_list.create_csv()

                try:
                    self.do_upload(file)
                    self.do_preparation()
                    self.do_verification()

                    self.driver.switch_to_window(self.driver.window_handles[0])

                    for item in self.active_list:
                        self.do_verify_validation_method(item, credential)

                    self.do_cleanup()
                except Exception as err:
                    print('Error', err)

                file_index += 1
            self.driver.quit()
