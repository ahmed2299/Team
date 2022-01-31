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


class DrLehnerImmobilienSpider(scrapy.Spider):

    name = "madras"
    start_urls = ['https://www.madrasnieruchomosci.pl/oferty/wynajem/',
                  '']
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
        apartments_urls=response.css('.overlayLink::attr(href)').getall()

        for apartment_url in apartments_urls:
            yield scrapy.Request(url='https://www.madrasnieruchomosci.pl/'+apartment_url,callback=self.populate_item)
            print("apartments_url:",apartment_url)



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

        title1 = response.css('.main-panel span::text').getall()
        title= "".join(title1)
        print("title:",title)


        descri=response.css('#offerDescription p::text').getall()
        description="".join(descri)

        try:
            city= response.css('.location::text').get().strip(",")
            print("city ",city)
        except:
            city="None"
        #
        address1= response.css('.pageTitle span::text').getall()
        address=" ".join(address1).replace("Mieszkanie na wynajem","")
        print("add:",address)

        longitude,latitude=extract_location_from_address(address)
        print("lon",longitude)
        print("lat",latitude)
        zipcode,x,y=extract_location_from_coordinates(longitude,latitude)
        print(zipcode)

        if "Mieszkanie" in title.lower():
            property_type = "apartment"
        else :
            property_type = "house"

        square_meters=int(extract_number_only(str(response.css('.vir_oferta_powierzchnia .propValue::text').get()),thousand_separator,scale_separator))

        room_count=int(extract_number_only(str(response.css('.vir_oferta_iloscpokoi .propValue::text').get()),thousand_separator,scale_separator))
        if room_count==0:
            room_count=1
        bathroom_count=int(extract_number_only(str(response.css('.vir_oferta_ilosclazienek .propValue::text').get()),thousand_separator,scale_separator))
        if bathroom_count==0:
            bathroom_count=1
        if ("pet" not in description.lower()) and ("zwierzę domowe" not in description.lower()):
            pets_allowed = False
        if ('umeblować'.lower() not in description.lower()) and ('furnish' not in description.lower()):
            furnished = False
        if ('garaż' not in description.lower()) and ('garage' not in description.lower()) :
            parking = False

        if ('elevator' not in description.lower()) and ('winda' not in description.lower()) :
            elevator = False

        if ('balcon' not in description.lower()) and ('balkon' not in description.lower()) :
            balcony = False

        if ('terrace' not in description.lower()) and ('taras' not in description.lower()):
            terrace = False

        if ('pool' not in description.lower()) and ('basen' not in description.lower()) :
            swimming_pool = False

        if ('washer' not in description.lower()) and ('pralka' not in description.lower()) :
            washing_machine = False
        if ('dishwasher' not in description.lower()) and ('zmywarka' not in description.lower()):
            dishwasher = False
        #
        currency="PLN"
        images=response.css(".bx-next , #offerGallery img").getall()
        print("images:",images)
        # images=response.css('.bilder-slider img::attr(src)').getall()
        #
        rent= str(response.css("strong::text").getall())
        rent1 = []
        for word in rent.split():
            if word.isdigit():
                rent1.append(int(word))
        rent=int(extract_number_only(str(rent1),thousand_separator,scale_separator))

        print("rent",rent)


        if rent <= 0 and rent > 40000:
            return
        #
        landlord_name = response.css(".agentName::text").get()
        landlord_number = response.css(".agentLandline::text").get()
        landlord_email = response.css(".smallEmail::text").get()
        #
        #
        item_loader.add_value("external_link", response.url) # String
        item_loader.add_value("external_source", self.external_source) # String

        item_loader.add_value("external_id", external_id) # String
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
        item_loader.add_value("floor", floor) # String
        item_loader.add_value("property_type", property_type) # String => ["apartment", "house", "room", "student_apartment", "studio"]
        item_loader.add_value("square_meters", square_meters) # Int
        item_loader.add_value("room_count", room_count) # Int
        item_loader.add_value("bathroom_count", bathroom_count) # Int

        #item_loader.add_value("available_date", available_date) # String => date_format

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
        #
        # item_loader.add_value("water_cost", water_cost) # Int
        # item_loader.add_value("heating_cost", heating_cost) # Int

        item_loader.add_value("energy_label", energy_label) # String

        # LandLord Details

        item_loader.add_value("landlord_name", landlord_name) # String
        item_loader.add_value("landlord_phone", landlord_number) # String
        item_loader.add_value("landlord_email", landlord_email) # String

        self.position += 1
        yield item_loader.load_item()


        # data = {key: [] for key in xpaths}
        # xpaths = {
        #     'external_id': external_id,
        #     'title': title,
        #     'description': description,
        #     'city': '.entry-title::text',
        #     'zipcode': zipcode,
        #     'address': address,
        #     'latitude': latitude,
        #     'longitude': longitude,
        #     'floor': floor,
        #     'rent': rent,
        #     'utilities': utilities,
        #     'currency': currency,
        #     'energy_label': energy_label,
        #     'landlord_name': landlord_name,
        #     'landlord_number': landlord_number,
        #     'landlord_email': landlord_email
        # }






