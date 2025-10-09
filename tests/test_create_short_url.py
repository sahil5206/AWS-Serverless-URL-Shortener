import json
import pytest
from unittest.mock import patch, MagicMock
from lambda.create_short_url import (
    lambda_handler,
    validate_url,
    generate_short_code,
    check_short_code_exists,
    create_short_url_record
)


class TestValidateUrl:
    def test_valid_http_url(self):
        is_valid, error = validate_url("http://example.com")
        assert is_valid is True
        assert error is None

    def test_valid_https_url(self):
        is_valid, error = validate_url("https://example.com")
        assert is_valid is True
        assert error is None

    def test_url_without_protocol(self):
        is_valid, error = validate_url("example.com")
        assert is_valid is False
        assert "protocol" in error

    def test_url_with_invalid_protocol(self):
        is_valid, error = validate_url("ftp://example.com")
        assert is_valid is False
        assert "protocols are allowed" in error

    def test_empty_url(self):
        is_valid, error = validate_url("")
        assert is_valid is False
        assert "required" in error

    def test_none_url(self):
        is_valid, error = validate_url(None)
        assert is_valid is False
        assert "required" in error

    def test_invalid_url_format(self):
        is_valid, error = validate_url("not-a-url")
        assert is_valid is False
        assert "Invalid URL format" in error


class TestGenerateShortCode:
    def test_short_code_length(self):
        code = generate_short_code()
        assert len(code) == 6

    def test_short_code_alphanumeric(self):
        code = generate_short_code()
        assert code.isalnum()

    def test_custom_length(self):
        code = generate_short_code(length=10)
        assert len(code) == 10

    def test_uniqueness(self):
        codes = set()
        for _ in range(100):
            codes.add(generate_short_code())
        # Very high probability of uniqueness
        assert len(codes) > 95


class TestCheckShortCodeExists:
    @patch('lambda.create_short_url.table')
    def test_short_code_exists(self, mock_table):
        mock_table.get_item.return_value = {'Item': {'short_code': 'abc123'}}
        
        result = check_short_code_exists('abc123')
        assert result is True
        mock_table.get_item.assert_called_once_with(Key={'short_code': 'abc123'})

    @patch('lambda.create_short_url.table')
    def test_short_code_not_exists(self, mock_table):
        mock_table.get_item.return_value = {}
        
        result = check_short_code_exists('xyz789')
        assert result is False

    @patch('lambda.create_short_url.table')
    def test_database_error(self, mock_table):
        from botocore.exceptions import ClientError
        mock_table.get_item.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException'}}, 'GetItem'
        )
        
        with pytest.raises(Exception):
            check_short_code_exists('abc123')


class TestCreateShortUrlRecord:
    @patch('lambda.create_short_url.table')
    def test_create_record_success(self, mock_table):
        create_short_url_record('abc123', 'https://example.com')
        
        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args[1]['Item']
        assert call_args['short_code'] == 'abc123'
        assert call_args['long_url'] == 'https://example.com'
        assert 'created_at' in call_args
        assert call_args['click_count'] == 0
        assert call_args['is_active'] is True

    @patch('lambda.create_short_url.table')
    def test_create_record_with_ip(self, mock_table):
        create_short_url_record('abc123', 'https://example.com', '192.168.1.1')
        
        call_args = mock_table.put_item.call_args[1]['Item']
        assert call_args['created_by_ip'] == '192.168.1.1'


class TestLambdaHandler:
    def create_event(self, url=None):
        return {
            'body': json.dumps({'url': url}) if url is not None else '{}',
            'requestContext': {
                'domainName': 'api.example.com',
                'identity': {
                    'sourceIp': '192.168.1.1'
                }
            }
        }

    @patch('lambda.create_short_url.check_short_code_exists')
    @patch('lambda.create_short_url.create_short_url_record')
    def test_successful_url_creation(self, mock_create_record, mock_check_exists):
        mock_check_exists.return_value = False
        
        event = self.create_event('https://example.com')
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert 'short_url' in body
        assert 'short_code' in body
        assert body['original_url'] == 'https://example.com'
        assert 'created_at' in body

    def test_missing_url(self):
        event = self.create_event()
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body

    def test_invalid_url(self):
        event = self.create_event('invalid-url')
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body

    def test_invalid_json(self):
        event = {
            'body': 'invalid-json',
            'requestContext': {'domainName': 'api.example.com'}
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Invalid JSON' in body['error']

    @patch('lambda.create_short_url.check_short_code_exists')
    def test_short_code_generation_retry(self, mock_check_exists):
        # Simulate existing codes that need retries
        mock_check_exists.side_effect = [True, True, False]
        
        event = self.create_event('https://example.com')
        
        with patch('lambda.create_short_url.create_short_url_record'):
            response = lambda_handler(event, {})
        
        assert response['statusCode'] == 201
        assert mock_check_exists.call_count == 3

    @patch('lambda.create_short_url.check_short_code_exists')
    def test_max_retries_exceeded(self, mock_check_exists):
        # All attempts return existing codes
        mock_check_exists.return_value = True
        
        event = self.create_event('https://example.com')
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'Failed to generate unique short code' in body['error']

    @patch('lambda.create_short_url.create_short_url_record')
    @patch('lambda.create_short_url.check_short_code_exists')
    def test_database_error(self, mock_check_exists, mock_create_record):
        from lambda.create_short_url import URLShortenerError
        mock_check_exists.return_value = False
        mock_create_record.side_effect = URLShortenerError("Database error")
        
        event = self.create_event('https://example.com')
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'Database error' in body['error']
