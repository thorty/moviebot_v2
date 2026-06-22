# PSA-Massnahmenkatalog Moviebot

Stand: 2026-06-11

## Zweck und Scope

Dieser Massnahmenkatalog fasst die PSA-relevanten Datenschutz- und Sicherheitsmassnahmen fuer Moviebot zusammen. Moviebot ist ein LLM-basierter Film- und Serienempfehlungsassistent mit FastAPI/LangGraph Backend, React/Supabase Frontend, Supabase Auth, persistierten Chatverlaeufen und externen Diensten wie Google Gemini, Google Search Grounding und TMDB.

Der Katalog ersetzt keine formale PSA-Freigabe. Er dient als Arbeitsgrundlage fuer PSA-Fragebogen, Datenschutzkontakt, Security Review und Umsetzungsplanung.

## Relevante PSA-Anforderungsdokumente

| Bereich | PSA-Dokument | Relevante Anforderungen |
| --- | --- | --- |
| Digitale Webdienste | Digital Services (App & Web), `00000204` | Sichere Protokolle, Datenminimierung, keine personenbezogenen Daten in URLs, keine Interessen/personenbezogenen Daten im Klartext in lokalen Objekten, Privacy Policy, Einwilligung/Widerspruch, Third-Party-Hinweise, CDP/TIA |
| DSGVO-Verarbeitung | Processing of Personal Data according to GDPR, `84994` | CDP/DPA vor Verarbeitung, TOMs, Prozessor-Nachweise, PSA-Questionnaire, Drittlandpruefung, SCC/TIA |
| Kuenstliche Intelligenz | Artificial intelligence, `00000944` | AI-Interaktion offenlegen, Prompt-/Generation-Speicherung erklaeren, GenAI-Risiken mindern, personenbezogene Daten in Prompts redigieren, Training/Model-Improvement nur mit Rechtsgrundlage |
| Betrieb und Plattform | Cloud Computing, Public Cloud Usage, Database Systems, PostgreSQL databases, Web Applications, Web Services, IAM, CICD Chains | Deployment-, IAM-, Datenbank-, Pipeline- und Betriebsanforderungen je nach Zielumgebung nachziehen |

## Systembefund aus dem Repo

| Befund | Evidenz |
| --- | --- |
| Backend prueft Supabase JWT pro Request | `main.py`, `require_user_context`; `backend/utils/helper.py`, `verify_and_decode_supabase_jwt` |
| Chatnachrichten und Antworten werden append-only persistiert | `main.py`, `/api/v1/chat`; `backend/persistence/message_logs.py`; `supabase/migrations/20260216173000_task6_conversations_message_logs.sql` |
| User-Filterpraeferenzen werden persistiert | `backend/persistence/user_filter_preferences.py`; `supabase/migrations/20260223103000_task12_user_filter_preferences.sql` |
| RLS ist fuer Conversations, Message Logs und Filterpraeferenzen aktiviert | Supabase-Migrationen unter `supabase/migrations/` |
| Prompts werden an Google Gemini/Google Search Grounding uebergeben | `backend/graph.py`; `backend/tools.py` |
| TMDB wird als externer Metadaten-/Availability-Dienst genutzt | `backend/utils/tmdb/tmdb_api_client.py` |
| Frontend speichert Filter zusaetzlich im Browser-LocalStorage | `frontend/web/src/pages/ChatPage.tsx` |
| Eine Run-/Trace-Datei mit User- und Conversation-IDs ist im Repo versioniert | `run-019d0632-4a01-7480-b04b-7e9aee94c7ce.json` |

## Massnahmen

| ID | Prioritaet | Massnahme | PSA-Bezug | Status |
| --- | --- | --- | --- | --- |
| PSA-01 | Hoch | Formale PSA fuer Moviebot starten und Scope dokumentieren: Webapp, Backend API, Supabase Auth/DB, LLM-Verarbeitung, externe Such-/Metadatendienste, Hosting. | `84994 Req 11`, Digital Services `Req 35` | Offen |
| PSA-02 | Hoch | Datenschutzklassifizierung je Datenfeld festlegen: E-Mail/Auth-ID, User-ID, Chatinhalt, Assistant-Antworten, Filterpraeferenzen, Logs, Trace-Daten. Finale DSK/DPC durch Datenschutzkontakt bestaetigen lassen. | GDPR, DSK/DPC, Datenminimierung | Offen |
| PSA-03 | Hoch | Individuelle Datenschutzhinweise im Frontend bereitstellen und jederzeit erreichbar machen. Inhalt: Zwecke, Rechtsgrundlage, Speicherdauer, Empfaenger, Drittanbieter, Widerspruch/Loeschung, AI-Nutzung. | Digital Services `Req 60`, `Req 61`, `Req 63`, `Req 64`; AI `Req 9`, `Req 17` | Offen |
| PSA-04 | Hoch | AI-Hinweis im Chat sichtbar machen: Nutzer interagieren mit einem AI-System; Antworten sind Empfehlungen, keine verbindlichen Entscheidungen; Feedback-/Meldeweg fuer fehlerhafte oder problematische Ausgaben anbieten. | AI `Req 9`, `Req 11`, `Req 12`, `Req 16` | Offen |
| PSA-05 | Hoch | Prompt- und Output-Speicherung transparent machen. Speicherdauer, Zweck und Rechtsgrundlage fuer `message_logs.content` dokumentieren. | AI `Req 17`; Digital Services `Req 52`; GDPR `84994` | Offen |
| PSA-06 | Hoch | Retention- und Loeschkonzept umsetzen: automatische Aufbewahrungsfrist fuer Conversations/Message Logs, User-initiierte Loeschung, Account-Loeschung pruefen, technische Loeschjobs oder RPCs ergaenzen. | Datenminimierung, Speicherbegrenzung, Digital Services `Req 4`, AI `Req 17` | Offen |
| PSA-07 | Hoch | PII-/Sensitive-Data-Redaction vor LLM-Aufrufen bewerten und umsetzen, sofern personenbezogene Daten im Prompt fuer den Empfehlungszweck nicht erforderlich sind. | AI `Req 18`; Digital Services `Req 4` | Offen |
| PSA-08 | Hoch | Drittanbieter- und Subprocessor-Register erstellen: Google/Gemini, Google Search Grounding, Supabase, Hosting-Provider, TMDB, optional LangSmith. Fuer jeden Anbieter DPA/CDP, TOMs, Region, Subprocessor, Training/Retention und Loeschung dokumentieren. | Digital Services `Req 34`, `Req 36`; GDPR `Req 1`, `Req 2`, `Req 7`, `Req 8` | Offen |
| PSA-09 | Hoch | Drittlandzugriff/TIA pruefen, insbesondere fuer Google, Supabase, Hosting und LangSmith. Falls Drittlandzugriff nicht ausgeschlossen ist: TIA, SCC/BCRP und Freigabe dokumentieren. | Digital Services `Req 37`; GDPR `Req 12`, `Req 13`, `Req 20` | Offen |
| PSA-10 | Hoch | Versionierte Run-/Trace-Dateien mit Userdaten aus dem Repository entfernen und `run-*.json` sowie vergleichbare Trace-Artefakte in `.gitignore` aufnehmen. Bestehende Repo-Historie auf personenbezogene Daten und Secrets pruefen. | Datenminimierung, Vertraulichkeit, Security Logging | Offen |
| PSA-11 | Mittel | Browser-LocalStorage fuer Filterpraeferenzen minimieren oder entfernen. Wenn Interessen/Praeferenzen lokal gespeichert werden, nicht im Klartext oder nur mit belastbarer Begruendung und Hinweis. | Digital Services `Req 12` | Offen |
| PSA-12 | Mittel | CORS und HTTP-Header fuer Produktion haerten: nur produktive Origins, keine Wildcard-Methoden/Headers ohne Bedarf, HTTPS-only, Security Header im Frontend/Hosting. | Web Applications, Web Services, Digital Services `Req 3` | Teilweise |
| PSA-13 | Mittel | Secrets- und Env-Konzept schaerfen: keine echten Secrets in `.env`, keine Service-Role-Nutzung im Browser, Rotation fuer kompromittierte Keys, produktive Secrets nur im Secret Store/Hosting. | IAM, Cloud/Operations, TOMs | Teilweise |
| PSA-14 | Mittel | Logging minimieren: keine Chatinhalte, Tokens, personenbezogenen Daten oder vollstaendige Providerantworten in App-, Docker-, LangSmith- oder Hosting-Logs. Bestehende `print`-/Debug-Ausgaben reviewen. | Datenminimierung, TOMs, AI `Req 17` | Offen |
| PSA-15 | Mittel | RLS-/Auth-Evidenzpaket pflegen: Tests fuer Zugriff nur auf eigene Conversations, Message Logs und Filterpraeferenzen; Nachweis, dass Backend JWTs validiert und Supabase RLS greift. | GDPR TOMs, Database Systems, IAM | Teilweise |
| PSA-16 | Mittel | GenAI-Schutzmassnahmen dokumentieren und testen: Halluzinationen, toxische Inhalte, falsche Verfuegbarkeit, Quellen-/Providerklarheit, menschliche Korrektur/Feedback. | AI `Req 12`, `Req 16` | Teilweise |
| PSA-17 | Mittel | Keine nicht notwendigen Tracking-, Analytics-, Session-Replay-, Canvas-Fingerprinting- oder Third-Party-SDKs einsetzen. Falls spaeter ergaenzt: Consent/CMP und Datenschutzhinweise vor Aktivierung. | Digital Services `Req 11`, `Req 15`, `Req 22`, `Req 23`, `Req 25`, `Req 55`, `Req 56` | Offen |
| PSA-18 | Niedrig | Exit-Strategie fuer AI-/Cloud-Dienstleister dokumentieren: Datenexport, Loeschung, Providerwechsel, Sperrung weiterer Verarbeitung nach Vertragsende. | AI `Req 6`; GDPR Processor Requirements | Offen |

## Definition of Done fuer PSA-Readiness

- PSA-Fragebogen ist fuer den tatsaechlichen Zielbetrieb ausgefuellt.
- Datenschutzkontakt hat Datenfelder, DSK/DPC, Rechtsgrundlagen und Speicherdauern bestaetigt.
- Datenschutzhinweise und AI-Hinweise sind im Frontend sichtbar und jederzeit erreichbar.
- DPA/CDP, TOMs, Subprocessor-Liste und TIA/SCC/BCRP-Nachweise liegen fuer relevante Anbieter vor.
- Chat- und Filterdaten haben ein dokumentiertes Retention-/Loeschkonzept mit technischer Umsetzung.
- Keine personenbezogenen Run-/Trace-Artefakte oder Secrets liegen im Repository.
- Tests/Nachweise fuer Auth, RLS, Zugriffstrennung, Loeschung und Logging-Minimierung liegen vor.
- Produktionsdeployment nutzt HTTPS, eingeschraenkte Origins, Secret Store und dokumentierte Betriebsprozesse.

## Empfohlene Reihenfolge

1. `PSA-10`: Run-/Trace-Artefakte aus Repo entfernen und Gitignore haerten.
2. `PSA-03` bis `PSA-05`: Privacy- und AI-Hinweise erstellen.
3. `PSA-06` und `PSA-07`: Retention, Loeschung und Prompt-Redaction umsetzen.
4. `PSA-08` und `PSA-09`: Anbieter-, DPA- und TIA-Paket klaeren.
5. `PSA-12` bis `PSA-16`: technische Haertung und Evidenztests abschliessen.
