import json
import boto3
import logging
import os
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TABLE_NAME', 'URLShortener')
table = dynamodb.Table(table_name)

class URLShortenerError(Exception):
    """Custom exception for URL shortener errors"""
    pass

def get_short_url_stats(short_code):
    """Get statistics for a specific short URL"""
    try:
        response = table.get_item(Key={'short_code': short_code})
        item = response.get('Item')
        
        if not item:
            return None
            
        return {
            'short_code': short_code,
            'original_url': item.get('long_url'),
            'created_at': item.get('created_at'),
            'click_count': item.get('click_count', 0),
            'is_active': item.get('is_active', True)
        }
    except ClientError as e:
        logger.error(f"Database error retrieving stats for {short_code}: {e}")
        raise URLShortenerError("Failed to retrieve URL statistics")

def lambda_handler(event, context):
    """Lambda handler for getting URL analytics"""
    try:
        # Log the incoming event
        logger.info(f"Received analytics event: {json.dumps(event)}")
        
        # Extract short code from path parameters
        path_params = event.get('pathParameters', {})
        short_code = path_params.get('shortCode')
        
        if not short_code:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Short code is required'})
            }
        
        # Validate short code format
        if not short_code.isalnum():
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid short code format'})
            }
        
        # Get statistics
        stats = get_short_url_stats(short_code)
        
        if not stats:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Short URL not found'})
            }
        
        logger.info(f"Retrieved analytics for {short_code}")
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(stats)
        }
        
    except URLShortenerError as e:
        logger.error(f"URL Shortener Error: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
    except Exception as e:
        logger.error(f"Unexpected error in analytics handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }
