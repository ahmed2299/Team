# -*- coding: utf-8 -*-
# Author: Fill with the developer's Name
import scrapy
from ..loaders import ListingLoader

from scrapy.loader import ItemLoader
from ..items import ListingItem

from ..helper import *
import re


class MichaelsImmobilienSpider(scrapy.Spider):
    name = "michaels_immobilien"
    start_urls = ['https://www.michaels-immobilien.de/wohnungen-miete.html?fbclid=IwAR2_7ap5bL_Ldwmtb0e2EMsaYy_DfPrhqoOd2bKdMOxd_lCBe8NEg8Df3JE',
                  'https://www.michaels-immobilien.de/wohnungen-miete.html?&kategoriefilter=miete-wohnungen&sort=sorting&perPage=3&page=2',
                  'https://www.michaels-immobilien.de/wohnungen-miete.html?&kategoriefilter=miete-wohnungen&sort=sorting&perPage=3&page=3']
    allowed_domains = ["de"]
    country = 'germany'  # Fill in the Country's name
    locale = 'de'  # Fill in the Country's locale, look up the docs if unsure
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
        url = 'https://www.michaels-immobilien.de/'
        apartments_urls = response.css('.object_button a::attr(href)').getall()
        try:
            for apartment_url in apartments_urls:
                yield scrapy.Request(url=url + apartment_url, callback=self.populate_item)
        except:
            pass

    # 3. SCRAPING level 3
    def populate_item(self, response):
        item_loader = ListingLoader(response=response)

        # Enforces rent between 0 and 40,000 please dont delete these lines

        # manipulation of span list
        # # MetaData
        title = response.css('h1::text').get()
        # external_id = response.xpath('//div[@class="object_base"]/div/div[2]/text()').get()
        description = response.xpath('/html/body/div[1]/div[2]/div/div/div/div/div/div/div[9]/div[2]/p/text()').get()
        #
        # ###################################
        # # # Property Details
        city = response.xpath('//div[@class="fieldLine detail_region"]/div/span[2]/text()').get()
        zipcode = response.xpath('//div[@class="fieldLine detail_region"]/div/span[1]/text()').get()
        address = ' '.join(
            response.xpath('//div[@class="fieldLine detail_street"]/div[2]/span/text()').getall())  # String
        longitude, latitude = extract_location_from_address(address)
        property_type="apartment"
        room_count = int(float(extract_number_only(str(response.xpath('/html/body/div[1]/div[2]/div/div/div/div/div/div/div[8]/div[2]/text()').get()),'.',',')))
        if room_count==0:
            room_count=1
        bathroom_count = 1
        square_meters = extract_number_only(response.xpath('/html/body/div[1]/div[2]/div/div/div/div/div/div/div[7]/div[2]/text()').get())  # Int
        ###################################
        parking = True
        elevator = True
        balcony = True
        washing_machine = True
        dishwasher = True
        terrace = True
        furnished = True
        pets_allowed = True
        swimming_pool = 1

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
        # ############################################
        # # # Images
        images = response.css('.object_images img::attr(src)').getall()
        url1 = "https://www.michaels-immobilien.de/"
        for i in range(0, len(images)):
            images[i] = url1 + images[i]
        # ############################################
        # # # Monetary Status
        rent = int(float(extract_number_only(response.xpath('/html/body/div[1]/div[2]/div/div/div/div/div/div/div[19]/div[2]/text()').get(),'.',',')))
        if rent==0:
            rent=1
        deposit = int(float(extract_number_only(response.xpath('/html/body/div[1]/div[2]/div/div/div/div/div/div/div[22]/div[2]/text()').get(),'.',',')))
        utilities = int(float(extract_number_only(response.xpath('/html/body/div[1]/div[2]/div/div/div/div/div/div/div[20]/div[2]/text()').get(),'.',',')))
        currency = "EUR"
        energy_label = response.xpath('/html/body/div[1]/div[2]/div/div/div/div/div/div/div[11]/div[2]/text()').get()  # String
        # ######################################
        # # # LandLord Details
        landlord_number = '03435922562'
        landlord_name = 'Frau Jennifer Scheffler'
        landlord_email = 'https://www.facebook.com/michaels.immobilien/'
        #
        if int(rent) <= 0 and int(rent) > 40000:
            return

        # # MetaData
        item_loader.add_value("external_link", response.url)  # String
        item_loader.add_value("external_source", self.external_source)  # String

        # item_loader.add_value("external_id", external_id) # String
        item_loader.add_value("position", self.position)  # Int
        item_loader.add_value("title", title) # String
        item_loader.add_value("description", description) # String

        # # Property Details
        item_loader.add_value("city", city) # String
        item_loader.add_value("zipcode", zipcode) # String
        item_loader.add_value("address", address) # String
        item_loader.add_value("latitude", latitude) # String
        item_loader.add_value("longitude", longitude) # String
        # item_loader.add_value("floor", floor) # String
        item_loader.add_value("property_type", property_type) # String => ["apartment", "house", "room", "student_apartment", "studio"]
        item_loader.add_value("square_meters", square_meters) # Int
        item_loader.add_value("room_count", room_count) # Int
        item_loader.add_value("bathroom_count", bathroom_count) # Int

        # item_loader.add_value("available_date", available_date) # String => date_format

        item_loader.add_value("pets_allowed", pets_allowed) # Boolean
        item_loader.add_value("furnished", furnished) # Boolean
        item_loader.add_value("parking", parking) # Boolean
        item_loader.add_value("elevator", elevator) # Boolean
        item_loader.add_value("balcony", balcony) # Boolean
        item_loader.add_value("terrace", terrace) # Boolean
        item_loader.add_value("swimming_pool", swimming_pool) # Boolean
        item_loader.add_value("washing_machine", washing_machine) # Boolean
        item_loader.add_value("dishwasher", dishwasher) # Boolean

        # # Images
        item_loader.add_value("images", images) # Array
        item_loader.add_value("external_images_count", len(images)) # Int
        # item_loader.add_value("floor_plan_images", floor_plan_images) # Array

        # # Monetary Status
        item_loader.add_value("rent", rent) # Int
        item_loader.add_value("deposit", deposit) # Int
        # item_loader.add_value("prepaid_rent", prepaid_rent) # Int
        item_loader.add_value("utilities", utilities) # Int
        item_loader.add_value("currency", currency) # String

        # item_loader.add_value("water_cost", water_cost) # Int
        # item_loader.add_value("heating_cost", heating_cost) # Int

        item_loader.add_value("energy_label", energy_label) # String

        # # LandLord Details
        item_loader.add_value("landlord_name", landlord_name) # String
        item_loader.add_value("landlord_phone", landlord_number) # String
        item_loader.add_value("landlord_email", landlord_email) # String

        self.position += 1
        yield item_loader.load_item()