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

from exceptions import CredentialInvalid
from services import BusinessService, CredentialService
from config import BASE_DIR, PER_CREDENTIAL, WAIT_TIME
from constants import TEXT_PHONE_VERIFICATION
from logger import UploaderLogger


logger = UploaderLogger()


class Uploader:
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
            self.driver.execute_script("arguments[0].click();", element)
        except Exception:
            pass

    def do_verification(self, credential):
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
            return

        tab_index = len(self.active_list)

        for item in self.active_list:
            element = item['element'].find_element_by_css_selector(
                'div.lm-listing-data.lm-pointer'
            )
            self.driver.execute_script("arguments[0].click();", element)
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

            if TEXT_PHONE_VERIFICATION in text:
                logger(instance=biz, data='Success')
                biz.report_success(credential)
                has_success = True
            else:
                biz.report_fail()

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

        index, name, address, phone, status, action = row.text.split('\n')

        if status.upper() == 'PUBLISHED':
            return

        element = row.find_element_by_css_selector(
            'div.lm-action-col'
        )
        biz = self.biz_list.get_by_name(name)

        if action == 'Get verified' and not self.in_active_list(biz):
            logger(instance=biz, data={'action': action, 'status': status})
            self.active_list.append(dict(
                biz=biz,
                element=element,
                row=row,
                phone=phone,
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

    def handle(self, *args, **options):
        file_index = 0
        credential_list = self.service_cred.get_list()

        for credential in credential_list:
            '''
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_extension(
                os.path.join(BASE_DIR, 'expressvpn.crx')
            )
            '''

            if platform.system() == 'Windows':
                self.driver = webdriver.Chrome(
                    executable_path=os.path.join(BASE_DIR, 'chromedriver'),
                    # chrome_options=chrome_options
                )
            else:
                self.driver = webdriver.Chrome(
                    # chrome_options=chrome_options
                )

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

                if "t find your Google Account" in text:
                    logger(instance=credential, data="Account doesn't exists.")
                    logger(instance=credential, data='Reported fail')
                    credential.report_fail()
                elif "Account disabled" in text:
                    logger(instance=credential, data="Account disabled.")
                    logger(instance=credential, data='Reported fail')
                    credential.report_fail()
                else:
                    logger(instance=credential, data='Pass')
                self.driver.quit()
                continue

            self.biz_list = self.biz_list or self.service_biz.get_list()

            for index in range(PER_CREDENTIAL):
                if file_index > 0:
                    self.biz_list.get_next_page()

                file = self.biz_list.create_csv()
                logger(instance=self.biz_list, data={'file': file})

                try:
                    self.do_upload(file)
                    self.do_preparation()
                    has_success = self.do_verification(credential)
                    self.driver.switch_to_window(self.driver.window_handles[0])

                    if has_success:
                        break
                except Exception as err:
                    logger(instance=err, data=err)

                file_index += 1

            credential.report_success()
            self.driver.quit()
