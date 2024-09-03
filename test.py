import base64
from PyPDF2 import PdfReader
import io
import spacy
import re
from flask import Flask, jsonify, request
import pandas as pd
import Levenshtein


app = Flask(__name__)

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")
stopWords =['naukri','linkedin','resume','salesforce','heroku','mulesoft','software','engineer',
            'computer','science','pdf']

@app.route('/extract', methods=['POST'])
def extract_info():
    # Extract the base64 string from the request
    data = request.json.get('base64_string')
    fileName = request.json.get('fileName')
    
    if not data:
        return jsonify({'error': 'No base64_string provided','status':'Failed'}), 400
    
    try:
        # Decode the base64 string
        pdf_data = base64.b64decode(data)
        
        # Read the PDF content
        all_text = ""
        with io.BytesIO(pdf_data) as pdf_file:
            reader = PdfReader(pdf_file)
            number_of_pages = len(reader.pages)
            
            for page_number in range(number_of_pages):
                page = reader.pages[page_number]
                text = page.extract_text()
                if text:
                    all_text += text
    except Exception as e:
        return jsonify({'error': 'Failed to process the PDF: ' + str(e),'status':'Failed'}), 400
        
    emails,phone_numbers = extractEmailAndPhone(all_text)
    filtered_names = extractName(all_text)
    CandidateNames = calculateSimilarity(fileName , filtered_names , stopWords)
    
    return jsonify({
        'data':{
            'names': CandidateNames.iloc[0]['Name'],
            'emails': emails,
            'phone_numbers': phone_numbers
        },
        'status':"Success",
        }), 200


def extractEmailAndPhone(text):
    try:
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        phone_pattern = r'\+?\d[\d\s-]{7,}\d'
        
        emails = re.findall(email_pattern, text)
        phone_numbers = re.findall(phone_pattern, text)
        return emails,phone_numbers
    except Exception as e:
        return ['Error in Finding Email'],['Error in Finding Phone']

def extractName(text):
    try:
        processed_text = re.sub(r'(?<!\s)([A-Z][a-z]+)', r' \1', text)
        doc = nlp(processed_text)
        names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
        potential_names = re.findall(r'\b[A-Z][A-Za-z]+\s[A-Z][A-Za-z]+\b', processed_text)
        all_detected_names = list(set(names + potential_names))
        filtered_names = [name for name in all_detected_names if name.replace(" ", "")]
        
        return filtered_names
    except:
        return ['Error in Finding Name']

def calculateSimilarity(string1 , string2 , stopWords):
    df = pd.DataFrame(columns=['Name', 'score'])
    claenstring1 = re.sub(r'[^A-Za-z]', '', string1).lower()
    for word in stopWords:
            claenstring1 = claenstring1.replace(word, "")
    for name in string2:
    # Calculate Levenshtein distance
        claenstring2 = re.sub(r'[^A-Za-z]', '', name).lower()
        for word in stopWords:
            claenstring2 = claenstring2.replace(word, "")
        
        lev_distance = Levenshtein.distance(claenstring1, claenstring2)
        # Calculate similarity score (1 - normalized Levenshtein distance)
        similarity_score = 1 - (lev_distance / max(len(claenstring1), len(claenstring2)))

        # Append the new row
        new_data = pd.DataFrame([{'Name': claenstring2, 'score': similarity_score}])
        df = pd.concat([df, new_data], ignore_index=True)
    df_sorted = df.sort_values(by='score', ascending=False)
    return df_sorted

if __name__ == '__main__':
    app.run(debug=True)
