# -*- coding: utf-8 -*-
# Author: Fill with the developer's Name
import scrapy
from ..loaders import ListingLoader
import re
from dateutil.parser import parse
from datetime import datetime
from scrapy import Selector
from ..helper import extract_number_only, extract_rent_currency, extract_location_from_address, extract_location_from_coordinates

class ReitelshoferheiderimmobilienohgSpider(scrapy.Spider):
    name = "ReitelshoferHeiderImmobilienOHG"
    start_urls = ['https://www.rhi-immobilien.de/vermietung/']
    allowed_domains = ["rhi-immobilien.de"]
    country = 'germany' # Fill in the Country's name
    locale = 'de' # Fill in the Country's locale, look up the docs if unsure
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
        for listing in response.css("div.box-title a::attr(href)").getall():
            yield scrapy.Request(listing , callback=self.populate_item)

    # 3. SCRAPING level 3
    def populate_item(self, response):
        washing_machine = address = property_type = pets_allowed = balcony = terrace = elevator = external_id = floor = parking = None
        utilities = bathroom_count = available_date = deposit = total_rent = rent = currency = square_meters = landlord_email = landlord_name = landlord_phone = None
        room_count = 1
        property_type = 'apartment'
        external_id = response.css("span.id-area::text").get().split(':')[-1].strip()
        title = response.css("span.header1::text").get().strip()
        if len([x.strip() for x in response.css("div.row").extract() if '<div class="box-title">Objektbeschreibung' in x]) != 0:
            description = re.sub(re.compile('<.*?>'), '\n',re.findall('<div class="box-content">.*?</div>',[x.strip() for x in response.css("div.row").extract() if '<div class="box-title">Objektbeschreibung' in x][0])[0]).strip()
        elif len([x.strip() for x in response.css("div.row").extract() if '<div class="box-title">Lage' in x]) != 0:
            description = re.sub(re.compile('<.*?>'), '\n',re.findall('<div class="box-content">.*?</div>',[x.strip() for x in response.css("div.row").extract() if '<div class="box-title">Lage' in x][0])[0]).strip()
        
        lower_description = description.lower() + ' ' +  title.lower()
        if 'wohnung' not in title.lower() and 'wohnen' not in title.lower():
            return
        if "stellplatz" in lower_description or "garage" in lower_description or "parkhaus" in lower_description or "tiefgarage" in lower_description:
            parking = True
        if 'balkon' in lower_description:
            balcony = True
        if 'aufzug' in lower_description:
            elevator = True
        if 'terrasse' in lower_description:
            terrace = True
        if 'waschmaschine' in lower_description:
            washing_machine = True
            
        keys = response.css("div.box-content td:nth-child(1)::text").getall()
        vals = response.css("div.box-content td:nth-child(2)::text").getall()
        for row in zip(keys, vals):
            key = row[0].strip()
            val = row[1].strip()
            key = key.lower()
            if "kaltmiete" in key:
                rent, currency = extract_rent_currency(val, self.country, ReitelshoferheiderimmobilienohgSpider)
                rent = get_price(val)
            elif "nebenkosten" in key:
                utilities = get_price(val)
            elif "kaution" in key:
                deposit = get_price(val)
            elif "badezimmer" in key:
                bathroom_count = int(float(val.split(',')[0]))
            elif "zimmer" in key:
                room_count = int(float(val.replace(',', '.')))
            elif "wohnfläche" in key:
                square_meters = int(float(extract_number_only(val, thousand_separator='.', scale_separator=',')))
            elif "verfügbar ab" in key:
                if 'sofort' in val.lower():
                    available_date = datetime.now().strftime("%Y-%m-%d")
                elif 'rücksprache' in val.lower() or 'vereinbarung' in val.lower():
                    available_date = None
                elif 'vermietet' in val.lower():
                    return
                else:
                    available_date = parse(val).strftime("%Y-%m-%d")
            elif "objekttyp" in key:
                property_type = val
                if 'wohnung' in property_type.lower():
                    property_type = 'apartment'
                elif 'familienhaus' in property_type.lower():
                    property_type = 'house'
                elif 'souterrain' in property_type.lower():
                    property_type = 'apartment'
                elif 'apartment' in property_type.lower():
                    property_type = 'apartment'
                elif 'dach­geschoss' in property_type.lower():
                    property_type = 'apartment'
                elif 'zimmer' in property_type.lower():
                    property_type = 'room'
                else: return
            elif 'adresse' in key:
                address = val
            elif "etage" in key:
                floor = val.strip()[0]
                floor = None if not floor.isnumeric() else floor
            elif "balkon" in key:
                balcony = True
            elif "warmmiete" in key:
                total_rent, currency = extract_rent_currency(val, self.country, ReitelshoferheiderimmobilienohgSpider)
                total_rent = get_price(val)
                
            elif "stellplatz" in key:
                parking = False if 'nein' in val.lower() else True
            elif "aufzug" in key:
                elevator = True
            elif key.find("terrasse") != -1:
                terrace = True if 'terrasse' in val.lower() else None

        address = Selector(text=[x.strip() for x in response.css("div.column.immo-show-column").extract() if 'Objekt-ID' in x][0]).css("strong::text")[-1].get().strip()
        longitude, latitude = extract_location_from_address(address)
        zipcode, city, address = extract_location_from_coordinates(longitude=longitude, latitude=latitude)
        if address == zipcode:
            address = zipcode + " " + city

        
        images = response.css("div#immo-show-picturebar img::attr(src)").getall()
        floor_plan_images = None
        landlord_name = 'Reitelshöfer + Heider Immobilien oHG'
        landlord_email = 'info@rhi-immobilien.de'
        landlord_phone = '0981-12224'
        item_loader = ListingLoader(response=response)

        # # MetaData
        item_loader.add_value("external_link", response.url) # String
        item_loader.add_value("external_source", self.external_source) # String
        item_loader.add_value("position", self.position) # Int

        item_loader.add_value("external_id", external_id) # String
        item_loader.add_value("title", title) # String
        item_loader.add_value("description", description) # String

        # Property Details
        item_loader.add_value("city", city) # String
        item_loader.add_value("zipcode", zipcode) # String
        item_loader.add_value("address", address) # String
        item_loader.add_value("latitude", str(latitude)) # String
        item_loader.add_value("longitude", str(longitude)) # String
        item_loader.add_value("floor", floor) # String
        item_loader.add_value("property_type", property_type) # String => ["apartment", "house", "room", "student_apartment", "studio"]
        item_loader.add_value("square_meters", square_meters) # Int
        item_loader.add_value("room_count", room_count) # Int
        item_loader.add_value("bathroom_count", bathroom_count) # Int

        item_loader.add_value("available_date", available_date) # String => date_format

        item_loader.add_value("pets_allowed", pets_allowed) # Boolean
        # item_loader.add_value("furnished", furnished) # Boolean
        item_loader.add_value("parking", parking) # Boolean
        item_loader.add_value("elevator", elevator) # Boolean
        item_loader.add_value("balcony", balcony) # Boolean
        item_loader.add_value("terrace", terrace) # Boolean
        # item_loader.add_value("swimming_pool", swimming_pool) # Boolean
        item_loader.add_value("washing_machine", washing_machine) # Boolean
        # item_loader.add_value("dishwasher", dishwasher) # Boolean

        # Images
        item_loader.add_value("images", images) # Array
        item_loader.add_value("external_images_count", len(images)) # Int
        item_loader.add_value("floor_plan_images", floor_plan_images) # Array

        # Monetary Status
        item_loader.add_value("rent", rent) # Int
        item_loader.add_value("deposit", deposit) # Int
        # item_loader.add_value("prepaid_rent", prepaid_rent) # Int
        item_loader.add_value("utilities", utilities) # Int
        item_loader.add_value("currency", currency) # String

        # item_loader.add_value("water_cost", water_cost) # Int
        # item_loader.add_value("heating_cost", heating_cost) # Int

        # item_loader.add_value("energy_label", energy_label) # String

        # LandLord Details
        item_loader.add_value("landlord_name", landlord_name) # String
        item_loader.add_value("landlord_phone", landlord_phone) # String
        item_loader.add_value("landlord_email", landlord_email) # String

        self.position += 1
        yield item_loader.load_item()


def get_price(val):
    v = int(float(extract_number_only(val, thousand_separator=',', scale_separator='.')))
    v2 = int(float(extract_number_only(val, thousand_separator='.', scale_separator=',')))
    price = min(v, v2)
    if price < 10:
        price = max(v, v2)
    return price
