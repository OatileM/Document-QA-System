import requests

def test_options():
    response = requests.options('http://127.0.0.1:5000/ask', 
                                headers={
                                    'Origin': 'http://127.0.0.1:5500',
                                    'Access-Control-Request-Method': 'POST'
                                })
    print("OPTIONS Response:")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Content: {response.text}")

def test_post():
    response = requests.post('http://127.0.0.1:5000/ask', 
                             json={'question': 'What is AWS?'},
                             headers={'Content-Type': 'application/json'})
    print("\nPOST Response:")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Content: {response.text}")

if __name__ == "__main__":
    test_options()
    test_post()
