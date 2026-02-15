"use client"

import { useState, useRef, useEffect, useCallback, useMemo } from "react"
import { useChat } from "@ai-sdk/react"
import { DefaultChatTransport } from "ai"
import {
  Clapperboard,
  Plus,
  ChevronDown,
  ChevronUp,
  SlidersHorizontal,
} from "lucide-react"
import { ChatMessages } from "@/components/chat-messages"
import { ChatInput } from "@/components/chat-input"
import { ExamplePrompts } from "@/components/example-prompts"
import { FilterPanel, type Filters } from "@/components/filter-panel"
import { cn } from "@/lib/utils"

export default function MoviebotPage() {
  const [input, setInput] = useState("")
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [chatKey, setChatKey] = useState(0)
  const [filters, setFilters] = useState<Filters>({
    source: "streaming",
    providers: [
      "netflix",
      "disney-plus",
      "amazon",
      "wow",
      "paramount-plus",
      "apple-tv",
      "magenta-tv",
    ],
    paymentTypes: ["flatrate", "rent"],
  })
  const scrollRef = useRef<HTMLDivElement>(null)

  const transport = useMemo(
    () =>
      new DefaultChatTransport({
        api: "/api/chat",
        prepareSendMessagesRequest: ({ id, messages }) => ({
          body: {
            messages,
            id,
            filters,
          },
        }),
      }),
    [filters]
  )

  const { messages, sendMessage, status, setMessages } = useChat({
    key: String(chatKey),
    transport,
  })

  const isLoading = status === "streaming" || status === "submitted"
  const hasMessages = messages.length > 0

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, isLoading])

  const handleSend = useCallback(() => {
    if (!input.trim() || isLoading) return
    sendMessage({ text: input })
    setInput("")
  }, [input, isLoading, sendMessage])

  const handleExampleSelect = useCallback(
    (prompt: string) => {
      sendMessage({ text: prompt })
    },
    [sendMessage]
  )

  const handleNewChat = useCallback(() => {
    setMessages([])
    setInput("")
    setChatKey((k) => k + 1)
  }, [setMessages])

  const activeFilterCount =
    filters.source === "mediathek"
      ? 1
      : filters.providers.length + filters.paymentTypes.length

  return (
    <div className="flex h-dvh flex-col bg-background">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-border px-4 py-3 md:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10">
            <Clapperboard className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="font-display text-lg font-bold tracking-tight text-foreground">
              Moviebot
            </h1>
            <p className="text-xs text-muted-foreground hidden sm:block">
              Dein Film- & Serienberater
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Filter Toggle */}
          <button
            onClick={() => setFiltersOpen(!filtersOpen)}
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
            {filtersOpen ? (
              <ChevronUp className="h-3.5 w-3.5" />
            ) : (
              <ChevronDown className="h-3.5 w-3.5" />
            )}
          </button>

          {/* New Chat */}
          {hasMessages && (
            <button
              onClick={handleNewChat}
              className="flex items-center gap-2 rounded-lg bg-secondary px-3 py-2 text-sm font-medium text-muted-foreground transition-all hover:text-foreground hover:bg-secondary/80"
            >
              <Plus className="h-4 w-4" />
              <span className="hidden sm:inline">Neuer Chat</span>
            </button>
          )}
        </div>
      </header>

      {/* Filter Panel */}
      {filtersOpen && (
        <div className="border-b border-border bg-card px-4 py-4 md:px-6">
          <FilterPanel filters={filters} onFiltersChange={setFilters} />
        </div>
      )}

      {/* Chat Area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-4 py-6 md:px-6">
          {!hasMessages ? (
            <ExamplePrompts onSelect={handleExampleSelect} />
          ) : (
            <ChatMessages messages={messages} isLoading={isLoading} />
          )}
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-border bg-background px-4 py-4 md:px-6">
        <div className="mx-auto max-w-3xl">
          <ChatInput
            value={input}
            onChange={setInput}
            onSubmit={handleSend}
            isLoading={isLoading}
          />
          <p className="mt-2 text-center text-[11px] text-muted-foreground">
            Moviebot kann Fehler machen. Verfügbarkeit auf Plattformen kann
            variieren.
          </p>
        </div>
      </div>
    </div>
  )
}
