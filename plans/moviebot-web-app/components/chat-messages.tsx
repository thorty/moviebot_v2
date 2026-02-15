"use client"

import { UIMessage } from "ai"
import { Bot, User } from "lucide-react"
import { cn } from "@/lib/utils"
import ReactMarkdown from "react-markdown"
import { LoadingDots } from "./loading-dots"

function getMessageText(message: UIMessage): string {
  if (!message.parts || !Array.isArray(message.parts)) return ""
  return message.parts
    .filter((p): p is { type: "text"; text: string } => p.type === "text")
    .map((p) => p.text)
    .join("")
}

interface ChatMessagesProps {
  messages: UIMessage[]
  isLoading: boolean
}

export function ChatMessages({ messages, isLoading }: ChatMessagesProps) {
  return (
    <div className="flex flex-col gap-6">
      {messages.map((message) => {
        const text = getMessageText(message)
        const isUser = message.role === "user"

        return (
          <div
            key={message.id}
            className={cn("flex gap-3 max-w-full", isUser && "flex-row-reverse")}
          >
            <div
              className={cn(
                "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
                isUser ? "bg-secondary" : "bg-primary/10"
              )}
            >
              {isUser ? (
                <User className="h-4 w-4 text-foreground" />
              ) : (
                <Bot className="h-4 w-4 text-primary" />
              )}
            </div>
            <div
              className={cn(
                "flex flex-col gap-1 max-w-[85%] md:max-w-[75%]",
                isUser && "items-end"
              )}
            >
              <span className="text-xs text-muted-foreground">
                {isUser ? "Du" : "Moviebot"}
              </span>
              <div
                className={cn(
                  "rounded-2xl px-4 py-3 text-sm leading-relaxed",
                  isUser
                    ? "bg-primary text-primary-foreground rounded-tr-md"
                    : "bg-secondary text-foreground rounded-tl-md"
                )}
              >
                {isUser ? (
                  <p>{text}</p>
                ) : (
                  <div className="prose prose-invert prose-sm max-w-none [&>p]:my-1 [&>ul]:my-2 [&>ol]:my-2 [&_strong]:text-primary">
                    <ReactMarkdown>{text}</ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          </div>
        )
      })}

      {isLoading &&
        (messages.length === 0 ||
          messages[messages.length - 1]?.role === "user") && (
          <div className="flex gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
              <Bot className="h-4 w-4 text-primary" />
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-xs text-muted-foreground">Moviebot</span>
              <div className="rounded-2xl rounded-tl-md bg-secondary px-4 py-3">
                <LoadingDots />
              </div>
            </div>
          </div>
        )}
    </div>
  )
}
