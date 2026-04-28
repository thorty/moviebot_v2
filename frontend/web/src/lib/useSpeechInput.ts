import { useCallback, useEffect, useRef, useState } from "react"

interface UseSpeechInputOptions {
  onTranscript: (text: string) => void
  lang?: string
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type SpeechRecognitionInstance = any

export function useSpeechInput({ onTranscript, lang = "de-DE" }: UseSpeechInputOptions) {
  const [isListening, setIsListening] = useState(false)
  const recognitionRef = useRef<SpeechRecognitionInstance>(null)
  const onTranscriptRef = useRef(onTranscript)

  // Always update ref with the latest callback
  useEffect(() => {
    onTranscriptRef.current = onTranscript
  }, [onTranscript])

  const SpeechRecognitionCtor =
    typeof window !== "undefined"
      ? // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
      : null

  const isSupported = !!SpeechRecognitionCtor

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop()
    setIsListening(false)
  }, [])

  const startListening = useCallback(() => {
    if (!SpeechRecognitionCtor || isListening) {
      console.warn("[useSpeechInput] startListening blocked:", {
        supported: !!SpeechRecognitionCtor,
        isListening,
      })
      return
    }

    console.log("[useSpeechInput] Starting recognition with lang:", lang)
    const recognition: SpeechRecognitionInstance = new SpeechRecognitionCtor()
    recognition.lang = lang
    recognition.interimResults = false
    recognition.maxAlternatives = 1

    recognition.onstart = () => {
      console.log("[useSpeechInput] Recognition started")
    }

    recognition.onresult = (event: SpeechRecognitionInstance) => {
      console.log("[useSpeechInput] Result event:", event)
      const transcript: string = event.results[0][0].transcript
      console.log("[useSpeechInput] Transcript received:", transcript)
      onTranscriptRef.current(transcript)
    }

    recognition.onend = () => {
      console.log("[useSpeechInput] Recognition ended")
      setIsListening(false)
      recognitionRef.current = null
    }

    recognition.onerror = (event: SpeechRecognitionInstance) => {
      console.error("[useSpeechInput] Recognition error:", event.error)
      setIsListening(false)
      recognitionRef.current = null
    }

    recognitionRef.current = recognition
    console.log("[useSpeechInput] Calling recognition.start()")
    recognition.start()
    setIsListening(true)
  }, [SpeechRecognitionCtor, isListening, lang])

  useEffect(() => {
    return () => {
      // eslint-disable-next-line react-hooks/exhaustive-deps
      recognitionRef.current?.stop()
    }
  }, [])

  return { isListening, isSupported, startListening, stopListening }
}
