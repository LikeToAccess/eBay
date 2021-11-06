import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


def authenticate(scopes):
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


class Sheets:
	def __init__(self, spreadsheet_id="1S8EEc6qQA0o-dUIjvHWBEg94pl20Q6hbGurJvwm4FhY"):
		self.scopes = ["https://www.googleapis.com/auth/spreadsheets"]
		self.spreadsheet_id = spreadsheet_id
		self.creds = authenticate(self.scopes)
		service = build("sheets", "v4", credentials=self.creds)
		self.sheet = service.spreadsheets()

	def read(self, range_name):
		result = self.sheet.values().get(
				 	spreadsheetId=self.spreadsheet_id,
				 	range=range_name
				 ).execute()
		values = result.get("values", [])

		if not values:
			print("No data found.")
		return values


if __name__ == "__main__":
	sheets = Sheets()
	range_name_ = "Data!B2:B3"
	print(f"Values for range, \"{range_name_}\":")
	for row in sheets.read(range_name_):
		print(row)
