import boto3, json, os, string, random
from urllib.parse import urlparse

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def generate_short_id(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def is_valid_url(url):
    try:
        parsed = urlparse(url)
        return all([parsed.scheme in ("http", "https"), parsed.netloc])
    except Exception:
        return False

def lambda_handler(event, context):
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        long_url = body.get('longUrl')

        if not long_url or not is_valid_url(long_url):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid or missing longUrl"})
            }

        # Generate unique shortId
        short_id = generate_short_id()

        # Save item in DynamoDB
        table.put_item(Item={
            "shortId": short_id,
            "longUrl": long_url,
            "hits": 0
        })

        # Construct short URL from request host
        domain = event['headers'].get('Host', 'example.com')
        stage = event.get('requestContext', {}).get('stage', '')
        base_url = f"https://{domain}/{stage}" if stage else f"https://{domain}"
        short_url = f"{base_url}/{short_id}"

        return {
            "statusCode": 200,
            "body": json.dumps({"shortId": short_id, "shortUrl": short_url})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
