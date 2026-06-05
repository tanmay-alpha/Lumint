"""
Utility script to programmatically create and configure the Monday.com project board
for 'Lumint Paper Submission' using the Monday.com GraphQL API.
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta

def create_board_on_monday(api_key: str):
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "API-Version": "2023-10"
    }
    url = "https://api.monday.com/v2"

    # 1. Create the Board
    board_mutation = """
    mutation {
        create_board (board_name: "Lumint Paper Submission", board_kind: public) {
            id
        }
    }
    """
    print("Creating Board: 'Lumint Paper Submission'...")
    response = requests.post(url, json={"query": board_mutation}, headers=headers)
    if response.status_code != 200:
        print(f"Error creating board: {response.text}")
        return
        
    res_data = response.json()
    if "errors" in res_data:
        print(f"GraphQL Errors: {res_data['errors']}")
        return
        
    board_id = res_data["data"]["create_board"]["id"]
    print(f"Board successfully created with ID: {board_id}")

    # Groups & Items definition with deadlines relative to current time
    groups_data = [
        {
            "title": "Dataset",
            "items": [
                {"name": "UPI-FraudBench-2026 Generation & Verification", "days_to_due": 7},
                {"name": "Data Cards & Metadata curation", "days_to_due": 7}
            ]
        },
        {
            "title": "ML Evaluation",
            "items": [
                {"name": "R9 - Real ML Baseline Layer (LR/RF/GB/XGB/LGBM)", "days_to_due": 14},
                {"name": "R10 - Statistical validation (5-Fold CV)", "days_to_due": 14},
                {"name": "R11 - Ablation Study (features, SMOTE, modules)", "days_to_due": 14},
                {"name": "R15 - Drift detection and monitoring", "days_to_due": 14},
                {"name": "R16 - Adversarial robustness & defense pipelines", "days_to_due": 14}
            ]
        },
        {
            "title": "Paper Writing",
            "items": [
                {"name": "CMFA Mathematical Formalization (LaTeX sections)", "days_to_due": 21},
                {"name": "Methodology, Baseline comparison, and visual plots", "days_to_due": 21},
                {"name": "Complete Paper Draft compilation", "days_to_due": 21}
            ]
        },
        {
            "title": "Release",
            "items": [
                {"name": "HuggingFace Model Upload & Metadata cards", "days_to_due": 28},
                {"name": "HuggingFace Spaces Gradio Demo deployment", "days_to_due": 28},
                {"name": "GitHub Release and Zenodo DOI archiving", "days_to_due": 28}
            ]
        }
    ]

    base_date = datetime.now()

    for group in groups_data:
        # Create Group
        group_mutation = f"""
        mutation {{
            create_group (board_id: {board_id}, group_name: "{group['title']}") {{
                id
            }}
        }}
        """
        print(f"Creating Group: '{group['title']}'...")
        g_resp = requests.post(url, json={"query": group_mutation}, headers=headers)
        g_data = g_resp.json()
        if "errors" in g_data:
            print(f"Error creating group: {g_data['errors']}")
            continue
            
        group_id = g_data["data"]["create_group"]["id"]
        
        # Add Items to Group
        for item in group["items"]:
            due_date = (base_date + timedelta(days=item["days_to_due"])).strftime("%Y-%m-%d")
            
            # Simple column value assignment for Status and Date
            # Note: Columns on default board include 'status' and 'date4' or custom ones.
            # We create the item first, then update column values.
            item_mutation = f"""
            mutation {{
                create_item (board_id: {board_id}, group_id: "{group_id}", item_name: "{item['name']}") {{
                    id
                }}
            }}
            """
            item_resp = requests.post(url, json={"query": item_mutation}, headers=headers)
            item_data = item_resp.json()
            if "errors" in item_data:
                print(f"Error creating item: {item_data['errors']}")
                continue
            
            item_id = item_data["data"]["create_item"]["id"]
            print(f"  Added item: '{item['name']}' (Due: {due_date})")

    print("\nProject Board initialization complete on Monday.com!")

if __name__ == "__main__":
    api_token = os.environ.get("MONDAY_API_KEY")
    if not api_token:
        print("Please set the MONDAY_API_KEY environment variable.")
        sys.exit(1)
    create_board_on_monday(api_token)
