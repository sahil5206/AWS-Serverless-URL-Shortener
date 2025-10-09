
import json
import boto3
import string
import random

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('URLShortener')

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    long_url = body.get('url')

    if not long_url:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'URL is required'})
        }

    short_code = generate_short_code()

    table.put_item(Item={
        'short_code': short_code,
        'long_url': long_url
    })

    domain = event['requestContext']['domainName']
    return {
        'statusCode': 200,
        'body': json.dumps({
            'short_url': f"https://{domain}/{short_code}"
        })
    }
