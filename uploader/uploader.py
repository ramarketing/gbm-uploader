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

from exceptions import CredentialInvalid, EmptyUpload
from services import BusinessService, CredentialService
from config import BASE_DIR, DEBUG, PDB_DEBUG, PER_CREDENTIAL, WAIT_TIME
from constants import TEXT_PHONE_VERIFICATION
from logger import UploaderLogger


logger = UploaderLogger()
success_logger = UploaderLogger('success')


class BaseManager:
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

            raise_exception = kwargs.get('raise_exception', True)

            if timeout:
                time.sleep(timeout)

            while not success:
                retry += 1

                if retry > max_retries:
                    if raise_exception:
                        if PDB_DEBUG:
                            import pdb; pdb.set_trace()
                        raise TimeoutException
                    else:
                        return success

                try:
                    if isinstance(selector, (list, tuple)):
                        for s in selector:
                            try:
                                logger(data={
                                    'action': func.__name__,
                                    'selector': s,
                                    'args': args,
                                    'retry': retry,
                                })
                                func(self, by, s, *args, **kwargs)
                                success = True
                                break
                            except Exception as e:
                                pass
                        if not success:
                            raise TimeoutException
                    else:
                        logger(data={
                            'action': func.__name__,
                            'selector': selector,
                            'args': args,
                            'retry': retry,
                        })
                        func(self, by, selector, *args, **kwargs)
                        success=True
                except (TimeoutException, WebDriverException):
                    time.sleep(1)

            return success

        return wrapper

    @perform_action
    def fill_input(self, by, selector, content, source=None, *args, **kwargs):
        source = source or self.driver
        element = source.find_element(by, selector)
        element.send_keys(content)

    @perform_action
    def click_element(self, by, selector, source=None, *args, **kwargs):
        source = source or self.driver
        element = source.find_element(by, selector)
        disabled = element.get_attribute('aria-disabled')
        if disabled == 'true':
            time.sleep(5)
            raise WebDriverException
        element.click()


class Uploader(BaseManager):
    service_cred = CredentialService()
    service_biz = BusinessService()
    biz_list = None

    def __init__(self, *args):
        pass

    def do_login(self, credential):
        logger(instance=credential)

        self.fill_input(
            By.ID,
            'identifierId',
            credential.email + Keys.RETURN
        )
        self.fill_input(
            By.NAME,
            'password',
            credential.password + Keys.RETURN,
            timeout=3
        )
        time.sleep(1)

        try:
            self.wait.until(
                EC.url_contains('https://myaccount.google.com/')
            )
            return
        except Exception:
            pass

        try:
            self.click_element(
                By.XPATH,
                '//div[@data-challengetype="12"]'
            )
            self.fill_input(
                By.NAME,
                'knowledgePreregisteredEmailResponse',
                credential.recovery_email + Keys.RETURN,
                timeout=5
            )
        except TimeoutException:
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
        self.driver.get('https://business.google.com/locations')

        try:
            alert = self.driver.switch_to_alert()
            alert.accept()
        except Exception:
            pass

        def load_csv():
            body = self.driver.find_element(By.CSS_SELECTOR, 'body')
            if "You haven't added any locations" not in body.text:
                self.delete_all(force=True, clean_listing=False)
                self.driver.get(
                    'https://business.google.com/locations'
                )

            self.click_element(By.XPATH, '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/c-wiz[3]/div/content/div/div/div/div')

            self.click_element(
                By.XPATH,
                (
                    '//*[@id="js"]/div[9]/div/div/content[2]/div[2]',
                    '//*[@id="js"]/div[10]/div/div/content[2]/div[2]',
                    '//*[@id="js"]/div[11]/div/div/content[2]/div[2]'
                ),
                timeout=3
            )
            self.fill_input(
                By.NAME,
                'Filedata',
                file,
                timeout=5
            )

        try:
            load_csv()
        except TimeoutException:
            self.click_element(
                By.XPATH,
                '//*[@id="js"]/div[9]/div/div[2]/div[3]/div',
                raise_exception=False
            )
            self.click_element(
                By.XPATH,
                '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/div[1]/c-wiz/div[2]/div[2]/div[1]',
                raise_exception=False
            )
            self.click_element(
                By.XPATH,
                '//*[@id="js"]/div[9]/div/div[2]/content/div/div[2]/div[3]/div[2]/div',
                raise_exception=False
            )
            load_csv()

        self.click_element(
            By.XPATH,
            '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/div[1]/c-wiz/div/div[2]/div[2]',
            timeout=20
        )
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[9]/div/div[2]/content/div/div[2]/div[3]/div[2]/div[2]',
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[2]/div[3]/div[2]/div[2]',
                '//*[@id="js"]/div[9]/div/div[2]/content/div/div[2]/div[3]/div[2]/div',
            ),
            timeout=5
        )
        self.click_element(
            By.XPATH,
            '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/div[1]/c-wiz/div/div[2]/div',
            timeout=20,
            raise_exception=False,
        )
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[9]/div/div[2]/content/div/div[2]/div[3]/div[2]/div',
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[2]/div[3]/div[2]/div',
                '//*[@id="js"]/div[9]/div/div[2]/content/div/div[2]/div[3]/div[2]/div[2]'
            ),
            timeout=5,
            raise_exception=False,
        )

        time.sleep(5)
        self.driver.refresh()
        time.sleep(5)

        body = self.driver.find_element(By.CSS_SELECTOR, 'body')
        if "You haven't added any locations" in body.text:
            raise EmptyUpload


    def do_verification(self, credential):
        self.active_list = []
        rows = self.driver.find_elements_by_xpath('//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/c-wiz[3]/div/content/c-wiz[2]/div[2]/table/tbody/tr')

        if not rows:
            return

        selected = 0

        for row in rows:
            self.do_verification_row(row)

        if len(self.active_list) == 0:
            return

        tab_index = len(self.active_list)

        for item in self.active_list:
            item['tab_index'] = tab_index
            tab_index -= 1
            element = item['element']

            if platform.system() == 'Darwin':
                ActionChains(self.driver).key_down(Keys.COMMAND).click(element).key_up(Keys.COMMAND).perform()
            else:
                ActionChains(self.driver) \
                    .key_down(Keys.CONTROL) \
                    .click(element) \
                    .key_up(Keys.CONTROL) \
                    .perform()

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

            if 'Is this your business' in title:
                try:
                    option = self.driver.find_elements(By.XPATH, '//*[@id="main_viewpane"]/c-wiz[1]/div/div[2]/div/div/div[1]/div/content/label')
                    option = option[-1].find_element(By.XPATH, 'div')
                    option.click()
                    self.click_element(
                        By.XPATH,
                        '//*[@id="main_viewpane"]/c-wiz[1]/div/div[2]/div/div/div[2]/button'
                    )
                    time.sleep(5)
                except Exception:
                    pass

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
        text = [i.text for i in row.find_elements_by_xpath('td')]

        try:
            empty, index, name_address, status, action = text
            name, address = name_address.split('\n')
        except ValueError:
            return

        if (
            status.upper() == 'PUBLISHED' or
            action.upper() != 'VERIFY NOW'
        ):
            return

        element = row.find_element(By.XPATH, 'td[5]/content/div/div')
        biz = self.biz_list.get_by_name(name)

        if not biz:
            return
        elif action == 'Verify now' and not self.in_active_list(biz):
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

    def delete_all(self, force=False, clean_listing=True):
        # self.driver.get('https://business.google.com/locations')
        rows = self.driver.find_elements_by_xpath('//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/c-wiz[3]/div/content/c-wiz[2]/div[2]/table/tbody/tr')

        if not rows:
            return

        selected = 0

        for row in rows:
            text = [i.text for i in row.find_elements_by_xpath('td')]
            try:
                empty, index, name_address, status, action = text
                name, address = name_address.split('\n')
            except ValueError:
                continue

            if not force:
                biz = self.biz_list.get_by_name(name)

                if not biz or biz.date_success:
                    continue

            if status.upper() == 'PUBLISHED':
                continue

            self.click_element(
                By.XPATH,
                'td[1]/content/div',
                source=row,
                max_retries=2
            )
            selected += 1

        if not selected:
            return

        self.click_element(
            By.XPATH,
            '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/c-wiz[3]/div/content/div/div[2]/div[2]/span'
        )
        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[9]/div/div/content[8]',
            timeout=3
        )
        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[9]/div/div[2]/content/div/div[2]/div[3]/div[2]',
            timeout=5
        )

        time.sleep(5)
        if clean_listing:
            self.biz_list = None

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
        credential_page = 0
        credential_list = self.service_cred.get_list(**kwargs)

        while credential_list.count:
            credential_page += 1

            for credential in credential_list:
                if any([credential.date_success, credential.date_fail]):
                    continue

                upload_errors = 0

                if platform.system() == 'Windows':
                    self.driver = webdriver.Chrome(
                        executable_path=os.path.join(BASE_DIR, 'chromedriver'),
                    )
                else:
                    self.driver = webdriver.Chrome()

                self.wait = WebDriverWait(self.driver, WAIT_TIME)
                self.driver.get('https://accounts.google.com/ServiceLogin')
                has_success = False

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
                            'https://business.google.com/locations'
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
                    if upload_errors >= 3:
                        credential.report_fail()
                        logger(instance=credential, data="Didn't upload anything 3 times.")
                        break

                    if file_index > 0:
                        if self.biz_list:
                            self.biz_list.get_next_page()
                        else:
                            self.biz_list = self.service_biz.get_list(**kwargs)

                    try:
                        file = self.biz_list.create_csv()
                    except EmptyUpload:
                        self.biz_list.get_next_page()
                        file = self.biz_list.create_csv()

                    logger(instance=self.biz_list, data={'file': file})

                    try:
                        self.do_upload(file)
                        has_success = self.do_verification(credential)
                        self.driver.switch_to_window(self.driver.window_handles[0])
                        self.delete_all()
                        if has_success:
                            break
                    except EmptyUpload:
                        logger(instance=self.biz_list, data="No business show up on the screen.")
                        upload_errors += 1
                        for biz in self.biz_list:
                            try:
                                biz.report_fail()
                            except Exception:
                                continue
                        continue

                    file_index += 1

                if has_success:
                    credential.report_success()
                self.driver.quit()

            if credential_list.next:
                credential_list.get_next_page()
            else:
                logger(data="Process has finished successfully.")
                break
