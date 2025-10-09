
import json
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('URLShortener')

def lambda_handler(event, context):
    short_code = event['pathParameters']['shortCode']

    response = table.get_item(Key={'short_code': short_code})
    item = response.get('Item')

    if not item:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Short URL not found'})
        }

    return {
        'statusCode': 301,
        'headers': {
            'Location': item['long_url']
        },
        'body': ''
    }
