import json
import platform
import traceback

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from ..constants import COUNTRY_CHOICES
from ..base.exceptions import (
    CredentialInvalid, EmptyList, EntityInvalid,
    EntityIsSuccess, InvalidValidationMethod, NotFound, MaxRetries,
    TerminatedByUser
)
from ..base.selenium import BaseSelenium
from ..utils import phone_clean
from .service import BusinessService


class UploaderSelenium(BaseSelenium):
    active_list = []

    def __init__(self, entity, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entity = entity
        self.biz_service = BusinessService()
        try:
            self.handle()
        except TerminatedByUser:
            self.quit_driver()
        except (
            CredentialInvalid, EntityInvalid, EmptyList, NotFound, MaxRetries,
            InvalidValidationMethod
        ):
            self.entity.report_fail()
            self.quit_driver()
        except EntityIsSuccess:
            self.quit_driver()
        except Exception as err:
            print(err)
            print(traceback.format_exc())
            self._start_debug()
        self.quit_driver()

    def handle(self):
        self.driver = self.get_driver(size=(1200, 700))
        self.do_login()
        self.go_to_manager()
        self.do_pagination()
        self.verify_rows()
        self.verify_tabs()
        self.report_success()

    def go_to_manager(self):
        url = 'https://business.google.com/locations'
        if not self.driver.current_url.startswith(url):
            self.driver.get(url)
            self._wait(5)

    def get_rows(self, raise_exception=True):
        self.go_to_manager()
        rows = self.get_elements(
            By.XPATH,
            '//table/tbody/tr',
            raise_exception=raise_exception
        )
        return rows or []

    def do_delete_all(self):
        rows = self.get_rows()

        if not rows:
            return

        self.click_element(
            By.XPATH,
            (
                '/html/body/div[4]/c-wiz/div[2]/div[1]/c-wiz/div/c-wiz[3]/'
                'div/content/c-wiz[2]/div[2]/table/thead/tr/th[1]/span/div'
            ),
            move=True
        )
        self.click_element(
            By.XPATH,
            (
                '/html/body/div[4]/c-wiz/div[2]/div[1]/c-wiz/div/c-wiz[3]/'
                'div/content/div/div[2]/div[2]/span/div'
            ),
            timeout=3
        )
        self.click_element(
            By.XPATH,
            (
                '/html/body/div[5]/div/div/content[8]'
            ),
            timeout=3
        )
        self.click_element(
            By.XPATH,
            (
                '/html/body/div[5]/div/div[2]/content/div/div[2]/'
                'div[3]/div[2]',
                '/html/body/div[4]/div[4]/div/div[2]/content/div/'
                'div[2]/div[3]/div[2]',
            ),
            timeout=3
        )
        self._wait(20)

    def verify_rows(self):
        self.object_list = []
        rows = self.get_rows()
        if not rows:
            return

        for row in rows:
            self.verify_row(row)

    def verify_row(self, row):
        columns = self.get_elements(
            By.XPATH,
            'td',
            source=row
        )

        empty, pk, name_address, status, action_column = columns
        pk = pk.text
        name, address = name_address.text.split('\n')
        status = status.text
        action = action_column.text

        obj = {
            'pk': pk,
            'name': name,
            'address': address,
            'phone': None,
            'status': status,
            'action': action,
            'row': row,
            'window': None
        }

        if action != 'Verify now':
            return

        element = self.get_element(
            By.XPATH,
            'content/div/div',
            source=action_column,
            move=True
        )

        before_length = len(self.driver.window_handles)

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

        after_length = len(self.driver.window_handles)

        if before_length != after_length:
            obj['window'] = self.driver.window_handles[-1]

        self.object_list.append(obj)

    def verify_tabs(self):
        for obj in self.object_list:
            if not obj['window']:
                continue

            self.driver.switch_to.window(obj['window'])
            self.verify_tab(obj)

    def verify_tab(self, obj):
        text = self.get_element(
            By.TAG_NAME,
            'body',
            move=False
        ).text.strip()

        if 'Is this your business' in text:
            elements = self.get_elements(
                By.XPATH,
                (
                    '//*[@id="main_viewpane"]/c-wiz[1]/div/div[2]/div/div/'
                    'div[1]/div/content/label'
                )
            )
            self.click_element(
                By.XPATH,
                'div[1]',
                source=elements[-1],
                timeout=5
            )
            self.click_element(
                By.XPATH,
                (
                    '//*[@id="main_viewpane"]/c-wiz[1]/div/div[2]/div/div/'
                    'div[2]/button'
                )
            )
            text = self.get_element(
                By.XPATH,
                '//body',
                move=False,
                timeout=5
            ).text.strip()

        if (
            'Enter the code' not in text and
            'Get your code at this number now by automated call' not in text
        ):
            self.logger(instance=obj, data="Cannot validate by phone.")
            self.driver.close()
            return

        phone = self.get_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[2]/div/div/div/'
                'div[1]/div/div[1]/h3',
            ),
            move=False
        ).text
        obj['phone'] = phone_clean(phone)

    def do_pagination(self):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="yDmH0d"]/c-wiz/div[2]/div[1]/c-wiz/div/c-wiz[3]/'
                'div/content/c-wiz[2]/div[4]/div/span[1]/div[2]',

            ),
            move=True
        )
        success = self.click_element(
            By.XPATH,
            (
                '//*[@id="yDmH0d"]/c-wiz/div[2]/div[1]/c-wiz/div/c-wiz[3]/'
                'div/content/c-wiz[2]/div[4]/div/span[1]/div[2]/div[2]/div[4]',
            ),
            timeout=3,
            raise_exception=False
        )
        if not success:
            input('Please do the pagination manually then press any key.')
        else:
            self._wait(5)

    def report_success(self):
        for obj in self.object_list:
            if not obj['phone']:
                continue

            obj['email'] = self.entity.email
            obj['password'] = self.entity.password
            obj['recovery_email'] = self.entity.recovery_email

            full_address = obj.pop('address')
            try:
                address, city, state_zip_code, country = full_address \
                    .split(', ')
            except ValueError:
                country = 'United States'
                address, city, state_zip_code = full_address \
                    .split(', ')

            state, zip_code = state_zip_code.split(' ')

            obj['final_address'] = address
            obj['final_city'] = city.title()
            obj['final_state'] = state
            obj['final_zip_code'] = zip_code
            obj['final_country'] = COUNTRY_CHOICES[country]
            obj['final_phone_number'] = obj['phone']

            try:
                self.biz_service.create(**obj)
            except json.decoder.JSONDecodeError:
                self._start_debug(obj=obj, message="Error creating business.")
                continue

        self.entity.report_success()
