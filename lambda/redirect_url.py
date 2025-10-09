
import json
import boto3
import logging
import os
from datetime import datetime
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

def get_client_ip(event):
    """Extract client IP from API Gateway event"""
    return event.get('requestContext', {}).get('identity', {}).get('sourceIp')

def get_user_agent(event):
    """Extract User-Agent from API Gateway event"""
    return event.get('headers', {}).get('User-Agent', 'Unknown')

def increment_click_count(short_code):
    """Increment the click count for a short URL"""
    try:
        table.update_item(
            Key={'short_code': short_code},
            UpdateExpression='ADD click_count :inc',
            ExpressionAttributeValues={':inc': 1},
            ConditionExpression='attribute_exists(short_code)'
        )
    except ClientError as e:
        # Log the error but don't fail the redirect
        logger.warning(f"Failed to increment click count for {short_code}: {e}")

def log_redirect_analytics(short_code, client_ip, user_agent):
    """Log redirect analytics (optional - can be enhanced with CloudWatch Insights)"""
    logger.info(json.dumps({
        'event': 'redirect',
        'short_code': short_code,
        'client_ip': client_ip,
        'user_agent': user_agent,
        'timestamp': datetime.utcnow().isoformat()
    }))

def lambda_handler(event, context):
    """Lambda handler for redirecting short URLs"""
    try:
        # Log the incoming event
        logger.info(f"Received redirect event: {json.dumps(event)}")
        
        # Extract short code from path parameters
        path_params = event.get('pathParameters', {})
        short_code = path_params.get('shortCode')
        
        if not short_code:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Short code is required'})
            }
        
        # Validate short code format (alphanumeric only)
        if not short_code.isalnum():
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid short code format'})
            }
        
        # Get analytics data
        client_ip = get_client_ip(event)
        user_agent = get_user_agent(event)
        
        # Retrieve the URL from DynamoDB
        try:
            response = table.get_item(Key={'short_code': short_code})
            item = response.get('Item')
        except ClientError as e:
            logger.error(f"Database error retrieving short code {short_code}: {e}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Internal server error'})
            }
        
        if not item:
            logger.info(f"Short code not found: {short_code}")
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Short URL not found'})
            }
        
        # Check if the short URL is active
        if not item.get('is_active', True):
            logger.info(f"Inactive short code accessed: {short_code}")
            return {
                'statusCode': 410,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Short URL is no longer active'})
            }
        
        long_url = item['long_url']
        
        # Increment click count asynchronously (non-blocking)
        try:
            increment_click_count(short_code)
        except Exception as e:
            # Don't fail the redirect if analytics fail
            logger.warning(f"Failed to update click count: {e}")
        
        # Log analytics
        log_redirect_analytics(short_code, client_ip, user_agent)
        
        logger.info(f"Redirecting {short_code} to {long_url}")
        
        # Return redirect response
        return {
            'statusCode': 301,
            'headers': {
                'Location': long_url,
                'Cache-Control': 'no-cache'
            },
            'body': ''
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in redirect handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }
