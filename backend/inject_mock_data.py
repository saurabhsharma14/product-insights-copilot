import sqlite3
import json

def mock_data():
    db_path = 'data/groww_intelligence.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get latest completed run
    cursor.execute("SELECT batch_id FROM analysis_runs WHERE status='completed' ORDER BY created_at DESC LIMIT 1")
    row = cursor.fetchone()
    if not row:
        print("No completed runs found")
        return
        
    batch_id = row[0]
    print(f"Injecting data into {batch_id}")
    
    themes = [
        {
            "theme_name": "Hidden Charges & AMC",
            "description": "Users complain about unexpected account maintenance charges and hidden fees when trying to close accounts.",
            "sentiment": "negative",
            "count": 342
        },
        {
            "theme_name": "Smooth Onboarding",
            "description": "Users praise the simple and paperless KYC process during initial account setup.",
            "sentiment": "positive",
            "count": 215
        },
        {
            "theme_name": "App Crashes",
            "description": "Frequent crashes reported during peak trading hours resulting in missed opportunities.",
            "sentiment": "negative",
            "count": 128
        }
    ]
    
    fee_issue = {
        "fee_type": "Account Maintenance Charge (AMC)",
        "user_confusion": "Users are confused because the marketing materials claim 'Zero AMC', but they are being charged ₹120 quarterly. They do not realize this only applies to the first year or specific account tiers.",
        "severity_score": 9
    }
    
    product_pulse = {
        "title": "High Friction in Fee Transparency & Stability",
        "summary": "While onboarding remains a strong acquisition channel due to its seamless UX, user retention is severely threatened by unexpected AMC charges and app instability during market open. Immediate communication clarity regarding the fee structure is required.",
        "key_findings": [
            "AMC confusion accounts for 41% of all negative reviews this week.",
            "App crashes between 9:15 AM - 10:00 AM spike negative sentiment by 2.4x.",
            "Onboarding completion rates are praised but post-onboarding trust drops."
        ]
    }
    
    fee_explainer = {
        "explanation_for_user": "We understand the confusion. Groww offers Zero AMC for the first year. From the second year onwards, a nominal maintenance charge of ₹120 per quarter applies to keep your account active and secure.",
        "suggested_ui_changes": [
            "Add a clear tooltip next to 'Zero AMC' mentioning 'for 1st year'.",
            "Send an in-app notification 30 days before the first AMC deduction.",
            "Create a dedicated 'Charges & Fees' transparent dashboard in the profile section."
        ]
    }
    
    cursor.execute('''
        UPDATE analysis_runs 
        SET themes = ?, fee_issues = ?, product_pulse = ?, fee_explainer = ?
        WHERE batch_id = ?
    ''', (json.dumps(themes), json.dumps(fee_issue), json.dumps(product_pulse), json.dumps(fee_explainer), batch_id))
    
    conn.commit()
    conn.close()
    print("Injected successfully.")

if __name__ == "__main__":
    mock_data()
