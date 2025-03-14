import dropbox
import requests
import os
import pandas as pd

# 🔹 Dropbox App Credentials
APP_KEY = "o20t0l0x6zy8x3q"
APP_SECRET = "q8iww963hh4odop"
REFRESH_TOKEN = "4zgruw-6AbIAAAAAAAAAAVCoMg0tPn6dON4DtERSLqGxr7ERBI7NG2yG07El7zHr"

# 🔹 Path to the XLS file in Dropbox
DROPBOX_FILE_PATH = "/S&P500_140_API GPT_Only Metadata.xlsx"

# 🔹 Step 1: Get a New Access Token Using the Refresh Token
def get_dropbox_access_token():
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": APP_KEY,
        "client_secret": APP_SECRET
    }
    response = requests.post(url, data=data)
    
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print("❌ Error retrieving Dropbox token:", response.json())
        return None

# 🔹 Step 2: Download the Latest XLS from Dropbox
def download_xls_from_dropbox():
    DROPBOX_ACCESS_TOKEN = get_dropbox_access_token()
    
    if not DROPBOX_ACCESS_TOKEN:
        return "❌ Error: Unable to authenticate with Dropbox."

    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

    try:
        _, res = dbx.files_download(DROPBOX_FILE_PATH)

        # Save locally
        local_xls_path = "S&P500_Metadata.xlsx"
        with open(local_xls_path, "wb") as f:
            f.write(res.content)

        return local_xls_path
    except Exception as e:
        return f"❌ Error downloading file: {e}"

# 🔹 Step 3: Retrieve Case Studies with Dynamic Refinement
def search_cases(query=None, company=None, industry=None, strategy=None, hack_type=None, platform_type=None):
    xls_path = download_xls_from_dropbox()
    
    if not xls_path:
        return "❌ Error: Unable to download the XLS file."

    try:
        df = pd.ExcelFile(xls_path).parse("Dataset finale - 140 casi")  # Modify sheet name if needed
    except Exception as e:
        return f"❌ Error loading Excel file: {e}"

    # 🔹 Apply filters
    if company:
        df = df[df["Company"].str.contains(company, case=False, na=False)]
    if industry:
        df = df[(df["Industry1stOrder"].str.contains(industry, case=False, na=False)) |
                (df["Industry2ndOrder"].str.contains(industry, case=False, na=False))]
    if strategy:
        df = df[df["Strategy"].str.contains(strategy, case=False, na=False)]
    if hack_type:
        df = df[df["HACK"].str.contains(hack_type, case=False, na=False)]
    if platform_type:
        df = df[df["TypeOfPlatform"].str.contains(platform_type, case=False, na=False)]

    # 🔹 Apply general search across multiple columns
    if query:
        search_columns = ["Company", "Industry1stOrder", "Industry2ndOrder", "Initiative", "Strategy",
                          "Department", "HACK", "TypeOfPlatform", "FirstSide", "OtherSide", "IdleAssets", "Openness"]
        df = df[df.apply(lambda row: any(query.lower() in str(row[col]).lower() for col in search_columns), axis=1)]

    # 🔹 If too many results, suggest filtering options
    if len(df) > 5:
        filter_suggestions = {
            "Industries": df["Industry1stOrder"].dropna().unique().tolist(),
            "Strategies": df["Strategy"].dropna().unique().tolist(),
            "Hacks": df["HACK"].dropna().unique().tolist(),
            "Platform Types": df["TypeOfPlatform"].dropna().unique().tolist()
        }

        return {
            "message": f"📌 {len(df)} cases match your request. Please refine by selecting one of the following:",
            "filters": filter_suggestions
        }

    # 🔹 Return up to 5 cases with Full Case Text
    case_list = df.head(5)[["Company", "Initiative", "Strategy", "HACK", "TypeOfPlatform", "Full Case Text"]]
    return case_list.to_dict(orient="records")

# ✅ Test the function locally
if __name__ == "__main__":
    print(search_cases(industry="Healthcare", strategy="Platform as a New Service"))
