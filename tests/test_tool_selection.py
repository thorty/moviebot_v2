from backend.tools import get_tools_for_providers


def test_mediatheken_uses_search_tools_only():
    tools = get_tools_for_providers(["Mediatheken"])
    tool_names = {tool.name for tool in tools}

    assert "internet_search_google" in tool_names
    assert "filter_streaming_providers" not in tool_names


def test_streaming_uses_search_and_filter_tools():
    tools = get_tools_for_providers(["Netflix", "Disney Plus"])
    tool_names = {tool.name for tool in tools}

    assert "internet_search_google" in tool_names
    assert "filter_streaming_providers" in tool_names
