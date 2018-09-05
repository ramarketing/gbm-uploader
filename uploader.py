import os
import platform
import requests
import sys
import time

from dotenv import load_dotenv
from openpyxl import load_workbook
from selenium import webdriver
from selenium.common.exceptions import ElementNotVisibleException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


load_dotenv()

API_ROOT = os.getenv('API_ROOT')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WAIT_TIME = int(os.getenv('WAIT_TIME'))


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

        time.sleep(1)

        element = self.wait.until(
            EC.presence_of_element_located((By.NAME, 'password'))
        )
        element.send_keys(password + Keys.RETURN)

        time.sleep(1)

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
            'https://www.google.com/'
        )

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
        self.active_list = list()
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

            if self.text_phone_verification not in text:
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

        '''
        else:
            checkbox = row.find_element_by_xpath('//md-checkbox')
            checked = checkbox.get_attribute('aria-checked')
            if checked == 'false':
                self.driver.execute_script("arguments[0].click();", checkbox)
        '''

    def do_verify_validation_method(self, item, login):
        '''
        checkbox = item['row'].find_element_by_xpath(
            '//md-checkbox'
        )
        checked = checkbox.get_attribute('aria-checked')
        '''

        if item['is_success']:
            '''
            if checked == 'true':
                self.driver.execute_script("arguments[0].click();", checkbox)
            '''

            dataset = item['row'].find_element_by_xpath(
                '//div[@flex-gt-sm="35"]/div[@class="lm-listing-data"]'
            )
            name = dataset.find_element_by_css_selector(
                'div.lm-darkText'
            ).text.strip()
            address = dataset.find_element_by_css_selector(
                'div.lm-listing-data-less-dark'
            ).text.strip()
            phone = item['row'].find_element_by_xpath(
                '//div[@flex-gt-sm="25"]/div[@class="lm-listing-data"]'
            ).text.strip()
            self.report_success(
                name=name, address=address, phone=phone, **login
            )

        '''
        else:
            if checked == 'false':
                self.driver.execute_script("arguments[0].click();", checkbox)
        '''

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

        for login in self.login_list:
            if platform.system() == 'Windows':
                self.driver = webdriver.Chrome(
                    os.path.join(BASE_DIR, 'chromedriver')
                )
            else:
                self.driver = webdriver.Chrome()

            self.wait = WebDriverWait(self.driver, WAIT_TIME)
            self.driver.get('https://accounts.google.com/ServiceLogin')

            try:
                self.do_login(
                    login['email'],
                    login['password'],
                    login['recovery']
                )
            except Exception:
                print('Invalid credentails')
                continue

            for index in range(3):
                file = self.file_list[file_index]
                errors = False

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
                    errors = err
                finally:
                    if errors:
                        message = 'Error %(file)s: %(errors)s'
                    else:
                        message = 'Success %(file)s'

                    print(message % dict(file=file, errors=errors))

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
