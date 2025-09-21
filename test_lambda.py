import json

# Test the Lambda function logic
def test_lambda():
    # Simulate API Gateway event for root path
    event = {
        "httpMethod": "GET",
        "pathParameters": None,
        "body": None
    }
    
    # Simulate the Lambda function logic
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,OPTIONS"
    }
    
    # Handle OPTIONS request for CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps({"message": "CORS preflight"})
        }
    
    # Handle root path request (no shortId)
    short_id = event.get('pathParameters', {}).get('shortId') if event.get('pathParameters') else None
    
    if not short_id:
        # This is a request to the root path - return simple HTML page
        return {
            "statusCode": 200,
            "headers": {
                **cors_headers,
                "Content-Type": "text/html"
            },
            "body": "<html><body><h1>URL Shortener API</h1><p>Use POST /shorten to create short URLs</p><p>Use GET /{shortId} to redirect</p></body></html>"
        }
    
    return {"statusCode": 404, "body": "Not found"}

if __name__ == "__main__":
    result = test_lambda()
    print(json.dumps(result, indent=2))
