# -*- coding: utf-8 -*-
# Author: Fill with the developer's Name
import scrapy
from ..loaders import ListingLoader

from scrapy.loader import ItemLoader
from ..items import ListingItem

from ..helper import *
import re
import string

class RzeszowskieNieruchomosciSpider(scrapy.Spider):
    name = "rzeszowskie_nieruchomosci"
    start_urls = ['https://rzeszowskie-nieruchomosci.pl/wyszukiwarka/&typ=domy&rodzaj=wynajem',
                  'https://rzeszowskie-nieruchomosci.pl/wyszukiwarka/&typ=mieszkania&rodzaj=wynajem']
    # allowed_domains = ["en"]
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
        url = 'https://rzeszowskie-nieruchomosci.pl'
        apartments_urls = response.css('.offer__link::attr(href)').getall()
        try:
            for apartment_url in apartments_urls:
                print("apartment_url:",apartment_url)
                yield scrapy.Request(url='https://rzeszowskie-nieruchomosci.pl/' + apartment_url, callback=self.populate_item)
        except:
            pass

    # 3. SCRAPING level 3
    def populate_item(self, response):
        item_loader = ListingLoader(response=response)

        # Enforces rent between 0 and 40,000 please dont delete these lines

        # manipulation of span list
        # # MetaData
        # is_rent = response.xpath("/html/body/main/section[2]/div/div[1]/span[2]/text()").get().split('-')[1]
        # if 'wynajem' not in is_rent:
        #     return

        title = response.xpath("/html/body/main/section[2]/div/div[1]/h2/text()").get()
        print("title",title)
        description1 = response.css(".text-box p::text").getall()
        description="".join(description1)
        print(description)

        # ###################################
        # # # Property Details
        # props = response.xpath("/html/body/main/section[3]/div/div/ul[2]/li/span/text()").getall()
        # balcony = True
        # floor = '1'
        # for i in range(0, len(props)):
        #     if 'Piętro' in props[i]:
        #         floor = props[i + 1]
        #     if 'Balkon' in props[i]:
        #         balcony = props[i + 1]
        #
        # city = response.xpath('//div[@class="fieldLine detail_region"]/div/span[2]/text()').get()
        city=response.css(".description__place::text").get().split()[0]
        print("city:",city)
        address1 = response.css(".description__place::text").get().split()  # String
        address = " ".join(address1).replace(",", "")
        print("address:", address)
        longitude, latitude = extract_location_from_address(address)
        print("lon",longitude)
        print("lat",latitude)
        zipcode,x,y=extract_location_from_coordinates(longitude,latitude)
        print("zipcode",zipcode)
        property_type = response.css(".description__info::text").get()
        room = response.xpath("/html/body/main/section[3]/div/div/ul[2]/li[1]/span[1]/text()").get()
        room2 = response.xpath("/html/body/main/section[2]/div/div[1]/p/span[1]/text()").get()
        room_count = None
        if 'pokoi' in room:
            room_count = int(response.xpath("/html/body/main/section[3]/div/div/ul[2]/li[1]/span[2]/text()").get())
        if room_count is None and 'pokoje' in room2:
            room_count = extract_number_only(response.xpath("/html/body/main/section[2]/div/div[1]/p/span[1]/text()").get())
        print("room_count:",room_count)
        bathroom_count = 1
        square_meters = int(float(extract_number_only(str(response.xpath("/html/body/main/section[3]/div/div/ul[1]/li[4]/span[2]/text()").get())))) # Int
        if square_meters==0:
            square_meters=1
        print("square_meters",square_meters)
        # ###################################
        balcony=True
        parking = True
        elevator = True
        washing_machine = True
        dishwasher = True
        terrace = True
        furnished = True
        pets_allowed = True
        swimming_pool = True
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
        images = response.xpath("/html/body/main/section[2]/div/div[2]/ul[1]/li/a/picture/img/@src").getall()

        url1 = "https://rzeszowskie-nieruchomosci.pl"
        for i in range(0, len(images)):
            images[i] = url1 + images[i]
        print("image :", images)
        # ############################################
        # # # Monetary Status
        rent = int(float(extract_number_only(response.xpath('/html/body/main/section[2]/div/div[1]/span[3]/b/text()').get().replace(" ",""))))
        print("rent:",rent)
        currency = "PLN"
        # ######################################
        # # # LandLord Details
        landlord_number = response.xpath("/html/body/main/section[3]/div/aside/div/a[1]/b/text()").get()
        landlord_name = response.xpath("/html/body/main/section[3]/div/aside/div/span/text()").get()
        landlord_email= response.css(".aside__email span::text").get()
        external_id=response.xpath("/html/body/main/section[3]/div/div/ul[1]/li[1]/span[2]/text()").get()

        if rent <= 0 and rent > 40000:
            return

        # # MetaData
        item_loader.add_value("external_link", response.url)  # String
        item_loader.add_value("external_source", self.external_source)  # String

        item_loader.add_value("external_id", external_id) # String
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
        # item_loader.add_value("deposit", deposit) # Int
        # item_loader.add_value("prepaid_rent", prepaid_rent) # Int
        # item_loader.add_value("utilities", utilities) # Int
        item_loader.add_value("currency", currency) # String

        # item_loader.add_value("water_cost", water_cost) # Int
        # item_loader.add_value("heating_cost", heating_cost) # Int

        # item_loader.add_value("energy_label", energy_label) # String

        # # LandLord Details
        item_loader.add_value("landlord_name", landlord_name) # String
        item_loader.add_value("landlord_phone", landlord_number) # String
        item_loader.add_value("landlord_email", landlord_email) # String

        self.position += 1
        yield item_loader.load_item()