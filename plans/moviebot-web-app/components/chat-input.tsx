"use client"

import { SendHorizontal } from "lucide-react"
import { cn } from "@/lib/utils"
import { useRef, useEffect } from "react"

interface ChatInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  isLoading: boolean
}

export function ChatInput({ value, onChange, onSubmit, isLoading }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`
    }
  }, [value])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      if (!isLoading && value.trim()) {
        onSubmit()
      }
    }
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        if (!isLoading && value.trim()) {
          onSubmit()
        }
      }}
      className="flex items-end gap-3 rounded-2xl border border-border bg-secondary p-2 transition-colors focus-within:border-primary/50"
    >
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Welchen Film oder welche Serie suchst du?"
        rows={1}
        disabled={isLoading}
        className="flex-1 resize-none bg-transparent px-2 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none disabled:opacity-50"
      />
      <button
        type="submit"
        disabled={isLoading || !value.trim()}
        className={cn(
          "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-all",
          value.trim() && !isLoading
            ? "bg-primary text-primary-foreground shadow-lg shadow-primary/30 hover:bg-primary/90"
            : "bg-muted text-muted-foreground"
        )}
        aria-label="Nachricht senden"
      >
        <SendHorizontal className="h-4 w-4" />
      </button>
    </form>
  )
}
