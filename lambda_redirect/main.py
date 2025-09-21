import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    # CORS headers
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Origin,Accept",
        "Access-Control-Allow-Methods": "GET,OPTIONS,POST",
        "Access-Control-Allow-Credentials": "false"
    }
    
    # Handle OPTIONS request for CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps({"message": "CORS preflight"})
        }
    
    # Handle root path request (no shortId)
    short_id = event.get('pathParameters', {}).get('shortId')
    
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

    response = table.get_item(Key={"shortId": short_id})
    item = response.get("Item")

    if not item:
        return {
            "statusCode": 404, 
            "headers": cors_headers,
            "body": json.dumps({"error": "Short ID not found"})
        }

    return {
        "statusCode": 302, 
        "headers": {
            **cors_headers,
            "Location": item['longUrl']
        }
    }
