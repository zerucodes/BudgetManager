import csv
import re
import os
import pandas as pd
from collections import defaultdict
from dateutil import parser 
import sqlite3
from datetime import date
# Define common regex patterns
re_header = re.compile(r'(.*date)(.*description)(.*amount)',re.IGNORECASE)
re_date = re.compile(r'\d{1,2}/\d{1,2}/\d{1,4}')
re_amount = re.compile(r'\d{1,5}')
# Define regex patterns for each vendor



def identify_vendor(file_path):
    headers = []
    indeces = {
    "date" : -1 , "description": -1, "amount": -1
    }
    charges = 0 #  track if amount holds pos/neg values
    counts = defaultdict(int)
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        # Check first 15 lines for header (index) information
        for i, row in enumerate(reader):
            try:        
                if i >= 15:
                    break
                line = ','.join(row)
                # Find the line containing header information
                if (re_header.search(line)):
                    headers = row
                    for header in headers:
                        for index in indeces:
                            if index in header.lower():
                                # Populate indeces with col #
                                # indeces[index] = [h.lower() for h in headers].index(index)
                                if (indeces[index] == -1):
                                    indeces[index] =  next((i for i, s in enumerate(headers) if index in s.lower()), None)
                    continue
                # When headers are defined, figure out if amount is negative or positive
                if headers:
                    _amount = row[indeces["amount"]]
                    _amount = _amount.replace('"','').replace("'",'').replace(",",'')
                    _amount = float(_amount)
                    if _amount < 0 :
                        charges -=1
                    else:
                        charges +=1
            except Exception as e:
                print(e)
    # If charges is > 0 (more postive amounts) it is likely tracking charges with postive numbers
    invert = charges > 0
    return headers,indeces,invert

def normalize_charges(file_path, headers,indeces,invert):
    normalized_data = []
    normalized_headers = ['Date','Description','Amount']
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            try:
                _date = row[indeces['date']]
                desc = row[indeces['description']]
                amount = row[indeces['amount']]
                amount = amount.replace('"','').replace("'",'').replace(",",'')
                amount = float(amount)

                try:
                    date = parser.parse(_date)
                except Exception as e:
                    print(f"Skipping {row} due to bad date {_date}")
                    continue
                
                if invert:
                    amount *= -1
                normalized_row = [date,desc,amount]
              
                normalized_data.append(normalized_row)
            except Exception as e:
                print(f"Skipping {row} due to {e}")
            
    
    return normalized_data


def save_to_csv(transactions, csv_path):
    df = pd.DataFrame(transactions, columns=["Date", "Description", "Amount"])
    csv_path = csv_path.replace(".pdf",".csv")
    df.to_csv(csv_path, index=False)

def save_to_db(transactions):
    conn = sqlite3.connect('local.sqlite')
    cursor = conn.cursor()

    # SQL command to insert a new record
    insert_sql = """
    INSERT INTO transactions (date, description, amount)
    VALUES (?, ?, ?)
    """

    for t in transactions:
        data = (t[0], t[1], t[2]) 
        try:
            cursor.execute(insert_sql, data)
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
    conn.commit()
    conn.close()

def process_dir(input_dir='bin',file_extension='.csv'):
    normalized_data = []
    for root, _, files in os.walk(input_dir):
        for filename in files:
            if filename.lower().endswith(file_extension):
                print(f'Processing {filename}')
                input_path = os.path.join(root, filename)
                headers,indeces,invert = identify_vendor(input_path)
                normalized_data.extend(normalize_charges(input_path, headers,indeces,invert))
    save_to_csv(normalized_data,'out/aggregated.csv')
    save_to_db(normalized_data)


process_dir()

