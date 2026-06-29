import { supabase } from "@/lib/supabase"

const backendApiUrl = import.meta.env.VITE_BACKEND_API_URL || "http://localhost:8000"

export type ChatRequestPayload = {
  message: string
  userstreamingproviders: string[]
  paymenttypes: string[]
  include_mediatheken: boolean
}

export type MediaType = "movie" | "documentary" | "series"

export type RecommendationCandidate = {
  title: string
  media_type: MediaType
  description: string
  cover_url: string | null
  rating: number | null
  rating_source: string | null
  streaming_providers: string[]
}

export type ChatResponsePayload = {
  status: string
  user_id: string
  conversation_id: string
  reply: string
  recommendations: RecommendationCandidate[]
}

export type NewChatResponsePayload = {
  status: string
  user_id: string
  conversation_id: string
}

export type UserFilterPreferencesPayload = {
  source: "streaming" | "mediathek"
  providers: string[]
  paymenttypes: string[]
  include_mediatheken: boolean
}

export type UserFilterPreferencesResponse = {
  status: string
  user_id: string
  source: "streaming" | "mediathek"
  providers: string[]
  paymenttypes: string[]
  include_mediatheken: boolean
}

export type WatchlistItemPayload = {
  title: string
  media_type: MediaType
  description: string
  cover_url: string | null
  rating: number | null
  rating_source: string | null
  streaming_providers: string[]
}

export type WatchlistItem = WatchlistItemPayload & {
  id: string
  user_id: string
  created_at?: string | null
  updated_at?: string | null
}

export type WatchlistItemsResponse = {
  status: string
  user_id: string
  items: WatchlistItem[]
}

export type WatchlistItemResponse = {
  status: string
  user_id: string
  item: WatchlistItem
}

export type WatchlistDeleteResponse = {
  status: string
  user_id: string
  item_id: string
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

export async function getUserFilters(): Promise<UserFilterPreferencesResponse> {
  const accessToken = await getAccessToken()

  const response = await fetch(`${backendApiUrl}/api/v1/user/filters`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    throw await buildHttpError(response)
  }

  return (await response.json()) as UserFilterPreferencesResponse
}

export async function saveUserFilters(
  payload: UserFilterPreferencesPayload
): Promise<UserFilterPreferencesResponse> {
  const accessToken = await getAccessToken()

  const response = await fetch(`${backendApiUrl}/api/v1/user/filters`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw await buildHttpError(response)
  }

  return (await response.json()) as UserFilterPreferencesResponse
}

export async function getWatchlist(): Promise<WatchlistItemsResponse> {
  const accessToken = await getAccessToken()

  const response = await fetch(`${backendApiUrl}/api/v1/user/watchlist`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    throw await buildHttpError(response)
  }

  return (await response.json()) as WatchlistItemsResponse
}

export async function saveWatchlistItem(payload: WatchlistItemPayload): Promise<WatchlistItemResponse> {
  const accessToken = await getAccessToken()

  const response = await fetch(`${backendApiUrl}/api/v1/user/watchlist`, {
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

  return (await response.json()) as WatchlistItemResponse
}

export async function deleteWatchlistItem(itemId: string): Promise<WatchlistDeleteResponse> {
  const accessToken = await getAccessToken()

  const response = await fetch(`${backendApiUrl}/api/v1/user/watchlist/${encodeURIComponent(itemId)}`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    throw await buildHttpError(response)
  }

  return (await response.json()) as WatchlistDeleteResponse
}
