import boto3
from flask import Flask, request, jsonify, render_template, make_response
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from PyPDF2 import PdfReader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.vectorstores import FAISS
import json
import logging
from botocore.exceptions import ClientError

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5500"}})

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create the uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    logger.info(f"Created upload folder: {UPLOAD_FOLDER}")

# Global variable to store the knowledge base
knowledge_base = None

# Initialize Bedrock client
try:
    bedrock_runtime = boto3.client(
        service_name='bedrock-runtime',
        region_name='us-east-1'
    )
except Exception as e:
    logger.error(f"Failed to initialize Bedrock client: {str(e)}")
    # Handle the error appropriately

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_document(file_path):
    try:
        # Read PDF
        pdf_reader = PdfReader(file_path)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        # Split text
        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_text(text)
        
        # Create embeddings and knowledge base
        try:
            embeddings = BedrockEmbeddings(
                client=bedrock_runtime,
                model_id="anthropic.claude-v2:1"
            )
            knowledge_base = FAISS.from_texts(chunks, embeddings)
            logger.info(f"Successfully processed document: {file_path}")
            return knowledge_base
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"AWS Bedrock error: {error_code} - {error_message}")
            if error_code == 'AccessDeniedException':
                raise ValueError("Access denied. Please check your AWS credentials and permissions.")
            elif error_code == 'ValidationException':
                raise ValueError(f"Invalid request to Bedrock: {error_message}")
            else:
                raise ValueError(f"Error calling Bedrock: {error_message}")
        except Exception as e:
            logger.error(f"Unexpected error with Bedrock embeddings: {str(e)}")
            raise ValueError(f"Unexpected error processing embeddings: {str(e)}")
    
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"The file {file_path} was not found.")
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise ValueError(f"Error processing document: {str(e)}")

@app.route('/')
def home():
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
        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            knowledge_base = process_document(file_path)
            return jsonify({'message': 'File uploaded and processed successfully'}), 200
        except FileNotFoundError as e:
            return jsonify({'error': str(e)}), 404
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return jsonify({'error': 'An unexpected error occurred'}), 500
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
            modelId="anthropic.claude-v2:1"
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
