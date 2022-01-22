# -*- coding: utf-8 -*-
# Author: Mehmet Kurtipek

from scrapy.loader.processors import MapCompose
from scrapy import Spider
from scrapy import Request,FormRequest
from scrapy.selector import Selector
from w3lib.html import remove_tags
from python_spiders.loaders import ListingLoader
import json
from python_spiders.helper import ItemClear
class MySpider(Spider):
    name = 'disher_com_au'
    execution_type='testing'
    country='australia'
    locale='en'
    headers = {
        'authority': 'disher.com.au',
        'content-length': '0',
        'accept': '*/*',
        'origin': 'https://disher.com.au',
        'referer': 'https://disher.com.au/listings?post_type=listings&count=20&orderby=meta_value&meta_key=dateListed&sold=0&saleOrRental=Rental&type=Residential&paged=1&extended=1&minprice=&maxprice=&minbeds=&maxbeds=&minbaths=&maxbaths=&cars=&subcategory=Apartment&order=&externalID=&minlandarea=&maxlandarea=&landareaunit=&minbuildarea=&maxbuildarea=&buildareaunit=',
        'accept-language': 'tr,en;q=0.9'
    }

    def start_requests(self):
        queries = [
            {
                "query": ["Unit","Apartment","Flat",],
                "property_type": "apartment",
            },
            {
                "query": ["House","Townhouse","Villa","DuplexSemi-detached","Terrace",],
                "property_type": "house",
            },
            {
                "query": ["Studio",],
                "property_type": "studio",
            },
        ]
        start_url = "https://disher.com.au/wp-admin/admin-ajax.php?action=get_posts&query%5Bpost_type%5D%5Bvalue%5D=listings&query%5Bcount%5D%5Bvalue%5D=20&query%5Borderby%5D%5Bvalue%5D=meta_value&query%5Bmeta_key%5D%5Bvalue%5D=dateListed&query%5Bsold%5D%5Bvalue%5D=0&query%5BsaleOrRental%5D%5Bvalue%5D=Rental&query%5BsaleOrRental%5D%5Btype%5D=equal&query%5Btype%5D%5Bvalue%5D=Residential&query%5Btype%5D%5Btype%5D=equal&query%5Bextended%5D%5Bvalue%5D=1&query%5Bsubcategory%5D%5Bvalue%5D={}&query%5Bpaged%5D%5Bvalue%5D=1"
        for item in queries:
            for query in item.get("query"):
                yield FormRequest(start_url.format(query),
                            callback=self.parse,
                            headers=self.headers,
                            meta={'property_type': item.get('property_type')})

    # 1. FOLLOWING
    def parse(self, response):

        page = response.meta.get("page", 2)
        seen = False

        data = json.loads(response.body)
        for item in data["data"]["listings"]:
            seen = True
            follow_url = item["url"]
            yield Request(follow_url, callback=self.populate_item, meta={"property_type":response.meta["property_type"],"item":item})

        if page == 2 or seen: 
            f_url = response.url.replace("query%5Bpaged%5D%5Bvalue%5D=" + str(page - 1), "query%5Bpaged%5D%5Bvalue%5D=" + str(page))
            yield FormRequest(f_url, headers=self.headers, callback=self.parse, meta={'property_type':response.meta["property_type"], "page":page+1})
    
    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = ListingLoader(response=response)

        item_loader.add_value("property_type", response.meta["property_type"])
        item_loader.add_value("external_link", response.url)
        ItemClear(response=response, item_loader=item_loader, item_name="external_source", input_value="Disher_Com_PySpider_australia", input_type="VALUE")
        ItemClear(response=response, item_loader=item_loader, item_name="address", input_value="//p[contains(@class,'address')]/text()", input_type="F_XPATH")
        ItemClear(response=response, item_loader=item_loader, item_name="city", input_value="//p[contains(@class,'address')]/text()", input_type="F_XPATH", split_list={",":-1})
        ItemClear(response=response, item_loader=item_loader, item_name="room_count", input_value="//p[contains(@class,'bed')]/text()", input_type="F_XPATH", get_num=True)
        ItemClear(response=response, item_loader=item_loader, item_name="bathroom_count", input_value="//p[contains(@class,'bath')]/text()", input_type="F_XPATH", get_num=True)
        
        item = response.meta.get('item')
        item_loader.add_value("title", item["title"])
        item_loader.add_value("latitude", item["lat"])
        item_loader.add_value("longitude", item["long"])

        rent = item["price"]
        if rent:
            rent = rent.split("$")[-1].lower().split('p')[0].strip().replace(',', '')
            item_loader.add_value("rent", int(float(rent)) * 4)
        item_loader.add_value("currency", 'AUD')
        if "floor" in item["post_content"]:
            floor = item["post_content"].split("floor")[0].strip().split(" ")[-1]
            if "Polis" not in floor and "timber" not in floor:
                item_loader.add_value("floor", floor)

        ItemClear(response=response, item_loader=item_loader, item_name="description", input_value="//div[@class='b-description__text']//text()", input_type="M_XPATH")
        ItemClear(response=response, item_loader=item_loader, item_name="external_id", input_value="//div[@class='section-header'][contains(.,'Key')]//strong[contains(.,'ID')]/following-sibling::text()", input_type="F_XPATH")
        ItemClear(response=response, item_loader=item_loader, item_name="deposit", input_value="//div[@class='section-header'][contains(.,'Key')]//strong[contains(.,'bond')]/following-sibling::text()", input_type="F_XPATH", split_list={"$":1}, replace_list={",":""})
        ItemClear(response=response, item_loader=item_loader, item_name="available_date", input_value="//div[@class='section-header'][contains(.,'Key')]//strong[contains(.,'available')]/text() | //div[@class='section-header'][contains(.,'Key')]//strong[contains(.,'available')]/following-sibling::text()", input_type="M_XPATH", split_list={"available":1})
        ItemClear(response=response, item_loader=item_loader, item_name="square_meters", input_value="//div[@class='section-header'][contains(.,'Key')]//strong[contains(.,'build')]/following-sibling::text()", input_type="F_XPATH", get_num=True, split_list={"m":0})
        ItemClear(response=response, item_loader=item_loader, item_name="parking", input_value="//p[contains(@class,'car')]/text()[.!='0']", input_type="F_XPATH", tf_item=True)
        ItemClear(response=response, item_loader=item_loader, item_name="balcony", input_value="//section[@id='single-listings-content']//li[.='Balcony']/text()", input_type="F_XPATH", tf_item=True)
        ItemClear(response=response, item_loader=item_loader, item_name="dishwasher", input_value="//section[@id='single-listings-content']//li[.='Dishwasher']/text()", input_type="F_XPATH", tf_item=True)
        ItemClear(response=response, item_loader=item_loader, item_name="swimming_pool", input_value="//section[@id='single-listings-content']//li[contains(.,'Pool ')]/text()", input_type="F_XPATH", tf_item=True)
        ItemClear(response=response, item_loader=item_loader, item_name="images", input_value="//div[@id='media-gallery']//@href", input_type="M_XPATH")
        ItemClear(response=response, item_loader=item_loader, item_name="landlord_name", input_value="//h5[contains(@class,'card-title')]/a/text()", input_type="F_XPATH")
        ItemClear(response=response, item_loader=item_loader, item_name="landlord_phone", input_value="//span[contains(@class,'phone-number')]/a/text()", input_type="F_XPATH")
        ItemClear(response=response, item_loader=item_loader, item_name="landlord_email", input_value="//p/a[contains(@href,'mail')]/text()[contains(.,'@')]", input_type="F_XPATH")

        pets = "".join(response.xpath("//div[@class='section-body post-content']/p/text()[contains(.,'pets')]").getall())
        if pets:
            if "no" in pets.lower():
                item_loader.add_value("pets_allowed", False)
            elif "yes" in pets.lower():
                item_loader.add_value("pets_allowed", True)        
        furnished = response.xpath("//section[@id='single-listings-content']//li[contains(.,'Furnished') or contains(.,'furnished')]/text()").get()
        if furnished:
            if "unfurnished" in furnished.lower():
                item_loader.add_value("furnished", False)
            elif "furnished" in furnished.lower():
                item_loader.add_value("furnished", True)  
        yield item_loader.load_item()