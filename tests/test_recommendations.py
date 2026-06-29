from backend.recommendations import extract_recommendations_from_reply, normalize_title_key


def test_extract_recommendations_enriches_streaming_and_mediathek_titles() -> None:
    reply = """
    ![Inception Cover](https://image.tmdb.org/t/p/w342/inception.jpg)
    🎬 **Inception (2010)** [Film]
    **TMDB-Bewertung:** 8.4/10 (35 Stimmen)
    *Ein verschachtelter Sci-Fi-Thriller über Träume und Realität.*

    **Verfügbar auf:**
    • Netflix: 🟢 Flatrate

    ---

    🎬 **Terra X: Vulkane (2024)** [Doku]
    *Eine kompakte Naturdoku über aktive Vulkane und ihre Folgen.*

    **Verfügbar in:**
    • [ZDF Mediathek](https://www.zdf.de/dokumentation/terra-x) 🟢 Kostenlos
    """

    filter_results = {
        "available_titles": [
            {
                "title": "Inception",
                "media_type": "movie",
                "overview": "Tool overview",
                "vote_average": 8.4,
                "flatproviders": ["Netflix"],
                "rentproviders": ["Amazon Video"],
            }
        ]
    }

    recommendations = extract_recommendations_from_reply(reply, filter_results=filter_results)

    assert len(recommendations) == 2
    assert recommendations[0]["title"] == "Inception"
    assert recommendations[0]["media_type"] == "movie"
    assert recommendations[0]["cover_url"] == "https://image.tmdb.org/t/p/w342/inception.jpg"
    assert recommendations[0]["rating"] == 8.4
    assert recommendations[0]["rating_source"] == "TMDB"
    assert recommendations[0]["streaming_providers"] == ["Netflix", "Amazon Video"]
    assert recommendations[1]["title"] == "Terra X: Vulkane"
    assert recommendations[1]["media_type"] == "documentary"
    assert recommendations[1]["cover_url"] is None
    assert recommendations[1]["rating"] is None
    assert recommendations[1]["streaming_providers"] == ["ZDF Mediathek"]


def test_extract_recommendations_ignores_incomplete_blocks() -> None:
    reply = """
    🎬 **Unvollständig (2020)** [Film]
    *Eine Beschreibung ohne belegte Verfügbarkeit.*
    """

    assert extract_recommendations_from_reply(reply) == []


def test_normalize_title_key_removes_case_and_punctuation_noise() -> None:
    assert normalize_title_key("  Terra X: Vulkane! ") == "terra x vulkane"
