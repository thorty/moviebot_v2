import { Bot, User } from "lucide-react"
import { useEffect, useState } from "react"
import ReactMarkdown from "react-markdown"

import { cn } from "@/lib/utils"

import { LoadingDots } from "./LoadingDots"

export interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
}

interface ChatMessagesProps {
  messages: ChatMessage[]
  isLoading: boolean
  loadingText?: string
}

export function ChatMessages({ messages, isLoading, loadingText }: ChatMessagesProps) {
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
                  <div className="prose max-w-none [&>p]:my-1 [&>ul]:my-2 [&>ol]:my-2">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
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
