from backend.graph import result_validator


def test_result_validator_prefers_available_filter_result_over_no_results_signal() -> None:
    result = result_validator(
        {
            "control_signal": "no_results",
            "found_titles": [],
            "last_filter_results": {"found_count": 1},
            "last_mediatheken_results": {},
        }
    )

    assert result["validation_status"] == "success"
    assert result["next_agent"] == "__END__"


def test_result_validator_routes_no_results_to_fallback_when_no_tool_result_exists() -> None:
    result = result_validator(
        {
            "control_signal": "no_results",
            "found_titles": [],
            "last_filter_results": {"found_count": 0},
            "last_mediatheken_results": {},
        }
    )

    assert result["validation_status"] == "max_retries"
    assert result["next_agent"] == "fallback_response"

