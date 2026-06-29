import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { Bookmark, Bot, Film, ImageOff, LogOut, MessageCircle, Plus, SlidersHorizontal, Trash2 } from "lucide-react"

import { cn } from "@/lib/utils"
import { ChatInput } from "@/components/chat/ChatInput"
import { ChatMessages, type ChatMessage } from "@/components/chat/ChatMessages"
import { ExamplePrompts } from "@/components/chat/ExamplePrompts"
import { FilterPanel, type Filters } from "@/components/chat/FilterPanel"
import { ApiHttpError } from "@/lib/chatApi"
import {
  deleteWatchlistItem,
  getUserFilters,
  getWatchlist,
  saveUserFilters,
  saveWatchlistItem,
  sendChatMessage,
  startNewChatContext,
  type RecommendationCandidate,
  type WatchlistItem,
} from "@/lib/chatApi"

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

const WATCHLIST_MEDIA_LABELS: Record<WatchlistItem["media_type"], string> = {
  movie: "Film",
  documentary: "Doku",
  series: "Serie",
}

const getWatchlistKey = (item: Pick<WatchlistItem | RecommendationCandidate, "title" | "media_type">) => {
  return `${item.media_type}:${item.title.trim().toLowerCase()}`
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

type ActiveView = "chat" | "watchlist"

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
  const [activeView, setActiveView] = useState<ActiveView>("chat")
  const [watchlistItems, setWatchlistItems] = useState<WatchlistItem[]>([])
  const [watchlistError, setWatchlistError] = useState("")
  const [savingRecommendationKeys, setSavingRecommendationKeys] = useState<string[]>([])
  const [deletingWatchlistItemIds, setDeletingWatchlistItemIds] = useState<string[]>([])
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
    let isCancelled = false

    const loadWatchlist = async () => {
      try {
        const stored = await getWatchlist()
        if (isCancelled) {
          return
        }
        setWatchlistItems(stored.items)
        setWatchlistError("")
      } catch (error) {
        if (isCancelled) {
          return
        }
        setWatchlistError(error instanceof Error ? error.message : "Merkliste konnte nicht geladen werden.")
      }
    }

    void loadWatchlist()

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

  const watchlistKeys = useMemo(() => {
    return new Set(watchlistItems.map(getWatchlistKey))
  }, [watchlistItems])

  const savingRecommendationKeySet = useMemo(() => {
    return new Set(savingRecommendationKeys)
  }, [savingRecommendationKeys])

  const deletingWatchlistItemIdSet = useMemo(() => {
    return new Set(deletingWatchlistItemIds)
  }, [deletingWatchlistItemIds])

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
        recommendations: response.recommendations || [],
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
  }, [buildRequestFilters, filters, userEmail])

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

  const handleSaveRecommendation = useCallback(async (recommendation: RecommendationCandidate) => {
    const recommendationKey = getWatchlistKey(recommendation)
    if (watchlistKeys.has(recommendationKey) || savingRecommendationKeySet.has(recommendationKey)) {
      return
    }

    setSavingRecommendationKeys((current) => current.includes(recommendationKey) ? current : [...current, recommendationKey])
    setWatchlistError("")

    try {
      const response = await saveWatchlistItem({
        title: recommendation.title,
        media_type: recommendation.media_type,
        description: recommendation.description,
        cover_url: recommendation.cover_url,
        rating: recommendation.rating,
        rating_source: recommendation.rating_source,
        streaming_providers: recommendation.streaming_providers,
      })

      setWatchlistItems((current) => {
        const savedKey = getWatchlistKey(response.item)
        return [response.item, ...current.filter((item) => getWatchlistKey(item) !== savedKey)]
      })
    } catch (error) {
      setWatchlistError(error instanceof Error ? error.message : "Titel konnte nicht gemerkt werden.")
    } finally {
      setSavingRecommendationKeys((current) => current.filter((key) => key !== recommendationKey))
    }
  }, [savingRecommendationKeySet, watchlistKeys])

  const handleDeleteWatchlistItem = useCallback(async (item: WatchlistItem) => {
    if (deletingWatchlistItemIdSet.has(item.id)) {
      return
    }

    setDeletingWatchlistItemIds((current) => current.includes(item.id) ? current : [...current, item.id])
    setWatchlistError("")

    try {
      await deleteWatchlistItem(item.id)
      setWatchlistItems((current) => current.filter((currentItem) => currentItem.id !== item.id))
    } catch (error) {
      setWatchlistError(error instanceof Error ? error.message : "Titel konnte nicht entfernt werden.")
    } finally {
      setDeletingWatchlistItemIds((current) => current.filter((itemId) => itemId !== item.id))
    }
  }, [deletingWatchlistItemIdSet])

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
            onClick={() => {
              setActiveView("chat")
              setFiltersOpen((current) => activeView === "watchlist" ? true : !current)
            }}
            className={cn(
              "moviebot-header-button",
              activeView === "chat" && filtersOpen && "border-primary/40 text-foreground shadow-[0_0_20px_hsl(var(--primary)/0.18)]"
            )}
            aria-expanded={activeView === "chat" && filtersOpen}
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
            onClick={() => setActiveView((current) => current === "watchlist" ? "chat" : "watchlist")}
            className={cn(
              "moviebot-header-button",
              activeView === "watchlist" && "border-primary/40 text-foreground shadow-[0_0_20px_hsl(var(--primary)/0.18)]"
            )}
          >
            <Bookmark className="h-4 w-4" />
            <span className="hidden sm:inline">Merkliste</span>
            {watchlistItems.length > 0 && (
              <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1.5 text-[10px] font-bold text-primary-foreground">
                {watchlistItems.length}
              </span>
            )}
          </button>

          <button
            onClick={() => {
              setActiveView("chat")
              void handleNewChat()
            }}
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

      {activeView === "chat" && filtersOpen && (
        <section className="relative z-10 border-b border-white/5 bg-black/20 px-4 py-4 backdrop-blur-sm">
          <div className="mx-auto max-w-6xl">
            <FilterPanel filters={filters} onFiltersChange={setFilters} />
          </div>
        </section>
      )}

      {activeView === "watchlist" ? (
        <main className="relative z-10 flex-1 overflow-y-auto px-4 py-6 md:px-8">
          <div className="mx-auto max-w-7xl">
            <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-normal text-primary">Merkliste</p>
                <h2 className="mt-1 text-2xl font-black text-foreground md:text-3xl">
                  Gemerkte Titel
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  {watchlistItems.length} Titel aus deinen Empfehlungen.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setActiveView("chat")}
                className="moviebot-header-button self-start sm:self-auto"
              >
                <MessageCircle className="h-4 w-4" />
                Zurück zum Chat
              </button>
            </div>

            {watchlistError && (
              <p className="mb-4 rounded-lg border border-red-400/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
                {watchlistError}
              </p>
            )}

            {watchlistItems.length === 0 ? (
              <div className="flex min-h-[22rem] flex-col items-center justify-center rounded-lg border border-white/10 bg-white/[0.03] px-6 text-center">
                <Film className="mb-4 h-12 w-12 text-primary" />
                <h3 className="text-lg font-bold text-foreground">Noch keine gemerkten Titel</h3>
                <p className="mt-2 max-w-md text-sm text-muted-foreground">
                  Empfehlungen, die du im Chat merkst, erscheinen hier mit Cover und Verfügbarkeiten.
                </p>
                <button
                  type="button"
                  onClick={() => setActiveView("chat")}
                  className="moviebot-header-button mt-5"
                >
                  <MessageCircle className="h-4 w-4" />
                  Zum Chat
                </button>
              </div>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {watchlistItems.map((item) => {
                  const isDeleting = deletingWatchlistItemIdSet.has(item.id)

                  return (
                    <article key={item.id} className="overflow-hidden rounded-lg border border-white/10 bg-white/[0.04]">
                      <div className="relative mx-auto mt-3 aspect-[2/3] w-1/2 overflow-hidden rounded-md bg-black/30">
                        {item.cover_url ? (
                          <img
                            src={item.cover_url}
                            alt={`${item.title} Cover`}
                            loading="lazy"
                            className="h-full w-full object-cover"
                          />
                        ) : (
                          <div className="flex h-full w-full items-center justify-center text-muted-foreground">
                            <ImageOff className="h-10 w-10" />
                          </div>
                        )}
                        <button
                          type="button"
                          onClick={() => void handleDeleteWatchlistItem(item)}
                          disabled={isDeleting}
                          className="absolute right-1.5 top-1.5 inline-flex h-8 w-8 items-center justify-center rounded-lg border border-white/15 bg-black/60 text-white backdrop-blur transition hover:border-red-300/50 hover:text-red-200 disabled:cursor-not-allowed disabled:opacity-50"
                          aria-label={`${item.title} entfernen`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>

                      <div className="p-4">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="rounded-full border border-white/10 px-2 py-0.5 text-[11px] font-bold text-muted-foreground">
                            {WATCHLIST_MEDIA_LABELS[item.media_type]}
                          </span>
                          {item.rating !== null && item.rating !== undefined && (
                            <span className="rounded-full border border-primary/25 bg-primary/10 px-2 py-0.5 text-[11px] font-bold text-primary">
                              {item.rating.toFixed(1)}
                            </span>
                          )}
                        </div>
                        <h3 className="mt-3 line-clamp-2 text-base font-bold leading-snug text-foreground">
                          {item.title}
                        </h3>
                        <p className="mt-2 line-clamp-4 min-h-[4.5rem] text-sm leading-relaxed text-muted-foreground">
                          {item.description}
                        </p>
                        <div className="mt-4 flex flex-wrap gap-1.5">
                          {item.streaming_providers.map((provider) => (
                            <span
                              key={`${item.id}-${provider}`}
                              className="rounded-full border border-white/10 bg-black/20 px-2 py-1 text-[11px] font-semibold text-muted-foreground"
                            >
                              {provider}
                            </span>
                          ))}
                        </div>
                      </div>
                    </article>
                  )
                })}
              </div>
            )}
          </div>
        </main>
      ) : (
        <>
          <div ref={scrollRef} className="relative z-10 flex-1 overflow-y-auto">
            <div className={cn("moviebot-stage mx-auto w-full px-4 md:px-6", hasMessages ? "max-w-4xl py-8" : "max-w-6xl py-5")}>
              {!hasMessages ? (
                <ExamplePrompts onSelect={handleExampleSelect} />
              ) : (
                <ChatMessages
                  messages={messages}
                  isLoading={isLoading}
                  loadingText={loadingHint}
                  watchlistKeys={watchlistKeys}
                  savingRecommendationKeys={savingRecommendationKeySet}
                  onSaveRecommendation={handleSaveRecommendation}
                />
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
        </>
      )}
    </div>
  )
}
