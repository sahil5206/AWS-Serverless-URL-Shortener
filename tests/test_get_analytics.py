import json
import pytest
from unittest.mock import patch, MagicMock
from lambda.get_analytics import lambda_handler, get_short_url_stats


class TestGetShortUrlStats:
    @patch('lambda.get_analytics.table')
    def test_get_stats_success(self, mock_table):
        mock_table.get_item.return_value = {
            'Item': {
                'short_code': 'abc123',
                'long_url': 'https://example.com',
                'created_at': '2024-01-01T00:00:00',
                'click_count': 42,
                'is_active': True
            }
        }
        
        stats = get_short_url_stats('abc123')
        
        assert stats['short_code'] == 'abc123'
        assert stats['original_url'] == 'https://example.com'
        assert stats['created_at'] == '2024-01-01T00:00:00'
        assert stats['click_count'] == 42
        assert stats['is_active'] is True

    @patch('lambda.get_analytics.table')
    def test_get_stats_not_found(self, mock_table):
        mock_table.get_item.return_value = {}
        
        stats = get_short_url_stats('nonexistent')
        
        assert stats is None

    @patch('lambda.get_analytics.table')
    def test_get_stats_database_error(self, mock_table):
        from botocore.exceptions import ClientError
        mock_table.get_item.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException'}}, 'GetItem'
        )
        
        with pytest.raises(Exception):
            get_short_url_stats('abc123')


class TestLambdaHandler:
    def create_event(self, short_code=None):
        event = {}
        
        if short_code:
            event['pathParameters'] = {'shortCode': short_code}
        
        return event

    @patch('lambda.get_analytics.get_short_url_stats')
    def test_successful_analytics_retrieval(self, mock_get_stats):
        mock_get_stats.return_value = {
            'short_code': 'abc123',
            'original_url': 'https://example.com',
            'created_at': '2024-01-01T00:00:00',
            'click_count': 42,
            'is_active': True
        }
        
        event = self.create_event('abc123')
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['short_code'] == 'abc123'
        assert body['original_url'] == 'https://example.com'
        assert body['click_count'] == 42

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

    @patch('lambda.get_analytics.get_short_url_stats')
    def test_short_code_not_found(self, mock_get_stats):
        mock_get_stats.return_value = None
        
        event = self.create_event('nonexistent')
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'Short URL not found' in body['error']

    @patch('lambda.get_analytics.get_short_url_stats')
    def test_database_error(self, mock_get_stats):
        from lambda.get_analytics import URLShortenerError
        mock_get_stats.side_effect = URLShortenerError("Database error")
        
        event = self.create_event('abc123')
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'Database error' in body['error']

    @patch('lambda.get_analytics.get_short_url_stats')
    def test_unexpected_error(self, mock_get_stats):
        mock_get_stats.side_effect = Exception("Unexpected error")
        
        event = self.create_event('abc123')
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'Internal server error' in body['error']
