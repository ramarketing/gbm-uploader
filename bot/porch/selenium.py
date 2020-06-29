import json

import requests
from selenium.webdriver.common.by import By

from ..base.selenium import BaseSelenium
from .. import config


class PorchSelenium(BaseSelenium):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self):
        try:
            return self.handle()
        except Exception as err:
            print(err)
            self._wait(10)
        finally:
            self.quit_driver()

    def handle(self):
        self.driver = self.get_driver(size=(1200, 700))
        self.do_login()
        self.go_to_oportunities()
        links = self.get_list_items()
        for link in links:
            content = self.get_link_data(link)
            self.send_to_airtable(content)
        self._wait(10)

    def do_login(self):
        self.driver.get('https://pro.homeadvisor.com/login?execution=e1s1')
        self.fill_input(By.ID, 'username', config.HA_USERNAME)
        self.fill_input(By.ID, 'password', config.HA_PASSWORD)
        self.click_element(By.CSS_SELECTOR, 'input[type="submit"]')

    def go_to_oportunities(self):
        self.driver.get('https://pro.homeadvisor.com/opportunities/')
        self._wait(5)

    def get_list_items(self):
        elements = self.get_elements(
            By.CSS_SELECTOR, '.lead-card-link'
        )
        response = []
        for element in elements:
            link = element.get_attribute('href')
            link = link.replace('/opportunities/details/OL/', '/ols/lead/')
            if not link.startswith('http'):
                link = f'https://pro.homeadvisor.com{link}'
            response.append(link)
        return response

    def get_link_data(self, link):
        self.driver.get(link)
        content = self.get_element(By.ID, 'jsonModel')
        return content.get_attribute('innerHTML')

    def parse_content(self, content):
        if content.startswith('"'):
            content = content[1:-1]
        content = json.loads(content)

        fields = [
            'postApprovalConsumerName',
            'conAddressLine1',
            'conAddressLine2',
            'consumerCity',
            'consumerState',
            'consumerZip',
            'consumerDayTimePhone',
            'consumerEveningPhone',
            'consumerCellPhone',
            'taskDescription',
            'token',
            'preciseLatitude',
            'preciseLongitude',
        ]
        response = {}

        for field in fields:
            try:
                response[field] = content[field]
            except KeyError:
                continue

        response['submitDateTime'] = (
            '{year}-{month}-{day}T{hour}:{minute}:{second}.000Z'
        ).format(
            year=content['submitDateTime']['year'],
            month=content['submitDateTime']['month'],
            day=content['submitDateTime']['dayOfMonth'],
            hour=content['submitDateTime']['hour'],
            minute=content['submitDateTime']['minute'],
            second=content['submitDateTime']['second'],
        )

        return response

    def send_to_airtable(self, content):
        content = self.parse_content(content)
        url = config.HA_AIRTABLE
        content = dict(records=[dict(fields=content)])
        requests.post(url, json=content, headers={
            'Authorization': f'Bearer {config.HA_AIRTABLE_KEY}'
        })
