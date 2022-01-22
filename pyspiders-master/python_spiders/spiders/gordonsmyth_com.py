# -*- coding: utf-8 -*-
# Author: Mehmet Kurtipek

from scrapy.loader.processors import MapCompose
from scrapy import Spider
from scrapy import Request,FormRequest
from scrapy.selector import Selector
from w3lib.html import remove_tags
from python_spiders.loaders import ListingLoader
import json
import dateparser

class MySpider(Spider):
    name = 'gordonsmyth_com'
    execution_type='testing'
    country='united_kingdom'
    locale='en' 
    thousand_separator = ','
    scale_separator = '.'   

    def start_requests(self):

        start_urls = [
            {
                "url" : [
                    "https://www.gordonsmyth.com/grid?sta=toLet&sta=letAgreed&sta=let&st=rent&pt=residential&stygrp=3",
                ],
                "property_type" : "apartment",
            },
            {
                "url" : [
                    "https://www.gordonsmyth.com/grid?sta=toLet&sta=letAgreed&sta=let&st=rent&pt=residential&stygrp=2",
                ],
                "property_type" : "house"
            },
        ]
        for url in start_urls:
            for item in url.get("url"):
                yield Request(item,
                            callback=self.parse,
                            meta={'property_type': url.get('property_type')})

    # 1. FOLLOWING
    def parse(self, response):

        for item in response.xpath("//div[@class='list-item-content']/h2/a/@href").getall():
            yield Request(response.urljoin(item), callback=self.populate_item, meta={"property_type":response.meta["property_type"]})
        
        next_button = response.xpath("//a[@class='paging-next']/@href").get()
        if next_button: yield Request(response.urljoin(next_button), callback=self.parse, meta={"property_type":response.meta["property_type"]})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = ListingLoader(response=response)

        item_loader.add_value("property_type", response.meta.get('property_type'))
        item_loader.add_value("external_link", response.url)
        item_loader.add_value("external_source", "Gordonsmyth_PySpider_united_kingdom")  
        item_loader.add_value("external_id", response.url.split("/")[-1])        
        item_loader.add_xpath("room_count", "//tr[th[.='Bedrooms']]/td/text()")
        address = " ".join(response.xpath("//h1//text()[normalize-space()]").getall())
        if address:
            item_loader.add_value("title", address.replace("\n","").strip())
            item_loader.add_value("address", address.replace("\n","").strip())
        zipcode = " ".join(response.xpath("//h1//span[@class='addr-postcode']/span/text()").getall())
        if zipcode:
            item_loader.add_value("zipcode", zipcode.strip())
   
        item_loader.add_xpath("city","//h1//span[@class='addr-town']/text()")
        available_date = response.xpath("//tr[th[.='Available From']]/td/text()").get()
        if available_date:
            date_parsed = dateparser.parse(available_date, date_formats=["%d/%m/%Y"])
            if date_parsed:
                item_loader.add_value("available_date", date_parsed.strftime("%Y-%m-%d"))
      
        rent = "".join(response.xpath("//tr[th[.='Rent']]/td//text()").getall()) 
        if rent:
            item_loader.add_value("rent_string", rent)
     
        energy_label = response.xpath("//tr[th[.='EPC Rating']]/td//a/text()[contains(.,'/')]").get()
        if energy_label:
            item_loader.add_value("energy_label", energy_label[0])
  
        description = " ".join(response.xpath("//div[@class='ListingDescr-text']/p//text()").getall()) 
        if description:
            item_loader.add_value("description", description.strip())
    
        item_loader.add_xpath("deposit", "//tr[th[.='Deposit']]/td/text()")
        furnished = response.xpath("//tr[th[.='Furnished']]/td/text()").get()
        if furnished:
            if "unfurnished" in furnished.lower():
                item_loader.add_value("furnished", False)
            elif "furnished" in furnished.lower():
                item_loader.add_value("furnished", True)
        parking = response.xpath("//li[contains(.,'Parking')]//text()").get()
        if parking:
            item_loader.add_value("parking", True)
        elevator = response.xpath("//li[contains(.,'Lift Access')]//text()").get()
        if elevator:
            item_loader.add_value("elevator", True)
        item_loader.add_xpath("latitude", "//meta[@property='og:latitude']/@content")
        item_loader.add_xpath("longitude", "//meta[@property='og:longitude']/@content")
        images = [x for x in response.xpath("//div[@class='slideshow-thumbs']/a/@href").getall()]
        if images:
            item_loader.add_value("images", images)
        item_loader.add_value("landlord_name", "Gordon Smyth Estate Agents")
        item_loader.add_value("landlord_phone", "028 9131 0310")
        item_loader.add_value("landlord_email", "office@gordonsmyth.com")

        yield item_loader.load_item()