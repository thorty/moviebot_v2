from backend.graph import build_content_researcher_prompt


def test_build_content_researcher_prompt_uses_streaming_mode() -> None:
    prompt, mode = build_content_researcher_prompt(
        ["Netflix", "Disney Plus"],
        include_mediatheken=False,
        analystresult="Sci-Fi Serien",
        paymenttypes=["free"],
    )

    assert mode == "streaming"
    assert "filter_streaming_providers" in prompt
    assert "search_public_mediatheken" not in prompt
    assert "Knowledge-First Candidate Generation" in prompt
    assert "Do NOT call `internet_search_google` before the first `filter_streaming_providers`" in prompt
    assert "Web search is a fallback, not the default path." in prompt


def test_build_content_researcher_prompt_uses_mediatheken_mode() -> None:
    prompt, mode = build_content_researcher_prompt(
        [],
        include_mediatheken=True,
        analystresult="Naturdokus",
        paymenttypes=["rent"],
    )

    assert mode == "mediatheken"
    assert "Mediatheken-only search" in prompt
    assert "Knowledge-First Mediatheken Shortlist" in prompt
    assert "MUST call `search_public_mediatheken` at least once" in prompt
    assert "deeplink_url" in prompt
    assert "filter_streaming_providers" not in prompt


def test_build_content_researcher_prompt_uses_combined_mode() -> None:
    prompt, mode = build_content_researcher_prompt(
        ["Netflix"],
        include_mediatheken=True,
        analystresult="Krimi Serien",
        paymenttypes=["free"],
    )

    assert mode == "combined"
    assert "filter_streaming_providers" in prompt
    assert "search_public_mediatheken" in prompt
    assert "official_results" in prompt
    assert "deeplink_url" in prompt
    assert "NEVER pass \"Mediatheken\"" in prompt
    assert "Do NOT call `internet_search_google` before the first `filter_streaming_providers`" in prompt
    assert "do NOT call `internet_search_google` or `search_public_mediatheken`" in prompt
    assert "Whenever you evaluate or output mediatheken availability" in prompt
