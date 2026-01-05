# Test Configuration

Dieses Verzeichnis enthält Unit Tests für den LangGraph Filmempfehlungs-Chatbot.

## Tests ausführen

```bash
# Alle Tests
pytest tests/ -v

# Nur Tool-Tests
pytest tests/test_tools.py -v

# Mit Coverage
pytest tests/ --cov=backend --cov-report=html

# Einzelner Test
pytest tests/test_tools.py::TestFilterStreamingProviders::test_filter_with_flatproviders_available -v
```

## Test-Struktur

- `test_tools.py` - Tests für backend/tools.py (Streaming Filter, Web Search)
- Weitere Tests können hinzugefügt werden für:
  - `test_graph.py` - Graph Flow Tests
  - `test_states.py` - State Management Tests
  - `test_prompts.py` - Prompt Template Tests

## Requirements

```bash
pip install pytest pytest-cov pytest-mock
```
