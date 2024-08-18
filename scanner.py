import pytesseract
from PIL import Image
from openai import OpenAI
import pandas as pd
import re

client = OpenAI(api_key='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')

# Function to extract text from an image
def extract_text_from_image(image_path):
    try:
        # Open image using PIL
        image = Image.open(image_path)
        # Use Tesseract to do OCR on the image
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return None
    
# Function to send text to OpenAI for analysis
def analyze_receipt_text(receipt_text):
    try:
        # Construct the messages for OpenAI Chat API
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": (
                "Analyze the following receipt text and extract the items, their values, costs, and any taxes, include tax as an item:\n\n"
                f"{receipt_text}\n\n"
                "Format the response as a list of items with their costs."
            )}
        ]

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500
        )

        # Extracting the content from the response
        result = response.choices[0].message.content
        return result
    except Exception as e:
        print(f"Error analyzing receipt text: {e}")
        return None

# Function to clean item names by removing special characters
def clean_item_name(item_name):
    # Use regex to remove special characters and keep only alphabets, numbers, and spaces
    cleaned_name = re.sub(r'[^a-zA-Z0-9\s]', '', item_name)
    return cleaned_name.strip()

# Function to convert the response to a Pandas DataFrame
def response_to_dataframe(response_text):
    try:
        # Split response text into lines
        lines = response_text.strip().split("\n")
        data = []
        
        # Regular expression to find numbers (with optional decimal points)
        currency_pattern = r"[-+]?\$?\d*\.?\d+"

        # Parse each line assuming it's in the format "Item: Cost"
        for line in lines:
            parts = line.split(":")
            if len(parts) == 2:
                item_name = clean_item_name(parts[0].strip())
                
                # Extract cost using regex, removing any currency symbols
                cost_match = re.search(currency_pattern, parts[1])
                
                # Convert extracted string to float
                cost = float(cost_match.group().replace("$", "")) if cost_match else 0.0
                
                data.append([item_name, cost])

        # Create a DataFrame with the parsed data
        df = pd.DataFrame(data, columns=["Item", "Cost"])
        return df
    except Exception as e:
        print(f"Error converting response to DataFrame: {e}")
        return None

# Example usage
if __name__ == "__main__":
    image_path = 'receipt.jpg'  # Path to your receipt image file
    receipt_text = extract_text_from_image(image_path)

    if receipt_text:
        print("Extracted Text:\n", receipt_text)
        analysis = analyze_receipt_text(receipt_text)
        
        if analysis:
            print("\nAnalysis:\n", analysis)
            df = response_to_dataframe(analysis)
            if df is not None:
                print("\nDataFrame:\n", df)
