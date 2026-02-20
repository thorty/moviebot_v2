import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { ChevronDown, ChevronUp, Clapperboard, Plus, SlidersHorizontal } from "lucide-react"

import { cn } from "@/lib/utils"
import { ChatInput } from "@/components/chat/ChatInput"
import { ChatMessages, type ChatMessage } from "@/components/chat/ChatMessages"
import { ExamplePrompts } from "@/components/chat/ExamplePrompts"
import { FilterPanel, type Filters } from "@/components/chat/FilterPanel"
import { ApiHttpError } from "@/lib/chatApi"
import { sendChatMessage, startNewChatContext } from "@/lib/chatApi"

const DEFAULT_FILTERS: Filters = {
  source: "streaming",
  providers: ["Netflix", "Disney Plus", "Amazon", "WOW", "Paramount Plus", "Apple TV", "MagentaTV"],
  paymentTypes: ["free", "rent"],
}

const DEFAULT_PAYMENT_TYPES = ["free", "rent"]

const LOADING_HINTS = [
  "suche nach den besten Treffern ",
  "durchsuche Videotheken ",
  "denke nach ",
  "schaue Trailer ",
  "lese Bewertungen ",
  "denke über den Sinn des Lebens nach ",  
]

const GENERIC_BACKEND_500_MESSAGE = "Sorry da ist leider etwas schief gegangen. Versuch es gerne erneut."

type ChatPageProps = {
  userEmail?: string
  onLogout?: () => void
}

export function ChatPage({ userEmail, onLogout }: ChatPageProps) {
  const [input, setInput] = useState("")
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS)
  const [isLoading, setIsLoading] = useState(false)
  const [loadingHint, setLoadingHint] = useState(LOADING_HINTS[0])
  const [isResetting, setIsResetting] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  const hasMessages = messages.length > 0

  useEffect(() => {
    if (!isLoading) {
      return
    }

    const intervalId = window.setInterval(() => {
      setLoadingHint((current) => {
        let nextHint = current
        while (nextHint === current) {
          nextHint = LOADING_HINTS[Math.floor(Math.random() * LOADING_HINTS.length)]
        }
        return nextHint
      })
    }, 10000)

    return () => {
      window.clearInterval(intervalId)
    }
  }, [isLoading])

  const activeFilterCount = useMemo(() => {
    if (filters.source === "mediathek") {
      return 1
    }
    return filters.providers.length + filters.paymentTypes.length
  }, [filters])

  const appendConversation = useCallback(async (userText: string) => {
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: userText,
    }

    setMessages((current) => [...current, userMessage])
    setLoadingHint(LOADING_HINTS[Math.floor(Math.random() * LOADING_HINTS.length)])
    setIsLoading(true)

    const requestProviders =
      filters.source === "mediathek"
        ? ["Mediatheken"]
        : (filters.providers.length > 0 ? filters.providers : DEFAULT_FILTERS.providers)
    const requestPaymentTypes =
      filters.source === "mediathek"
        ? ["free"]
        : filters.paymentTypes.length > 0
          ? filters.paymentTypes
          : DEFAULT_PAYMENT_TYPES

    try {
      const response = await sendChatMessage({
        message: userText,
        userstreamingproviders: requestProviders,
        paymenttypes: requestPaymentTypes,
      })

      const botMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.reply || "Ich habe aktuell keine Antwort erhalten.",
      }
      setMessages((current) => [...current, botMessage])
    } catch (error) {
      const errorMessage =
        error instanceof ApiHttpError && error.status === 500
          ? GENERIC_BACKEND_500_MESSAGE
          : error instanceof Error
            ? error.message
            : "Unbekannter Fehler"
      const botMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: errorMessage,
      }
      setMessages((current) => [...current, botMessage])
    } finally {
      setIsLoading(false)
      if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight
      }
    }
  }, [filters])

  const handleSend = useCallback(() => {
    const trimmed = input.trim()
    if (!trimmed || isLoading) {
      return
    }
    void appendConversation(trimmed)
    setInput("")
  }, [appendConversation, input, isLoading])

  const handleExampleSelect = useCallback(
    (prompt: string) => {
      if (isLoading) {
        return
      }
      void appendConversation(prompt)
    },
    [appendConversation, isLoading]
  )

  const handleNewChat = useCallback(async () => {
    if (isLoading || isResetting) {
      return
    }

    setIsResetting(true)
    try {
      await startNewChatContext()
      setMessages([])
      setInput("")
    } catch (error) {
      const errorMessage =
        error instanceof ApiHttpError && error.status === 500
          ? GENERIC_BACKEND_500_MESSAGE
          : error instanceof Error
            ? error.message
            : "Unbekannter Fehler"
      const botMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: errorMessage,
      }
      setMessages((current) => [...current, botMessage])
    } finally {
      setIsResetting(false)
    }
  }, [isLoading, isResetting])

  return (
    <div className="flex h-dvh flex-col" style={{ backgroundColor: "hsl(var(--background))" }}>
      <header className="flex items-center justify-between border-b px-4 py-3 md:px-6" style={{ borderColor: "hsl(var(--border))" }}>
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10">
            <Clapperboard className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-foreground">Moviebot</h1>
            <p className="hidden text-xs text-muted-foreground sm:block">Dein Film- & Serienberater</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {userEmail && (
            <span className="hidden max-w-[220px] truncate rounded-lg bg-secondary px-3 py-2 text-xs text-muted-foreground md:block">
              {userEmail}
            </span>
          )}

          {onLogout && (
            <button
              onClick={onLogout}
              className="rounded-lg bg-secondary px-3 py-2 text-sm font-medium text-muted-foreground transition-all hover:bg-secondary/80 hover:text-foreground"
            >
              Logout
            </button>
          )}

          <button
            onClick={() => setFiltersOpen((current) => !current)}
            className={cn(
              "flex items-center gap-2.5 rounded-xl px-4 py-3 text-sm font-bold tracking-wide transition-all border"
            )}
            style={
              filtersOpen
                ? {
                    color: "hsl(var(--primary-foreground))",
                    borderColor: "hsl(var(--primary))",
                    background: "linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--secondary)) 100%)",
                    boxShadow: "0 0 0 2px hsl(var(--primary) / 0.35)",
                  }
                : {
                    color: "hsl(var(--primary-foreground))",
                    borderColor: "hsl(var(--primary))",
                    background: "linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--secondary)) 100%)",
                  }
            }
          >
            <SlidersHorizontal className="h-5 w-5" />
            <span>FILTER</span>
            {activeFilterCount > 0 && (
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground">
                {activeFilterCount}
              </span>
            )}
            {filtersOpen ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>

          {hasMessages && (
            <button
              onClick={() => void handleNewChat()}
              disabled={isLoading || isResetting}
              className="flex items-center gap-2 rounded-lg bg-secondary px-3 py-2 text-sm font-medium text-muted-foreground transition-all hover:text-foreground hover:bg-secondary/80"
            >
              <Plus className="h-4 w-4" />
              <span className="hidden sm:inline">Neuer Chat</span>
            </button>
          )}
        </div>
      </header>

      {filtersOpen && (
        <div className="border-b bg-card px-4 py-4 md:px-6" style={{ borderColor: "hsl(var(--border))" }}>
          <FilterPanel filters={filters} onFiltersChange={setFilters} />
        </div>
      )}

      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-4 py-6 md:px-6">
          {!hasMessages ? (
            <ExamplePrompts onSelect={handleExampleSelect} />
          ) : (
            <ChatMessages messages={messages} isLoading={isLoading} loadingText={loadingHint} />
          )}
        </div>
      </div>

      <div className="border-t px-4 py-4 md:px-6" style={{ borderColor: "hsl(var(--border))" }}>
        <div className="mx-auto max-w-3xl">
          <ChatInput value={input} onChange={setInput} onSubmit={handleSend} isLoading={isLoading} />
          <p className="mt-2 text-center text-[11px] text-muted-foreground">
            Moviebot kann Fehler machen. Verfügbarkeit auf Plattformen kann variieren.
          </p>          
        </div>
      </div>
    </div>
  )
}
