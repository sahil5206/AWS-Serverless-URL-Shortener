import json
import boto3
import os
import string
import random

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def generate_short_id(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def lambda_handler(event, context):
    # CORS headers
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Origin,Accept",
        "Access-Control-Allow-Methods": "POST,OPTIONS,GET",
        "Access-Control-Allow-Credentials": "false"
    }
    
    # Handle OPTIONS request for CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps({"message": "CORS preflight"})
        }
    
    try:
        body = json.loads(event.get("body", "{}"))
        long_url = body.get("longUrl")
    except:
        return {
            "statusCode": 400, 
            "headers": cors_headers,
            "body": json.dumps({"error": "Invalid JSON"})
        }

    if not long_url:
        return {
            "statusCode": 400, 
            "headers": cors_headers,
            "body": json.dumps({"error": "Missing 'longUrl'"})
        }

    short_id = generate_short_id()
    table.put_item(Item={"shortId": short_id, "longUrl": long_url})

    return {
        "statusCode": 200, 
        "headers": cors_headers,
        "body": json.dumps({"shortId": short_id})
    }
