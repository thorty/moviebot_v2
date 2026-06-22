from backend.tools import get_tools_for_availability, get_tools_for_providers


def test_mediatheken_only_uses_public_mediatheken_search_only():
    tools = get_tools_for_availability([], include_mediatheken=True)
    tool_names = {tool.name for tool in tools}

    assert "search_public_mediatheken" in tool_names
    assert "internet_search_web" not in tool_names
    assert "filter_streaming_providers" not in tool_names


def test_streaming_uses_search_and_filter_tools():
    tools = get_tools_for_availability(["Netflix", "Disney Plus"], include_mediatheken=False)
    tool_names = {tool.name for tool in tools}

    assert "internet_search_web" in tool_names
    assert "filter_streaming_providers" in tool_names
    assert "search_public_mediatheken" not in tool_names


def test_streaming_plus_mediatheken_uses_both_tool_families():
    tools = get_tools_for_availability(["Netflix"], include_mediatheken=True)
    tool_names = {tool.name for tool in tools}

    assert "internet_search_web" in tool_names
    assert "filter_streaming_providers" in tool_names
    assert "search_public_mediatheken" in tool_names


def test_legacy_mediatheken_provider_still_routes_to_public_search():
    tools = get_tools_for_providers(["Mediatheken"])
    tool_names = {tool.name for tool in tools}

    assert "search_public_mediatheken" in tool_names
    assert "filter_streaming_providers" not in tool_names


def test_legacy_mixed_provider_routes_to_combined_tools():
    tools = get_tools_for_providers(["Netflix", "Mediatheken"])
    tool_names = {tool.name for tool in tools}

    assert "internet_search_web" in tool_names
    assert "filter_streaming_providers" in tool_names
    assert "search_public_mediatheken" in tool_names
