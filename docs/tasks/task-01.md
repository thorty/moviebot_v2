# Task 01 — Lokale Infrastruktur starten

## 1) Kurzüberblick
- Ziel dieses Tasks: Das lokale Startfundament über Docker Compose herstellen.
- Ergebnis: Alle relevanten Services starten mit einem Befehl stabil.
- Umgesetzt in: `docker-compose.yml`, `readme.md`, `frontend/web/README.md`.

## 2) Erklärung für Junior Dev (einfach)
Dieser Task baut das „Startknopf-Fundament“ der App.

Ohne diesen Task kann das Team die App nicht einheitlich lokal starten. Jeder hätte andere manuelle Schritte und andere Fehler.

Mit diesem Task gilt:
- ein gemeinsamer Startbefehl,
- gleiche lokale Services für alle,
- reproduzierbares Verhalten für die nächsten Tasks.

## 3) Was du manuell machen musst
1. Prüfen, ob Docker Desktop läuft.
2. Im Projektordner sein.
3. Starten: `docker compose up -d`
4. Falls ein Service nicht startet: Logs prüfen und Ursache dokumentieren.
5. Stoppen: `docker compose down`

## 4) So testest du genau diesen Task
### Voraussetzungen
- Docker ist installiert und aktiv.
- `docker-compose.yml` ist im Repo vorhanden.

### Testschritte
1. `docker compose config`
2. `docker compose up -d`
3. `docker compose ps`
4. `curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:8000`
5. `docker compose logs --tail=60 frontend-web`

### Erwartetes Ergebnis
- Compose-Konfiguration ist gültig.
- Services laufen: `moviebot-backend`, `moviebot-frontend-web`, `moviebot-supabase-db`.
- Backend ist erreichbar und liefert HTTP `200` auf `http://localhost:8000`.
- Frontend-Log zeigt erwarteten Platzhalter-Hinweis für Task 1.

### Tatsächlich beobachtete Ergebnisse
- `docker compose config` lief erfolgreich.
- `docker compose up -d` startete alle 3 Services erfolgreich.
- `docker compose ps` zeigte `Up` für alle Services; Healthcheck war für `backend` und `supabase-db` grün.
- Backend-Check lieferte `200`.
- Frontend-Log: `frontend/web not initialized yet (Task 4). Keeping container alive for Task 1.`

## 5) Troubleshooting
- Problem: `supabase/postgres:latest` lässt sich nicht ziehen (`manifest unknown`).
  - Ursache: Der Tag existiert nicht.
  - Lösung: In Compose auf `postgres:15-alpine` wechseln.

- Problem: Container startet und stoppt sofort.
  - Ursache: Fehlende Env-Variable oder falscher Port.
  - Lösung: `.env`/Compose-Variablen prüfen, Ports freimachen, neu starten.

- Problem: `docker compose up` hängt bei Image/Pull.
  - Ursache: Netzwerk oder fehlende Berechtigung.
  - Lösung: Internetzugang prüfen, Docker neu starten, erneut versuchen.

- Problem: Port bereits belegt.
  - Ursache: Lokaler Prozess nutzt denselben Port.
  - Lösung: Prozess beenden oder Port-Mapping in Compose anpassen.

## 6) Definition of Done (Task)
- [x] `docker compose up` startet alle relevanten Services ohne Sonderwege
- [x] Kurze Start-/Restart-Hinweise sind in `readme.md` dokumentiert
- [x] Lerndoku ist vollständig und nach der Umsetzung mit realen Werten aktualisiert

## 7) Nach der Implementierung ergänzen
- Service-Namen: `moviebot-backend`, `moviebot-frontend-web`, `moviebot-supabase-db`
- Ports: `8000`, `3000`, `54322`
- Fehlerbild im ersten Lauf: ungültiger Image-Tag `supabase/postgres:latest` (behoben auf `postgres:15-alpine`)
- Finaler Startbefehl: `docker compose up -d`
