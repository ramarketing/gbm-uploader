import os
import platform
from random import randint
import time
import traceback

from selenium import webdriver
from selenium.common.exceptions import (
    JavascriptException, TimeoutException, WebDriverException
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from exceptions import (
    CredentialBypass, CredentialInvalid, CredentialPendingVerification, EmptyUpload
)
from services import BusinessService, CredentialService
from config import BASE_DIR, PDB_DEBUG, PER_CREDENTIAL, WAIT_TIME
from constants import TEXT_PHONE_VERIFICATION
from logger import UploaderLogger

if PDB_DEBUG:
    import pdb


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

            return_method = func.__name__.startswith('get_')
            raise_exception = kwargs.get('raise_exception', True)

            if timeout:
                time.sleep(timeout)

            while not success:
                retry += 1

                if retry > max_retries:
                    if raise_exception:
                        if PDB_DEBUG:
                            pdb.set_trace()
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
                                response = func(self, by, s, *args, **kwargs)
                                success = True
                                break
                            except Exception:
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
                        response = func(self, by, selector, *args, **kwargs)
                        success = True
                except (TimeoutException, WebDriverException):
                    time.sleep(1)

            return response if return_method else success

        return wrapper

    @perform_action
    def get_text(self, by, selector, source=None, *args, **kwargs):
        source = source or self.driver
        element = source.find_element(by, selector)
        return element.text

    @perform_action
    def fill_input(self, by, selector, content, source=None, *args, **kwargs):
        source = source or self.driver
        element = source.find_element(by, selector)
        element.send_keys(content)

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
            credential.password + Keys.RETURN
        )

        success = self.click_element(
            By.XPATH,
            '//div[@data-challengetype="12"]',
            raise_exception=False,
            timeout=randint(3, 7)
        )
        if success:
            self.fill_input(
                By.NAME,
                'knowledgePreregisteredEmailResponse',
                credential.recovery_email + Keys.RETURN,
                timeout=randint(3, 7)
            )

        phone = self.get_text(
            By.ID,
            'deviceAddress',
            raise_exception=False
        )

        if phone:
            raise CredentialInvalid(msg="Phone number is required")

        self.wait.until(
            EC.url_contains('https://myaccount.google.com/')
        )

    def do_upload(self, file):
        self.driver.get('https://business.google.com/locations')

        success = self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/div[1]/c-wiz/div/div[2]/div[1]',
                '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div[2]/div[1]/c-wiz/div/div[2]/div[1]',
                '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div[2]/div[1]/c-wiz/div/div[2]/div'
            ),
            raise_exception=False
        )
        if success:
            self.click_element(
                By.XPATH,
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[2]/div[3]/div[2]/div',
                raise_exception=False,
                timeout=5
            )

        body = self.driver.find_element(By.CSS_SELECTOR, 'body')
        if "You haven't added any locations" not in body.text:
            raise CredentialPendingVerification(
                msg="Credential has business to be verified."
            )

        self.click_element(
            By.XPATH,
            '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/c-wiz[3]/div/content/div/div/div/div'
        )

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

        self.click_element(
            By.XPATH,
            '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/div[1]/c-wiz/div/div[2]/div[2]',
            max_retries=10,
            timeout=20
        )

        response = self.get_text(
            By.XPATH,
            (
                (
                    '//*[@id="js"]/div[9]/div/div[2]/content/div/div[2]/div[2]/div[1]/div[3]',
                    '//*[@id="js"]/div[10]/div/div[2]/content/div/div[2]/div[2]/div[1]/div[3]'
                ),
            ),
            raise_exception=False
        )

        try:
            msg, count = response.split('\n')
            if msg == 'Errors' and int(count) == self.biz_list.count:
                raise EmptyUpload(
                    msg=traceback.format_exc()
                )
        except (AttributeError, ValueError, UnicodeEncodeError):
            logger(data="Invalid response %s" % response)

        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[9]/div/div[2]/content/div/div[2]/div[3]/div[2]/div[2]',
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[2]/div[3]/div[2]/div[2]',
                '//*[@id="js"]/div[9]/div/div[2]/content/div/div[2]/div[3]/div[2]/div',
            ),
            timeout=5
        )
        success = self.click_element(
            By.XPATH,
            '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/div[1]/c-wiz/div/div[2]/div',
            timeout=20,
            raise_exception=False,
        )
        if success:
            self.click_element(
                By.XPATH,
                (
                    '//*[@id="js"]/div[9]/div/div[2]/content/div/div[2]/div[3]/div[2]/div',
                    '//*[@id="js"]/div[10]/div/div[2]/content/div/div[2]/div[3]/div[2]/div',
                    '//*[@id="js"]/div[9]/div/div[2]/content/div/div[2]/div[3]/div[2]/div[2]',
                    '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div[2]/div[1]/c-wiz/div/div[2]/div[1]'
                ),
                timeout=5,
            )

        time.sleep(5)

    def do_verification(self):
        url = 'https://business.google.com/manage/?noredirect=1#/list'
        url_old = 'https://business.google.com/manage'
        url_new = 'https://business.google.com/locations'
        self.driver.get(url)
        time.sleep(5)
        print('\n\n\nStarting verification\n\n\n')
        if self.driver.current_url.startswith(url_old):
            return self.do_verification_old()
        elif self.driver.current_url.startswith(url_new):
            return self.do_verification_new()
        raise NotImplementedError(
            "do_verification not implemented for url" % self.driver.current_url
        )

    def do_verification_old(self):
        self.active_list = []
        self.clean_old()
        rows = self.driver.find_elements_by_xpath(
            '//*[@id="lm-listings-content-container"]/div[2]/div[1]/md-card-content[2]/div')

        if not rows:
            return
        for row in rows[1:]:
            self.do_verification_old_row(row)

        if len(self.active_list) == 0:
            return

    def do_verification_new(self, special=False):
        self.active_list = []

        success = self.click_element(
            By.XPATH,
            '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/c-wiz[3]/div/content/c-wiz[2]/div[4]/div/span[1]/div[2]',
            move=True,
            raise_exception=False
        )
        if success:
            self.click_element(
                By.XPATH,
                '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/c-wiz[3]/div/content/c-wiz[2]/div[4]/div/span[1]/div[2]/div[2]/div[4]'
            )

        time.sleep(5)
        rows = self.driver.find_elements_by_xpath(
            '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/c-wiz[3]/div/content/c-wiz[2]/div[2]/table/tbody/tr')

        if not rows:
            return

        for row in rows:
            self.do_verification_new_row(row)

        if len(self.active_list) == 0:
            return

    def post_do_verification(self, credential):
        tab_index = len(self.active_list)

        for item in self.active_list:
            item['tab_index'] = tab_index
            tab_index -= 1
            element = item['element']
            before_count = len(self.driver.window_handles)

            # Trick
            special_element = self.driver.find_element(
                By.XPATH,
                '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/div[2]'
            )
            ActionChains(self.driver) \
                .move_to_element(special_element) \
                .perform()
            # End of trick

            ActionChains(self.driver) \
                .move_to_element(element) \
                .perform()

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

            after_count = len(self.driver.window_handles)

            if before_count == after_count:
                text = self.get_text(
                    By.XPATH,
                    '//*[@id="verifyDialog"]/md-dialog-content/div[1]',
                    raise_exception=False
                )
                pdb.set_trace()
                if text and 'Get verified to manage all of your locations' in text:
                    self.delete_all(force=True, clean_listing=True)
                    return False

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
                    option = self.driver.find_elements(
                        By.XPATH, '//*[@id="main_viewpane"]/c-wiz[1]/div/div[2]/div/div/div[1]/div/content/label')
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

    def clean_old(self):
        if hasattr(self, 'is_cleanup') and self.is_cleanup:
            return

        success = self.click_element(
            By.XPATH, '//*[@id="dialogContent_8"]/div[3]/md-checkbox', raise_exception=False)
        if success:
            self.click_element(
                By.XPATH, '/html/body/div[27]/md-dialog/md-dialog-actions/button')

        success = self.click_element(
            By.XPATH,
            '//*[@id="dialogContent_10"]/div[3]/md-checkbox',
            raise_exception=False
        )
        if success:
            self.click_element(
                By.XPATH, '/html/body/div[27]/md-dialog/md-dialog-actions/button')

        success = self.click_element(
            By.XPATH, '//*[@id="bulkInsightsHighlight"]/div/div/div[1]/button', raise_exception=False)
        if success:
            self.click_element(
                By.XPATH, '//*[@id="localAnalyticsDialogForm"]/button')

        self.click_element(
            By.XPATH,
            '//*[@id="lm-listings-switch-view-container"]/div[1]/div/div/div/div[1]/button',
            raise_exception=False
        )
        self.click_element(
            By.XPATH,
            '//*[@id="lm-list-view-promo-use-list-btn"]',
            raise_exception=False
        )
        self.click_element(
            By.XPATH,
            '//*[@id="lm-listings-switch-view-btn-1"]',
            raise_exception=False
        )

        try:
            self.click_element(
                By.XPATH, '//*[@id="lm-listings-pager-menu-btn"]',
                raise_exception=False
            )
            self.click_element(
                By.XPATH, '//*[@id="lm-listings-pager-menu-item-100"]')
        except TimeoutException:
            raise EmptyUpload(
                msg=traceback.format_exc()
            )

        self.is_cleanup = True

    def do_verification_old_row(self, row):
        try:
            id_, name, address, phone, status, action = row.text.split('\n')
        except ValueError:
            return

        if (
            status.upper() != 'NOT PUBLISHED' or
            action.upper() != 'GET VERIFIED'
        ):
            return

        element = row.find_element(
            By.XPATH, 'div[2]/div[4]/div[2]/div/div/div')
        biz = self.biz_list.get_by_id(id_)

        if not biz:
            try:
                biz = self.service_biz.get_detail(id_)
            except AssertionError:
                biz = None

        if biz.date_success:
            return

        if not self.in_active_list(biz):
            logger(instance=biz, data={'action': action, 'status': status})
            self.active_list.append(dict(
                biz=biz,
                element=element,
                row=row,
            ))
        else:
            biz.report_fail()
            logger(instance=biz, data='OUT')

    def do_verification_new_row(self, row):
        text = [i.text for i in row.find_elements_by_xpath('td')]

        try:
            empty, id_, name_address, status, action = text
            name, address = name_address.split('\n')
        except ValueError:
            return

        if (
            status.upper() == 'PUBLISHED' or
            action.upper() != 'VERIFY NOW'
        ):
            return

        element = row.find_element(By.XPATH, 'td[5]/content/div/div')
        biz = self.biz_list.get_by_pk(id_)

        if not biz:
            try:
                biz = self.service_biz.get_detail(id_)
            except AssertionError:
                biz = None

        if not biz or biz.date_success:
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

    def delete_all(self, **kwargs):
        if self.driver.current_url.startswith(
            'https://business.google.com/manage/?noredirect=1#/list'
        ):
            return self.delete_all_old(**kwargs)
        elif self.driver.current_url.startswith(
            'https://business.google.com/locations'
        ):
            return self.delete_all_new(**kwargs)
        raise NotImplementedError(
            'delete_all it not implemented for URL: %s' % (
                self.driver.current_url
            )
        )

    def delete_all_old(self, force=False, clean_listing=True):
        rows = self.driver.find_elements_by_xpath(
            '//*[@id="lm-listings-content-container"]/div[2]/div[1]/md-card-content[2]/div')

        if not rows:
            return

        selected = 0
        current_index = -2

        for row in rows[1:]:
            current_index += 1
            try:
                id_, name, address, phone, status, action = row.text.split(
                    '\n')
            except ValueError:
                continue

            if not force:
                biz = self.biz_list.get_by_pk(id_)

                if not biz:
                    try:
                        biz = self.service_biz.get_detail(id_)
                    except AssertionError:
                        biz = None

                if biz and biz.date_success:
                    continue

            if status.upper() != 'NOT PUBLISHED':
                continue

            self.click_element(
                By.XPATH, 'div[1]/md-checkbox', source=row, move=True
            )
            selected += 1

        if not selected:
            return

        self.click_element(
            By.XPATH, '//*[@id="lm-title-bars-see-options-btn"]')
        self.click_element(
            By.XPATH, '//*[@id="lm-title-bars-remove-btn"]',
            timeout=5
        )
        self.click_element(
            By.XPATH,
            '//*[@id="lm-confirm-dialog-list-selection-remove-selected-2-btn"]',
            timeout=5
        )
        if clean_listing:
            self.biz_list = None

    def delete_all_new(self, force=False, clean_listing=True):
        success = self.click_element(
            By.XPATH,
            '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/c-wiz[3]/div/content/c-wiz[2]/div[4]/div/span[1]/div[2]',
            move=True,
            raise_exception=False
        )
        if success:
            self.click_element(
                By.XPATH,
                '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/c-wiz[3]/div/content/c-wiz[2]/div[4]/div/span[1]/div[2]/div[2]/div[4]'
            )
        else:
            return

        time.sleep(5)
        rows = self.driver.find_elements_by_xpath(
            '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/c-wiz[3]/div/content/c-wiz[2]/div[2]/table/tbody/tr'
        )

        if not rows:
            return

        selected = 0

        # Trick
        element = self.driver.find_element(
            By.XPATH,
            '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/div[2]'
        )
        ActionChains(self.driver).move_to_element(element).perform()
        # End of trick

        for row in rows:
            text = [i.text for i in row.find_elements_by_xpath('td')]
            try:
                empty, id_, name_address, status, action = text
                name, address = name_address.split('\n')
            except ValueError:
                continue

            if not force:
                biz = self.biz_list.get_by_pk(id_)

                if not biz:
                    try:
                        biz = self.service_biz.get_detail(id_)
                    except AssertionError:
                        biz = None

                if biz and biz.date_success:
                    continue

            if status.upper() == 'PUBLISHED':
                continue

            self.click_element(
                By.XPATH,
                'td[1]/content/div',
                source=row,
                move=True,
            )
            selected += 1

        if not selected:
            return

        self.click_element(
            By.XPATH,
            '//*[@id="main_viewpane"]/c-wiz[1]/c-wiz/div/c-wiz[3]/div/content/div/div[2]/div[2]/span',
            move=True
        )
        try:
            self.click_element(
                By.XPATH,
                (
                    '//*[@id="js"]/div[9]/div/div/content[8]',
                    '//*[@id="js"]/div[10]/div/div/content[8]'
                ),
                timeout=3
            )
        except TimeoutException:
            logger(instance=self.biz_list, data="Unable to delete businesses.")
            return

        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[9]/div/div[2]/content/div/div[2]/div[3]/div[2]',
            timeout=5
        )

        time.sleep(selected + 5)
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
                self.is_cleanup = False

                if platform.system() == 'Windows':
                    self.driver = webdriver.Chrome(
                        executable_path=os.path.join(BASE_DIR, 'chromedriver')
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
                except Exception:
                    text = self.get_text(By.XPATH, '//body').strip()

                    if (
                        "t find your Google Account" in text or
                        "Account disabled" in text
                    ):
                        logger(instance=credential,
                               data="Account doesn't exists.")
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

                self.biz_list = self.biz_list or self.service_biz.get_list(
                    **kwargs)

                if max_success and not self.can_continue(max_success, **kwargs):
                    logger(data="Completed.")
                    return

                for index in range(PER_CREDENTIAL):
                    if upload_errors >= 3:
                        credential.report_fail()
                        logger(instance=credential,
                               data="Didn't upload anything 3 times.")
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
                        self.do_verification()
                        has_success = self.post_do_verification(credential)
                        self.driver.switch_to_window(
                            self.driver.window_handles[0]
                        )
                        self.delete_all()
                        if has_success:
                            break
                    except CredentialPendingVerification:
                        self.do_verification()
                        has_success = self.post_do_verification(credential)
                        self.driver.switch_to_window(
                            self.driver.window_handles[0]
                        )
                        self.delete_all()
                        if has_success:
                            break
                    except EmptyUpload:
                        for biz in self.biz_list:
                            try:
                                biz.report_fail()
                            except Exception:
                                continue
                        self.biz_list = None
                        has_success = False
                    except CredentialBypass:
                        logger(
                            instance=credential,
                            data={
                                'message': "Bypassing this credential.",
                                'url': self.driver.current_url,
                            }
                        )
                        has_success = False
                        break

                    file_index += 1

                if has_success:
                    credential.report_success()
                self.driver.quit()

            if credential_list.next and credential == credential_list[-1]:
                credential_list.get_next_page()
            else:
                logger(data="Process has finished successfully.")
                break
