# Sprint Cut Deliverables (Tag 1–3)

## Tag 1

### Ziel des Tages
Lokale Fullstack-Basis und Auth-Grundfluss stabil bereitstellen, damit ab Tag 2 Backend-Regeln sauber integriert werden können.

### Technische Aufgaben
- Docker-Compose-Setup für lokales E2E prüfen/ergänzen (Backend, Frontend, Supabase lokal)
- Env-Handling für lokale Supabase-URLs/Keys vereinheitlichen
- Frontend-Basisfluss für Supabase Auth vorbereiten (Login-Status nutzbar im App-Flow)
- Design-Prototyp unter `plans/moviebot-web-app` als UI-Basis einplanen (Komponenten, Layout, Filter, Loading)
- Technische Entscheidung dokumentieren: Prototyp ist nutzbar, aber nicht direkt deploybar ohne Auth + Backend-API-Umstellung
- DB-Basisschema für Conversations/Logs als MVP-Grundlage festlegen

### Dateiziele (specific repo paths)
- `docker-compose.yml` (neu oder erweitern, falls vorhanden)
- `.env.example` (neu oder aktualisiert)
- `readme.md` (lokale Start-/Setup-Schritte präzisieren)
- `frontend/` (Auth-Einstiegspunkt und Konfiguration, z. B. App-Start + Supabase-Client)
- `plans/moviebot-web-app/app/page.tsx` (Referenz für Chat-UX/Struktur)
- `plans/moviebot-web-app/components/` (Referenz für wiederverwendbare UI-Bausteine)
- `plans/moviebot-web-app/app/api/chat/route.ts` (ersetzen durch produktive Backend-Anbindung)
- `plans/prototype-component-mapping.md` (verbindliche Umzugsmatrix Prototyp → Produktiv)
- `backend/utils/setupenv.py` (Env-Ladepfad für lokale Services)
- `backend/` (Migrations-/Schema-Referenz, falls im Repo so abgelegt)

### Abnahmekriterien
- Alle relevanten Container starten lokal ohne manuelle Sonderwege
- Frontend kann Auth-Status ermitteln (eingeloggt/nicht eingeloggt)
- Prototyp-Übernahme ist entschieden: UI ja, API-Route nein
- DB-Struktur für “1 aktive Conversation” und minimales Logging ist definiert
- Dokumentation für lokalen Start ist für Team nachvollziehbar

### Test/Verifikation
- `docker compose up` läuft lokal stabil
- Health-Check auf Backend-Endpunkt erfolgreich
- Manueller Login/Logout-Smoke-Test im Frontend
- Sichtprüfung: notwendige Tabellen/Constraints vorhanden

### Risiken & Fallback
- Risiko: Inkonsistente lokale Env-Werte  
  Fallback: zentrale `.env.example` + klare Pflichtvariablen im Readme
- Risiko: Supabase lokal startet unzuverlässig  
  Fallback: reproduzierbarer Restart-Ablauf dokumentieren

---

## Tag 2

### Ziel des Tages
Backend-seitige Sicherheits- und Datenregeln für MVP umsetzen: JWT-Verifikation je Request, 1 aktive Conversation pro User, minimales Logging.

### Technische Aufgaben
- JWT-Verifikation gegen Supabase im FastAPI-Requestpfad erzwingen
- User-Kontext aus Token ableiten und in Chat-/Conversation-Logik verwenden
- Regel “genau 1 aktive Conversation pro User” in Persistenz + Service-Logik absichern
- Logging strikt auf zwei Felder reduzieren: User-Query und finale Antwort
- Frontend-Transport vom Prototypen (`/api/chat`) auf produktiven Backend-Endpoint umstellen
- Unerlaubte/ungültige Requests sauber mit 401/403 behandeln

### Dateiziele (specific repo paths)
- `main.py` (Auth-abhängige API-Integration)
- `backend/graph.py` (User-Kontext/Conversation-Anbindung im Ablauf)
- `backend/states.py` (State-Felder für minimales Logging und aktive Conversation)
- `backend/tools.py` (nur falls für persistente Operations nötig)
- `backend/utils/helper.py` (Hilfsfunktionen für Auth/Conversation-Zugriff)
- `backend/utils/setupenv.py` (JWT-/Supabase-Settings)
- `plans/moviebot-web-app/app/page.tsx` (API-Request-Struktur als Vorlage für Frontend-Integration)
- `tests/` (gezielte Tests für Auth-Guard, 1-Conversation-Regel, Logging-Reduktion)

### Abnahmekriterien
- Jede geschützte Request scheitert ohne valides JWT
- Mit validem JWT ist User eindeutig auf Backend-Seite identifizierbar
- Pro User existiert gleichzeitig nur eine aktive Conversation
- Persistierte Logs enthalten ausschließlich Query + finale Antwort

### Test/Verifikation
- Positive/negative API-Tests auf Auth-Guard
- Testfall: zweiter Start derselben User-Conversation reaktiviert/ersetzt statt parallel
- Testfall: Log-Record enthält keine zusätzlichen sensiblen Felder
- Testfall: Frontend sendet nicht mehr an Next-Prototyp-Route, sondern an produktiven Backend-Pfad
- Manueller API-Smoke-Test via lokaler Umgebung

### Risiken & Fallback
- Risiko: Token-Validierung schlägt lokal wegen Konfigurationsabweichung fehl  
  Fallback: dedizierter Debug-Endpoint nur lokal, danach wieder entfernen
- Risiko: Race-Condition bei “1 aktive Conversation”  
  Fallback: DB-seitige Constraint + transaktionaler Upsert-Pfad

---

## Tag 3

### Ziel des Tages
End-to-End-Verifikation, Stabilisierung und review-fähige Übergabe des MVP-Scope.

### Technische Aufgaben
- E2E-Durchlauf lokal: Auth → Chat-Request → Antwort → minimales Logging
- Fehlerfälle verifizieren (abgelaufenes JWT, unauthenticated access, doppelte aktive Conversation)
- Dokumentation finalisieren (Start, Testpfad, bekannte Grenzen)
- Offene Kanten glätten, ohne Scope zu erweitern

### Dateiziele (specific repo paths)
- `readme.md` (finaler lokaler E2E-Runbook-Abschnitt)
- `tests/` (stabile Smoke-/Integrationsfälle für MVP-Kernregeln)
- `frontend/gradio/readme.md` (falls Frontend-spezifische Startschritte nötig)
- `plans/moviebot-web-app/` (als Design-Referenz klar als „Prototype only“ markieren)
- `todos.md` (nur MVP-relevante Restpunkte klar markieren)

### Abnahmekriterien
- Voller lokaler E2E-Flow läuft reproduzierbar durch
- Sicherheits- und Datenregeln aus Entscheidungen sind nachweisbar erfüllt
- Dokumentation erlaubt Onboarding ohne mündliche Zusatzinfos
- Kein Scope-Drift gegenüber MVP-Minimalvorgaben

### Test/Verifikation
- End-to-End Smoke: Login, Chat, Antwort, Persistenzprüfung
- Negativtests: ohne Token, mit ungültigem Token, parallele aktive Conversation
- Team-Review mit Review-Checkliste abgeschlossen

### Risiken & Fallback
- Risiko: Letzte Integrationsfehler zwischen Frontend/Auth/Backend  
  Fallback: harte Priorisierung auf Kernpfad, nicht-kritische Teile auf nachgelagerten Sprint
- Risiko: Dokumentationslücken  
  Fallback: kurzes “Happy Path + Known Limitations” Minimaldokument erzwingen

---

## Review-Checkliste
- [ ] Lokales Setup startet mit `docker compose up` ohne Sondertricks
- [ ] Supabase Auth ist aktiv und Backend prüft JWT pro Request
- [ ] Genau 1 aktive Conversation pro User ist technisch erzwungen
- [ ] Logs enthalten nur User-Query und finale Antwort
- [ ] Design-Prototyp wurde korrekt eingeordnet: UI-Basis nutzbar, API/Login produktiv neu integriert
- [ ] MVP-Non-Goals wurden nicht implementiert
- [ ] Readme/Testpfad ist für Product + Engineering nachvollziehbar
