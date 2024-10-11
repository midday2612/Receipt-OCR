import os
import json
import requests
import uuid
import time
import pandas as pd  
import openai
from config import api_key, api_url, secret_key, image_file, json_file_path, excel_file_path

os.environ["OPENAI_API_KEY"] = api_key

class OpenAIClient:
    def __init__(self, api_key):
        openai.api_key = api_key

    def chat(self, messages):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Ensure this is the correct model name
            messages=messages
        )
        return response.choices[0].message['content']

request_json = {
    'images': [
        {
            'format': 'jpg',
            'name': 'receipt'
        }
    ],
    'requestId': str(uuid.uuid4()),
    'version': 'V2',
    'timestamp': int(round(time.time() * 1000))
}

payload = {'message': json.dumps(request_json).encode('UTF-8')}
files = [
    ('file', open(image_file, 'rb'))
]
headers = {
    'X-OCR-SECRET': secret_key
}

response = requests.post(api_url, headers=headers, data=payload, files=files)
json_data = response.json()

# Transform response content into receipt format
string_result = ''
for i in json_data.get('images', [{}])[0].get('fields', []):
    linebreak = '\n' if i.get('lineBreak', False) else ''
    string_result += i.get('inferText', '') + linebreak

print(string_result)

# Save response to JSON file for analysis
with open(json_file_path, 'w', encoding='utf-8') as file:
    json.dump(json_data, file, ensure_ascii=False, indent=4)

client = OpenAIClient(api_key)

# Call ChatGPT for analysis
response_content = client.chat([
    {"role": "system", "content": "You are a helpful assistant to analyze the purchase date, items, quantity, and amount from the receipt and output it in JSON format."},
    {"role": "user", "content": f'Please analyze the following receipt: {string_result}. Only extract items and date. If an item is free, set its cost to 0.'},
])

# Parse the response
try:
    data = json.loads(response_content)
except json.JSONDecodeError as e:
    print(f"Error decoding JSON: {e}")
    data = {}

# Convert to pandas DataFrame and add purchase date
if 'items' in data and 'purchase_date' in data:
    df = pd.DataFrame(data['items'])
    df['purchase_date'] = data['purchase_date']

    # Save DataFrame to Excel
    df.to_excel(excel_file_path, index=False)
    print(f"Excel file has been saved to '{excel_file_path}'.")
else:
    print("The expected keys 'items' or 'purchase_date' are missing in the response.")
