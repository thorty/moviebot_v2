import { useCallback, useMemo, useRef, useState } from "react"
import { ChevronDown, ChevronUp, Clapperboard, Plus, SlidersHorizontal } from "lucide-react"

import { cn } from "@/lib/utils"
import { ChatInput } from "@/components/chat/ChatInput"
import { ChatMessages, type ChatMessage } from "@/components/chat/ChatMessages"
import { ExamplePrompts } from "@/components/chat/ExamplePrompts"
import { FilterPanel, type Filters } from "@/components/chat/FilterPanel"
import { sendChatMessage, startNewChatContext } from "@/lib/chatApi"

const DEFAULT_FILTERS: Filters = {
  source: "streaming",
  providers: ["netflix", "disney-plus", "amazon"],
  paymentTypes: ["flatrate", "rent"],
}

const PROVIDER_MAP: Record<string, string> = {
  netflix: "Netflix",
  "disney-plus": "Disney Plus",
  amazon: "Amazon Prime Video",
  wow: "WOW",
  "paramount-plus": "Paramount Plus",
  "apple-tv": "Apple TV Plus",
  "magenta-tv": "MagentaTV",
}

const DEFAULT_PAYMENT_TYPES = ["free", "flatrate", "rent", "buy"]

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
  const [isResetting, setIsResetting] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  const hasMessages = messages.length > 0

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
    setIsLoading(true)

    const requestProviders =
      filters.source === "mediathek"
        ? ["Mediatheken"]
        : (filters.providers.length > 0 ? filters.providers : DEFAULT_FILTERS.providers).map(
            (provider) => PROVIDER_MAP[provider] || provider
          )
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
      const errorMessage = error instanceof Error ? error.message : "Unbekannter Fehler"
      const botMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: `Fehler beim Senden an das Backend: ${errorMessage}`,
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
      const errorMessage = error instanceof Error ? error.message : "Unbekannter Fehler"
      const botMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: `Fehler beim Starten eines neuen Chats: ${errorMessage}`,
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
              "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all",
              filtersOpen || activeFilterCount > 0
                ? "bg-primary/10 text-primary"
                : "bg-secondary text-muted-foreground hover:text-foreground"
            )}
          >
            <SlidersHorizontal className="h-4 w-4" />
            <span className="hidden sm:inline">Filter</span>
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
            <ChatMessages messages={messages} isLoading={isLoading} />
          )}
        </div>
      </div>

      <div className="border-t px-4 py-4 md:px-6" style={{ borderColor: "hsl(var(--border))" }}>
        <div className="mx-auto max-w-3xl">
          <ChatInput value={input} onChange={setInput} onSubmit={handleSend} isLoading={isLoading} />
          <p className="mt-2 text-center text-[11px] text-muted-foreground">
            Produktiver Transport aktiv: `POST /api/v1/chat` mit Bearer-Token.
          </p>
        </div>
      </div>
    </div>
  )
}
