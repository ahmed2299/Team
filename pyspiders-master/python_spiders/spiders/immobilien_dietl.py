import scrapy

from ..loaders import ListingLoader
from ..helper import *
import re
import json

from scrapy.loader import ItemLoader
from ..items import ListingItem


class ImmobilienDietlSpider(scrapy.Spider):
    name = 'immobilien_dietl'
    # allowed_domains = ['https://www.immobilien-dietl.de/mieten']
    start_urls = ['https://www.makler24.com/immobilien-vermarktungsart/miete/']
    country = 'germany'  # Fill in the Country's name
    locale = 'de'
    external_source = "{}_PySpider_{}_{}".format(
        name.capitalize(), country, locale)
    execution_type = 'testing'

    position = 1

    # 1. SCRAPING level 1
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response, **kwargs):
        apartments_urls=response.css(".property-title a::attr(href)").getall()

        for apartment_url in apartments_urls:
            yield scrapy.Request(url=apartment_url,callback=self.populate_item)

    # 3. SCRAPING level 3
    def populate_item(self, response):


        item_loader = ListingLoader(response=response)


        # # Enforces rent between 0 and 40,000 please dont delete these lines
        description = ""
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
        swimming_pool = 1
        external_id = None
        rent = None
        thousand_separator = '.'
        scale_separator = ','

        title=response.css(".property-title::text").get()
        description= response.xpath("/html/body/div[1]/div[4]/div[3]/div[2]/div/div[6]/div[2]/div[2]/p/text()").extract()
        desc=""
        for i in description:
            desc+=i
        description=desc
        city= str(response.xpath("/html/body/div[1]/div[4]/div[3]/div[2]/div/div[1]/h2/text()").extract()[0]).split(',')[0].split(' ')[1]
        rent = response.css('.list-group-item:nth-child(2) .col-sm-7::text').get()
        rent = int(extract_number_only(rent, '.', ','))
        landlord_number = '0 49 41 - 97 57 - 0'
        landlord_email = 'info@makler24.com'
        landlord_name = 'Harms & Harms'
        currency = "EUR"
        address=str(response.xpath("/html/body/div[1]/div[4]/div[3]/div[2]/div/div[1]/h2/text()").extract()[0]).split(',')[0]
        longitude, latitude = extract_location_from_address(address)
        zipcode,x,y=extract_location_from_coordinates(longitude,latitude)
        if "wohnung" in description.lower():
            property_type = "apartment"
        elif "haus" in description.lower() or "Haushalt" in description.lower() or "kammer" in description.lower() or "parlament" in description.lower():
            property_type = "house"
        elif "zimmer" in description.lower() or "raum" in description.lower() or "platz" in description.lower() or "saal" in description.lower() or "stube" in description.lower() or "kammer" in description.lower():
            property_type = "room"
        elif "studio" in description.lower() or "atelier" in description.lower() or "werkstatt" in description.lower():
            property_type = "studio"
        else:
            return
        square_meters= int(extract_number_only(str(response.xpath('/html/body/div[1]/div[4]/div[3]/div[2]/div/div[3]/div/ul/li[7]/div/div[2]/text()').extract()),thousand_separator,scale_separator))
        if square_meters==0:
            square_meters=1
        room_count=1
        bathroom_count=1
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

        # available_date = response.css(".list-group-item:nth-child(4) .col-sm-7::text").get()
        images=response.css('.rsThumbsArrowRight , img::attr(src)').getall()
        print(len(images))
        if int(rent) <= 0 and int(rent) > 40000:
            return

        # # # MetaData
        item_loader.add_value("external_link", response.url) # String
        item_loader.add_value("external_source", self.external_source) # String
        #
        # #item_loader.add_value("external_id", external_id) # String
        item_loader.add_value("position", self.position) # Int
        item_loader.add_value("title", title) # String
        item_loader.add_value("description", description) # String
        #
        # # # Property Details
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
        #
        # item_loader.add_value("available_date", available_date) # String => date_format
        #
        item_loader.add_value("pets_allowed", pets_allowed) # Boolean
        item_loader.add_value("furnished", furnished) # Boolean
        item_loader.add_value("parking", parking) # Boolean
        item_loader.add_value("elevator", elevator) # Boolean
        item_loader.add_value("balcony", balcony) # Boolean
        item_loader.add_value("terrace", terrace) # Boolean
        item_loader.add_value("swimming_pool", swimming_pool) # Boolean
        item_loader.add_value("washing_machine", washing_machine) # Boolean
        item_loader.add_value("dishwasher", dishwasher) # Boolean
        #
        # # # Images
        item_loader.add_value("images", images) # Array
        item_loader.add_value("external_images_count", len(images)) # Int
        item_loader.add_value("floor_plan_images", images) # Array
        #
        # # # Monetary Status
        item_loader.add_value("rent", rent) # Int
        # #item_loader.add_value("deposit", deposit) # Int
        # #item_loader.add_value("prepaid_rent", prepaid_rent) # Int
        # #item_loader.add_value("utilities", utilities) # Int
        item_loader.add_value("currency", currency) # String
        #
        # #item_loader.add_value("water_cost", water_cost) # Int
        # #item_loader.add_value("heating_cost", heating_cost) # Int
        #
        # #item_loader.add_value("energy_label", energy_label) # String
        #
        # # # LandLord Details
        item_loader.add_value("landlord_name", landlord_name) # String
        item_loader.add_value("landlord_phone", landlord_number) # String
        item_loader.add_value("landlord_email", landlord_email) # String

        self.position += 1
        yield item_loader.load_item()