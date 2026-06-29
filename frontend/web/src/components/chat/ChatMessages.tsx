import { BookmarkPlus, Bot, Check, User } from "lucide-react"
import { useEffect, useState } from "react"
import ReactMarkdown from "react-markdown"

import type { RecommendationCandidate } from "@/lib/chatApi"
import { cn } from "@/lib/utils"

import { LoadingDots } from "./LoadingDots"

export interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  recommendations?: RecommendationCandidate[]
}

interface ChatMessagesProps {
  messages: ChatMessage[]
  isLoading: boolean
  loadingText?: string
  watchlistKeys?: Set<string>
  savingRecommendationKeys?: Set<string>
  onSaveRecommendation?: (recommendation: RecommendationCandidate) => void
}

const getRecommendationKey = (recommendation: Pick<RecommendationCandidate, "title" | "media_type">) => {
  return `${recommendation.media_type}:${recommendation.title.trim().toLowerCase()}`
}

const MEDIA_TYPE_LABELS: Record<RecommendationCandidate["media_type"], string> = {
  movie: "Film",
  documentary: "Doku",
  series: "Serie",
}

export function ChatMessages({
  messages,
  isLoading,
  loadingText,
  watchlistKeys,
  savingRecommendationKeys,
  onSaveRecommendation,
}: ChatMessagesProps) {
  const [typedLoadingText, setTypedLoadingText] = useState("")
  const [dotCount, setDotCount] = useState(0)

  useEffect(() => {
    if (!isLoading || !loadingText) {
      setTypedLoadingText("")
      return
    }

    setTypedLoadingText("")
    let characterIndex = 0
    const typeIntervalId = window.setInterval(() => {
      characterIndex += 1
      setTypedLoadingText(loadingText.slice(0, characterIndex))

      if (characterIndex >= loadingText.length) {
        window.clearInterval(typeIntervalId)
      }
    }, 95)

    return () => {
      window.clearInterval(typeIntervalId)
    }
  }, [isLoading, loadingText])

  useEffect(() => {
    if (!isLoading) {
      setDotCount(0)
      return
    }

    const dotIntervalId = window.setInterval(() => {
      setDotCount((current) => (current >= 5 ? 0 : current + 1))
    }, 550)

    return () => {
      window.clearInterval(dotIntervalId)
    }
  }, [isLoading])

  return (
    <div className="flex flex-col gap-6">
      {messages.map((message) => {
        const isUser = message.role === "user"

        return (
          <div key={message.id} className={cn("flex gap-3 max-w-full", isUser && "flex-row-reverse")}>
            <div
              className={cn(
                "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg",
                isUser ? "bg-secondary" : "bg-primary/10"
              )}
            >
              {isUser ? <User className="h-6 w-6" /> : <Bot className="h-6 w-6 text-primary" />}
            </div>
            <div className={cn("flex flex-col max-w-[85%] md:max-w-[75%]", isUser && "items-end")}>
              <div
                className={cn(
                  "rounded-2xl px-4 py-3 text-base leading-relaxed",
                  isUser
                    ? "bg-primary text-primary-foreground rounded-tr-md"
                    : "bg-secondary text-foreground rounded-tl-md"
                )}
              >
                {isUser ? (
                  <p>{message.content}</p>
                ) : (
                  <div>
                    <div className="prose prose-invert max-w-none prose-p:my-3 prose-p:text-foreground prose-li:my-1 prose-li:text-foreground prose-ul:my-3 prose-ol:my-3 prose-headings:my-4 prose-headings:text-foreground prose-strong:text-foreground prose-ul:list-disc prose-ol:list-decimal prose-ul:pl-6 prose-ol:pl-6 prose-li:pl-1 prose-li:marker:text-muted-foreground [&_ul_ul]:my-2 [&_ol_ol]:my-2 [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
                      <ReactMarkdown
                        components={{
                          img: ({ alt, src }) => (
                            <img
                              alt={alt ?? ""}
                              src={src ?? ""}
                              loading="lazy"
                              className="my-3 aspect-[2/3] w-28 rounded-md object-cover shadow-sm sm:w-32"
                            />
                          ),
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>

                    {message.recommendations && message.recommendations.length > 0 && (
                      <div className="mt-4 border-t border-white/10 pt-3">
                        <p className="mb-2 text-xs font-semibold uppercase tracking-normal text-muted-foreground">
                          Gefundene Titel
                        </p>
                        <div className="flex flex-col gap-2">
                          {message.recommendations.map((recommendation) => {
                            const recommendationKey = getRecommendationKey(recommendation)
                            const isSaved = Boolean(watchlistKeys?.has(recommendationKey))
                            const isSaving = Boolean(savingRecommendationKeys?.has(recommendationKey))

                            return (
                              <div
                                key={recommendationKey}
                                className="flex flex-col gap-2 rounded-lg border border-white/10 bg-black/20 p-3 sm:flex-row sm:items-center sm:justify-between"
                              >
                                <div className="min-w-0">
                                  <div className="flex flex-wrap items-center gap-2">
                                    <p className="max-w-full truncate text-sm font-semibold text-foreground">
                                      {recommendation.title}
                                    </p>
                                    <span className="rounded-full border border-white/10 px-2 py-0.5 text-[11px] font-bold text-muted-foreground">
                                      {MEDIA_TYPE_LABELS[recommendation.media_type]}
                                    </span>
                                  </div>
                                  <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-muted-foreground">
                                    {recommendation.streaming_providers.join(", ")}
                                  </p>
                                </div>
                                <button
                                  type="button"
                                  onClick={() => onSaveRecommendation?.(recommendation)}
                                  disabled={isSaved || isSaving || !onSaveRecommendation}
                                  className={cn(
                                    "inline-flex min-h-9 shrink-0 items-center justify-center gap-2 rounded-lg border px-3 text-xs font-bold transition",
                                    isSaved
                                      ? "border-emerald-400/35 bg-emerald-400/10 text-emerald-200"
                                      : "border-primary/35 bg-primary/10 text-primary hover:border-primary/60 hover:bg-primary/15",
                                    (isSaved || isSaving || !onSaveRecommendation) && "cursor-not-allowed opacity-80"
                                  )}
                                >
                                  {isSaved ? <Check className="h-4 w-4" /> : <BookmarkPlus className="h-4 w-4" />}
                                  {isSaved ? "Gemerkt" : isSaving ? "Speichert" : "Merken"}
                                </button>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )
      })}

      {isLoading && (messages.length === 0 || messages[messages.length - 1]?.role === "user") && (
        <div className="flex gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
            <Bot className="h-6 w-6 text-primary" />
          </div>
          <div className="flex flex-col">
            <div className="rounded-2xl rounded-tl-md bg-secondary px-4 py-3">
              <LoadingDots />
              {loadingText && (
                <p className="text-sm text-muted-foreground min-h-5">
                  {typedLoadingText}
                  {".".repeat(dotCount)}
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
