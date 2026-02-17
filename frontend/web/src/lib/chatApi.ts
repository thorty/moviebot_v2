import { supabase } from "@/lib/supabase"

const backendApiUrl = import.meta.env.VITE_BACKEND_API_URL || "http://localhost:8000"

export type ChatRequestPayload = {
  message: string
  userstreamingproviders: string[]
  paymenttypes: string[]
}

export type ChatResponsePayload = {
  status: string
  user_id: string
  conversation_id: string
  reply: string
}

export async function sendChatMessage(payload: ChatRequestPayload): Promise<ChatResponsePayload> {
  if (!supabase) {
    throw new Error("Supabase ist nicht konfiguriert.")
  }

  const {
    data: { session },
  } = await supabase.auth.getSession()

  const accessToken = session?.access_token
  if (!accessToken) {
    throw new Error("Keine aktive Session gefunden. Bitte neu einloggen.")
  }

  const response = await fetch(`${backendApiUrl}/api/v1/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const fallback = `Backend-Fehler (${response.status})`
    try {
      const errorBody = await response.json()
      throw new Error(errorBody?.detail || fallback)
    } catch {
      throw new Error(fallback)
    }
  }

  return (await response.json()) as ChatResponsePayload
}
