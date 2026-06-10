import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { Bot, LogOut, MessageCircle, Plus, SlidersHorizontal } from "lucide-react"

import { cn } from "@/lib/utils"
import { ChatInput } from "@/components/chat/ChatInput"
import { ChatMessages, type ChatMessage } from "@/components/chat/ChatMessages"
import { ExamplePrompts } from "@/components/chat/ExamplePrompts"
import { FilterPanel, type Filters } from "@/components/chat/FilterPanel"
import { ApiHttpError } from "@/lib/chatApi"
import { getUserFilters, saveUserFilters, sendChatMessage, startNewChatContext } from "@/lib/chatApi"

// Fallback UUID generator für Browser ohne crypto.randomUUID() (z.B. Firefox über HTTP)
function generateUUID(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  // Fallback: v4 UUID mit Math.random()
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

const DEFAULT_STREAMING_PROVIDERS = ["Netflix", "Disney Plus", "Amazon", "WOW", "Paramount Plus", "Apple TV", "Magenta TV"]

const DEFAULT_FILTERS: Filters = {
  source: "streaming",
  providers: DEFAULT_STREAMING_PROVIDERS,
  paymentTypes: ["free", "rent"],
  includeMediatheken: false,
}

const FILTERS_STORAGE_KEY = "moviebot.userFilters"

const DEFAULT_PAYMENT_TYPES: Filters["paymentTypes"] = ["free", "rent"]

const getFiltersStorageKey = (userEmail?: string) => {
  return userEmail ? `${FILTERS_STORAGE_KEY}.${userEmail}` : FILTERS_STORAGE_KEY
}

const normalizeProviderName = (provider: string) => provider === "MagentaTV" ? "Magenta TV" : provider

const normalizeFiltersForUi = (filters: Filters): Filters => {
  const includeMediatheken = Boolean(filters.includeMediatheken || filters.source === "mediathek")
  const providers = filters.source === "mediathek"
    ? []
    : (filters.providers || []).map(normalizeProviderName)
  const shouldUseDefaultStreamingProviders = providers.length === 0 && !includeMediatheken

  return {
    source: "streaming",
    providers: shouldUseDefaultStreamingProviders ? DEFAULT_STREAMING_PROVIDERS : providers,
    paymentTypes: filters.paymentTypes?.length ? filters.paymentTypes : DEFAULT_PAYMENT_TYPES,
    includeMediatheken,
  }
}

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

  const buildRequestFilters = useCallback(
    (selectedFilters: Filters): { userstreamingproviders: string[]; paymenttypes: string[]; include_mediatheken: boolean } => {
      const includeMediatheken = selectedFilters.includeMediatheken || selectedFilters.source === "mediathek"
      const requestProviders = selectedFilters.source === "mediathek"
        ? []
        : selectedFilters.providers.length > 0
          ? selectedFilters.providers
          : includeMediatheken
            ? []
            : DEFAULT_FILTERS.providers

      const requestPaymentTypes =
        requestProviders.length === 0 && includeMediatheken
          ? ["free"]
          : selectedFilters.paymentTypes.length > 0
            ? selectedFilters.paymentTypes
            : DEFAULT_PAYMENT_TYPES

      return {
        userstreamingproviders: requestProviders,
        paymenttypes: requestPaymentTypes,
        include_mediatheken: includeMediatheken,
      }
    },
    []
  )

  useEffect(() => {
    const storageKey = getFiltersStorageKey(userEmail)

    try {
      const cachedRaw = window.localStorage.getItem(storageKey)
      if (cachedRaw) {
        const cachedFilters = JSON.parse(cachedRaw) as Filters
        if (cachedFilters?.source) {
          setFilters(normalizeFiltersForUi(cachedFilters))
        }
      }
    } catch {
      // ignore invalid local cache
    }

    let isCancelled = false

    const loadFilters = async () => {
      try {
        const stored = await getUserFilters()
        if (isCancelled) {
          return
        }

        const nextFilters = normalizeFiltersForUi({
          source: stored.source,
          providers: stored.providers,
          paymentTypes: stored.paymenttypes as Filters["paymentTypes"],
          includeMediatheken: stored.include_mediatheken,
        })

        setFilters(nextFilters)
        window.localStorage.setItem(storageKey, JSON.stringify(nextFilters))
      } catch {
        // keep local/default filters if backend filters are unavailable
      }
    }

    void loadFilters()

    return () => {
      isCancelled = true
    }
  }, [userEmail])

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
    return filters.providers.length + (filters.providers.length > 0 ? filters.paymentTypes.length : 0) + (filters.includeMediatheken ? 1 : 0)
  }, [filters])

  const appendConversation = useCallback(async (userText: string) => {
    const userMessage: ChatMessage = {
      id: generateUUID(),
      role: "user",
      content: userText,
    }

    setMessages((current) => [...current, userMessage])
    setLoadingHint(LOADING_HINTS[Math.floor(Math.random() * LOADING_HINTS.length)])
    setIsLoading(true)

    const requestFilters = buildRequestFilters(filters)
    const persistedFilters: Filters = {
      source: "streaming",
      providers: requestFilters.userstreamingproviders,
      paymentTypes: requestFilters.paymenttypes as Filters["paymentTypes"],
      includeMediatheken: requestFilters.include_mediatheken,
    }

    window.localStorage.setItem(getFiltersStorageKey(userEmail), JSON.stringify(persistedFilters))
    void saveUserFilters({
      source: persistedFilters.source,
      providers: persistedFilters.providers,
      paymenttypes: persistedFilters.paymentTypes,
      include_mediatheken: persistedFilters.includeMediatheken,
    }).catch(() => {
      // local cache remains fallback if backend save fails
    })

    try {
      const response = await sendChatMessage({
        message: userText,
        userstreamingproviders: requestFilters.userstreamingproviders,
        paymenttypes: requestFilters.paymenttypes,
        include_mediatheken: requestFilters.include_mediatheken,
      })

      const botMessage: ChatMessage = {
        id: generateUUID(),
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
        id: generateUUID(),
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
  }, [buildRequestFilters, filters])

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
        id: generateUUID(),
        role: "assistant",
        content: errorMessage,
      }
      setMessages((current) => [...current, botMessage])
    } finally {
      setIsResetting(false)
    }
  }, [isLoading, isResetting])

  return (
    <div className="moviebot-shell relative flex h-dvh flex-col overflow-hidden">
      <header className="relative z-20 flex items-center justify-between border-b border-white/10 bg-black/35 px-4 py-3 backdrop-blur-xl md:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/10 shadow-[0_0_24px_rgba(168,85,247,0.18)]">
            <Bot className="h-7 w-7 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-normal text-foreground md:text-3xl">Moviebot</h1>
            <p className="hidden text-xs text-muted-foreground sm:block">Dein Film- & Serienberater</p>
          </div>
        </div>

        <div className="flex items-center gap-2 md:gap-4">
          <button
            onClick={() => setFiltersOpen((current) => !current)}
            className={cn(
              "moviebot-header-button",
              filtersOpen && "border-primary/40 text-foreground shadow-[0_0_20px_hsl(var(--primary)/0.18)]"
            )}
            aria-expanded={filtersOpen}
          >
            <SlidersHorizontal className="h-4 w-4" />
            <span className="hidden sm:inline">Filter</span>
            {activeFilterCount > 0 && (
              <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1.5 text-[10px] font-bold text-primary-foreground">
                {activeFilterCount}
              </span>
            )}
          </button>

          <button
            onClick={() => void handleNewChat()}
            disabled={isLoading || isResetting}
            className="moviebot-header-button text-primary"
          >
            <MessageCircle className="h-4 w-4" />
            <span className="hidden sm:inline">Neuer Chat</span>
            <Plus className="hidden h-3.5 w-3.5 sm:block" />
          </button>

          {userEmail && (
            <span className="hidden max-w-[220px] truncate text-xs text-muted-foreground lg:block">
              {userEmail}
            </span>
          )}

          {onLogout && (
            <button onClick={onLogout} className="moviebot-header-button">
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          )}
        </div>
      </header>

      <section className={cn("relative z-10 border-b border-white/5 bg-black/20 px-4 py-4 backdrop-blur-sm md:block", !filtersOpen && "hidden md:block")}>
        <div className="mx-auto max-w-6xl">
          <FilterPanel filters={filters} onFiltersChange={setFilters} />
        </div>
      </section>

      <div ref={scrollRef} className="relative z-10 flex-1 overflow-y-auto">
        <div className={cn("moviebot-stage mx-auto w-full px-4 md:px-6", hasMessages ? "max-w-4xl py-8" : "max-w-6xl py-5")}>
          {!hasMessages ? (
            <ExamplePrompts onSelect={handleExampleSelect} />
          ) : (
            <ChatMessages messages={messages} isLoading={isLoading} loadingText={loadingHint} />
          )}
        </div>
      </div>

      <div className="relative z-20 px-4 pb-4 pt-2 md:px-6 md:pb-6">
        <div className="mx-auto max-w-5xl">
          <ChatInput value={input} onChange={setInput} onSubmit={handleSend} isLoading={isLoading} />
          <p className="mt-3 text-center text-[11px] text-muted-foreground">
            Moviebot kann Fehler machen. Verfügbarkeit auf Plattformen kann variieren. (Powered by tmdb)
          </p>          
        </div>
      </div>
    </div>
  )
}
