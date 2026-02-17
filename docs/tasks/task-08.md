# Task 08 — Genau 1 aktive Conversation + vollständige Nachrichtenpersistenz (Subtask 8.1)

## 1) Kurzüberblick
- Ziel dieses Subtasks: pro User technisch genau eine aktive Conversation sicherstellen.
- Ergebnis:
  - DB-seitig existiert ein transaktionaler RPC-Upsert-Pfad `get_or_create_active_conversation()`.
  - Backend ruft diesen Pfad pro Chat-Request auf und verwendet immer die aktive Conversation-ID.
- Umgesetzt in:
  - `supabase/migrations/20260217123000_task8_single_active_conversation_rpc.sql`
  - `backend/persistence/conversations.py`
  - `main.py`, `backend/states.py`, `backend/graph.py`
  - `tests/test_auth_guard.py`, `tests/test_conversations_service.py`

## 2) Erklärung für Junior Dev (einfach)
Stell dir vor, ein User klickt zweimal fast gleichzeitig auf "Senden".

Ohne Schutz könnten zwei aktive Conversations entstehen.

Deshalb kombinieren wir zwei Ebenen:
1. **DB-Constraint** (Task 6): Partial-Unique-Index erlaubt nur 1 aktive Conversation pro User.
2. **Transaktionaler Service-Pfad** (Task 8.1):
   - RPC liest aktive Conversation.
   - Wenn keine da ist, wird eine erstellt.
   - Bei Race-Condition fängt der Code `unique_violation` ab und liest erneut.

So entsteht am Ende immer genau **eine** aktive Conversation.

## 3) Was du manuell machen musst
1. Supabase lokal starten: `supabase start`
2. Migrationen anwenden: `supabase db reset`
3. Backend starten: `uvicorn main:app --reload`

## 4) So testest du genau diesen Task
### Voraussetzungen
- Lokaler Supabase-Stack läuft.
- Migrationen sind eingespielt.
- JWT-Auth aus Task 7 ist aktiv.

### Testschritte
1. `pytest tests/test_auth_guard.py tests/test_conversations_service.py -v`
2. Optional manuell zwei Requests mit gleichem JWT schnell nacheinander senden.
3. In DB prüfen, dass nur eine aktive Conversation für den User existiert.

### Erwartetes Ergebnis
- Tests sind grün.
- Backend liefert für denselben User dieselbe `conversation_id`, solange Conversation aktiv ist.
- In `public.conversations` existiert pro User maximal 1 Zeile mit `status='active'`.

## 5) Troubleshooting
- Problem: RPC liefert 401/403.
  - Ursache: Ungültiger/fehlender User-JWT im Backend-Request an Supabase.
  - Lösung: `Authorization: Bearer <JWT>` korrekt durchreichen und JWT-Validierung prüfen.

- Problem: `supabase db reset` schlägt bei Migration fehl.
  - Ursache: Lokaler Supabase-Stack nicht gestartet oder altes Schema.
  - Lösung: `supabase start` und dann `supabase db reset` erneut ausführen.

- Problem: Mehrere aktive Conversations sichtbar.
  - Ursache: Index/Migration nicht angewendet.
  - Lösung: Migration-Stand prüfen und neu anwenden.

## 6) Definition of Done (Subtask 8.1)
- [x] Regel „genau 1 aktive Conversation pro User“ in Persistenz + Service-Logik abgesichert
- [x] DB-Constraint + transaktionaler Upsert-Pfad verbindlich kombiniert
- [x] Tests für Service- und Request-Flow vorhanden
- [x] Lerndoku vollständig
