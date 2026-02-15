# Prototyp → Produktiv-Frontend Mapping

## Ziel
Konkreter Umzugsplan für den Design-Prototyp unter `plans/moviebot-web-app` in ein produktives Frontend (MVP), ohne Scope-Erweiterung.

## Annahmen (MVP)
- Produktives Frontend wird als React/TypeScript App unter `frontend/web/` aufgebaut.
- Supabase Auth steuert den Zugriff (Login-Gate).
- Backend ist FastAPI/LangGraph und wird über einen echten API-Endpoint angesprochen (nicht über Next-internal API-Route).

## Struktur-Mapping (Top-Level)
| Prototyp (Quelle) | Ziel (Produktiv) | Aktion |
|---|---|---|
| `plans/moviebot-web-app/app/page.tsx` | `frontend/web/src/pages/ChatPage.tsx` | Übernehmen und API/Auth-Logik austauschen |
| `plans/moviebot-web-app/components/*` | `frontend/web/src/components/*` | Nahezu 1:1 übernehmen, Imports anpassen |
| `plans/moviebot-web-app/components/ui/*` | `frontend/web/src/components/ui/*` | Selektiv übernehmen (nur genutzte Komponenten) |
| `plans/moviebot-web-app/lib/utils.ts` | `frontend/web/src/lib/utils.ts` | Übernehmen |
| `plans/moviebot-web-app/hooks/*` | `frontend/web/src/hooks/*` | Nur bei tatsächlicher Nutzung übernehmen |
| `plans/moviebot-web-app/styles/*` + `app/globals.css` | `frontend/web/src/styles/*` bzw. `frontend/web/src/index.css` | Styles konsolidieren |
| `plans/moviebot-web-app/app/api/chat/route.ts` | `frontend/web/src/lib/api/chat.ts` | Nicht übernehmen, neu als HTTP-Client bauen |

## Komponenten-Mapping (Detail)
| Prototyp-Komponente | Ziel-Datei | Status | Hinweise |
|---|---|---|---|
| `components/chat-input.tsx` | `frontend/web/src/components/chat/ChatInput.tsx` | Übernehmen | `onSubmit`/`isLoading` beibehalten |
| `components/chat-messages.tsx` | `frontend/web/src/components/chat/ChatMessages.tsx` | Übernehmen | Markdown-Rendering beibehalten |
| `components/example-prompts.tsx` | `frontend/web/src/components/chat/ExamplePrompts.tsx` | Übernehmen | Texte optional produktseitig anpassen |
| `components/filter-panel.tsx` | `frontend/web/src/components/chat/FilterPanel.tsx` | Übernehmen mit Anpassung | Provider-IDs auf Backend-Kanon mappen |
| `components/loading-dots.tsx` | `frontend/web/src/components/chat/LoadingDots.tsx` | Übernehmen | Unverändert möglich |
| `components/theme-provider.tsx` | `frontend/web/src/providers/ThemeProvider.tsx` | Optional | Nur wenn Theme-Switch gewünscht |

## API-Mapping (kritisch)
| Prototyp | Produktiv |
|---|---|
| `useChat` + `DefaultChatTransport` mit `api: "/api/chat"` | Eigener API-Client gegen Backend, z. B. `POST /api/v1/chat` |
| Request enthält `messages` + `filters` | MVP-Request auf Backend-Vertrag abbilden (`message`, `provider_mode`, `payment_types`) |
| KI-Antwort wird in Next-Route generiert | Antwort kommt ausschließlich aus FastAPI/LangGraph |

## Auth-Mapping (kritisch)
| Prototyp | Produktiv |
|---|---|
| Keine Login-Seite | Neue Login-Seite + Route-Guard |
| Keine Token-Nutzung | Supabase Session/JWT als Bearer Token an Backend senden |
| Keine Access-Control-Strategie | CORS + Auth-Fehlerzustände im UI behandeln |

## Daten-/Filter-Mapping
Der Prototyp nutzt Provider-IDs wie `disney-plus`, `apple-tv`, `paramount-plus`, `amazon`.
Für MVP muss ein kanonisches Mapping auf die Backend-Providerliste definiert werden, damit Filter konsistent funktionieren.

Empfohlene Mapping-Tabelle (Start):

| UI-ID (Prototyp) | Backend-Kanon (Vorschlag) |
|---|---|
| `netflix` | `Netflix` |
| `disney-plus` | `Disney Plus` |
| `amazon` | `Amazon Prime Video` |
| `wow` | `WOW` |
| `paramount-plus` | `Paramount Plus` |
| `apple-tv` | `Apple TV Plus` |
| `magenta-tv` | `MagentaTV` |

## Reihenfolge für die Umsetzung
1. Grundgerüst `frontend/web/` anlegen (React/TS, Routing, Basis-Styles).
2. Chat-UI-Komponenten aus Prototyp übernehmen (ohne API/Auth zuerst nur statisch).
3. Auth einbauen (Login-Seite, Guard, Session-Verwaltung).
4. API-Client gegen FastAPI anbinden (Next-Route vollständig entfernen).
5. Filter-Provider-Mapping zentralisieren und in Request-Builder verwenden.
6. E2E testen: Login → Chat → Antwort → Fehlerpfade.

## Go/No-Go Einschätzung
- Go für UI/UX-Übernahme: Ja.
- Go für direkte Produktivnutzung ohne Anpassung: Nein.
- Minimale Muss-Anpassungen vor Einsatz: Auth, API-Anbindung, Provider-Mapping.
