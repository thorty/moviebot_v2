"""
Unit tests for backend/tools.py
Tests the streaming filter and search tools
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.tools import (
    filter_streaming_providers,
    internet_search_serper,
    process_content,
    get_all_tools
)


class TestFilterStreamingProviders:
    """Tests for filter_streaming_providers tool"""
    
    @patch('backend.tools.get_filtered_titles_tmdb')
    def test_filter_with_flatproviders_available(self, mock_tmdb):
        """Test filtering when titles have flatproviders"""
        # Mock TMDB response
        mock_tmdb.return_value = [
            {
                'title': 'Ghost in the Shell',
                'flatproviders': ['Amazon Prime Video'],
                'rentproviders': [],
                'overview': 'A cyborg policewoman...',
                'release_date': '1995-11-18',
                'id': 9323
            },
            {
                'title': 'Akira',
                'flatproviders': ['Netflix'],
                'rentproviders': [],
                'overview': 'A secret military project...',
                'release_date': '1988-07-16',
                'id': 149
            }
        ]
        
        # Call the tool
        result = filter_streaming_providers.invoke({
            'titleList': ['Ghost in the Shell', 'Akira'],
            'userstreamingproviders': ['Amazon Prime'],
            'paymenttype': ['free', 'rent']
        })
        
        # Assertions
        assert result['found_count'] == 2
        assert result['total_checked'] == 2
        assert len(result['available_titles']) == 2
        assert len(result['unavailable_titles']) == 0
        assert result['available_titles'][0]['title'] == 'Ghost in the Shell'
        
    @patch('backend.tools.get_filtered_titles_tmdb')
    def test_filter_with_only_flatproviders_available(self, mock_tmdb):
        """Test filtering when titles have flatproviders"""
        # Mock TMDB response
        mock_tmdb.return_value = [
            {
                'title': 'Ghost in the Shell',
                'flatproviders': [],
                'rentproviders': ['Amazon Prime Video'],
                'overview': 'A cyborg policewoman...',
                'release_date': '1995-11-18',
                'id': 9323
            },
            {
                'title': 'Akira',
                'flatproviders': ['Netflix'],
                'rentproviders': [],
                'overview': 'A secret military project...',
                'release_date': '1988-07-16',
                'id': 149
            }
        ]
        
        # Call the tool
        result = filter_streaming_providers.invoke({
            'titleList': ['Ghost in the Shell', 'Akira'],
            'userstreamingproviders': ['Amazon Prime'],
            'paymenttype': ['free']
        })
        
        # Assertions
        assert result['found_count'] == 1
        assert result['total_checked'] == 2
        assert len(result['available_titles']) == 1
        assert len(result['unavailable_titles']) == 1
        assert result['available_titles'][0]['title'] == 'Akira'        
    
    @patch('backend.tools.get_filtered_titles_tmdb')
    def test_filter_with_rentproviders_available(self, mock_tmdb):
        """Test filtering when titles only have rentproviders"""
        mock_tmdb.return_value = [
            {
                'title': 'Blade Runner 2049',
                'flatproviders': [],
                'rentproviders': ['Apple TV', 'Amazon Video'],
                'overview': 'A young blade runner...',
                'release_date': '2017-10-04',
                'id': 335984
            }
        ]
        
        result = filter_streaming_providers.invoke({
            'titleList': ['Blade Runner 2049'],
            'userstreamingproviders': ['Apple TV+', 'Amazon Prime'],
            'paymenttype': ['free', 'rent']
        })
        
        assert result['found_count'] == 1
        assert len(result['available_titles']) == 1
        assert result['available_titles'][0]['title'] == 'Blade Runner 2049'
    
    @patch('backend.tools.get_filtered_titles_tmdb')
    def test_filter_with_no_providers(self, mock_tmdb):
        """Test filtering when titles have no providers"""
        mock_tmdb.return_value = [
            {
                'title': 'Obscure Film',
                'flatproviders': [],
                'rentproviders': [],
                'overview': 'Not available anywhere...',
                'release_date': '2000-01-01',
                'id': 12345
            }
        ]
        
        result = filter_streaming_providers.invoke({
            'titleList': ['Obscure Film'],
            'userstreamingproviders': ['Netflix', 'Disney Plus'],
            'paymenttype': ['free', 'rent']
        })
        
        assert result['found_count'] == 0
        assert len(result['available_titles']) == 0
        assert len(result['unavailable_titles']) == 1
    
    @patch('backend.tools.get_filtered_titles_tmdb')
    def test_filter_mixed_results(self, mock_tmdb):
        """Test filtering with mixed available/unavailable titles"""
        mock_tmdb.return_value = [
            {
                'title': 'Available Film',
                'flatproviders': ['Netflix'],
                'rentproviders': [],
                'overview': 'Available on Netflix',
                'release_date': '2020-01-01',
                'id': 1
            },
            {
                'title': 'Unavailable Film',
                'flatproviders': [],
                'rentproviders': [],
                'overview': 'Not available',
                'release_date': '2020-01-01',
                'id': 2
            },
            {
                'title': 'Rent Only Film',
                'flatproviders': [],
                'rentproviders': ['Apple TV'],
                'overview': 'Rent only',
                'release_date': '2020-01-01',
                'id': 3
            }
        ]
        
        result = filter_streaming_providers.invoke({
            'titleList': ['Available Film', 'Unavailable Film', 'Rent Only Film'],
            'userstreamingproviders': ['Netflix', 'Apple TV+'],
            'paymenttype': ['free', 'rent']
        })
        
        assert result['found_count'] == 2
        assert result['total_checked'] == 3
        assert len(result['available_titles']) == 2
        assert len(result['unavailable_titles']) == 1
    
    @patch('backend.tools.get_filtered_titles_tmdb')
    def test_filter_empty_list(self, mock_tmdb):
        """Test filtering with empty title list"""
        mock_tmdb.return_value = []
        
        result = filter_streaming_providers.invoke({
            'titleList': [],
            'userstreamingproviders': ['Netflix'],
            'paymenttype': ['free', 'rent']
        })
        
        assert result['found_count'] == 0
        assert result['total_checked'] == 0
        assert len(result['available_titles']) == 0
    
    @patch('backend.tools.get_filtered_titles_tmdb')
    def test_filter_large_list(self, mock_tmdb, capsys):
        """Test filtering with large list (50+ titles) - should not show warning"""
        # Create 60 mock titles
        mock_titles = [
            {
                'title': f'Film {i}',
                'flatproviders': ['Netflix'] if i % 2 == 0 else [],
                'rentproviders': [],
                'overview': f'Film {i} overview',
                'release_date': '2020-01-01',
                'id': i
            }
            for i in range(60)
        ]
        mock_tmdb.return_value = mock_titles
        
        title_list = [f'Film {i}' for i in range(60)]
        result = filter_streaming_providers.invoke({
            'titleList': title_list,
            'userstreamingproviders': ['Netflix'],
            'paymenttype': ['free', 'rent']
        })
        
        # Should find 30 titles (every even number)
        assert result['found_count'] == 30
        assert result['total_checked'] == 60
        
        # Check no warning in output
        captured = capsys.readouterr()
        assert 'WARNING' not in captured.out
    
    @patch('backend.tools.get_filtered_titles_tmdb')
    def test_filter_small_list_shows_warning(self, mock_tmdb, capsys):
        """Test filtering with small list (<30 titles) - should show warning"""
        mock_tmdb.return_value = [
            {
                'title': f'Film {i}',
                'flatproviders': ['Netflix'],
                'rentproviders': [],
                'overview': 'Film overview',
                'release_date': '2020-01-01',
                'id': i
            }
            for i in range(15)
        ]
        
        result = filter_streaming_providers.invoke({
            'titleList': [f'Film {i}' for i in range(15)],
            'userstreamingproviders': ['Netflix'],
            'paymenttype': ['free', 'rent']
        })
        
        # Check warning in output
        captured = capsys.readouterr()
        assert 'WARNING' in captured.out
        assert '15 titles' in captured.out


class TestInternetSearchSerper:
    """Tests for internet_search_serper tool"""
    
    @patch('backend.tools.GoogleSerperAPIWrapper')
    def test_search_returns_results(self, mock_wrapper_class):
        """Test successful search with results"""
        # Setup mock
        mock_wrapper = Mock()
        mock_wrapper.run.return_value = "Search results for cyberpunk films"
        mock_wrapper_class.return_value = mock_wrapper
        
        # Call the tool
        result = internet_search_serper.invoke({'query': 'cyberpunk films'})
        
        # Assertions
        assert result == "Search results for cyberpunk films"
        mock_wrapper.run.assert_called_once_with('cyberpunk films')
    
    @patch('backend.tools.GoogleSerperAPIWrapper')
    def test_search_with_complex_query(self, mock_wrapper_class):
        """Test search with complex query string"""
        mock_wrapper = Mock()
        mock_wrapper.run.return_value = "Complex search results"
        mock_wrapper_class.return_value = mock_wrapper
        
        query = "best cyberpunk anime films 2020-2024 dystopian"
        result = internet_search_serper.invoke({'query': query})
        
        assert result == "Complex search results"
        mock_wrapper.run.assert_called_once_with(query)


class TestProcessContent:
    """Tests for process_content tool"""
    
    @patch('backend.tools.requests.get')
    def test_process_webpage_content(self, mock_get):
        """Test processing HTML content from webpage"""
        # Mock HTML response
        mock_response = Mock()
        mock_response.content = b'<html><body><h1>Title</h1><p>Content here</p></body></html>'
        mock_get.return_value = mock_response
        
        result = process_content.invoke({'url': 'https://example.com'})
        
        # Should extract text from HTML
        assert 'Title' in result
        assert 'Content here' in result
        mock_get.assert_called_once_with('https://example.com')
    
    @patch('backend.tools.requests.get')
    def test_process_empty_webpage(self, mock_get):
        """Test processing empty webpage"""
        mock_response = Mock()
        mock_response.content = b'<html><body></body></html>'
        mock_get.return_value = mock_response
        
        result = process_content.invoke({'url': 'https://example.com/empty'})
        
        # Should return minimal text
        assert isinstance(result, str)
        assert len(result) >= 0


# Pytest fixtures
@pytest.fixture
def sample_tmdb_response():
    """Sample TMDB response for testing"""
    return [
        {
            'title': 'Ghost in the Shell',
            'flatproviders': ['Amazon Prime Video', 'Amazon Prime Video with Ads'],
            'rentproviders': ['Apple TV', 'Amazon Video'],
            'overview': 'Major Kusanagi wurde als Cyborg wieder zum Leben erweckt...',
            'release_date': '2017-03-29',
            'id': 315837
        },
        {
            'title': 'Expelled From Paradise',
            'flatproviders': ['Amazon Prime Video', 'Aniverse Amazon Channel'],
            'rentproviders': [],
            'overview': 'Man schreibt das Jahr 2700...',
            'release_date': '2014-11-15',
            'id': 304023
        }
    ]


@pytest.fixture
def sample_streaming_providers():
    """Sample streaming provider list"""
    return ['Disney Plus', 'Amazon Prime', 'Apple TV+', 'Netflix']


# Run tests with: pytest tests/test_tools.py -v
# Run with coverage: pytest tests/test_tools.py --cov=backend.tools --cov-report=html
