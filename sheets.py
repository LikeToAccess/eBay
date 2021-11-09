# -*- coding: utf-8 -*-
# filename          : sheets.py
# description       : Easily read and write data to any Google Sheet
# author            : LikeToAccess
# email             : liketoaccess@protonmail.com
# date              : 11-07-2021
# version           : v1.0
# usage             : python sheets.py
# notes             : On fisrt run you should be asked to login with a Google account
# license           : MIT
# py version        : 3.9.7 (must run on 3.6 or higher)
#==============================================================================
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


class Sheets:
	"""Easily read and write from any Google Sheet accessible from your Google Account.

	On first run user will be prompted to sign-in with Google, this will give the program access to all of the same Google Sheets the user has access to.

	"""
	def __init__(self, spreadsheet_id):
		"""Runs all Authentication and setup.

		Note:
			The spreadsheet_id is contained within the address bar, "https://docs.google.com/spreadsheets/d/fo-OB4r/edit#gid=0" where "fo-OB4r" would be the spreadsheet_id.

		Args:
			spreadsheet_id (str): The unique ID of the Google Sheet page that should be edited.

		"""
		self.scopes = ["https://www.googleapis.com/auth/spreadsheets"]
		self.spreadsheet_id = spreadsheet_id
		self.creds = authenticate(self.scopes)
		service = build("sheets", "v4", credentials=self.creds)
		self.sheet = service.spreadsheets()

	def read(self, range_name):
		"""Reads data from the selected Sheet.

		Args:
			range_name (str): The range of tiles the API is allowed to access.

		Returns:
			A list of the data contained inside the selected range.

		Examples:
			>>> print(Sheets.read("Sheet Name!A1:Z99"))
			[['Hello World!'], ['This text will apear on tile A2!']]

		"""
		result = self.sheet.values().get(
			spreadsheetId=self.spreadsheet_id,
			range=range_name
		).execute()
		values = result.get("values", [])

		if not values:
			print("No data found.")
		return values

	def write(self, range_name, data):
		"""Writes data into the selected Sheet.

		Args:
			range_name (str): The maximum range of tiles the API is allowed to modify.
			data (list): A list containing data that will be written to the beggining of the selected range

		Returns:
			A disctionary containing information about what was accessed during the update

		Examples:
			>>> print(Sheets.write("Sheet Name!A1:Z99", [["Hello World!"],["This text will apear on tile A2!"]]))
			Sheet successfully updated.
			{'spreadsheetId': '1S8EEc6qQA0o-dUIjvHWBEg94pl20Q6hbGurJvwm4FhY', 'updatedRange': "'Sheet Name'!A1:A2", 'updatedRows': 2, 'updatedColumns': 1, 'updatedCells': 2}

		"""
		response_metrics = self.sheet.values().update(
			spreadsheetId=self.spreadsheet_id,
			valueInputOption="RAW",
			range=range_name,
			body=dict(
				majorDimension="ROWS",
				values=data)
		).execute()
		print("Sheet successfully updated.")
		return response_metrics


def authenticate(scopes):
	"""Generates token.json to allow access to the Google Sheet.

	Args:
		scopes (list): A list of the permissions required to read and write to Google Sheets on the user's behalf.

	Returns:
		An OAuth 2.0 credentials object used to login as a Google Account with specified permissions listed in the scopes argument

	Examples:
		>>> authenticate(["https://www.googleapis.com/auth/spreadsheets"])  # Running the program for the first time.
		No valid credentials found, please authenticate for Google Sheets API...         
		Please visit this URL to authorize this application: https://accounts.google.com/o/oauth2/auth?response_type=code&...&access_type=offline
		Credentials for Google Sheets API saved succesfully.
		
		>>> authenticate(["https://www.googleapis.com/auth/spreadsheets"])  # Running the program after token.json was generated.
		Authenticating with Google Sheets API...
		Using existing credentials for Google Sheets API.

	"""
	creds = None
	print("Authenticating with Google Sheets API...")
	if os.path.exists("token.json"):
		print("Using existing credentials for Google Sheets API.")
		creds = Credentials.from_authorized_user_file("token.json", scopes)
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			print("Refreshing expired credentials for Google Sheets API...")
			creds.refresh(Request())
		else:
			print("No valid credentials found, please authenticate for Google Sheets API...")
			flow = InstalledAppFlow.from_client_secrets_file(
				"credentials.json", scopes)
			creds = flow.run_local_server(port=0)
		with open("token.json", "w") as token:
			token.write(creds.to_json())
			print("Credentials for Google Sheets API saved succesfully.")
	return creds


if __name__ == "__main__":
	sheets = Sheets("1S8EEc6qQA0o-dUIjvHWBEg94pl20Q6hbGurJvwm4FhY")
	range_name_ = "Copy of Data!A1:ZZ10000"
	print(f"Values for range, \"{range_name_}\":")
	print(sheets.read(range_name_))
	# for row in :
	# 	for item in row:
	# 		print(item)
	# help(sheets.write)
