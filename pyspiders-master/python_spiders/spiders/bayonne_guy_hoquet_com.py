# -*- coding: utf-8 -*-
# Author: Mehmet Kurtipek


from scrapy.loader.processors import MapCompose
from scrapy import Spider
from scrapy import Request,FormRequest
from scrapy.selector import Selector
from w3lib.html import remove_tags
from python_spiders.loaders import ListingLoader
import json
from  geopy.geocoders import Nominatim

class MySpider(Spider):
    name = 'bayonne_guy_hoquet_com'
    execution_type='testing'
    country='france'
    locale='fr'

    headers = {
        'content-type': "application/json; charset=utf-8",
        'accept': "*/*",
        'accept-encoding': "gzip, deflate, br",
        'accept-language': "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        'referer': "https://bayonne.guy-hoquet.com/biens/result",
        'sec-fetch-dest': "empty",
        'sec-fetch-mode': "cors",
        'sec-fetch-site': "same-origin",
        'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36",
        'x-csrf-token': "lLQU3BfyCHGGnGYStFddhV4BTZWSRSsyJEm3pHDm",
        'x-requested-with': "XMLHttpRequest",
        'cache-control': "no-cache",
    }
    

    def start_requests(self):
        start_urls = [
           
            {"url": "https://bayonne.guy-hoquet.com/biens/result?1&templates%5B%5D=properties&p=1&t=&filters%5B10%5D%5B%5D=2&filters%5B30%5D%5B0%5D%5B%5D=appartement&with_markers=false&_=1603888257465", "property_type": "apartment"},
	        {"url": "https://bayonne.guy-hoquet.com/biens/result?1&templates%5B%5D=properties&p=1&t=&filters%5B10%5D%5B%5D=2&filters%5B30%5D%5B0%5D%5B%5D=maison&with_markers=false&_=1603888257467", "property_type": "house"},
        ] 
        for url in start_urls:
            yield Request(url=url.get('url'),
                            headers=self.headers,
                            callback=self.parse,
                            meta={'property_type': url.get('property_type')})

    # 1. FOLLOWING
    def parse(self, response):
        
        data=json.loads(response.body)
        data_html = data["templates"]["properties"]
        sel = Selector(text=data_html, type="html")

        data_url=sel.xpath("//div[contains(@class,'resultat-item')]/a/@href").extract()
        for item in data_url:
            follow_url = response.urljoin(item)
            yield Request(follow_url, callback=self.populate_item ,dont_filter=True, meta={'property_type': response.meta.get('property_type')})
        
           
    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = ListingLoader(response=response)

        desc="".join(response.xpath("//span[@class='description-more']/text()").getall())
        if "pascale rocheron" in desc.lower():
            return
        
        item_loader.add_value("external_source", "Bayonne_guy_hoquet_PySpider_"+ self.country + "_" + self.locale)
        
        item_loader.add_value("external_link", response.url)
        item_loader.add_value("property_type", response.meta.get('property_type'))
        item_loader.add_xpath("title", "//div/h1/text()")
        
        
        rent="".join(response.xpath("//div[@class='price']/text()").getall())
        if rent:
            item_loader.add_value("rent_string", rent)
        
        square_meters="".join(response.xpath(
            "//div[@class='biens-list']//div/i[contains(@class,'ico scale')]/parent::div//text()").getall())
        if square_meters:
            item_loader.add_value("square_meters", square_meters.split('m²')[0].strip())
        
        room_count="".join(response.xpath(
            "//div[@class='biens-list']//div/i[contains(@class,'ico room')]/parent::div//text()").getall())
        if room_count:
            item_loader.add_value("room_count", room_count.strip().split(' ')[0])
        
        latitude_longitude = response.xpath("//script[@type='text/javascript'][contains(.,'Lat')]/text()").get()
        if latitude_longitude:
                latitude = latitude_longitude.split(" Lat = '")[1].split("';")[0]
                longitude = latitude_longitude.split("Lng = '")[1].split("';")[0]
                geolocator = Nominatim(user_agent=response.url)
                try:
                    location = geolocator.reverse(latitude + ', ' + longitude, timeout=None)
                    if location.address:
                            address = location.address
                            if location.raw['address']['postcode']:
                                zipcode = location.raw['address']['postcode']
                except:
                    address = None
                    zipcode = None
                if address:
                    item_loader.add_value("address", address)
                    item_loader.add_value("zipcode", zipcode)
                    item_loader.add_value("longitude", longitude)
                    item_loader.add_value("latitude", latitude)
           
        external_id=response.xpath("//div[@class='code']/text()").get()
        if external_id:
            item_loader.add_value("external_id", external_id.split(":")[1].strip())

        desc="".join(response.xpath("//span[@class='description-more']/text()").getall())
        if desc:
            item_loader.add_value("description", desc.strip())
        
        floor=response.xpath("//div[@class='horaires-item']/div/div[contains(.,'Etage')]//following-sibling::div/text()").get()
        if floor:
            item_loader.add_value("floor", floor.strip())
            
        images=[x for x in response.xpath("//div[@class='de-biens-slider']/div/@href").getall()]
        if images:
            item_loader.add_value("images", images)
            item_loader.add_value("external_images_count", str(len(images)))
        
        utilties=response.xpath(
            "//div[@class='horaires-item']/div/div[contains(.,'Charge')]//following-sibling::div/text()").get()
        if utilties:
            item_loader.add_value("utilities", utilties.split('€')[0].strip())
        

        yield item_loader.load_item()