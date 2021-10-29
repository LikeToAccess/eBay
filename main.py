# -*- coding: utf-8 -*-
# filename          : main.py
# description       : Grabs data from eBay search links
# author            : LikeToAccess
# email             : liketoaccess@protonmail.com
# date              : 10-26-2021
# version           : v1.0
# usage             : python main.py
# notes             :
# license           : MIT
# py version        : 3.9.7 (must run on 3.6 or higher)
#==============================================================================
import os
from tqdm import tqdm
from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC


class Scraper:
	def __init__(
		self,
		minimize=True,
		user_data_dir=os.path.abspath("selenium_data"),
		executable = "chromedriver.exe" if os.name == "nt" else "chromedriver",
		headers = {
			"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
		},
	):
		options = Options()
		options.add_argument(f"user-data-dir={user_data_dir}")
		options.add_argument("log-level=3")
		self.executable = executable
		self.driver = webdriver.Chrome(executable_path=os.path.abspath(self.executable), options=options)
		self.headers = headers
		if minimize: self.driver.minimize_window()

	def open_link(self, url):
		self.driver.get(url)

	def close(self):
		self.driver.close()

	def current_url(self):
		return self.driver.current_url

	def get_data(self, listing_xpath, metadata_xpaths):
		combined_metadata = []
		data_views = []
		messages = []
		listings = self.driver.find_elements(
			By.XPATH, listing_xpath
		)

		for listing in tqdm(listings):
			# TODO: Fix the name
			dumb_variable_name = []
			for metadata_xpath in metadata_xpaths:
				# Find a specific piece of information off of a listing
				try:
					metadata = listing.find_element(
						By.XPATH, metadata_xpath).text
					if metadata:
						dumb_variable_name.append(metadata)
				except NoSuchElementException: messages.append(f"No metadata found for: {metadata_xpath}")
			if dumb_variable_name:
				dumb_variable_name.insert(0, listing.get_attribute("data-view"))
				combined_metadata.append(dumb_variable_name)
		for message in messages: print(message)
		return combined_metadata

def remove_by_keywords(data, keywords):
	for keyword in keywords:
		data = [item for item in data if keyword not in item[1].lower()]
	return data

def pad(stri, leng):
	result = stri
	for i in range(len(stri),leng):
		result = result+" "
	return result

def main(url):
	scraper = Scraper(minimize=False)
	scraper.open_link(url)
	combined_metadata = scraper.get_data(
		"//li[@class=\"s-item s-item__pl-on-bottom\"]",
		[
			"div/div[2]/a/h3",  # Listing Title
			"div/div[2]/div[4]/div",  # Price
			"div/div[2]/div[3]/div",  # Price
			"div/div[2]/div[1]/div/span[1]"  # Date
		]
	)

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
		]
	)
	combined_metadata = [metadata for metadata in combined_metadata if len(metadata) > 2]
	print(f"Number of valid listings: {len(combined_metadata)}")
	# print(combined_metadata)
	for metadata in combined_metadata:
		iid, _, price, date = metadata
		iid = iid.split("|")[1]
		iid = iid + " " if len(iid) < 6 else iid
		date = date.split("Sold ")[1]
		print(pad(iid+" | ",9)+pad(price,10)+"| "+date)




if __name__ == "__main__":
	search_url = "https://www.ebay.com/sch/i.html?_from=R40&_nkw=macbook+pro+2015+a1398+display+assembly&_sacat=0&rt=nc&LH_Sold=1&LH_Complete=1&_ipg=200"
	main(search_url)
