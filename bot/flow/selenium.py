import traceback

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from base.selenium import BaseSelenium


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
        self.go_to_creation()
        self.do_name()
        self.do_search_engine()
        self.do_address()
        self.do_outside()
        self.do_area()
        self.do_category()
        self.do_phone()
        self.do_finish()
        self.do_verify_tab()

    def go_to_creation(self):
        url = 'https://business.google.com/create'
        if not self.driver.current_url.startswith(url):
            self.driver.get(url)

    def do_name(self):
        xpath_input = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/div[2]/'
            'div/div/div/div/div/div[1]/div[2]/div[1]/div/div[1]/input',
        )
        self.clear_input(By.XPATH, xpath_input)
        self.fill_input(By.XPATH, xpath_input, self.entity.name + Keys.RETURN)

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
        xpath_country = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/div[2]/'
            'div/div/div[1]/div/div/c-wiz/c-wiz/div/div/div[1]/div[1]',
        )
        self.click_element(
            By.XPATH, xpath_country, timeout=self.WAIT_BEFORE_NEXT
        )
        xpath_country_options = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/div[2]/'
            'div/div/div[1]/div/div/c-wiz/c-wiz/div/div/div[1]/div[1]/'
            'div[2]/div',
        )
        country_options = self.get_elements(
            By.XPATH, xpath_country_options, timeout=3
        )
        for option in country_options:
            code = option.get_attribute('data-value')
            if code.upper() != self.entity.final_country.upper():
                continue
            option.click()

        # Street
        xpath_street = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/div[2]/'
            'div/div/div[1]/div/div/c-wiz/c-wiz/div/div/div[4]/div/div[1]/'
            'div/div[1]/input',
        )
        self.clear_input(
            By.XPATH, xpath_street, timeout=self.WAIT_BEFORE_NEXT
        )
        self.fill_input(
            By.XPATH, xpath_street, self.entity.final_address
        )

        # City
        xpath_city = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/div[2]/'
            'div/div/div[1]/div/div/c-wiz/c-wiz/div/div/div[5]/div/div[1]/'
            'div/div[1]/input',
        )
        self.clear_input(
            By.XPATH, xpath_city, timeout=self.WAIT_BEFORE_NEXT
        )
        self.fill_input(
            By.XPATH, xpath_city, self.entity.final_city
        )

        # State
        xpath_state = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/div[2]/'
            'div/div/div[1]/div/div/c-wiz/c-wiz/div/div/div[6]/div[1]',
        )
        self.click_element(
            By.XPATH, xpath_state, timeout=self.WAIT_BEFORE_NEXT
        )
        xpath_state_options = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/div[2]/'
            'div/div/div[1]/div/div/c-wiz/c-wiz/div/div/div[6]/div[1]/'
            'div[2]/div',
        )
        state_options = self.get_elements(
            By.XPATH, xpath_state_options, timeout=3
        )
        for option in state_options:
            code = option.get_attribute('data-value')
            if code.upper() != self.entity.final_state.upper():
                continue
            option.click()

        # ZIP
        xpath_zip_code = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/div[2]/'
            'div/div/div[1]/div/div/c-wiz/c-wiz/div/div/div[7]/div/div[1]/'
            'div/div[1]/input',
        )
        self.clear_input(
            By.XPATH, xpath_zip_code, timeout=self.WAIT_BEFORE_NEXT
        )
        self.fill_input(
            By.XPATH, xpath_zip_code, self.entity.final_zip_code
        )

        xpath_next = (
            '//*[@id="yDmH0d"]/c-wiz/div[2]/div/c-wiz/div/div[2]/div[3]/'
            'div[1]',
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
