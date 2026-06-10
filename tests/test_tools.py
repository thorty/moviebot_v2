"""
Unit tests for backend/tools.py
Tests the streaming filter and search tools
"""

import pytest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from backend.tools import (
    filter_streaming_providers,
    internet_search_google,
    search_public_mediatheken,
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
                'poster_path': '/ghost.jpg',
                'poster_url': 'https://image.tmdb.org/t/p/w342/ghost.jpg',
                'release_date': '1995-11-18',
                'vote_average': 7.9,
                'vote_count': 1400,
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
            'paymenttypes': ['free', 'rent']
        })
        
        # Assertions
        assert result['found_count'] == 2
        assert result['total_checked'] == 2
        assert len(result['available_titles']) == 2
        assert len(result['unavailable_titles']) == 0
        assert result['available_titles'][0]['title'] == 'Ghost in the Shell'
        assert result['available_titles'][0]['poster_path'] == '/ghost.jpg'
        assert result['available_titles'][0]['poster_url'] == 'https://image.tmdb.org/t/p/w342/ghost.jpg'
        assert result['available_titles'][0]['vote_average'] == 7.9
        assert result['available_titles'][0]['vote_count'] == 1400
        
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
            'paymenttypes': ['free']
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
            'paymenttypes': ['free', 'rent']
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
            'paymenttypes': ['free', 'rent']
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
            'paymenttypes': ['free', 'rent']
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
            'paymenttypes': ['free', 'rent']
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
            'paymenttypes': ['free', 'rent']
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
        
        filter_streaming_providers.invoke({
            'titleList': [f'Film {i}' for i in range(15)],
            'userstreamingproviders': ['Netflix'],
            'paymenttypes': ['free', 'rent']
        })
        
        # Check warning in output
        captured = capsys.readouterr()
        assert 'WARNING' in captured.out
        assert '15 titles' in captured.out


class TestInternetSearchGoogle:
    """Tests for internet_search_google tool"""
    
    @patch('backend.tools._run_google_grounded_search')
    def test_search_returns_compact_answer(self, mock_grounded_search):
        """Test successful search with results"""
        mock_response = Mock(text="Search results for cyberpunk films", candidates=[])
        mock_grounded_search.return_value = mock_response
        
        result = internet_search_google.invoke({'query': 'cyberpunk films'})
        
        assert result["query"] == "cyberpunk films"
        assert result["answer"] == "Search results for cyberpunk films"
        assert result["results"] == []
        mock_grounded_search.assert_called_once_with("cyberpunk films")
    
    @patch('backend.tools._run_google_grounded_search')
    def test_search_with_complex_query(self, mock_grounded_search):
        """Test search with complex query string"""
        mock_response = Mock(text="Complex search results", candidates=[])
        mock_grounded_search.return_value = mock_response
        
        query = "best cyberpunk anime films 2020-2024 dystopian"
        result = internet_search_google.invoke({'query': query})
        
        assert result["query"] == query
        assert result["answer"] == "Complex search results"
        mock_grounded_search.assert_called_once_with(query)

    @patch('backend.tools._run_google_grounded_search')
    def test_search_returns_structured_error_on_google_failure(self, mock_grounded_search):
        """Test search failures do not crash the chat request"""
        mock_grounded_search.side_effect = RuntimeError(
            "503 UNAVAILABLE. This model is currently experiencing high demand."
        )

        result = internet_search_google.invoke({'query': 'ARD Mediathek Krimi'})

        assert result["query"] == "ARD Mediathek Krimi"
        assert result["answer"] == ""
        assert result["results"] == []
        assert result["error"] == "google_search_unavailable"
        assert "503 UNAVAILABLE" in result["error_message"]


class TestSearchPublicMediatheken:
    @patch('backend.tools._run_google_grounded_search')
    def test_search_adds_public_mediatheken_context(self, mock_grounded_search):
        mock_response = Mock(text="ARD Mediathek result", candidates=[])
        mock_grounded_search.return_value = mock_response

        result = search_public_mediatheken.invoke({'query': 'Krimi Serie'})

        assert result["query"] == "Krimi Serie"
        assert result["answer"] == "ARD Mediathek result"
        assert result["found_count"] == 1
        called_query = mock_grounded_search.call_args.args[0]
        assert "ARD Mediathek" in called_query
        assert "ZDF Mediathek" in called_query
        assert "Arte" in called_query
        assert "3sat" in called_query

    @patch('backend.tools._run_google_grounded_search')
    def test_search_marks_official_mediatheken_deeplink_candidates(self, mock_grounded_search):
        official_url = "https://www.ardmediathek.de/video/test-title"
        unofficial_url = "https://www.justwatch.com/de/Serie/test-title"
        mock_response = SimpleNamespace(
            text="ARD Mediathek result",
            candidates=[
                SimpleNamespace(
                    grounding_metadata=SimpleNamespace(
                        grounding_chunks=[
                            SimpleNamespace(web=SimpleNamespace(uri=official_url, title="Test Title | ARD Mediathek")),
                            SimpleNamespace(web=SimpleNamespace(uri=unofficial_url, title="Test Title | JustWatch")),
                        ]
                    )
                )
            ],
        )
        mock_grounded_search.return_value = mock_response

        result = search_public_mediatheken.invoke({'query': 'Krimi Serie'})

        assert result["found_count"] == 1
        assert len(result["results"]) == 2
        assert len(result["official_results"]) == 1
        assert result["official_results"][0]["service"] == "ARD Mediathek"
        assert result["official_results"][0]["deeplink_url"] == official_url
        assert result["results"][1]["is_official_mediathek_source"] is False
        assert result["results"][1]["deeplink_url"] == ""

    @patch('backend.tools._run_google_grounded_search')
    def test_search_returns_structured_error_on_failure(self, mock_grounded_search):
        mock_grounded_search.side_effect = RuntimeError("503 UNAVAILABLE")

        result = search_public_mediatheken.invoke({'query': 'Doku Natur'})

        assert result["query"] == "Doku Natur"
        assert result["answer"] == ""
        assert result["results"] == []
        assert result["found_count"] == 0
        assert result["error"] == "google_search_unavailable"


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
