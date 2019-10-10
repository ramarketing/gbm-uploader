import phonenumbers
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from ..base.selenium import BaseSelenium
from ..base.exceptions import GBMException
from ..config import STATUS_PROCESSING


class FlowSelenium(BaseSelenium):
    DEFAULT_CATEGORY = 'Insulation contractor'
    WAIT_BEFORE_NEXT = 5

    def __init__(self, entity, credential, code, lead,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entity = entity
        self.code = code
        self.credential = credential
        self.lead = lead

    def handle(self):
        self.driver = self.get_driver(size=(1200, 900))
        self.do_login(credential=self.credential)
        self.go_to_listing()
        self.go_to_created_business()

        name = self.get_name()
        name = '{} {}'.format(
            self.code.person['first_name'],
            ' '.join(name.split(' ')[1:])
        )
        self.do_name(name)
        self.do_phone(self.code.person['phone'])
        self.open_verification_tab()
        retries = 0

        while not self.has_number_verification():
            if retries == 20:
                raise GBMException("Too many retries.")
            self.driver.get(self.driver.current_url)
            retries += 1

        self.request_code()

        self.driver.switch_to_window(self.driver.window_handles[0])

        while not any([self.code.code_1, self.code.code_2, self.code.code_3]):
            self.code = self.code.refresh()

        self.do_name(self.entity.name)
        self.do_category(self.entity.verification_category)
        self.do_phone(self.entity.phone)
        self.write_code()

        '''
        self.go_to_creation()  # 7/10 Updated
        self.do_name()  # 7/10 Updated
        self.do_can_visit()  # 7/10 Updated
        self.do_address()  # 7/10 Updated
        self.do_outside()
        self.do_area()
        self.do_category()
        self.do_phone()
        self.do_finish()
        self.do_verify_tab()
        '''

    def go_to_creation(self):
        url = 'https://business.google.com/create'
        if not self.driver.current_url.startswith(url):
            self.driver.get(url)

    def go_to_listing(self):
        url = 'https://business.google.com/locations'
        if not self.driver.current_url.startswith(url):
            self.driver.get(url)

    def go_to_created_business(self):
        xpath = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div[1]/c-wiz/div/c-wiz[3]/div/'
            'span/c-wiz[2]/div[2]/table/tbody/tr[1]'
        )
        row = self.get_element(By.XPATH, xpath)
        try:
            self.click_element(By.XPATH, '//td[2]/span/a', source=row)
        except TimeoutException:
            self.click_element(By.XPATH, '//td[3]/span/a', source=row)

        url = self.driver.current_url.replace('/dashboard/', '/edit/')
        self.driver.get(url)

    def get_name(self):
        content = self.get_text(
            By.XPATH,
            (
                '//*[@id="yDmH0d"]/c-wiz/div[2]/div[1]/c-wiz/div/div[2]/'
                'div[2]/span/div[2]'
            )
        )
        return content.strip()

    def do_name(self, name):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="yDmH0d"]/c-wiz/div[2]/div[1]/c-wiz/div/div[2]/'
                'div[2]/span/div[2]'
            )
        )

        xpath_input = (
            '//*[@id="yDmH0d"]/div[4]/div/div[2]/span/section/div[4]/div/'
            'div[1]/div/div[1]/input',
            '//*[@id="yDmH0d"]/div[4]/div/div[2]/span/c-wiz/section/'
            'div[4]/div/div[1]/div/div[1]/input',
        )

        self.clear_input(By.XPATH, xpath_input)
        self.fill_input(By.XPATH, xpath_input, name)
        self.click_element(
            By.XPATH,
            (
                '//*[@id="yDmH0d"]/div[4]/div/div[2]/span/section/div[5]/'
                'span[2]/div',
                '//*[@id="yDmH0d"]/div[4]/div/div[2]/span/c-wiz/section/'
                'div[5]/span[2]/div'
            ),
            timeout=3
        )

    def do_phone(self, phone):
        try:
            pn = phonenumbers.parse(phone)
            phone = phonenumbers.format_number(
                pn, phonenumbers.PhoneNumberFormat.NATIONAL
            )
        except phonenumbers.phonenumberutil.NumberParseException:
            pass

        self.click_element(
            By.XPATH,
            (
                '//*[@id="yDmH0d"]/c-wiz/div[2]/div[1]/c-wiz/div/div[2]/'
                'div[2]/span/div[8]'
            ),
            move=True
        )

        xpath_input = (
            '//*[@id="yDmH0d"]/div[4]/div/div[2]/span/section/div[3]/div[1]/'
            'div/div/div[2]/div[1]/div/div[1]/input'
        )

        # Fill new number
        self.clear_input(By.XPATH, xpath_input)
        self.fill_input(
            By.XPATH,
            xpath_input,
            phone
        )

        self.click_element(
            By.XPATH,
            (
                '//*[@id="yDmH0d"]/div[4]/div/div[2]/span/section/div[4]/'
                'span[2]/div'
            )
        )

    def open_verification_tab(self):
        url = self.driver.current_url.replace('/edit/', '/verify/')
        self.driver.execute_script(
            '''window.open("{}", "_blank");'''.format(url)
        )
        self.driver.switch_to_window(self.driver.window_handles[1])
        self.driver.get(url)

    def has_number_verification(self):
        content = self.get_text(By.TAG_NAME, 'body')

        if 'Is this your business?' in content:
            elements = self.get_elements(
                By.XPATH,
                (
                    '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div/div[2]/div/div/'
                    'div[1]/div/span/label'
                )
            )
            elements[-1].click()
            self.click_element(
                By.XPATH,
                (
                    '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div/div[2]/div/div/'
                    'div[2]/button'
                )
            )
            content = self.get_text(By.TAG_NAME, 'body', timeout=3)
        elif 'Enter the code' in content:
            self.click_element(
                By.XPATH,
                (
                    '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div/div[2]/div/div/'
                    'div[2]/div/div[2]/button'
                )
            )

        return 'Postcard by mail' not in content

    def request_code(self):
        content = self.get_text(By.TAG_NAME, 'body')

        if 'Enter code' in content:

            return

        self.click_element(
            By.XPATH,
            (
                '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div/div[2]/div/div/div/'
                'div[1]/div/div[2]/button[2]'
            )
        )
        self.lead.patch(status=STATUS_PROCESSING)

    def do_category(self, name):
        if not name:
            return

        self.click_element(
            By.XPATH,
            (
                '//*[@id="yDmH0d"]/c-wiz/div[2]/div[1]/c-wiz/div/div[2]/'
                'div[2]/span/div[3]'
            )
        )

        xpath_input = (
            '//*[@id="yDmH0d"]/div[4]/div/div[2]/span/section/div[4]/div/'
            'div[1]/div/div[1]/div[1]/input[2]'
        )

        self.clear_input(
            By.XPATH,
            xpath_input
        )
        self.fill_input(
            By.XPATH,
            xpath_input,
            name
        )

        try:
            self.click_element(
                By.XPATH,
                (
                    '//*[@id="yDmH0d"]/div[4]/div/div[2]/span/section/div[4]/'
                    'div/div[1]/div/div[1]/div[2]/div/div/div[1]'
                ),
                timeout=3
            )
            self.click_element(
                By.XPATH,
                (
                    '//*[@id="yDmH0d"]/div[4]/div/div[2]/span/section/div[5]/'
                    'span[2]/div'
                )
            )
        except TimeoutException:
            self.click_element(
                By.XPATH,
                (
                    '//*[@id="yDmH0d"]/div[4]/div/div[2]/span/section/div[5]/'
                    'span[1]/div'
                )
            )

    def do_hours(self, all_day=True):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="yDmH0d"]/c-wiz/div[2]/div[1]/c-wiz/div/div[2]/'
                'div[2]/span/div[6]'
            ),
            move=True
        )
        elements = self.get_elements(
            By.XPATH,
            '//*[@id="yDmH0d"]/div[4]/div/div[2]/span/section/div[3]/div/div'
        )
        for element in elements:
            checkbox = self.get_element(
                By.XPATH,
                'label/div',
                source=element
            )
            if checkbox.get_attribute('aria-checked') != 'true':
                checkbox.click()

            self.click_element(
                By.XPATH,
                'div[2]/div[1]/div/div[1]/div[1]/input[2]',
                source=element
            )

            if all_day:
                self.click_element(
                    By.XPATH,
                    'div[2]/div[1]/div/div[1]/div[2]/div/div/div[1]',
                    raise_exception=False,
                    source=element
                )
            else:
                self.click_element(
                    By.XPATH,
                    'div[2]/div[1]/div/div[1]/div[2]/div/div/div[21]',
                    move=True,
                    raise_exception=False,
                    source=element
                )
                self.click_element(
                    By.XPATH,
                    'div[2]/div[1]/div/div[2]/div[2]/div[1]/input[2]',
                    raise_exception=False,
                    source=element
                )
                self.click_element(
                    By.XPATH,
                    'div[2]/div[1]/div/div[2]/div[2]/div[2]/div/div/div[39]',
                    move=True,
                    raise_exception=False,
                    source=element
                )
            self._wait(1)

        self.click_element(
            By.XPATH,
            '//*[@id="yDmH0d"]/div[4]/div/div[2]/span/section/div[4]/'
            'span[2]/div'
        )

    def write_code(self):
        self.driver.switch_to_window(self.driver.window_handles[1])

        codes = [self.code.code_1, self.code.code_2, self.code.code_3]
        codes = [code for code in codes if code]
        code_valid = False

        while not code_valid:
            for code in codes:
                if code_valid:
                    continue

                self.fill_input(
                    By.XPATH,
                    (
                        '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div/div[2]/div/div/'
                        'div[1]/div[2]/div[1]/div/div[1]/input'
                    ),
                    code
                )
                self.click_element(
                    By.XPATH,
                    (
                        '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div/div[2]/div/div/'
                        'div[1]/div[3]/button'
                    )
                )
                self._wait(3)
                content = self.get_text(By.TAG_NAME, 'body')

                if (
                    'Enter the code' not in content and
                    'Wrong code' not in content
                ):
                    code_valid = True

        if not code_valid:
            raise GBMException("Didn't required a code.")

    '''
    def do_name(self):
        xpath_input = (
            'input[aria-label="Type your business name"]',
        )
        self.clear_input(By.CSS_SELECTOR, xpath_input)
        self.fill_input(
            By.CSS_SELECTOR,
            xpath_input,
            self.entity.name + Keys.RETURN
        )

        xpath = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[2]/div/div[2]/div/'
            'div/div[2]/div/div/div[1]'
        )
        self.click_element(By.XPATH, xpath, raise_exception=False)

        xpath = '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[3]/div[1]'
        self.click_element(By.XPATH, xpath)
    '''

    def do_can_visit(self):
        xpath = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[2]/div/div[1]/div'
        )
        self.click_element(By.XPATH, xpath)

        xpath = '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[3]/div[1]'
        self.click_element(By.XPATH, xpath)

    def do_search_engine(self):
        xpath_inputs = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/div[2]/div/'
            'div[1]/content/label',
        )
        options = self.get_elements(
            By.XPATH, xpath_inputs, move=False, timeout=5
        )

        for option in options:
            if option.text.lower() != 'yes':
                continue

            self.click_element(By.XPATH, 'div', source=option)

        xpath_submit = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/div[3]/'
            'div[1]',
        )
        self.click_element(By.XPATH, xpath_submit, timeout=3)

    def do_address(self):
        # Country
        self.click_element(
            By.CSS_SELECTOR, 'div[aria-label="Country / Region"]'
        )
        xpath_country_options = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[2]/div/div/'
            'div[1]/div/div/c-wiz/c-wiz/div/div/div[1]/div[1]/div[2]/div',
        )
        country_options = self.get_elements(By.XPATH, xpath_country_options)
        for option in country_options:
            code = option.get_attribute('data-value')
            if code.upper() != self.entity.country['code'].upper():
                continue
            option.click()

        self._wait(3)

        # Street
        xpath = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[2]/div/div/'
            'div[1]/div/div/c-wiz/c-wiz/div/div/div[4]/div/div[1]/div/'
            'div[1]/input'
        )
        self.fill_input(By.XPATH, xpath, self.entity.address)

        # City
        self.fill_input(
            By.CSS_SELECTOR,
            'input[aria-label="City"]',
            self.entity.city
        )

        # State
        self.click_element(By.CSS_SELECTOR, 'div[aria-label="State"]')
        xpath_state_options = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[2]/div/div/'
            'div[1]/div/div/c-wiz/c-wiz/div/div/div[6]/div[1]/div[2]/div',
        )
        state_options = self.get_elements(
            By.XPATH, xpath_state_options, timeout=3
        )
        for option in state_options:
            code = option.get_attribute('data-value')
            if code.upper() != self.entity.state.upper():
                continue
            option.click()

        # ZIP
        self.fill_input(
            By.CSS_SELECTOR,
            'input[aria-label="ZIP code"]',
            self.entity.zip_code.split('-')[0]
        )

        xpath_next = (
            '//*[@id="yDmH0d"]/c-wiz/c-wiz/div/div[1]/div[3]/div[1]',
        )
        self.click_element(By.XPATH, xpath_next, timeout=3)

    def do_outside(self):
        xpath_inputs = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/div[2]/'
            'div/div[1]/content/label'
        )
        options = self.get_elements(
            By.XPATH, xpath_inputs, move=False, timeout=self.WAIT_BEFORE_NEXT
        )

        for option in options:
            if 'yes' not in option.text.lower():
                continue

            self.click_element(By.XPATH, 'div', source=option)

        xpath_submit = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/'
            'div[3]/div[1]',
        )
        self.click_element(By.XPATH, xpath_submit, timeout=3)

    def do_area(self):
        xpath_input = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/div[2]/'
            'div/div/div/div/div/div/div[1]/div[2]/div[1]/div/div[1]/input'
        )
        content = '{}, {}'.format(
            self.entity.final_city, self.entity.final_state
        )
        self.fill_input(
            By.XPATH, xpath_input, content, timeout=self.WAIT_BEFORE_NEXT
        )
        xpath_option = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/div[2]/'
            'div/div/div/div/div/div/div[2]/div/div/div[1]'
        )
        self.click_element(By.XPATH, xpath_option, timeout=3)
        xpath_next = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/div[3]/'
            'div[1]',
        )
        self.click_element(By.XPATH, xpath_next, timeout=3)

    '''
    def do_category(self):
        xpath_input = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/div[2]/'
            'div/div/div/div/div/div[1]/div[2]/div[1]/div/div[1]/input'
        )
        content = self.entity.final_category_1 or self.DEFAULT_CATEGORY
        self.fill_input(
            By.XPATH, xpath_input, content, timeout=self.WAIT_BEFORE_NEXT
        )
        xpath_option = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/div[2]/'
            'div/div/div/div/div/div[2]/div/div/div[1]'
        )
        self.click_element(By.XPATH, xpath_option, timeout=3)
        xpath_next = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/div[3]/'
            'div[1]',
        )
        self.click_element(By.XPATH, xpath_next, timeout=3)
    '''

    '''
    def do_phone(self):
        xpath_phone = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/div[2]/'
            'div/form/div[1]/div/div/div/div/div[2]/div[1]/div/div[1]/input',
        )
        self.clear_input(
            By.XPATH, xpath_phone, timeout=self.WAIT_BEFORE_NEXT
        )
        self.fill_input(By.XPATH, xpath_phone, self.entity.final_phone_number)

        xpath_option = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/div[2]/'
            'div/form/div[2]/div/content/div[2]/div',
        )
        self.click_element(By.XPATH, xpath_option)

        xpath_next = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/div[3]/'
            'div[1]',
        )
        self.click_element(By.XPATH, xpath_next)
    '''

    def do_finish(self):
        xpath_button = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/div[3]/'
            'div[1]',
        )
        self.click_element(
            By.XPATH, xpath_button, timeout=self.WAIT_BEFORE_NEXT
        )
        self._wait(30)

    def do_verify_tab(self):
        text = self.get_element(By.TAG_NAME, 'body', move=False).text.strip()

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
            self.entity.report_fail()
            self.logger(instance=self.entity, data="Cannot validate by phone.")
            return

        self.entity.put(credential=self.credential.pk)
        self.credential.report_success()
