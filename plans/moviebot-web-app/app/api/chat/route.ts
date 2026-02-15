import {
  consumeStream,
  convertToModelMessages,
  streamText,
  UIMessage,
} from "ai"

export const maxDuration = 30

export async function POST(req: Request) {
  const {
    messages,
    filters,
  }: {
    messages: UIMessage[]
    filters: {
      source: "streaming" | "mediathek"
      providers: string[]
      paymentTypes: ("flatrate" | "rent")[]
    }
  } = await req.json()

  const filterContext = buildFilterContext(filters)

  const result = streamText({
    model: "openai/gpt-4o-mini",
    system: `Du bist Moviebot, ein freundlicher und kompetenter Film- und Serienberater. Du sprichst Deutsch.
Du empfiehlst Filme und Serien basierend auf den Wünschen des Nutzers.

${filterContext}

Für jede Empfehlung gibst du folgende Infos:
- **Titel** (mit Erscheinungsjahr)
- **Genre**
- **Kurze Beschreibung** (2-3 Sätze, spoilerfrei)
- **Warum es passt** (bezogen auf die Anfrage des Nutzers)
- **Verfügbarkeit** (auf welchem Dienst verfügbar, basierend auf den Filtern)

Wenn du mehrere Empfehlungen gibst, nummeriere sie. Sei enthusiastisch aber nicht übertrieben.
Wenn der Nutzer nach etwas Bestimmtem fragt, gib 2-4 passende Empfehlungen.
Wenn die Frage unklar ist, frage nach, was den Nutzer interessiert (Genre, Stimmung, etc.).`,
    messages: await convertToModelMessages(messages),
    abortSignal: req.signal,
  })

  return result.toUIMessageStreamResponse({
    originalMessages: messages,
    consumeSseStream: consumeStream,
  })
}

function buildFilterContext(filters: {
  source: "streaming" | "mediathek"
  providers: string[]
  paymentTypes: ("flatrate" | "rent")[]
}): string {
  if (filters.source === "mediathek") {
    return `Der Nutzer sucht nach Inhalten in **öffentlich-rechtlichen Mediatheken** (ARD, ZDF, Arte, 3sat, etc.). 
Empfehle nur Inhalte, die typischerweise in Mediatheken verfügbar sind (Dokumentationen, Eigenproduktionen, europäische Filme, etc.).`
  }

  if (filters.providers.length > 0) {
    const providerList = filters.providers.join(", ")
    const hasFlatrate = filters.paymentTypes.includes("flatrate")
    const hasRent = filters.paymentTypes.includes("rent")

    let paymentInfo = ""
    if (hasFlatrate && hasRent) {
      paymentInfo = "im Flatrate-Abo oder zum Ausleihen/Kaufen"
    } else if (hasFlatrate) {
      paymentInfo = "nur im Flatrate-Abo"
    } else if (hasRent) {
      paymentInfo = "zum Ausleihen/Kaufen"
    }

    return `Der Nutzer sucht nach Inhalten auf folgenden Streamingdiensten: ${providerList}${paymentInfo ? ` (${paymentInfo})` : ""}.
Empfehle nur Inhalte, die auf diesen Plattformen verfügbar sein könnten.`
  }

  return "Der Nutzer hat keine bestimmten Streaming-Filter gewählt. Du kannst Inhalte von allen Plattformen empfehlen."
}
