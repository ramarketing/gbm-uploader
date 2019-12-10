from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from .. import config
from ..base.exceptions import CredentialInvalid
from ..base.selenium import BaseSelenium
from . import constants


class GMBTaskSelenium(BaseSelenium):
    def __init__(self, gmbtask, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gmbtask = gmbtask
        try:
            self.handle()
        finally:
            self.quit_driver()

    def handle(self):
        self.driver = self.get_driver(size=(1200, 700))
        self.login_matrix()
        self.go_to_accounts()

        try:
            self.login_google()
        except TimeoutException:
            self.gmbtask.patch(
                status=constants.STATUS_FAIL,
                status_message='Proceed manually.'
            )
            return

        if not self.is_connected():
            self.click_allow()
            self.click_permit()
            self.click_sync()

        if self.gmbtask.action == constants.ACTION_PATCH:
            self.gmbtask.patch(status=constants.STATUS_WAITING)
        else:
            self.gmbtask.patch(status=constants.STATUS_COMPLETE)

    def login_matrix(self):
        url = config.API_ROOT.split('/')
        url = f'{url[0]}//{url[2]}/panel/'
        self.driver.get(url)
        self.fill_input(
            By.ID, 'id_username', config.API_USERNAME
        )
        self.fill_input(
            By.ID, 'id_password', config.API_PASSWORD + Keys.RETURN
        )

    def go_to_accounts(self):
        url = config.API_ROOT.split('/')
        url = f'{url[0]}//{url[2]}/panel/seo/accounts/'
        self.driver.get(url)
        self.click_element(
            By.XPATH,
            '//*[@id="page-wrapper"]/div[2]/div[2]/div/div/a'
        )

    def login_google(self):
        self.fill_input(
            By.ID,
            ('identifierId', 'Email'),
            self.gmbtask.account.username + Keys.RETURN
        )
        self.fill_input(
            By.NAME,
            ('password', 'Passwd'),
            self.gmbtask.account.password + Keys.RETURN,
            timeout=3
        )
        self._wait(3)
        element = self.get_element(
            By.NAME,
            ('password', 'Passwd'),
            max_retries=2,
            raise_exception=False
        )
        if element:
            raise CredentialInvalid("Wrong password.")

        by_recovery_email = self.click_element(
            By.CSS_SELECTOR,
            'div[data-challengetype="12"]',
            raise_exception=False,
            max_retries=2,
            timeout=3
        )
        if by_recovery_email:
            self.fill_input(
                By.NAME,
                'knowledgePreregisteredEmailResponse',
                self.gmbtask.account.recovery_email + Keys.RETURN,
                timeout=3
            )

        by_recovery_phone = self.click_element(
            By.CSS_SELECTOR,
            'div[data-challengetype="13"]',
            raise_exception=False,
            max_retries=2,
            timeout=3
        )
        if by_recovery_phone:
            self.fill_input(
                By.ID,
                'phoneNumberId',
                self.gmbtask.account.recovery_phone + Keys.RETURN,
                timeout=3
            )

        self._wait(3)

    def is_connected(self):
        url = config.API_ROOT.split('/')
        url = f'{url[0]}//{url[2]}/panel/seo/accounts/'
        return url in self.driver.current_url

    def click_allow(self):
        self.click_element(
            By.XPATH,
            '//*[@id="oauthScopeDialog"]/div[3]/div[1]'
        )
        self._wait(3)

    def click_permit(self):
        self.click_element(
            By.ID,
            'submit_approve_access'
        )
        self._wait(3)

    def click_sync(self):
        self.click_element(
            By.XPATH,
            '//*[@id="mainContent"]/div[2]/div[2]/table/tbody/tr[7]/td/a'
        )
