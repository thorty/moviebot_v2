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

export type NewChatResponsePayload = {
  status: string
  user_id: string
  conversation_id: string
}

export class ApiHttpError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = "ApiHttpError"
    this.status = status
  }
}

async function buildHttpError(response: Response): Promise<ApiHttpError> {
  const fallback = `Backend-Fehler (${response.status})`

  try {
    const errorBody = await response.json()
    return new ApiHttpError(response.status, errorBody?.detail || fallback)
  } catch {
    return new ApiHttpError(response.status, fallback)
  }
}

async function getAccessToken(): Promise<string> {
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

  return accessToken
}

export async function sendChatMessage(payload: ChatRequestPayload): Promise<ChatResponsePayload> {
  const accessToken = await getAccessToken()

  const response = await fetch(`${backendApiUrl}/api/v1/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw await buildHttpError(response)
  }

  return (await response.json()) as ChatResponsePayload
}

export async function startNewChatContext(): Promise<NewChatResponsePayload> {
  const accessToken = await getAccessToken()

  const response = await fetch(`${backendApiUrl}/api/v1/chat/new`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    throw await buildHttpError(response)
  }

  return (await response.json()) as NewChatResponsePayload
}
