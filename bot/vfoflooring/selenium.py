import requests
from selenium.webdriver.common.by import By

from ..base.selenium import BaseSelenium
from .. import config


class VFOSelenium(BaseSelenium):
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
        self.go_to_hardwoods()

        links = self.get_list_items()
        links = list(set(links))

        for link in links:
            details = self.get_product_details(link)
            self.send_to_airtable(details)

        self._wait(10)

    def go_to_hardwoods(self):
        self.driver.get(
            'https://vfoflooring.com/laminate-clearance-flooring.html'
            '#product_list_limit=all'
        )
        self._wait(10)

    def get_list_items(self):
        elements = self.get_elements(
            By.CSS_SELECTOR, 'li.product-item'
        )
        response = []
        for element in elements:
            element = self.get_element(
                By.CSS_SELECTOR, 'a.product-item-link', source=element
            )
            link = element.get_attribute('href')
            response.append(link)
        return response

    def get_product_details(self, link):
        modal = True
        while modal:
            self.driver.get(link)
            self._wait(10)
            modal = self.get_element(
                By.CSS_SELECTOR, '.modal-popup._show', raise_exception=False
            )

        image = self.get_element(By.CSS_SELECTOR, 'div.fotorama__stage__frame > img').get_attribute('src')
        name = self.get_text(
            By.CSS_SELECTOR, 'span[itemprop="name"]'
        )
        sku = self.get_text(
            By.CSS_SELECTOR, 'div[itemprop="sku"]'
        )
        description = self.get_text(
            By.CSS_SELECTOR, 'div[itemprop="description"]',
            raise_exception=False
        )
        price_per_sqft = self.get_text(
            By.CSS_SELECTOR, 'div[itemprop="price_per_sqft"]',
            raise_exception=False
        )

        price = self.get_element(
            By.CSS_SELECTOR, 'meta[itemprop="price"]',
            raise_exception=False
        )
        if price:
            price = price.get_attribute('content')

        per_box = self.get_text(
            By.CSS_SELECTOR, 'div[itemprop="per_box"]',
            raise_exception=False
        )

        details = self.get_element(
            By.CSS_SELECTOR, 'div#description > div > div',
            raise_exception=False
        )
        if details:
            details = details.get_attribute('innerHTML')

        specs = self.get_element(
            By.CSS_SELECTOR, 'div#additional > div',
            raise_exception=False
        )
        if specs:
            specs = specs.get_attribute('innerHTML')

        return dict(
            url=link,
            image=image,
            name=name,
            sku=sku,
            description=description if description else '',
            price_per_sqft=price_per_sqft if price_per_sqft else '',
            price=price if price else '',
            per_box=per_box if per_box else '',
            details=details if details else '',
            specs=specs if specs else ''
        )

    def send_to_airtable(self, content):
        url = config.HA_AIRTABLE
        content = dict(records=[dict(fields=content)])
        response = requests.post(url, json=content, headers={
            'Authorization': f'Bearer {config.HA_AIRTABLE_KEY}'
        })
        if response.status_code < 200 or response.status_code > 299:
            import pdb
            pdb.set_trace()
