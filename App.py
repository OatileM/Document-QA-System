import boto3
from flask import Flask, request, jsonify, render_template, make_response
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import BedrockEmbeddings
from langchain.vectorstores import FAISS
import json

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5500"}})

# Set up logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Global variable to store the knowledge base
knowledge_base = None

# Initialize Bedrock client
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'  # replace with your preferred region
)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_document(file_path):
    pdf_reader = PdfReader(file_path)
    text = ""
    
    for page in pdf_reader.pages:
        text += page.extract_text()
        
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    
    embeddings = BedrockEmbeddings(client=bedrock_runtime)
    knowledge_base = FAISS.from_texts(chunks, embeddings)
    
    return knowledge_base

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global knowledge_base
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        knowledge_base = process_document(file_path)
        logger.info(f"File {filename} uploaded and processed successfully")
        return jsonify({'message': 'File uploaded successfully'}), 200
    return jsonify({'error': 'File type not allowed'}), 400


@app.route('/ask', methods=['POST', 'OPTIONS'])
def ask_question():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://127.0.0.1:5500')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    global knowledge_base
    data = request.json
    question = data.get('question')
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    if knowledge_base is None:
        return jsonify({'error': 'No document has been uploaded yet'}), 400
    
    try:
        docs = knowledge_base.similarity_search(question)
        context = " ".join([doc.page_content for doc in docs])
        
        prompt = f"Human: Using the following context, answer the question. If the answer is not in the context, say 'I don't have enough information to answer that question.'\n\nContext: {context}\n\nQuestion: {question}\n\nAssistant:"
        
        body = json.dumps({
            "prompt": prompt,
            "max_tokens_to_sample": 300,
            "temperature": 0.7,
            "top_p": 0.9,
        })
        
        response = bedrock_runtime.invoke_model(
            body=body,
            modelId="anthropic.claude-v2"  # or another model of your choice
        )
        
        response_body = json.loads(response.get('body').read())
        answer = response_body.get('completion')
        
        logger.info(f"Question answered: {question}")
        return jsonify({'answer': answer}), 200
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        return jsonify({'error': 'An error occurred while processing your question'}), 500


@app.route('/test', methods=['GET'])
def test():
    return "Flask server is working!"

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
