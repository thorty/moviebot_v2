"""
Unit tests for backend/utils/helper.py
Tests the filter_streaming_providers function
"""

import pytest
from backend.utils.helper import choose_streaming_providers
from backend.utils.tmdb.common import FreeProvider


class TestFilterStreamingProvidersHelper:
    """Tests for filter_streaming_providers helper function"""
    
    def test_exact_match_free_providers(self):
        """Test exact matching of free providers"""
        user_providers = ["Netflix", "Disney Plus", "Amazon Prime Video"]
        payment_types = ["free"]
        
        result = choose_streaming_providers(user_providers, payment_types)
        
        assert len(result) == 3
        assert "Netflix" in result
        assert "Disney Plus" in result
        assert "Amazon Prime Video" in result
        assert "Paramount Plus" not in result  
    
    def test_fuzzy_match_amazon_prime(self):
        """Test fuzzy matching for Amazon Prime variants for free content (FreeProvider)"""
        user_providers = ["Amazon Prime", "Netflix"]
        payment_types = ["free"]
        
        result = choose_streaming_providers(user_providers, payment_types)
        
        assert len(result) == 2
        assert "Amazon Prime Video" in result
        assert "Netflix" in result
        assert "Paramount Plus" not in result
    
    def test_fuzzy_match_amazon_video(self):
        """Test fuzzy matching for Amazon for free content (FreeProvider)"""
        # User has "Amazon Video" should match with "Amazon Prime Video"
        user_providers = ["Amazon", "Disney Plus"]
        payment_types = ["free"]
        
        result = choose_streaming_providers(user_providers, payment_types)
        
        # Amazon Video should match with Amazon Prime Video
        assert len(result) == 2
        assert "Amazon Prime Video" in result
        assert "Disney Plus" in result
    
    def test_filter_out_non_free_providers(self):
        """Test filtering out providers not in FreeProvider when using free only"""
        # Magenta TV is not in FreeProvider (commented out)
        user_providers = ["Netflix", "Magenta TV", "Disney Plus"]
        payment_types = ["free"]
        
        result = choose_streaming_providers(user_providers, payment_types)
        
        # Should filter out Magenta TV (not in FreeProvider), but include Magenta TV+
        assert "Netflix" in result
        assert "Disney Plus" in result
        assert "MagentaTV" not in result
        assert "Magenta TV+" in result  # Fuzzy match with "Magenta TV"
    
    def test_filter_out_apple_tv(self):
        """Test Apple TV filtering for free + rent (uses Provider enum)"""
        user_providers = ["Apple", "Netflix"]
        payment_types = ["free", "rent"]
        
        result = choose_streaming_providers(user_providers, payment_types)
        
        # With rent included, uses Provider enum which has both Apple TV and Apple TV+
        assert "Apple TV+" in result        
        assert "Apple TV" in result
        assert "Netflix" in result
    
    def test_filter_free_only_excludes_apple_tv(self):
        """Test Apple TV filtering for free only (uses FreeProvider enum)"""
        user_providers = ["Apple", "Netflix"]
        payment_types = ["free"]
        
        result = choose_streaming_providers(user_providers, payment_types)
        
        # With free only, uses FreeProvider enum which only has Apple TV+
        assert "Apple TV+" in result
        assert "Apple TV" not in result
        assert "Netflix" in result    
    def test_payment_types_free_vs_rent(self):
        """Test that payment_types changes which enum is used"""
        user_providers = ["Amazon Video", "Apple TV"]
        
        # With free only - uses FreeProvider (no Amazon Video, no Apple TV)
        result_free = choose_streaming_providers(user_providers, ["free"])
        assert "Amazon Prime Video" in result_free  # Fuzzy match to Amazon Prime Video in FreeProvider
        assert "Apple TV+" in result_free  # Fuzzy match to Apple TV+ in FreeProvider
        assert "Apple TV" not in result_free  # Apple TV not in FreeProvider
        
        # With rent - uses Provider (has both Amazon Video and Apple TV)
        result_rent = choose_streaming_providers(user_providers, ["rent"])
        assert "Amazon Video" in result_rent  # Exact match in Provider
        assert "Apple TV" in result_rent  # Exact match in Provider
        
        # With both - uses Provider
        result_both = choose_streaming_providers(user_providers, ["free", "rent"])
        assert "Amazon Video" in result_both
        assert "Apple TV" in result_both   