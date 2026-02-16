# Task 04 — Produktives Frontend-Grundgerüst

## 1) Kurzüberblick
- Ziel dieses Tasks: `frontend/web` als produktiven Frontend-Pfad aufsetzen.
- Ergebnis: Eine lauffähige React/TypeScript-App ist vorhanden, Kern-UI aus Prototyp ist portiert.
- Umgesetzt in: `frontend/web/*`, `readme.md`.

## 2) Erklärung für Junior Dev (einfach)
Vor Task 4 gab es nur einen Frontend-Platzhalter. Jetzt gibt es eine echte Web-App im Zielpfad.

Wichtig dabei:
- Wir nutzen den Prototyp als Vorlage für das Design.
- Wir starten aber **nicht** die Prototyp-App selbst.
- Die produktive App läuft nur unter `frontend/web`.

Das ist die Basis für Auth (Task 5) und API-Anbindung (Task 9).

## 3) Was du manuell machen musst
1. Frontend-Service neu aufbauen/starten: `docker compose up -d --force-recreate frontend-web`
2. Status prüfen: `docker compose ps`
3. Im Browser öffnen: `http://localhost:3000`

## 4) So testest du genau diesen Task
### Voraussetzungen
- Task 1 bis Task 3 sind abgeschlossen.
- Docker läuft lokal.

### Testschritte
1. `docker compose up -d --force-recreate frontend-web`
2. `docker compose exec frontend-web sh -lc 'ps -ef | sed -n "1,120p"'`
3. `curl -sS http://localhost:3000 | head -n 5`

### Erwartetes Ergebnis
- Frontend-Container läuft auf Port 3000.
- Im Container läuft `npm run dev` (Vite-Server).
- HTTP-Response liefert HTML für die React-App.

### Tatsächlich beobachtete Ergebnisse
- `frontend-web` wurde erfolgreich neu erstellt.
- Prozessliste im Container zeigte `npm run dev` und `vite --host 0.0.0.0 --port 3000`.
- `curl http://localhost:3000` lieferte HTML (`<!doctype html> ...`).

## 5) Troubleshooting
- Problem: Container läuft, aber UI zeigt alten Platzhalter.
  - Ursache: Service wurde nicht neu erstellt.
  - Lösung: `docker compose up -d --force-recreate frontend-web`.

- Problem: `curl http://localhost:3000` liefert „Empty reply".
  - Ursache: Dev-Server ist noch nicht fertig gestartet.
  - Lösung: kurz warten und erneut testen.

- Problem: Fehlende Pakete/Type-Fehler lokal in VS Code.
  - Ursache: Frontend-Dependencies wurden nur im Container installiert.
  - Lösung: optional lokal `cd frontend/web && npm install`.

## 6) Definition of Done (Task)
- [x] `frontend/web` ist eine lauffähige App-Basis
- [x] UI-Kernbausteine sind aus Prototyp portiert (ohne Prototyp-Laufzeitpfad)
- [x] Frontend ist über Port 3000 erreichbar
- [x] Lerndoku ist vollständig

## 7) Nach der Implementierung ergänzen
- In Task 5 Login/Auth-Flow ergänzen.
- In Task 9 API-Transport auf `POST /api/v1/chat` umstellen.
