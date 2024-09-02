import base64
from PyPDF2 import PdfReader
import io
import spacy
import re
from flask import Flask, jsonify, request



app = Flask(__name__)

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

@app.route('/extract', methods=['POST'])
def extractInfo():
    data = request.json.get('base64_string')
    allText=''
    if not data:
        return jsonify({'error': 'No base64_string provided'}), 400
    try:
        pdf_data = base64.b64decode(str(data))

        with io.BytesIO(pdf_data) as pdf_file:
            reader = PdfReader(pdf_file)
            number_of_pages = len(reader.pages)
            
            for page_number in range(number_of_pages):
                page = reader.pages[page_number]
                text = page.extract_text()
                allText = allText + text
                # print(f"Page {page_number + 1} content:\n{text}")
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
    ###################################################################################################
    
    processed_text = re.sub(r'(?<!\s)([A-Z][a-z]+)', r' \1', allText)

    # Process the text with spaCy
    doc = nlp(allText)
    print("allText",allText)

    # Extract named entities labeled as PERSON
    names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    print("names",names)

    potential_names = re.findall(r'\b[A-Z][A-Za-z]+ [A-Z][A-Za-z]+\b', allText)
    print("potential_names",potential_names)

    # Combine spaCy and manually detected names and remove duplicates
    all_detected_names = list(set(names + potential_names))

    print("all_detected_names",all_detected_names)

    # Filter the detected names to exclude common non-human terms
    filtered_names = [name for name in all_detected_names if name.isalpha()]

    #######################################################################################################


    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'\+?\d[\d\s-]{7,}\d'
    emails = re.findall(email_pattern, allText)
    phone_numbers = re.findall(phone_pattern, allText)
    return jsonify({
        'Names':filtered_names,
        'emails': emails,
        'phone_numbers': phone_numbers
    })



    

    # print("Filtered detected human names:", filtered_names)
    # import nltk
    # from nltk.tag.stanford import  StanfordNERTagger
    # stanford_ner_jar = 'path/to/stanford-ner.jar'
    # stanford_ner_model = 'path/to/english.muc.7class.distsim.crf.ser.gz'

    # # Initialize the tagger
    # st = StanfordNERTagger(model_filename=stanford_ner_model, path_to_jar=stanford_ner_jar)


    # for sent in nltk.sent_tokenize(allText):
    #     tokens = nltk.tokenize.word_tokenize(sent)
    #     tags = st.tag(tokens)
    #     for tag in tags:
    #         if tag[1]=='PERSON': print("HumanName",tag)
   

    # print("Detected Emails:", emails)
    # print("Detected Phone Numbers:", phone_numbers)
    



if __name__ == '__main__':
    app.run(debug=True)