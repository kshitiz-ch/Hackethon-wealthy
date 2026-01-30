import requests
import time
import json
import os
import agent

API_URL = 'http://localhost:8000/api/v1/opportunities/data-dump'
CACHE_FILE = 'ai_cache.json'
SLEEP_SECONDS = 10

# Fallback dummy data if API fails
DUMMY_CLIENTS = [
    {
        "id": "1",
        "name": "Amit Sharma",
        "type": "SIP Stoppage",
        "raw_data": "Stopped 10k monthly SIP in Small Cap Fund after 2 years. Market dip panic suspected."
    },
    {
        "id": "2",
        "name": "Priya Verma",
        "type": "High Cash Balance",
        "raw_data": "Holding 50L in savings account for 6 months. Interested in low risk options."
    },
    {
        "id": "3",
        "name": "Rahul Dubey",
        "type": "Insurance Renewal",
        "raw_data": "Term policy expiring next month. Coverage 1Cr. Married, 2 kids."
    }
]

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Corrupt cache file. Starting fresh.")
    return {}

def save_cache(cache_data):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache_data, f, indent=4)

def fetch_clients():
    try:
        print(f"Fetching data from {API_URL}...")
        response = requests.get(API_URL, timeout=2)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, json.JSONDecodeError):
        print("API failed or not reachable. Using fallback dummy data.")
        return DUMMY_CLIENTS

def main():
    cache = load_cache()
    clients = fetch_clients()
    
    processed_count = 0
    limit = 5

    print(f"Starting processing. Limit: {limit} new clients.")

    for client in clients:
        if processed_count >= limit:
            print("Limit reached. Stopping.")
            break

        client_id = str(client.get('id'))
        
        if client_id in cache:
            print(f"Skipping client {client_id} ({client.get('name')}) - Already in cache.")
            continue

        print(f"Analyzing client {client_id} ({client.get('name')})...")
        
        # Analyze using the agent
        analysis_result = agent.analyze_opportunity(
            client_name=client.get('name', 'Unknown'),
            type=client.get('type', 'Unknown'),
            raw_data=client.get('raw_data', '')
        )

        # Merge result into cache. 
        # We store the analysis along with basic client info for easier viewing later
        cache[client_id] = {
            "client_details": client,
            "analysis": analysis_result,
            "timestamp": time.time()
        }

        save_cache(cache)
        processed_count += 1
        
        print("Analysis saved. Sleeping...")
        time.sleep(SLEEP_SECONDS)

    print("Done.")

if __name__ == "__main__":
    main()
