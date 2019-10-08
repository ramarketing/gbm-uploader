import traceback

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from ..base.selenium import BaseSelenium


class FlowSelenium(BaseSelenium):
    DEFAULT_CATEGORY = 'Insulation contractor'
    WAIT_BEFORE_NEXT = 5

    def __init__(self, entity, credential,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entity = entity
        self.credential = credential
        try:
            self.handle()
        except Exception as err:
            print(err)
            print(traceback.format_exc())
            self._start_debug()
        self.quit_driver()

    def handle(self):
        self.driver = self.get_driver(size=(1200, 700))
        self.do_login(credential=self.credential)
        self.go_to_listing()
        self.go_to_created_business()
        self.do_name('test cleaning service')
        self.do_phone('(818) 297-6038')

        import pdb
        pdb.set_trace()

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
        xpath = '//*[@id="yDmH0d"]/c-wiz/div[2]/div[1]/c-wiz/div/c-wiz[3]/div/span/c-wiz[2]/div[2]/table/tbody/tr[1]'
        row = self.get_element(By.XPATH, xpath)
        self.click_element(By.XPATH, '//td[2]/span/a', source=row)
        url = self.driver.current_url.replace('/dashboard/', '/edit/')
        self.driver.get(url)

    def do_name(self, name):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="yDmH0d"]/c-wiz/div[2]/div[1]/c-wiz/div/div[2]/'
                'div[2]/span/div[2]',
            ),
            timeout=5
        )

        xpath_input = (
            '//*[@id="yDmH0d"]/div[4]/div/div[2]/span/section/div[4]/div/'
            'div[1]/div/div[1]/input'
        )

        self.clear_input(By.XPATH, xpath_input)
        self.fill_input(By.XPATH, xpath_input, name)
        self.click_element(
            By.XPATH,
            (
                '//*[@id="yDmH0d"]/div[4]/div/div[2]/span/section/div[5]/'
                'span[2]/div',
            ),
        )

    def do_phone(self, phone_number):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="yDmH0d"]/c-wiz/div[2]/div[1]/c-wiz/div/div[2]/'
                'div[2]/span/div[8]'
            ),
            move=True,
            timeout=self.WAIT_BEFORE_NEXT
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
            phone_number
        )

        self.click_element(
            By.XPATH,
            (
                '//*[@id="yDmH0d"]/div[4]/div/div[2]/span/section/div[4]/'
                'span[2]/div'
            )
        )

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
