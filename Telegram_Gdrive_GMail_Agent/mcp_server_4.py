from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from mcp import types
import sys
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
from pathlib import Path
from typing import List, Dict, Any

# Initialize FastMCP server
mcp = FastMCP("google-drive")

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_credentials():
    """Get valid user credentials from storage or prompt user to authorize."""
    creds = None
    token_path = Path("token.pickle")
    
    # The file token.pickle stores the user's access and refresh tokens
    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                # Try different ports if the default one fails
                for port in [8080, 8081, 8082, 8083, 8084]:
                    try:
                        creds = flow.run_local_server(port=port)
                        break
                    except Exception as e:
                        print(f"Failed to use port {port}, trying next...")
                        continue
                else:
                    raise Exception("Could not find an available port for OAuth flow")
            except Exception as e:
                print(f"Error during OAuth flow: {str(e)}")
                print("\nPlease make sure to:")
                print("1. Download credentials.json from Google Cloud Console")
                print("2. Add these redirect URIs in Google Cloud Console:")
                print("   - http://localhost:8080/")
                print("   - http://localhost:8081/")
                print("   - http://localhost:8082/")
                print("   - http://localhost:8083/")
                print("   - http://localhost:8084/")
                raise
        
        # Save the credentials for the next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

# @mcp.tool()
# def create_spreadsheet(title: str) -> str:
#     """
#     Create a new Google Spreadsheet with the given title.
    
#     Args:
#         title: The title of the spreadsheet to create
#     """
#     try:
#         creds = get_credentials()
#         service = build('sheets', 'v4', credentials=creds)
        
#         spreadsheet = {
#             'properties': {
#                 'title': title
#             }
#         }
        
#         spreadsheet = service.spreadsheets().create(body=spreadsheet).execute()
#         return f"Created spreadsheet with ID: {spreadsheet['spreadsheetId']}"
#     except Exception as e:
#         return f"Error creating spreadsheet: {str(e)}"

@mcp.tool()
def append_to_sheet(spreadsheet_id: str, range_name: str, values: List[List[Any]]) -> str:
    """
    Append values to a Google Sheet. If the sheet file doesn't exist, it will be created with the name specified in spreadsheet_id.
    Returns the URL of the Google Sheet.
    
    Args:
        spreadsheet_id: The name of the spreadsheet to create or modify
        range_name: The A1 notation of the range to append to (ignored, kept for compatibility)
        values: List of rows to append, where each row is a list of values
    """
    try:
        creds = get_credentials()
        sheets_service = build('sheets', 'v4', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Search for existing file with the given name
        query = f"name='{spreadsheet_id}' and mimeType='application/vnd.google-apps.spreadsheet'"
        results = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        files = results.get('files', [])
        
        if files:
            # Use existing file
            file_id = files[0]['id']
        else:
            # Create new spreadsheet with the given name
            spreadsheet = {
                'properties': {
                    'title': spreadsheet_id
                }
            }
            spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet).execute()
            file_id = spreadsheet['spreadsheetId']
        
        # Append the values to the first sheet
        body = {
            'values': values
        }
        
        result = sheets_service.spreadsheets().values().append(
            spreadsheetId=file_id,
            range='Sheet1!A1',  # Always append to first sheet
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        # Generate the Google Sheets URL
        sheet_url = f"https://docs.google.com/spreadsheets/d/{file_id}"
        
        return f"Successfully appended {len(values)} rows to '{spreadsheet_id}'. Sheet URL: {sheet_url}"
        
    except Exception as e:
        # logger.error(f"Error appending to sheet: {e}")
        return f"Error appending to sheet: {str(e)}"

if __name__ == "__main__":
    print("mcp_server_4.py starting")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
        print("\nShutting down...") 