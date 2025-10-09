
import json
import boto3
import string
import random
import logging
import os
from urllib.parse import urlparse
from datetime import datetime
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TABLE_NAME', 'URLShortener')
table = dynamodb.Table(table_name)

# Constants
SHORT_CODE_LENGTH = 6
MAX_RETRIES = 5
ALLOWED_PROTOCOLS = ['http', 'https']

class URLShortenerError(Exception):
    """Custom exception for URL shortener errors"""
    pass

def generate_short_code(length=SHORT_CODE_LENGTH):
    """Generate a random short code"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def validate_url(url):
    """Validate URL format and protocol"""
    if not url or not isinstance(url, str):
        return False, "URL is required and must be a string"
    
    try:
        parsed = urlparse(url)
        if not parsed.scheme:
            return False, "URL must include protocol (http:// or https://)"
        if parsed.scheme not in ALLOWED_PROTOCOLS:
            return False, f"Only {ALLOWED_PROTOCOLS} protocols are allowed"
        if not parsed.netloc:
            return False, "URL must include a valid domain"
        return True, None
    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"

def check_short_code_exists(short_code):
    """Check if short code already exists in database"""
    try:
        response = table.get_item(Key={'short_code': short_code})
        return 'Item' in response
    except ClientError as e:
        logger.error(f"Error checking short code existence: {e}")
        raise URLShortenerError("Database error while checking short code")

def create_short_url_record(short_code, long_url, ip_address=None):
    """Create a new short URL record in DynamoDB"""
    try:
        item = {
            'short_code': short_code,
            'long_url': long_url,
            'created_at': datetime.utcnow().isoformat(),
            'click_count': 0,
            'is_active': True
        }
        
        if ip_address:
            item['created_by_ip'] = ip_address
            
        table.put_item(Item=item)
        logger.info(f"Created short URL: {short_code} -> {long_url}")
        return True
    except ClientError as e:
        logger.error(f"Error creating short URL record: {e}")
        raise URLShortenerError("Failed to create short URL")

def get_client_ip(event):
    """Extract client IP from API Gateway event"""
    return event.get('requestContext', {}).get('identity', {}).get('sourceIp')

def get_api_domain(event):
    """Extract API domain from event"""
    return event['requestContext']['domainName']

def lambda_handler(event, context):
    """Lambda handler for creating short URLs"""
    try:
        # Log the incoming event
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Parse request body
        try:
            body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid JSON in request body'})
            }
        
        long_url = body.get('url')
        
        # Validate URL
        is_valid, error_msg = validate_url(long_url)
        if not is_valid:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': error_msg})
            }
        
        # Generate unique short code
        short_code = None
        for attempt in range(MAX_RETRIES):
            candidate = generate_short_code()
            if not check_short_code_exists(candidate):
                short_code = candidate
                break
        
        if not short_code:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Failed to generate unique short code'})
            }
        
        # Get client IP for tracking
        client_ip = get_client_ip(event)
        
        # Create short URL record
        create_short_url_record(short_code, long_url, client_ip)
        
        # Build response
        domain = get_api_domain(event)
        short_url = f"https://{domain}/{short_code}"
        
        response_data = {
            'short_url': short_url,
            'short_code': short_code,
            'original_url': long_url,
            'created_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Successfully created short URL: {short_url}")
        
        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response_data)
        }
        
    except URLShortenerError as e:
        logger.error(f"URL Shortener Error: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }
