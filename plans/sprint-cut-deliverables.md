# Sprint Cut Deliverables (Task-basiert)

## Lernmodus (verbindlich für die Umsetzung)

### Arbeitsweise
- Tasks werden strikt nacheinander umgesetzt (Task 1 → Task 2 → …).
- Ein neuer Task startet erst, wenn der Validierungs-Gate des vorherigen Tasks bestanden ist.
- Nach jedem abgeschlossenen Task wird eine Lern-Doku für Junior-Entwickler erstellt.

### Pflicht-Dokumentation pro Task
- Ablageort: `docs/tasks/`
- Dateiname: `task-XX.md` (z. B. `task-01.md`, `task-02.md`)
- Pflichtinhalt je Datei:
  - Kurzüberblick: Was wurde gebaut?
  - Erklärung für Junior Dev: Warum ist das wichtig und wie funktioniert es einfach erklärt?
  - Manuelle Schritte: Was muss lokal manuell gemacht werden?
  - Testanleitung: Wie wird genau dieser Task geprüft (Commands + erwartetes Ergebnis)?
  - Troubleshooting: Häufige Fehler + schnelle Lösung

### Abnahmeregel für Lernmodus
- Ein Task gilt erst als vollständig abgeschlossen, wenn
  1) der technische Gate bestanden ist und
  2) die zugehörige `docs/tasks/task-XX.md` vollständig vorliegt.

## Task 1 — Lokale Infrastruktur starten

### Ziel
Reproduzierbares lokales Startfundament mit Docker Compose (App-Services) und Supabase CLI (lokaler Supabase-Stack) herstellen.

### Scope
- `docker-compose.yml` erstellen/ergänzen (Backend, `frontend/web`)
- Supabase-CLI-Startpfad für den lokalen Supabase-Stack dokumentieren
- lokale Startreihenfolge und Restart-Hinweise dokumentieren

### Dateiziele
- `docker-compose.yml`
- `readme.md`

### Validierung (Gate)
- `docker compose up` startet alle relevanten Services ohne Sonderwege

---

## Task 2 — Env-Standardisierung

### Ziel
Einheitliche und vollständige Konfiguration für lokale Entwicklung sicherstellen.

### Scope
- `.env.example` als verbindliche Liste der Pflichtvariablen pflegen
- Env-Ladepfad für Supabase/JWT im Backend vereinheitlichen

### Dateiziele
- `.env.example`
- `backend/utils/setupenv.py`
- `readme.md`

### Validierung (Gate)
- Alle benötigten Variablen sind dokumentiert; lokaler Start gelingt ohne implizite Default-Werte

---

## Task 3 — FastAPI-Grundgerüst + Health

### Ziel
Produktiver API-Einstiegspunkt für die weiteren Backend-Regeln bereitstellen.

### Scope
- FastAPI `app` in `main.py`
- `GET /health` als stabiler technischer Check

### Dateiziele
- `main.py`

### Validierung (Gate)
- Health-Check auf `GET /health` ist lokal erfolgreich

---

## Task 4 — Produktives Frontend-Grundgerüst

### Ziel
Ein eigenständiges produktives Frontend unter `frontend/web` anlegen; Prototyp-Code wird nicht als Laufzeit-App verwendet.

### Scope
- `frontend/web` als eigenständigen App-Pfad initialisieren (eigene Laufzeit, eigene Konfiguration)
- UI/UX aus `plans/moviebot-web-app` als Quelle nutzen und in `frontend/web` portieren (Komponenten/Layout/Styles)
- Prototyp bleibt Referenz und wird nicht als produktive App gestartet oder weiterbetrieben

### Nicht im Scope (verbindlich)
- Kein produktiver Betrieb aus `plans/moviebot-web-app`
- Keine produktive Nutzung von `plans/moviebot-web-app/app/api/chat/route.ts`
- Kein „in-place Umbau“ des Prototyps als Zielanwendung

### Dateiziele
- `frontend/web/` (produktive App-Basis vorhanden)
- `plans/prototype-component-mapping.md` (Mapping Quelle → Ziel konkretisiert)
- `plans/moviebot-web-app/app/api/chat/route.ts` (klar als nicht-produktiv dokumentiert)

### Validierung (Gate)
- In der Doku ist explizit festgehalten: Prototyp = Quelle, `frontend/web` = einzig produktiver Frontend-Pfad
- `frontend/web` ist lauffähig als eigener App-Startpunkt
- Es gibt keinen produktiven Pfad, der `app/api/chat/route.ts` aus dem Prototyp nutzt

---

## Task 5 — Frontend Auth-Basis

### Ziel
Login-Status im produktiven Frontend nutzbar machen (Auth-Gate-Basis).

### Zeitpunkt und Ort der Nutzeranlage (verbindlich)
- Zeitpunkt: nach Task 1/2 (lokaler Supabase-Stack + Env steht) und vor dem Login/Logout-Smoke-Test in Task 5
- Ort: Supabase Auth, Tabelle `auth.users` (lokale Supabase-Instanz)
- Zweck: mindestens 1 lokaler Testnutzer für reproduzierbare Login-Tests

### Scope
- Supabase Auth Client/Session-Grundfluss integrieren
- Login-Status im App-Flow unterscheidbar machen
- Anlageweg für Testnutzer verbindlich dokumentieren: manuelle Anlage in der lokalen Supabase-Auth (`auth.users`)

### Dateiziele
- `frontend/web/`
- `readme.md` (kurze Schritte zur lokalen Testnutzer-Anlage)

### Validierung (Gate)
- Manueller Login/Logout-Smoke-Test erfolgreich
- Testlogin verwendet einen in `auth.users` vorhandenen lokalen Nutzer

---

## Task 6 — DB-Basisschema versionieren

### Ziel
Persistente Grundlage für Conversations und vollständige Nachrichtenhistorie schaffen.

### Scope
- SQL-Migrationen für Conversations/Logs anlegen
- Grundlage für „1 aktive Conversation pro User“ in Schema/Constraints vorbereiten

### Dateiziele
- `supabase/migrations/` (verbindliche SQL-Migrations-/Schema-Ablage)

### Validierung (Gate)
- Notwendige Tabellen und Constraints sind in SQL-Migrationen sichtbar

---

## Task 7 — JWT-Guard pro Request

### Ziel
Ungeschützte Requests verhindern und User-Kontext robust herstellen.

### Subtask 7.1 — Token-Validierung + Fehlerverhalten

#### Scope
- JWT-Verifikation im FastAPI-Requestpfad implementieren
- Fehlende/ungültige Tokens sauber mit 401/403 beantworten

#### Dateiziele
- `main.py`
- `backend/utils/helper.py`
- `backend/utils/setupenv.py`

#### Validierung (Gate)
- Negativtests für „ohne Token“ und „ungültiger Token“ sind erfolgreich

### Subtask 7.2 — User-Kontext in Backend-Flow

#### Scope
- User-Kontext aus validem Token ableiten
- User-Kontext in Chat-/Conversation-Logik durchreichen

#### Dateiziele
- `main.py`
- `backend/graph.py`
- `backend/states.py` (falls State-Felder angepasst werden)

#### Validierung (Gate)
- Positivtest mit validem Token zeigt eindeutige User-Identifikation im Request-Flow

---

## Task 8 — Genau 1 aktive Conversation + vollständige Nachrichtenpersistenz

### Ziel
Kern-Datenregel und vollständige, append-only Nachrichtenpersistenz technisch erzwingen.

### Subtask 8.1 — 1 aktive Conversation pro User

#### Scope
- Regel „genau 1 aktive Conversation pro User“ in Persistenz + Service-Logik absichern
- DB-Constraint und transaktionalen Upsert-Pfad verbindlich kombinieren

#### Dateiziele
- `backend/graph.py`
- `backend/states.py`
- `tests/`

#### Validierung (Gate)
- Zweiter Start derselben User-Conversation erzeugt keine parallele aktive Conversation

### Subtask 8.2 — Vollständige, append-only Nachrichtenpersistenz

#### Scope
- Alle User-Eingaben und Bot-Antworten pro Conversation vollständig persistieren
- Bestehende Nachrichten dürfen nicht überschrieben werden; neue Nachrichten werden append-only gespeichert

#### Dateiziele
- `backend/graph.py`
- `backend/states.py`
- `tests/`

#### Validierung (Gate)
- Persistenz enthält alle User-Eingaben und alle Bot-Antworten der Conversation
- Bei Folgeanfragen bleiben bestehende Nachrichten unverändert erhalten (kein Überschreiben)

---

## Task 9 — Produktiver API-Transport im Frontend

### Ziel
Frontend vollständig auf produktiven Backend-Endpoint umstellen.

### Scope
- Keine Nutzung von `app/api/chat/route.ts` im produktiven Flow
- Transport direkt gegen den produktiven Backend-Endpoint
- Request/Response strikt am produktiven Backend-Vertrag ausrichten
- Verbindlicher Endpoint für MVP: `POST /api/v1/chat`
- Auth-Header für geschützte Requests: `Authorization: Bearer <JWT>`

### Dateiziele
- `frontend/web/`
- `readme.md` (API-Endpoint und erwartetes Request/Response-Format dokumentiert)

### Validierung (Gate)
- Frontend sendet nur an produktiven Backend-Pfad
- Request/Response im Frontend entsprechen dem produktiven Backend-Vertrag
- Chat-Request aus dem Frontend geht an `POST /api/v1/chat` und enthält gültigen Bearer-Token

---

## Task 10 — E2E-Härtung + Übergabe

### Ziel
Review-fähige Abnahme mit dokumentiertem Happy Path und Negativtests.

### Scope
- E2E-Durchlauf: Auth → Chat → Antwort → Persistenz/Logging
- Negativfälle: ohne Token, ungültiger Token, paralleler Conversation-Start
- Dokumentation und Restpunkte ohne Scope-Erweiterung finalisieren

### Dateiziele
- `tests/`
- `readme.md`
- `todos.md`

### Validierung (Gate)
- Voller lokaler E2E-Flow reproduzierbar
- Review-Checkliste vollständig mit „ok“

---

## Risiken & Fallback (übergreifend)
- Risiko: Inkonsistente lokale Env-Werte  
  Fallback: zentrale `.env.example` + klare Pflichtvariablen im Readme
- Risiko: Supabase lokal startet unzuverlässig  
  Fallback: reproduzierbarer Restart-Ablauf dokumentieren
- Risiko: Race-Condition bei „1 aktive Conversation“  
  Fallback: DB-Constraint + transaktionaler Upsert-Pfad
- Risiko: Letzte Integrationsfehler zwischen Frontend/Auth/Backend  
  Fallback: Priorisierung auf Kernpfad, nicht-kritische Punkte in `todos.md`

---

## Review-Checkliste
- [ ] Task 1 bestanden: Lokales Setup startet mit `docker compose up` ohne Sondertricks
- [ ] Task 2 bestanden: `.env.example` und Env-Ladepfad sind vollständig und konsistent
- [ ] Task 3 bestanden: `GET /health` ist lokal stabil erreichbar
- [ ] Task 4 bestanden: `frontend/web` ist der einzige produktive Frontend-Pfad; Prototyp wird nur als UI-Quelle genutzt (kein Laufzeitbetrieb)
- [ ] Task 5 bestanden: Login/Logout-Smoke-Test im produktiven Frontend erfolgreich (mit lokalem Testnutzer aus `auth.users`)
- [ ] Task 6 bestanden: SQL-Migrationen enthalten Tabellen/Constraints für Conversations und Logs
- [ ] Subtask 7.1 bestanden: Ohne/ungültiges JWT wird zuverlässig mit 401/403 blockiert
- [ ] Subtask 7.2 bestanden: Valides JWT liefert eindeutigen User-Kontext im Request-Flow
- [ ] Subtask 8.1 bestanden: Pro User existiert gleichzeitig nur 1 aktive Conversation
- [ ] Subtask 8.2 bestanden: Alle User-Eingaben und Bot-Antworten werden append-only gespeichert (kein Überschreiben)
- [ ] Task 9 bestanden: Produktives Frontend nutzt keine Next-Prototyp-API-Route (`app/api/chat/route.ts`)
- [ ] Task 10 bestanden: Voller lokaler E2E-Flow inkl. Negativtests läuft reproduzierbar
- [ ] Für jeden abgeschlossenen Task existiert eine vollständige Lerndoku unter `docs/tasks/task-XX.md`
- [ ] MVP-Non-Goals wurden nicht implementiert
- [ ] Readme/Testpfad ist für Product + Engineering nachvollziehbar
