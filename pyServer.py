from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from PIL import Image
import pytesseract
import pandas as pd
import re
from openai import OpenAI

client = OpenAI(api_key='xx')

app = Flask(__name__)
CORS(app)

def extract_text_from_image(image):
    try:
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return None
    
def analyze_receipt_text(receipt_text):
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": (
                "Analyze the following receipt text and extract the items, their values, costs, and any taxes, include tax as an item:\n\n"
                f"{receipt_text}\n\n"
                "Format the response as a list of items with their costs. Send the data in exact format item : cost"
            )}
        ]

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500
        )

        result = response.choices[0].message['content']
        return result
    except Exception as e:
        print(f"Error analyzing receipt text: {e}")
        return None

def clean_item_name(item_name):
    cleaned_name = re.sub(r'[^a-zA-Z0-9\s]', '', item_name)
    return cleaned_name.strip()

def response_to_dataframe(response_text):
    try:
        lines = response_text.strip().split("\n")
        data = []
        
        currency_pattern = r"[-+]?\$?\d*\.?\d+"

        for line in lines:
            parts = line.split(":")
            if len(parts) == 2:
                item_name = clean_item_name(parts[0].strip())
                cost_match = re.search(currency_pattern, parts[1])
                cost = float(cost_match.group().replace("$", "")) if cost_match else 0.0
                data.append([item_name, cost])

        df = pd.DataFrame(data, columns=["Item", "Cost"])
        return df
    except Exception as e:
        print(f"Error converting response to DataFrame: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        image = Image.open(file)
        text = extract_text_from_image(image)

        if text is None:
            return jsonify({'error': 'Error extracting text from image'}), 500

        analysis = analyze_receipt_text(text)
        print(analysis)

        if analysis is None:
            return jsonify({'error': 'Error analyzing receipt text'}), 500

        df = response_to_dataframe(analysis)
        print("\nDataFrame:\n", df)

        if df is None:
            return jsonify({'error': 'Error converting response to DataFrame'}), 500

        # Convert DataFrame to list of dictionaries
        table_data = df.to_dict(orient='records')

        return render_template('result.html', table_data=table_data, text=text)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/submit', methods=['POST'])
def submit_data():
    try:
        form_data = request.form
        items = []

        for i in range(len(form_data)//9):
            item = {
                'Item': form_data.get(f'Item_{i}', ''),
                'Cost': form_data.get(f'Cost_{i}', ''),
                'Sudhanva': 'Sudhanva_' + str(i) in form_data,
                'Kartik R': 'Kartik_R_' + str(i) in form_data,
                'Karthik': 'Karthik_' + str(i) in form_data,
                'Sarthak A': 'Sarthak_A_' + str(i) in form_data,
                'Sarthak D': 'Sarthak_D_' + str(i) in form_data,
                'Aaditya': 'Aaditya_' + str(i) in form_data,
                'Sunny': 'Sunny_' + str(i) in form_data,
                'Include or not': 'Include_' + str(i) in form_data
            }
            items.append(item)

        # Process the data (e.g., save to database, send to Splitwise)
        print("Submitted Data:", items)

        return jsonify({'message': 'Data submitted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
