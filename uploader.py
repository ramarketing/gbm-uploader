import os
import requests
import sys
import time

from openpyxl import load_workbook
from selenium import webdriver
from selenium.common.exceptions import (
    ElementNotVisibleException, UnexpectedAlertPresentException
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


API_ROOT = 'https://matrix.cubo.pe/en/api/'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WAIT_TIME = 10


class Command:
    active_list = list()
    file_login_list = os.path.join(BASE_DIR, 'logins/1.xlsx')
    file_list = None
    help = 'Upload business to GBM'
    login_list = None
    text_phone_verification = 'Get your code at this number by automated call'

    def __init__(self, *args):
        username, password = args
        self.API_TOKEN = self.user_login(
            username=username,
            password=password
        )
        self.file_list = self.get_file_list()
        self.login_list = self.get_login_list()

        '''
        if (len(self.file_list) * 3) != len(self.login_list):
            raise Exception("Invalid number of files.")
        '''

    def get_file_list(self, folder=None):
        folder = folder or os.path.join(BASE_DIR, 'csv/')
        files = None

        for (dirpath, dirnames, filenames) in os.walk(folder):
            files = filenames
            break

        if not files:
            raise Exception("Files not found.")

        files = list()
        for filename in filenames:
            if not filename.endswith('.csv'):
                continue
            files.append(os.path.join(folder, filename))
        return files

    def get_login_list(self, file=None):
        file = file or self.file_login_list
        wb = load_workbook(file, read_only=True)
        ws = wb.worksheets[0]
        data = list()
        for row in ws.rows:
            email, password, recovery = [cel.value for cel in row[0:3]]
            if email is None or '@' not in email:
                continue
            data.append(dict(
                email=email,
                password=password,
                recovery=recovery
            ))
        return data

    def do_login(self, email, password, recovery):
        element = self.driver.find_element_by_id('identifierId')
        element.send_keys(email + Keys.RETURN)

        element = self.wait.until(
            EC.presence_of_element_located((By.NAME, 'password'))
        )
        element.send_keys(password + Keys.RETURN)

        # WARNING Check if needs to confirm their indentity
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
            element.send_keys(recovery + Keys.RETURN)

        self.wait.until(
            EC.url_contains('https://myaccount.google.com/')
        )

    def do_upload(self, file):
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
        except ElementNotVisibleException:
            pass

        element = self.wait.until(
            EC.presence_of_element_located(
                (By.NAME, 'spreadsheet')
            )
        )
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
        print('Start do_preparation')
        try:
            element = self.wait.until(
                EC.presence_of_element_located(
                    (By.ID, 'lm-tip-got-it-btn')
                )
            )
            element.click()
            print('Click "Got it"')
        except ElementNotVisibleException:
            print('"Got it" not found')

        # Change listing view
        print('Change to list view')
        element = self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//button[@aria-label="Sort locations"]')
            )
        )
        element.click()
        print('Change to list view ended')

        try:
            element = self.wait.until(
                EC.presence_of_element_located(
                    (By.ID, 'lm-list-view-promo-use-list-btn')
                )
            )
            element.click()
            print('Dismissing promo')
        except Exception:
            print('Promo not found.')

        print('End do_preparation')
        time.sleep(WAIT_TIME)

    def do_verification(self):
        print('Start do_verification')
        self.active_list = list()
        rows = self.driver.find_elements_by_css_selector(
            'div.lm-list-data-row'
        )

        for row in rows:
            self.do_verification_row(row)

        if len(self.active_list) == 0:
            return self.driver.quit()

        for item in self.active_list:
            print('Opening new tab')
            element = item['element'].find_element_by_css_selector(
                'div.lm-listing-data.lm-pointer'
            )
            element.click()
            print('Tab opened')

        for i in reversed(range(1, len(self.driver.window_handles))):
            self.driver.switch_to_window(self.driver.window_handles[i])

            if 'Success' not in self.driver.title:
                self.driver.close()
                continue

            text = self.driver.find_element_by_xpath('//body').text.strip()

            if self.text_phone_verification not in text:
                self.driver.close()
                continue

            self.active_list[i - 1]['is_success'] = True
            self.driver.close()
        print('End do_verification')

    def do_verification_row(self, row):
        print('Start do_verification_row')
        ActionChains(self.driver) \
            .move_to_element(row) \
            .perform()

        status = row.find_element_by_css_selector(
            'div.lm-statusColStatus'
        ).text.strip().upper()
        print('Status', status)
        if status == 'PUBLISHED':
            return

        element = row.find_element_by_css_selector(
            'div.lm-action-col'
        )
        action = element.text.strip().upper()
        print('Action', action)

        if action == 'GET VERIFIED':
            self.active_list.append(dict(
                row=row,
                element=element,
                is_success=False,
            ))
        else:
            print('Clicking checkbox')
            checkbox = row.find_element_by_xpath('//md-checkbox')
            checked = checkbox.get_attribute('aria-checked')
            if checked == 'false':
                checkbox.click()
                print('Checkbox clicked')
            print('Checkbox not clicked')
        print('End do_verification_row')

    def do_verify_validation_method(self, item, login):
        checkbox = item['row'].find_element_by_xpath(
            '//md-checkbox'
        )
        checked = checkbox.get_attribute('aria-checked')

        if item['is_success']:
            if checked == 'true':
                checkbox.click()

            name = item['row'].find_element_by_xpath(
                '//div[@flex-gt-sm="35"]/div[@class="lm-listing-data"]'
            ).find_element_by_css_selector(
                'div.lm-darkText'
            ).text.strip()
            phone = item['row'].find_element_by_xpath(
                '//div[@flex-gt-sm="25"]/div[@class="lm-listing-data"]'
            ).text.strip()
            self.report_success(name=name, phone=phone, **login)
        else:
            if checked == 'false':
                checkbox.click()

    def do_cleanup(self):
        element = self.wait.until(
            EC.element_to_be_clickable(
                (By.ID, 'lm-title-bars-see-options-btn')
            )
        )
        element.click()

        time.sleep(3)

        element = self.wait.until(
            EC.element_to_be_clickable(
                (By.ID, 'lm-title-bars-remove-btn')
            )
        )
        element.click()

        element = self.wait.until(
            EC.element_to_be_clickable((
                By.ID,
                'lm-confirm-dialog-list-selection-remove-selected-2-btn'
            ))
        )
        element.click()

        try:
            self.driver.get(
                'https://www.google.com/'
            )
        except UnexpectedAlertPresentException:
            alert = self.driver.switch_to_alert()
            alert.accept()

    def handle(self, *args, **options):
        file_index = 0

        for login in self.login_list:
            self.driver = webdriver.Chrome(
                os.path.join(BASE_DIR, 'chromedriver')
            )
            self.wait = WebDriverWait(self.driver, WAIT_TIME)
            self.driver.get('https://accounts.google.com/ServiceLogin')
            self.do_login(
                login['email'],
                login['password'],
                login['recovery']
            )

            for index in range(3):
                file = self.file_list[file_index]

                try:
                    self.do_upload(file)
                    self.do_preparation()
                    self.do_verification()

                    # Return and report
                    self.driver.switch_to_window(self.driver.window_handles[0])

                    for item in self.active_list:
                        self.do_verify_validation_method(item, login)

                    self.do_cleanup()
                except Exception as err:
                    print("An error has occurred %s" % err)
                finally:
                    print('Successfully uploaded file "%s"' % file)

                file_index += 1
            self.driver.quit()

    def user_login(self, **kwargs):
        url = API_ROOT + 'account/login/'
        try:
            r = requests.post(url, data=kwargs).json()
            return r['token']
        except Exception:
            raise Exception('Invalid credentials')

    def report_success(self, **kwargs):
        url = API_ROOT + 'mixer/business/success-from-google/'
        headers = {'Authorization': 'Token {}'.format(self.API_TOKEN)}
        try:
            r = requests.post(url, headers=headers, data=kwargs).json()
            return r['msg']
        except Exception as e:
            raise Exception(e)


def main(args):
    Command(*args).handle()


if __name__ == '__main__':
    main(sys.argv[1:])
