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
    assert "Generate 25-35 fitting titles" in prompt
    assert "below 25 titles" in prompt


def test_build_content_researcher_prompt_uses_mediatheken_mode() -> None:
    prompt, mode = build_content_researcher_prompt(
        [],
        include_mediatheken=True,
        analystresult="Naturdokus",
        paymenttypes=["rent"],
    )

    assert mode == "mediatheken"
    assert "Mediatheken-only search" in prompt
    assert "deeplink_url" in prompt
    assert "filter_streaming_providers" not in prompt


def test_build_content_researcher_prompt_uses_larger_single_provider_candidate_list() -> None:
    prompt, mode = build_content_researcher_prompt(
        ["Netflix"],
        include_mediatheken=False,
        analystresult="Unterwasser Sci-Fi",
        paymenttypes=["free"],
    )

    assert mode == "single_provider"
    assert "Generate 20-30 VERY WELL-KNOWN titles" in prompt
    assert "25-40 titles in the first pass" in prompt
    assert "below 25 titles" in prompt


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
    assert "Generate 25-35 fitting movie/TV candidates" in prompt
    assert "below 25 titles" in prompt
