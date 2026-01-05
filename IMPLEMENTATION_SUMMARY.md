# Implementation: Retry-Logik mit Result Validator

## ✅ Implementierte Features

### 1. **State-Erweiterungen** (`backend/states.py`)
Neue Felder im `AgentState`:
- `retry_count`: Zählt Retry-Versuche (0-3)
- `retry_strategy`: Dict mit aktueller Such-Strategie
- `last_filter_results`: Strukturierte Ergebnisse vom Filter-Tool
- `found_titles_count`: Anzahl gefundener verfügbarer Titel
- `validation_status`: Status der Validierung ("success" | "retry" | "max_retries" | "pending")
- `search_queries_used`: Liste verwendeter Suchanfragen (Duplikat-Vermeidung)

### 2. **Progressive Broadening Strategy** (`backend/graph.py`)
```python
get_retry_strategy(retry_count: int) -> dict
```
3 Stufen mit zunehmender Suchbreite:
- **Retry 0**: Exakte Übereinstimmung, 3 Jahre, strikte Genres
- **Retry 1**: Ähnliche Themen, 5 Jahre, flexible Genres, weniger bekannte Titel
- **Retry 2**: Breite Kategorie, 10 Jahre, alle Genres, alternative Vorschläge

### 3. **Result Validator Node** (Regelbasiert, kein LLM!)
```python
result_validator(state: AgentState)
```
**Entscheidungslogik:**
- ✅ `>= 2 Titel gefunden` → **SUCCESS** → END
- 🔄 `< 2 Titel AND retry_count < 3` → **RETRY** → content_researcher (mit neuer Strategie)
- ⚠️ `< 2 Titel AND retry_count >= 3` → **FALLBACK** → fallback_response

**Vorteile:**
- Keine zusätzlichen LLM-Kosten
- Schnelle, deterministische Entscheidungen
- Einfach zu debuggen
- Konsistente Logik

### 4. **Fallback Response Node**
```python
fallback_response(state: AgentState)
```
Generiert hilfreiche Nachricht wenn nach 3 Retries nichts gefunden wurde:
- Erklärt mögliche Gründe
- Schlägt Alternativen vor (breitere Anfrage, konkrete Beispiele, andere Plattformen)
- Freundlicher, konstruktiver Ton

### 5. **Enhanced Tools** (`backend/tools.py`)
```python
filter_streaming_providers() -> dict
```
Rückgabe-Format jetzt strukturiert:
```json
{
  "available_titles": [...],
  "unavailable_titles": [...],
  "total_checked": 25,
  "found_count": 3,
  "raw_results": [...]
}
```

### 6. **Tool Node mit State Tracking**
```python
tool_node_with_state_tracking(state: AgentState)
```
- Wrapper um Standard-ToolNode
- Extrahiert Filter-Ergebnisse automatisch
- Schreibt `last_filter_results` und `found_titles_count` in State

### 7. **Content Researcher mit Retry-Awareness**
```python
content_researcher(state: AgentState)
```
- Liest `retry_count` und `retry_strategy` aus State
- Erweitert System-Prompt bei Retries mit Strategie-Hinweisen
- Passt Suchanfragen basierend auf Strategie an

## 🔄 Neuer Graph-Flow

```
START 
  ↓
interest_analyst
  ↓ (wenn #FINISHED#)
content_researcher (Retry 0)
  ↓
tools (filter_streaming_providers)
  ↓
result_validator
  ├─→ END (>= 2 Titel) ✅
  ├─→ content_researcher (Retry 1) 🔄
  │     ↓
  │   tools
  │     ↓
  │   result_validator
  │     ├─→ END (>= 2 Titel) ✅
  │     ├─→ content_researcher (Retry 2) 🔄
  │     │     ↓
  │     │   tools
  │     │     ↓
  │     │   result_validator
  │     │     ├─→ END (>= 2 Titel) ✅
  │     │     └─→ fallback_response ⚠️
  │     │           ↓
  │     │         END
```

## 🎯 Konfiguration

- **Minimum Titles für Success**: 2 (konfigurierbar in `result_validator`)
- **Max Retries**: 3 (konfigurierbar in `result_validator`)
- **Retry Strategien**: 3 Stufen (definiert in `get_retry_strategy`)

## 📊 Logging & Debugging

Alle wichtigen Nodes loggen ihre Entscheidungen:
```
[VALIDATOR] Retry count: 1, Found titles: 0
[VALIDATOR] ↻ Retry 2/3 - Strategy: Ähnliche Themen und weniger bekannte Titel
[TOOL] filter_streaming_providers called: 25 titles, providers: ['Netflix', 'Amazon Prime']
[TOOL] Results: 0 available, 25 unavailable
[TOOL_NODE] Tracked filter results: 0 titles found
[CONTENT_RESEARCHER] filter_streaming_providers wird aufgerufen
```

## 🚀 Nächste Schritte (Optional)

1. **Search Query Tracking**: Implementiere `search_queries_used` um identische Suchanfragen zu vermeiden
2. **Metrics**: Füge Tracking für durchschnittliche Retry-Anzahl hinzu
3. **A/B Testing**: Teste verschiedene Minimum-Titel-Schwellwerte (2 vs 4 vs 6)
4. **Strategie-Tuning**: Optimiere die 3 Retry-Strategien basierend auf echten Daten
5. **User Feedback**: Frage bei Fallback ob User andere Provider testen möchte

## 🧪 Testing

Import-Test erfolgreich:
```bash
python -c "from backend.graph import create_graph; print('✓ Graph erfolgreich importiert')"
# ✓ Graph erfolgreich importiert
```

## ⚡ Performance-Vorteile

- **Keine zusätzlichen LLM-Calls** für Validierung → Kostenersparnis
- **Schnelle regelbasierte Entscheidungen** → Bessere Latenz
- **Maximale Transparenz** durch Logging → Einfaches Debugging
- **Deterministische Logik** → Vorhersagbares Verhalten
