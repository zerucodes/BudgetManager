import pdfplumber
import pandas as pd
import re
import os

"""
    Convert PDFs in bin folder to csv
    Tested for Bank of America End of Year Credit Card statement downloads
"""

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def parse_text_to_data(text):
    lines = text.split("\n")
    bofa_eoy_pattern = re.compile(r'\d{1,2}/\d{1,2}/\d{1,4}\s.*\d{1,4}')
    data = []
    junk = []
    for line in lines:
        if bofa_eoy_pattern.match(line):
            data.append(line)
        else:
            junk.append(line)
            print(f'Discarding text from data: {line}')

    return data

def parse_data_to_csv(data):
    transactions = []
    date_pattern = re.compile(r"(\d{1,2}/\d{1,2}/\d{1,4})")
    amount_pattern = re.compile(r"(-?\d+\.\d{2})$")
    
    for line in data:
        date_match = date_pattern.match(line)
        amount_match = amount_pattern.search(line)
        
        if date_match and amount_match:
            date = date_match.group(1)
            amount = amount_match.group(1)
            description = line[date_match.end():amount_match.start()].strip()
            transactions.append([date, description, amount])
    return transactions

def save_to_csv(transactions, csv_path):
    df = pd.DataFrame(transactions, columns=["Date", "Description", "Amount"])
    csv_path = csv_path.replace(".pdf",".csv")
    df.to_csv(csv_path, index=False)

def pdf_to_csv(pdf_path, csv_path):
    text = extract_text_from_pdf(pdf_path)
    data = parse_text_to_data(text)
    csv = parse_data_to_csv(data)
    save_to_csv(csv, csv_path)

def process_files(input_dir, output_dir, file_extension, processor):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for root, _, files in os.walk(input_dir):
        for filename in files:
            if filename.endswith(file_extension):
                input_path = os.path.join(root, filename)
                relative_path = os.path.relpath(input_path, input_dir)
                output_path = os.path.join(output_dir, relative_path)
                output_dir_path = os.path.dirname(output_path)
                
                if not os.path.exists(output_dir_path):
                    os.makedirs(output_dir_path)
                
                processor(input_path,output_path)
                

if __name__ == "__main__":

    process_files("bin","bin",".pdf",pdf_to_csv)
