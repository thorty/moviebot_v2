# Task 06 — DB-Basisschema versionieren

## 1) Kurzüberblick
- Ziel dieses Tasks: versioniertes DB-Basisschema für Conversations und vollständige Message-Historie bereitstellen.
- Ergebnis: SQL-Migration für `conversations` und `message_logs` ist im Repo vorhanden.
- Umgesetzt in: `supabase/migrations/20260216173000_task6_conversations_message_logs.sql`, `docs/tasks/task-06.md`.

## 2) Erklärung für Junior Dev (einfach)
Dieser Task schafft das Datenfundament für den Chat.

Neu sind zwei Tabellen:
- `conversations`: pro User Chat-Kontext (inkl. Status)
- `message_logs`: alle Nachrichten append-only (jede neue Nachricht = neuer Datensatz)

Wichtig für spätere Tasks:
- Per Partial-Unique-Index ist schon vorbereitet, dass pro User nur **eine aktive Conversation** existieren kann.
- Per Foreign-Key auf `(conversation_id, user_id)` ist sichergestellt, dass Nachrichten nur zur eigenen Conversation geschrieben werden.
- RLS ist aktiviert, damit User später nur eigene Daten sehen/schreiben.

## 3) Was du manuell machen musst
1. Lokalen Supabase-Stack starten: `supabase start`
2. Migrationen anwenden: `supabase db reset`
3. Schema prüfen (Studio oder SQL): Tabellen/Constraints/Policies vorhanden

## 4) So testest du genau diesen Task
### Voraussetzungen
- Task 1–5 abgeschlossen.
- Supabase CLI installiert.
- Lokaler Supabase-Stack ist startbar.

### Testschritte
1. `supabase start`
2. `supabase db reset`
3. `supabase db lint`
4. In Studio (`http://127.0.0.1:54323`) prüfen:
   - Tabellen `public.conversations`, `public.message_logs`
   - Unique-Index `conversations_one_active_per_user_idx`
   - RLS auf beiden Tabellen aktiv

### Erwartetes Ergebnis
- Migration läuft ohne Fehler durch.
- Tabellen und Constraints sind vorhanden.
- Grundlage für „1 aktive Conversation pro User“ ist im Schema vorbereitet.

### Tatsächlich beobachtete Ergebnisse
- Migration-Datei ist erstellt und versioniert.
- `supabase db reset` lief lokal erfolgreich durch (Migration angewendet).
- `supabase db lint` meldet: keine Schema-Fehler.

## 5) Troubleshooting
- Problem: `supabase db reset` schlägt fehl, weil Stack nicht läuft.
  - Ursache: Supabase-Container nicht gestartet.
  - Lösung: `supabase start` ausführen, dann `supabase db reset` wiederholen.

- Problem: Fehler bei `create policy if not exists`.
  - Ursache: Ältere Postgres/Supabase-Version ohne Unterstützung.
  - Lösung: Policies ohne `if not exists` anlegen oder vorherige Policy mit `drop policy if exists ...` bereinigen.

- Problem: Unique-Fehler bei zweiter aktiver Conversation eines Users.
  - Ursache: Erwartetes Verhalten des Partial-Unique-Index.
  - Lösung: Bestehende aktive Conversation erst auf `archived` setzen.

## 6) Definition of Done (Task)
- [x] SQL-Migrationen für Conversations und Logs im Repo versioniert
- [x] Schema enthält Constraint-Vorbereitung für „1 aktive Conversation pro User“
- [x] Lerndoku ist vollständig
- [x] Technischer Gate (`supabase db reset` + Sichtprüfung) lokal bestätigt
