from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

# 🔹 Path to the Excel database file

import dropbox
DROPBOX_APP_KEY = "o20t0l0x6zy8x3q"
DROPBOX_APP_SECRET = "q8iww963hh4odop"
DROPBOX_REFRESH_TOKEN = "4zgruw-6AbIAAAAAAAAAAVCoMg0tPn6dON4DtERSLqGxr7ERBI7NG2yG07El7zHr"
DROPBOX_FILE_PATH = "Applicazioni/platform-thinking-gpt/S&P500_140_API GPT_Only Metadata.xlsx"

def download_file_from_dropbox():
    """Downloads the Excel file from Dropbox."""
    try:
        dbx = dropbox.Dropbox(
            app_key=DROPBOX_APP_KEY,
            app_secret=DROPBOX_APP_SECRET,
            oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
        )
        metadata, res = dbx.files_download(DROPBOX_FILE_PATH)
        return pd.read_excel(res.content)
    except Exception as e:
        print(f"❌ Error downloading file from Dropbox: {e}")
        return None
def load_cases():
    """Loads the case study database from Dropbox."""
    return download_file_from_dropbox()
    """Loads the case study database from the Excel file and prints debug info."""
    try:

        # Check if file exists
            return None

        # Try loading the file
            print("✅ Loaded Excel file successfully. Columns:", df.columns.tolist())  # Debugging step
        return df
    except Exception as e:
        print(f"❌ Error loading Excel file: {e}")  # Debugging step
        return None


@app.route('/start_search', methods=['GET'])
def start_search():
    """Initiates a case study search and presents filter options."""
    
    df = load_cases()
    if df is None:
        return jsonify({"error": "Failed to load database"}), 500

    available_filters = {
        "Industry": df["Industry1stOrder"].value_counts().to_dict(),
        "Strategy": df["Strategy"].value_counts().to_dict(),
        "HACK": df["HACK"].value_counts().to_dict(),
        "IdleAssets": {
            "Data": int(df["Data"].sum()),
            "Relationships": int(df["Relationships"].sum()),
            "Know How": int(df["Know How"].sum()),
            "Physical Assets": int(df["Physical Assets"].sum())
        }
    }

    return jsonify({
        "message": "Hi, this is a search engine to find real cases from our 140 S&P500 Databases. You can filter using one of the following dimensions: Industry, Strategy, Hack, Idle Assets. Which filter do you want to use?",
        "available_filters": available_filters
    })

@app.route('/refine_search', methods=['GET'])
def refine_search():
    """Refines the search by applying additional filters."""
    
    df = load_cases()
    if df is None:
        return jsonify({"error": "Failed to load database"}), 500

    industry = request.args.get('industry')
    strategy = request.args.get('strategy')
    hack_type = request.args.get('hack_type')
    idle_assets_filter = request.args.get('idle_assets')  # Expecting one of the four main categories

    # Apply filters progressively
    if industry:
        df = df[df["Industry1stOrder"].str.contains(industry, case=False, na=False)]
    if strategy:
        df = df[df["Strategy"].str.contains(strategy, case=False, na=False)]
    if hack_type:
        df = df[df["HACK"].str.contains(hack_type, case=False, na=False)]
    if idle_assets_filter and idle_assets_filter in ["Data", "Relationships", "Know How", "Physical Assets"]:
        df = df[df[idle_assets_filter] == 1]  # Filtering only cases where the category is present

    if df.empty:
        return jsonify({"error": "No cases found matching your filters."}), 404

    # Compute next available filters
    next_filters = {k: v for k, v in {
        "Industry": df["Industry1stOrder"].value_counts().to_dict() if not industry else {},
        "Strategy": df["Strategy"].value_counts().to_dict() if not strategy else {},
        "HACK": df["HACK"].value_counts().to_dict() if not hack_type else {},
        "IdleAssets": {
            "Data": int(df["Data"].sum()),
            "Relationships": int(df["Relationships"].sum()),
            "Know How": int(df["Know How"].sum()),
            "Physical Assets": int(df["Physical Assets"].sum())
        } if not idle_assets_filter else {}
    }.items() if v}

    return jsonify({
        "filtered_cases_count": len(df),
        "next_filters": next_filters,
        "message": f"There are {len(df)} cases matching your filters. Would you like to refine further or see case summaries?"
    })

@app.route('/get_case_summaries', methods=['GET'])
def get_case_summaries():
    """Retrieves case summaries for the selected filters."""
    
    df = load_cases()
    if df is None:
        return jsonify({"error": "Failed to load database"}), 500

    industry = request.args.get('industry')
    strategy = request.args.get('strategy')
    hack_type = request.args.get('hack_type')
    idle_assets = request.args.get('idle_assets')
    retrieve_cases = request.args.get('retrieve_cases', 'false').lower() == 'true'

    # Apply filters
    if industry:
        df = df[df["Industry1stOrder"].str.contains(industry, case=False, na=False)]
    if strategy:
        df = df[df["Strategy"].str.contains(strategy, case=False, na=False)]
    if hack_type:
        df = df[df["HACK"].str.contains(hack_type, case=False, na=False)]
    if idle_assets and idle_assets in ["Data", "Relationships", "Know How", "Physical Assets"]:
        df = df[df[idle_assets] == 1]

    if df.empty:
        return jsonify({"error": "No cases found matching your filters."}), 404

    # Generate case summaries
    case_summaries = df[["Company", "Industry1stOrder", "Strategy", "HACK", "TypeOfPlatform", "Short Case Text"]].to_dict(orient="records")

    return jsonify({
        "case_summaries": case_summaries,
        "total_results": len(df),
        "message": "Here are the case summaries. Would you like to see a full case, go back, or refine further?"
    })

@app.route('/get_full_case', methods=['GET'])
def get_full_case():
    """Retrieves the full case details for a selected company."""
    
    df = load_cases()
    if df is None:
        return jsonify({"error": "Failed to load database"}), 500

    company_name = request.args.get('company')

    if not company_name:
        return jsonify({"error": "Please provide a company name to retrieve full case details."}), 400

    case = df[df["Company"].str.contains(company_name, case=False, na=False)]

    if case.empty:
        return jsonify({"error": "No matching case found for the given company name."}), 404

    return jsonify({
        "Company": company_name,
        "Full Case Text": case.iloc[0]["Full Case Text"]
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
