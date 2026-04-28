import { Mic, MicOff, SendHorizontal } from "lucide-react"
import { useCallback, useEffect, useRef } from "react"

import { useSpeechInput } from "@/lib/useSpeechInput"
import { cn } from "@/lib/utils"

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

  const handleTranscript = useCallback(
    (transcript: string) => {
      onChange(value ? `${value} ${transcript}` : transcript)
    },
    [value, onChange]
  )

  const { isListening, isSupported, startListening, stopListening } = useSpeechInput({
    onTranscript: handleTranscript,
  })

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault()
      if (!isLoading && value.trim()) {
        onSubmit()
      }
    }
  }

  const handleMicClick = () => {
    if (isListening) {
      stopListening()
    } else {
      startListening()
    }
  }

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault()
        if (!isLoading && value.trim()) {
          onSubmit()
        }
      }}
      className="flex items-end gap-3 rounded-2xl border bg-secondary p-2 transition-colors"
      style={{
        borderColor: "hsl(var(--border))",
        backgroundColor: "hsl(var(--secondary))",
      }}
    >
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Welchen Film oder welche Serie suchst du?"
        rows={1}
        disabled={isLoading}
        className="flex-1 resize-none bg-transparent px-2 py-2 text-sm focus:outline-none disabled:opacity-50"
      />
      {isSupported && (
        <button
          type="button"
          onClick={handleMicClick}
          disabled={isLoading}
          className={cn(
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-all",
            isListening
              ? "bg-destructive text-destructive-foreground animate-pulse"
              : "bg-muted text-muted-foreground hover:bg-muted/80"
          )}
          aria-label={isListening ? "Aufnahme stoppen" : "Spracheingabe starten"}
        >
          {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
        </button>
      )}
      <button
        type="submit"
        disabled={isLoading || !value.trim()}
        className={cn(
          "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-all",
          value.trim() && !isLoading
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-muted-foreground"
        )}
        aria-label="Nachricht senden"
      >
        <SendHorizontal className="h-4 w-4" />
      </button>
    </form>
  )
}
