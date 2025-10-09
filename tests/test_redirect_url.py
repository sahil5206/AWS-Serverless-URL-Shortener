import json
import pytest
from unittest.mock import patch, MagicMock
from lambda.redirect_url import (
    lambda_handler,
    get_client_ip,
    get_user_agent,
    increment_click_count,
    log_redirect_analytics
)


class TestGetClientIp:
    def test_get_client_ip_exists(self):
        event = {
            'requestContext': {
                'identity': {
                    'sourceIp': '192.168.1.1'
                }
            }
        }
        ip = get_client_ip(event)
        assert ip == '192.168.1.1'

    def test_get_client_ip_missing(self):
        event = {'requestContext': {}}
        ip = get_client_ip(event)
        assert ip is None


class TestGetUserAgent:
    def test_get_user_agent_exists(self):
        event = {
            'headers': {
                'User-Agent': 'Mozilla/5.0'
            }
        }
        ua = get_user_agent(event)
        assert ua == 'Mozilla/5.0'

    def test_get_user_agent_missing(self):
        event = {'headers': {}}
        ua = get_user_agent(event)
        assert ua == 'Unknown'


class TestIncrementClickCount:
    @patch('lambda.redirect_url.table')
    def test_increment_success(self, mock_table):
        increment_click_count('abc123')
        
        mock_table.update_item.assert_called_once_with(
            Key={'short_code': 'abc123'},
            UpdateExpression='ADD click_count :inc',
            ExpressionAttributeValues={':inc': 1},
            ConditionExpression='attribute_exists(short_code)'
        )

    @patch('lambda.redirect_url.table')
    def test_increment_database_error(self, mock_table):
        from botocore.exceptions import ClientError
        mock_table.update_item.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException'}}, 'UpdateItem'
        )
        
        # Should not raise exception, just log warning
        increment_click_count('abc123')
        mock_table.update_item.assert_called_once()


class TestLogRedirectAnalytics:
    @patch('lambda.redirect_url.logger')
    def test_log_analytics(self, mock_logger):
        log_redirect_analytics('abc123', '192.168.1.1', 'Mozilla/5.0')
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        log_data = json.loads(call_args)
        
        assert log_data['event'] == 'redirect'
        assert log_data['short_code'] == 'abc123'
        assert log_data['client_ip'] == '192.168.1.1'
        assert log_data['user_agent'] == 'Mozilla/5.0'
        assert 'timestamp' in log_data


class TestLambdaHandler:
    def create_event(self, short_code=None):
        event = {
            'requestContext': {
                'identity': {
                    'sourceIp': '192.168.1.1'
                }
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0'
            }
        }
        
        if short_code:
            event['pathParameters'] = {'shortCode': short_code}
        
        return event

    @patch('lambda.redirect_url.table')
    @patch('lambda.redirect_url.increment_click_count')
    def test_successful_redirect(self, mock_increment, mock_table):
        mock_table.get_item.return_value = {
            'Item': {
                'short_code': 'abc123',
                'long_url': 'https://example.com',
                'is_active': True
            }
        }
        
        event = self.create_event('abc123')
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 301
        assert response['headers']['Location'] == 'https://example.com'
        assert response['body'] == ''
        mock_increment.assert_called_once_with('abc123')

    def test_missing_short_code(self):
        event = self.create_event()
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Short code is required' in body['error']

    def test_invalid_short_code_format(self):
        event = self.create_event('abc-123!')
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Invalid short code format' in body['error']

    @patch('lambda.redirect_url.table')
    def test_short_code_not_found(self, mock_table):
        mock_table.get_item.return_value = {}
        
        event = self.create_event('nonexistent')
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'Short URL not found' in body['error']

    @patch('lambda.redirect_url.table')
    def test_inactive_short_code(self, mock_table):
        mock_table.get_item.return_value = {
            'Item': {
                'short_code': 'abc123',
                'long_url': 'https://example.com',
                'is_active': False
            }
        }
        
        event = self.create_event('abc123')
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 410
        body = json.loads(response['body'])
        assert 'no longer active' in body['error']

    @patch('lambda.redirect_url.table')
    def test_database_error(self, mock_table):
        from botocore.exceptions import ClientError
        mock_table.get_item.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException'}}, 'GetItem'
        )
        
        event = self.create_event('abc123')
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'Internal server error' in body['error']

    @patch('lambda.redirect_url.table')
    def test_analytics_failure_does_not_break_redirect(self, mock_table):
        mock_table.get_item.return_value = {
            'Item': {
                'short_code': 'abc123',
                'long_url': 'https://example.com',
                'is_active': True
            }
        }
        
        # Simulate analytics failure
        with patch('lambda.redirect_url.increment_click_count') as mock_increment:
            mock_increment.side_effect = Exception("Analytics failed")
            
            event = self.create_event('abc123')
            response = lambda_handler(event, {})
            
            # Redirect should still work
            assert response['statusCode'] == 301
            assert response['headers']['Location'] == 'https://example.com'
