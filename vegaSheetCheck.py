from __future__ import print_function
import os.path,base64,subprocess

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID of the spreadsheet.
SPREADSHEET_ID = '14rEoD2_j6Foy8p-VfJ1hLYSDGPykW_ChIZJXqeN83tU'

# The A1 notation of the values to read.
read_range = 'A2:G'

# The A1 notation of the values to edit. F2:F is (currently) the Valid/Invalid column
edit_range = 'G2:G'

def readSheet():
    values = []
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=read_range).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return
        return values

    except HttpError as err:
        print(err)

def editSheet(update):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('sheets', 'v4', credentials=creds)


        valueRange = {
            "majorDimension": "COLUMNS",
            "values": [
                    update
                ]
            }

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().update(spreadsheetId=SPREADSHEET_ID, range=edit_range,valueInputOption="RAW",body=valueRange).execute()

        return result['updatedCells']

    except HttpError as err:
        print(err)

def check_if_valid(message,signature,pubkey):
    message = base64.b64encode(message.encode(),altchars=None)
    signature = signature.encode()
    pubkey = pubkey.encode()
    # format the command corrently using byte strings
    command = b'./vegawallet message verify --message ' + message + b' --signature ' + signature + b' --pubkey ' + pubkey
    # print("command: ",command) - for debugging
    try:
        # run the command and get the output
        output = subprocess.check_output(command, shell=True)
        output = output.decode("utf-8")[2:3]
        return output
    except subprocess.CalledProcessError as e:
        print(e.output)
        return "E"

    
if __name__ == '__main__':
    # read the sheet and get the values
    values = readSheet()
    updated_values = []
    updatedValids = []
    # print(values) - for debugging
    for row in values:
        # print(row) # - for debugging
        # skip the first row (headers) (shouldn't be necessary)
        if row != ['Discord ', 'Pubkey', 'Signed', 'Teams', 'Submitted At', 'Token', 'Valid/Invalid']:
            print("CHECKING Pubkey:", row[1], "for", row[0])
            # check if the row has already been checked and updated (if so, skip) - this is to prevent rechecking the same pubkey
            if len(row) > 5:
                if row[5] == 'V':
                    print("ALREADY VALID")
                    updatedValids.append('V')
                    continue
                elif row[5] == 'I':
                    print("ALREADY INVALID")
                    updatedValids.append('I')
                    continue
                else: # if the row has neither a V or I, then we check it
                    output = check_if_valid(row[0],row[2],row[1])
                    updated_values.append([row[0],row[1],row[2],row[3],row[4],output])
                    
                    updatedValids.append(output)
                    if output == 'V':
                        print("VALID")
                    elif output == 'I':
                        print("INVALID")
                    else:
                        print("ERROR")
            else:
                output = check_if_valid(row[0],row[2],row[1])
                updated_values.append([row[0],row[1],row[2],row[3],row[4],output])
            
                updatedValids.append(output)
                if output == 'V':
                    print("VALID")
                elif output == 'I':
                    print("INVALID")
                else:
                    print("ERROR")

    # print(updatedValids) - for debugging
    updatedCells = editSheet(updatedValids)
    if updatedCells >= 0:
        print("Cells updated: ",updatedCells)