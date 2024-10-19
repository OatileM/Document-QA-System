# pip install requests
import requests
import os

BASE_URL = 'http://127.0.0.1:5000'

def test_home():
    response = requests.get(f'{BASE_URL}/')
    print("\nGET / Response:")
    print(f"Status Code: {response.status_code}")
    print(f"Content: {response.text}")

def test_test_route():
    response = requests.get(f'{BASE_URL}/test')
    print("\nGET /test Response:")
    print(f"Status Code: {response.status_code}")
    print(f"Content: {response.text}")

def test_options_ask():
    response = requests.options(f'{BASE_URL}/ask', 
                                headers={
                                    'Origin': 'http://127.0.0.1:5500',
                                    'Access-Control-Request-Method': 'POST'
                                })
    print("\nOPTIONS /ask Response:")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Content: {response.text}")

def test_post_ask():
    response = requests.post(f'{BASE_URL}/ask', 
                             json={'question': 'What is AWS?'},
                             headers={'Content-Type': 'application/json'})
    print("\nPOST /ask Response:")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Content: {response.text}")

def test_upload_file():
   
    test_file_path = r'C:\Python Projects\DocumentReader\test-file\test-file.pdf'
    
    if not os.path.exists(test_file_path):
        print(f"\nError: Test file not found at {test_file_path}")
        return

    with open(test_file_path, 'rb') as file:
        files = {'file': file}
        response = requests.post(f'{BASE_URL}/upload', files=files)
    
    print("\nPOST /upload Response:")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Content: {response.text}")

if __name__ == "__main__":
    test_home()
    test_test_route()
    test_upload_file()
    test_options_ask()
    test_post_ask()