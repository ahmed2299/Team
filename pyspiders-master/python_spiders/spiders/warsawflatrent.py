# -*- coding: utf-8 -*-
# Author: Ahmed Hossam
import scrapy

from ..loaders import ListingLoader
from ..helper import *
import re
import json

from scrapy.loader import ItemLoader
from ..items import ListingItem
import string


class WarsawflatrentSpider(scrapy.Spider):
    name = "warsawflatrent"
    start_urls = ['https://warsawflatrent.com/?fbclid=IwAR2g3OE9PJXhb6voLSv-nxSjTODc0BQfgxz8ONk9t4l8d9CVzlDfWz-Hdgk']
    #allowed_domains = ["de"]
    country = 'poland' # Fill in the Country's name
    locale = 'pl' # Fill in the Country's locale, look up the docs if unsure
    external_source = "{}_PySpider_{}_{}".format(
        name.capitalize(), country, locale)
    execution_type = 'testing'

    position = 1

    # 1. SCRAPING level 1
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse)

    # 2. SCRAPING level 2
    def parse(self, response, **kwargs):
        apartments_urls=response.css('.category-rent a::attr(href)').getall()

        for apartment_url in apartments_urls:
            yield scrapy.Request(url=apartment_url,callback=self.populate_item)

    # 3. SCRAPING level 3
    def populate_item(self, response):
        item_loader = ListingLoader(response=response)

        description = ""
        thousand_separator = '.'
        scale_separator = ','
        room_count = None
        bathroom_count = None
        floor = None
        parking = True
        elevator = True
        balcony = True
        washing_machine = True
        dishwasher = True
        utilities = None
        terrace = True
        furnished = True
        property_type = None
        energy_label = None
        deposit = None
        available = None
        pets_allowed = True
        square_meters = None
        swimming_pool = True
        external_id = None
        rent = None
        thousand_separator = '.'
        scale_separator = ','
        # # # MetaData
        title = response.css('.entry-title::text').get()

        descri = str(response.css('.entry-content span,p::text').getall())
        text_clean = "".join([i for i in descri if i not in string.punctuation])
        edit = str(text_clean)
        un = ['span', 'title', 'class', 'chopin', 'strong', 'br', 'classtlidtranslation', 'translation',
              'langenstrongspan', '2018']
        edit1 = edit.split()
        resultwords = [word for word in edit1 if word.lower() not in un]
        description = ' '.join(resultwords)

        try:
            city = response.css('.entry-title::text').get().split('–')[1]
            # print("city ", city)
        except:
            city = "None"
        try:
            address = str(response.css('.entry-title::text').get()).split('–')[1]
        except:
            address='Mokotów Cybernetyki 17'
        longitude, latitude = extract_location_from_address(address)

        zipcode, x, y = extract_location_from_coordinates(longitude, latitude)
        property_type = "apartment"
        try:
            square_meters = int(extract_number_only(str(response.css('.translation::text').getall()[1].split(":")[1].split('m')[0].strip(' ')), thousand_separator,scale_separator))
        except:
            square_meters=1
        room_count = int(extract_number_only(str(response.xpath('//div[@class="flaechen"]/table/tbody/tr[3]/td[2]/text()').extract()),thousand_separator, scale_separator))
        print('room count=',room_count)
        if room_count == 0:
            room_count = 1
        bathroom_count = int(extract_number_only(str(response.xpath('//div[@class="flaechen"]/table/tbody/tr[4]/td[2]/text()').extract()),thousand_separator, scale_separator))
        print('bathroom count=',bathroom_count)
        if bathroom_count == 0:
            bathroom_count = 1

        if ("pet" not in description.lower()) and ("haustiere" not in description.lower()):
            pets_allowed = False
        if ('MÖBLIERTES'.lower() not in description.lower()) and ('furnish' not in description.lower()):
            furnished = False
        if ('parking' not in description.lower()) and ('garage' not in description.lower()) and \
                ('parcheggio' not in description.lower()) and ('stellplatz' not in description.lower()):
            parking = False

        if ('elevator' not in description.lower()) and ('aufzug' not in description.lower()) and \
                ('ascenseur' not in description.lower()) and ('lift' not in description.lower()) and \
                ('aufzüg' not in description.lower()) and ('fahrstuhl' not in description.lower()):
            elevator = False

        if ('balcon' not in description.lower()) and ('balkon' not in description.lower()) and (
                'balcony' not in description.lower()):
            balcony = False

        if ('terrace' not in description.lower()) and ('terrazz' not in description.lower()) \
                and ('terras' not in description.lower()) and ('terrass' not in description.lower()):
            terrace = False

        if ('pool' not in description.lower()) and ('piscine' not in description.lower()) \
                and ('schwimmbad' not in description.lower()):
            swimming_pool = False

        if ('washer' not in description.lower()) and ('laundry' not in description.lower()) \
                and ('washing_machine' not in description.lower()) and ('waschmaschine' not in description.lower()) \
                and ('laveuse' not in description.lower()) and ('Wasch'.lower() not in description.lower()):
            washing_machine = False
        if ('dishwasher' not in description.lower()) and ('geschirrspüler' not in description.lower()) \
                and ('lave-vaiselle' not in description.lower()) and ('lave vaiselle' not in description.lower()):
            dishwasher = False
        currency = "PLN"
        images = response.css(".size-medium ,.wp-post-image").getall()

        rents = description
        numbers = []
        for word in rents.split():
            if word.isdigit():
                numbers.append(int(word))
        rent = numbers[-1]

        if rent <= 0 and rent > 40000:
            return
        landlord_name = "warsawflatrent."
        landlord_number = "+48 690 888 298"
        landlord_email = "office@warsawflatrent.com"
        item_loader.add_value("external_link", response.url)  # String
        item_loader.add_value("external_source", self.external_source)  # String

        # item_loader.add_value("external_id", external_id)  # String
        item_loader.add_value("position", self.position)  # Int
        item_loader.add_value("title", title)  # String
        item_loader.add_value("description", description)  # String
        # #
        # # # # Property Details
        item_loader.add_value("city", city)  # String
        item_loader.add_value("zipcode", zipcode)  # String
        item_loader.add_value("address", address)  # String
        item_loader.add_value("latitude", latitude)  # String
        item_loader.add_value("longitude", longitude)  # String
        # item_loader.add_value("floor", floor)  # String
        item_loader.add_value("property_type", property_type)  # String => ["apartment", "house", "room", "student_apartment", "studio"]
        item_loader.add_value("square_meters", square_meters)  # Int
        item_loader.add_value("room_count", room_count)  # Int
        item_loader.add_value("bathroom_count", bathroom_count)  # Int
        #
        # # item_loader.add_value("available_date", available_date) # String => date_format
        #
        item_loader.add_value("pets_allowed", pets_allowed)  # Boolean
        item_loader.add_value("furnished", furnished)  # Boolean
        item_loader.add_value("parking", parking)  # Boolean
        item_loader.add_value("elevator", elevator)  # Boolean
        item_loader.add_value("balcony", balcony)  # Boolean
        item_loader.add_value("terrace", terrace)  # Boolean
        item_loader.add_value("swimming_pool", swimming_pool)  # Boolean
        item_loader.add_value("washing_machine", washing_machine)  # Boolean
        item_loader.add_value("dishwasher", dishwasher)  # Boolean
        #
        # # # Images
        item_loader.add_value("images", images)  # Array
        item_loader.add_value("external_images_count", len(images))  # Int
        # # item_loader.add_value("floor_plan_images", floor_plan_images) # Array
        #
        # # # Monetary Status
        item_loader.add_value("rent", rent)  # Int
        # item_loader.add_value("deposit", deposit)  # Int
        # # item_loader.add_value("prepaid_rent", prepaid_rent) # Int
        # item_loader.add_value("utilities", utilities)  # Int
        item_loader.add_value("currency", currency)  # String
        # #
        # # item_loader.add_value("water_cost", water_cost) # Int
        # # item_loader.add_value("heating_cost", heating_cost) # Int
        #
        # item_loader.add_value("energy_label", energy_label)  # String
        #
        # # LandLord Details
        #
        item_loader.add_value("landlord_name", landlord_name)  # String
        item_loader.add_value("landlord_phone", landlord_number)  # String
        item_loader.add_value("landlord_email", landlord_email)  # String

        self.position += 1
        yield item_loader.load_item()

