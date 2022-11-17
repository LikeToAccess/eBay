# -*- coding: utf-8 -*-
# filename          : main.py
# description       : Grabs data from eBay search links
# author            : LikeToAccess
# email             : liketoaccess@protonmail.com
# date              : 11-16-2022
# version           : v2.0
# usage             : python main.py
# notes             :
# license           : MIT
# py version        : 3.11.0 (must run on 3.6 or higher)
#==============================================================================
import os
import time
import json
from tqdm import tqdm
from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import sheets
from settings import *


class Scraper:
	def __init__(self, headless=HEADLESS):
		init_timestamp = time.time()
		user_data_dir = os.path.abspath("selenium_data")
		options = Options()
		options.add_argument("autoplay-policy=no-user-gesture-required")
		options.add_argument("log-level=3")
		options.add_argument(f"user-data-dir={user_data_dir}")
		options.add_argument("--ignore-certificate-errors-spki-list")
		if headless:
			options.add_argument("--headless")
			options.add_argument("window-size=1920,1080")
			# options.add_argument("--disable-gpu")
			options.add_argument("--mute-audio")
		self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
		# self.headers = headers
		print(f"Completed init in {round(time.time()-init_timestamp,2)}s.")

	def open_link(self, url):
		self.driver.get(url)

	def close(self):
		self.driver.close()

	def current_url(self):
		return self.driver.current_url

	def get_data(self, listing_xpath, metadata_xpaths):
		combined_metadata = []
		messages = []
		listings = self.driver.find_elements(
			By.XPATH, listing_xpath
		)

		for listing in tqdm(listings):
			grouping = []
			for metadata_xpath in metadata_xpaths:
				# Find a specific piece of information off of a listing
				try:
					metadata = listing.find_element(By.XPATH, metadata_xpath).text
					if metadata: grouping.append(metadata)
				except NoSuchElementException: pass#messages.append(f"No metadata found for: {metadata_xpath}")
			if grouping:
				grouping.insert(0, listing.get_attribute("data-view"))
				combined_metadata.append(grouping)
		print("\n".join(messages))
		return combined_metadata

def remove_by_keywords(data, keywords):
	"""Removes items from a list of items if they contain any of the keywords

	Args:
		data (list): The items to remove from
		keywords (list): The keywords to check for

	Returns:
		list: The items that do not contain any of the keywords

	"""
	return [item for item in data if not any(keyword in item for keyword in keywords)]

def read_file(filename, encoding="utf8"):
	"""Reads a file and returns the contents

	Args:
		filename (str): The name of the file to read
		encoding (str, optional): The encoding of the file. Defaults to "utf8".

	Returns:
		str: The contents of the file

	"""
	with open(filename, "r", encoding=encoding) as file:
		return file.read()

def pad(data):
	"""Prints a list of items in a nicer format

	Args:
		data (dict): The items to print

	Returns:
		str: A formatted version of the arguments

	"""
	result = ""
	for iid, values in data.items():
		result += f"{iid:>{max(map(len, map(str, data.keys())))}} | "
		for value in values.values():
			if isinstance(value, list):
				value = value[0]
			result += f"{value:<{6}} | "
		result = result.strip(" |")
		result += "\n"

	return result

def captcha(url):
	"""Checks if the current screen is waiting for a captcha response.

	Args:
		url (str): The current URL

	Returns:
		True if the current screen is awaiting a captcha, otherwise False

	"""
	return "https://www.ebay.com/splashui/captcha" in url

def write_to_json_file(filename, data, encoding="utf8"):
	"""Writes the data to a JSON file

	Args:
		filename (str): The name of the file to write to
		encoding (str, optional): The encoding of the file. Defaults to "utf8".

	"""
	with open(filename, "w", encoding=encoding) as file:
		json.dump(data, file, indent=4)

class Macbook:
	def __init__(self, url="https://igotoffer.com/apple/macbook-pro-model-numbers"):
		self.url = url
		self.scraper = Scraper()
		self.scraper.open_link(url)
		self.raw_data = {}
		self.parsed_data = {}

	def get_data(self):
		"""Gets the data from the website

		Returns:
			dict: The data from the website

		"""
		print("Updating current MacBook data...")
		table = self.scraper.driver.find_element(By.XPATH, "//*[@id='tablepress-403']")
		for row in table.find_elements(By.XPATH, "tbody/tr[*]"):
			# print(row.text)
			model_identifier = None
			for column in row.find_elements(By.XPATH, "*"):
				# print(column.text)
				if column.text[:3] == "Mac":
					model_identifier = column.text
					self.raw_data[model_identifier] = []
				elif model_identifier:
					self.raw_data[model_identifier].append(column.text.replace("Sell your ", ""))
			# print()

		return self.raw_data

	def __str__(self):
		buffer = []
		for model_identifier, values in self.raw_data.items():
			values = "\n\t".join(values)
			buffer.append(f"{model_identifier}\n\t{values}")

		return "\n".join(buffer)

	def parse_data(self):
		for model_identifier, values in self.raw_data.items():
			model_number, part_number, description = values
			model_number, emc_number = model_number.split(" (")
			macbook_type = description.split(" (")[0]
			year = description.rsplit(", ", 1)[-1].strip(")")
			if macbook_type not in self.parsed_data:
				self.parsed_data[macbook_type] = []
			self.parsed_data[macbook_type].append(
				{
					"model_identifier": model_identifier,
					"model": model_number,
					"emc": emc_number.strip(")"),
					"year": year,
					"part_number": part_number,
					"description": description,
					"parts": {
						"display assembly": [],
						"battery": [],
						"palmrest": [],
						"trackpad": [],
					},
				}
			)

	def run(self):
		start_timer = time.time()
		self.get_data()
		self.scraper.close()
		print(f"Retrieved data in {round(time.time()-start_timer, 2)}s.")
		self.parse_data()
		write_to_json_file("macbook.json", self.parsed_data)


class Ebay:
	def __init__(self, item="", year="", model="", part=""):
		self.item = item
		self.year = year
		self.model = model
		self.part = part
		self.url = self.create_url()
		self.scraper = Scraper()
		self.scraper.open_link(self.url)
		self.data = {}
		# self.sheets = sheets.Sheets()
		print("Running scraper on eBay...")

	def create_url(self):
		"""Creates a search URL from the given arguments.

		Returns:
			str: A search URL based on the class arguments

		"""
		item = "+".join(self.item.split()).lower() + "+"
		year = "+".join(self.year.split()).lower() + "+"
		model = "+".join(self.model.split()).lower() + "+"
		part = "+".join(self.part.split()).lower()
		base_url = f"https://www.ebay.com/sch/i.html?_from=R40&_nkw={item}{year}{model}{part}&_sacat=0&LH_Sold=1&LH_Complete=1&_ipg=200&rt=nc&LH_ItemCondition=1500%7C3000%7C1000"

		return base_url

	def average_price(self):
		"""Calculates the average price of a list of items

		Returns:
			float: The average price of the items

		"""
		prices = []
		for value in self.data.values():
			prices += value["price"]
		prices = list(map(lambda x: float(x.replace(",", "")), prices))
		# prices = list(map(float, prices))

		return sum(prices) / len(prices)

	def run(self):
		"""Runs the scraper and saves the data to a spreadsheet

		"""
		if captcha(self.scraper.driver.current_url):
			print("Please solve the captcha to continue...")
			while captcha(self.scraper.driver.current_url):
				time.sleep(0.5)
			print("Captcha solve complete, continuing to search...")
		combined_metadata = self.scraper.get_data(
			"//li[@class=\"s-item s-item__pl-on-bottom\"]",
			[
				"div/div[2]/a/div",              # Listing Title
				"div/div[2]/div[3]/div",         # Price
				"div/div[2]/div[4]/div",         # Price
				# "div/div[2]/div[1]/div/span"     # Date
				"div/div[2]/div[1]/div/span[1]"  # Date
			]
		)
		print(combined_metadata[-1])

		print(f"Number of listings:       {len(combined_metadata)}")
		combined_metadata = remove_by_keywords(
			combined_metadata,
			[
				# blacklisted words to disqualify a listing
				"cracked",
				"only",
				"broken",
				"lot ",
				"issues",
				" d 1",
				" box only ",
			]
		)
		combined_metadata = [metadata for metadata in combined_metadata if len(metadata) > 3]
		print(f"Number of valid listings: {len(combined_metadata)}")

		for metadata in combined_metadata:
			iid, _, price, date = metadata

			iid = int(iid.split("|")[1].strip("iid:"))
			price = price.replace("$", "").split(" to ")
			date = date.split("Sold ")[1]

			self.data[iid] = {
				"price": [*price],
				"date": date,
			}

		# print(pad(data))
		average_price = round(self.average_price(), 2)
		print(f"Average price: ${average_price}")
		return average_price


def main():
	if input("(y/n) Do you want to update/reset the entire MacBook model list? (press enter for default, n)\n> ").lower() == "y":
		macbook = Macbook()
		macbook.run()

	data = json.loads(read_file("macbook.json"))

	for macbook_type, values in data.items():
		for index, value in enumerate(values):
			# model_identifier = value["model_identifier"]
			value["model"] = value["model"].replace(" ", "")
			model_number = value["model"]
			# emc_number = value["emc"]
			release_year = value["year"]
			# part_number = value["part_number"]
			# description = value["description"]
			parts = value["parts"]

			for part_name, cost in parts.items():
				if isinstance(cost, float):  # if the cost is already a float, skip
					continue
				ebay = Ebay(
					item=macbook_type,
					year=release_year,
					model=model_number,
					part=part_name
				)
				cost = ebay.run()
				data[macbook_type][index]["parts"][part_name] = cost
				write_to_json_file("macbook.json", data)
				print(f"{macbook_type} {model_number} {part_name} {cost}")
	# ebay = Ebay(laptop_name, release_year, model_number, part_name)
	# ebay.run()

if __name__ == "__main__":
	main()
