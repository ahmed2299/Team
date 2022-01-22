# -*- coding: utf-8 -*-
# Author: Mohamed Zakaria

import re
import math

from scrapy import Spider, Request
from python_spiders.loaders import ListingLoader
from python_spiders.helper import extract_location_from_address, extract_location_from_coordinates, description_cleaner

class Leipzig_estate_deSpider(Spider):
    name = 'leipzig_estate_de'
    country='germany'
    locale='de' 
    external_source = "{}_PySpider_{}_{}".format(name.capitalize(), country, locale)
    execution_type='testing'
    allowed_domains = ["www.leipzig-estate.de"]
    start_urls = ["https://www.leipzig-estate.de/immobilien.xhtml?f%5B6923-35%5D=0&f%5B6923-33%5D=0&f%5B6923-2%5D=miete&f%5B6923-3%5D=&f%5B6923-39%5D=&f%5B6923-5%5D=&f%5B6923-6%5D=&f%5B6923-7%5D=&f%5B6923-8%5D=&f%5B6923-41%5D=&f%5B6923-43%5D="]
    position = 1
    visited_pages = {}

    def parse(self, response):
        for url in response.css("div.image a::attr(href)").getall():
            yield Request(response.urljoin(url), callback=self.populate_item, dont_filter = True)
        if(self.visited_pages.get(response.url)):
            return
        
        self.visited_pages[response.url] = response.url


        next_page = response.css("a:contains('»')::attr(href)").get()
        if (next_page):
            yield response.follow(response.urljoin(next_page), callback=self.parse, dont_filter = True)        

    def populate_item(self, response):
        
        property_type = "apartment"

        title = response.css("div.detail h2::text").get()
        lowered_title = title.lower()
        if(
            "gewerbe" in lowered_title
            or "gewerbefläche" in lowered_title
            or "büro" in lowered_title
            or "praxisflächen" in lowered_title
            or "ladenlokal" in lowered_title
            or "arbeiten" in lowered_title 
            or "gewerbeeinheit" in lowered_title
            or "vermietet" in lowered_title
            or "stellplatz" in lowered_title
            or "stellplätze" in lowered_title
            or "garage" in lowered_title
            or "restaurant" in lowered_title
            or "lager" in lowered_title
            or "einzelhandel" in lowered_title
            or "sonstige" in lowered_title
            or "grundstück" in lowered_title
        ):
            return

        type_of_use = response.css("td:contains('Nutzungsart') + td span::text").get()
        lowered_type_of_use = type_of_use.lower()
        if(
            "gewerbe" in lowered_type_of_use
            or "gewerbefläche" in lowered_type_of_use
            or "büro" in lowered_type_of_use
            or "praxisflächen" in lowered_type_of_use
            or "ladenlokal" in lowered_type_of_use
            or "arbeiten" in lowered_type_of_use 
            or "gewerbeeinheit" in lowered_type_of_use
            or "vermietet" in lowered_type_of_use
            or "stellplatz" in lowered_type_of_use
            or "stellplätze" in lowered_type_of_use
            or "garage" in lowered_type_of_use
            or "restaurant" in lowered_type_of_use
            or "lager" in lowered_type_of_use
            or "einzelhandel" in lowered_type_of_use
            or "sonstige" in lowered_type_of_use
            or "grundstück" in lowered_type_of_use
            or "verkauf" in lowered_type_of_use
            or "reserviert" in lowered_type_of_use
        ):
            return

        cold_rent = response.css("td:contains('Kaltmiete') + td span::text").get()
        warm_rent = response.css("td:contains('Warmmiete') + td span::text").get()
        
        rent = None
        if( not cold_rent ):
            cold_rent = "0"
        
        if( not warm_rent):
            warm_rent = "0"

        cold_rent = re.findall(r"([0-9]+)", cold_rent)
        cold_rent = "".join(cold_rent)

        warm_rent = re.findall(r"([0-9]+)", warm_rent)
        warm_rent = "".join(warm_rent)
        
        cold_rent = int(cold_rent)
        warm_rent = int (warm_rent)
        if(warm_rent > cold_rent):
            rent = str(warm_rent)
        else: 
            rent = str(cold_rent)
        
        if(not re.search(r"([0-9]{2,})", rent)):
            return

        currency = "EUR"
        
        ad_type = response.css("td:contains('Vermarktungsart') + td span::text").get()
        if(ad_type != "Miete"):
            return
        
        utilities = response.css("td:contains('Nebenkosten') + td span::text").get()
        deposit = response.css("td:contains('Kaution') + td span::text").get()

        square_meters = response.css("td:contains('Wohnfläche') + td span::text").get()
        room_count = response.css("td:contains('Anzahl Zimmer') + td span::text").get()
        if(room_count):
            room_count = room_count.split(",")
            room_count = ".".join(room_count)
            room_count = math.ceil(float(room_count))
        else:
            room_count = "1"
        
        bathroom_count = response.css("td:contains('Anzahl Badezimmer') + td span::text").get()

        city = response.css("td:contains('Ort') + td span::text").get()
        zipcode = response.css("td:contains('PLZ') + td span::text").get()
        address = f"{zipcode} {city}"

        location_data = extract_location_from_address(address)
        latitude = str(location_data[1])
        longitude = str(location_data[0])

        description = response.css("div.information span::text").getall()
        description = " ".join(description)
        description = description_cleaner(description)
        description = re.sub(r"([0-9]{2,})", "", description)
        images = response.css("div.gallery ul li a::attr(href)").getall()

        external_id = response.css("td:contains('externe Objnr') + td span::text").get()
        floor = response.css("td:contains('Etage') + td span::text").get()

        balcony = response.css("td:contains('Balkon') + td span::text").get()
        if(balcony == "1"):
            balcony = True
        else:
            balcony = False
        
        terrace = response.css("td:contains('Terrasse') + td span::text").get()
        if(terrace == "Ja"):
            terrace = True
        else:
            terrace = False

        landlord_name = response.css("div.information p.center strong::text").get()
        landlord_phone = response.css("strong:contains('Tel.:') + span::text").get()
        landlord_email = "Lutz.Werner@Leipzig-estate.de"

        item_loader = ListingLoader(response=response)

        item_loader.add_value("external_link", response.url) 
        item_loader.add_value("external_source", self.external_source) 

        item_loader.add_value("external_id", external_id) 
        item_loader.add_value("position", self.position) 
        self.position += 1
        item_loader.add_value("title", title) 
        item_loader.add_value("description", description) 

        item_loader.add_value("city", city) 
        item_loader.add_value("zipcode", zipcode) 
        item_loader.add_value("address", address) 
        item_loader.add_value("latitude", latitude) 
        item_loader.add_value("longitude", longitude) 
        item_loader.add_value("floor", floor) 
        item_loader.add_value("property_type", property_type) 
        item_loader.add_value("square_meters", square_meters) 
        item_loader.add_value("room_count", room_count) 
        item_loader.add_value("bathroom_count", bathroom_count) 

        item_loader.add_value("balcony", balcony) 
        item_loader.add_value("terrace", terrace) 

        item_loader.add_value("images", images) 
        item_loader.add_value("external_images_count", len(images)) 

        item_loader.add_value("rent", rent) 
        item_loader.add_value("deposit", deposit) 
        item_loader.add_value("utilities", utilities) 
        item_loader.add_value("currency", currency) 

        item_loader.add_value("landlord_name", landlord_name) 
        item_loader.add_value("landlord_phone", landlord_phone) 
        item_loader.add_value("landlord_email", landlord_email) 

        yield item_loader.load_item()
