import streamlit as st
import pandas as pd
import gspread
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
import requests
import time

# Define the Google Sheets API scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly', 'https://www.googleapis.com/auth/drive.readonly']

# Function to authenticate Google Sheets
def authenticate_google_sheets():
    """Authenticate and return the Google Sheets client."""
    creds = None
    # Check if token.pickle exists (stored credentials)
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Load client secrets file and run OAuth2 flow
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)  # Ensure the client_secret.json is in the same directory
            creds = flow.run_local_server(port=0)

        # Save credentials to 'token.pickle' file for future use
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    # Authenticate and authorize with Google Sheets
    gc = gspread.authorize(creds)
    return gc

# Function to fetch data from a selected Google Sheet
def fetch_data_from_google_sheets(sheet_id):
    """Fetch data from the selected Google Sheet by its ID."""
    gc = authenticate_google_sheets()
    sheet = gc.open_by_key(sheet_id)
    worksheet = sheet.get_worksheet(0)
    data = pd.DataFrame(worksheet.get_all_records())
    return data

# Function to perform a web search using SerpAPI
def perform_web_search(query, api_key):
    search_url = "https://serpapi.com/search.json"
    params = {
        "q": query,
        "api_key": api_key,
        "num": 5
    }
    
    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        return response.json().get("organic_results", [])
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred: {e}")
        return []

# Streamlit UI
st.title("AI-Powered Information Retrieval Dashboard")
st.write("Authenticate with Google, choose a Google Sheet, and query its data.")

# Input for API key
api_key = st.text_input("Enter your SerpAPI key:", type="password")
if not api_key:
    st.warning("Please enter an API key to continue.")

# Option to choose data source
data_source = st.radio("Choose data source", ("CSV File", "Google Sheets"))
data = None

# Step 1: Data Source - CSV Upload
if data_source == "CSV File":
    uploaded_file = st.file_uploader("Upload your CSV file", type="csv")
    if uploaded_file:
        data = pd.read_csv(uploaded_file)
        st.dataframe(data)
        st.download_button("Download Full Data as CSV", data.to_csv(index=False), file_name="full_data.csv")

# Step 1: Data Source - Google Sheets Authentication
elif data_source == "Google Sheets":
    try:
        gc = authenticate_google_sheets()
        files = gc.list_spreadsheet_files()
        file_names = [file['name'] for file in files]
        file_ids = [file['id'] for file in files]

        selected_sheet_name = st.selectbox("Select a Google Sheet", file_names)
        selected_sheet_id = file_ids[file_names.index(selected_sheet_name)]
        data = fetch_data_from_google_sheets(selected_sheet_id)
        st.write("Data Preview:", data)

    except Exception as e:
        st.error(f"Error fetching Google Sheets: {e}")

# Continue if data is loaded from either source
if data is not None:
    columns = data.columns.tolist()
    selected_column = st.selectbox("Select the main column for querying", columns)
    user_query = st.text_input("Enter your question using {} as a placeholder, e.g., 'Find HIRE_DATA for {}'")

    rate_limit_interval = st.number_input("Rate Limit Interval (seconds)", min_value=1.0, value=2.0)

    if user_query and selected_column:
        results = []
        for entity in data[selected_column]:
            query = user_query.format(entity)
            matching_row = data[data[selected_column] == entity]

            if not matching_row.empty:
                target_column = user_query.split(" ")[1]
                result_value = matching_row[target_column].values[0] if target_column in matching_row.columns else "Column not found"
                result = {"Entity": entity, target_column: result_value}
            else:
                result = {"Entity": entity, "Message": "Entity not found"}

            search_query = f"Get me the email address of {entity}"
            search_results = perform_web_search(search_query, api_key)
            
            for search_result in search_results:
                result.update({
                    "Title": search_result.get("title"),
                    "URL": search_result.get("link"),
                    "Snippet": search_result.get("snippet")
                })
                results.append(result)

            time.sleep(rate_limit_interval)

        results_df = pd.DataFrame(results)
        st.write("Results:")
        st.dataframe(results_df)
        st.download_button("Download Results as CSV", results_df.to_csv(index=False), file_name="results.csv")
