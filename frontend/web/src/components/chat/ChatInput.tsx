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
      className="moviebot-input-bar flex items-end gap-3 p-2.5 transition-colors"
    >
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Welchen Film oder welche Serie suchst du?"
        rows={1}
        disabled={isLoading}
        className="min-h-10 flex-1 resize-none bg-transparent px-2.5 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none disabled:opacity-50 sm:min-h-12 sm:px-3 sm:py-3 sm:text-base"
      />
      {isSupported && (
        <button
          type="button"
          onClick={handleMicClick}
          disabled={isLoading}
          className={cn(
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-full border transition-all sm:h-12 sm:w-12",
            isListening
              ? "animate-pulse border-primary bg-primary text-primary-foreground shadow-[0_0_24px_hsl(var(--primary)/0.45)]"
              : "border-white/10 bg-white/10 text-primary hover:border-primary/40 hover:bg-primary/10"
          )}
          aria-label={isListening ? "Aufnahme stoppen" : "Spracheingabe starten"}
        >
          {isListening ? <MicOff className="h-4 w-4 sm:h-5 sm:w-5" /> : <Mic className="h-4 w-4 sm:h-5 sm:w-5" />}
        </button>
      )}
      <button
        type="submit"
        disabled={isLoading || !value.trim()}
        className={cn(
          "flex h-10 w-10 shrink-0 items-center justify-center rounded-full transition-all sm:h-12 sm:w-12",
          value.trim() && !isLoading
            ? "bg-primary text-primary-foreground shadow-[0_0_28px_hsl(var(--primary)/0.42)] hover:scale-105"
            : "bg-white/10 text-muted-foreground"
        )}
        aria-label="Nachricht senden"
      >
        <SendHorizontal className="h-4 w-4 sm:h-5 sm:w-5" />
      </button>
    </form>
  )
}
