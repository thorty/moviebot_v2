import { FormEvent, useEffect, useMemo, useState } from "react"

import { ChatPage } from "@/pages/ChatPage"
import { isSupabaseConfigured, supabase } from "@/lib/supabase"

type SessionState = "loading" | "authenticated" | "unauthenticated"

export default function App() {
  const [sessionState, setSessionState] = useState<SessionState>("loading")
  const [userEmail, setUserEmail] = useState<string>("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [authError, setAuthError] = useState<string>("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const missingSupabaseVars = useMemo(() => {
    const missing: string[] = []
    if (!import.meta.env.VITE_SUPABASE_URL) {
      missing.push("VITE_SUPABASE_URL")
    }
    if (!import.meta.env.VITE_SUPABASE_ANON_KEY) {
      missing.push("VITE_SUPABASE_ANON_KEY")
    }
    return missing
  }, [])

  useEffect(() => {
    if (!isSupabaseConfigured || !supabase) {
      setSessionState("unauthenticated")
      return
    }

    supabase.auth.getSession().then(({ data }) => {
      const session = data.session
      if (session) {
        setUserEmail(session.user.email ?? "")
        setSessionState("authenticated")
      } else {
        setSessionState("unauthenticated")
      }
    })

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session) {
        setUserEmail(session.user.email ?? "")
        setSessionState("authenticated")
      } else {
        setUserEmail("")
        setSessionState("unauthenticated")
      }
    })

    return () => {
      subscription.unsubscribe()
    }
  }, [])

  const handleLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!supabase) {
      setAuthError("Supabase ist noch nicht konfiguriert.")
      return
    }
    setAuthError("")
    setIsSubmitting(true)
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) {
      setAuthError(error.message)
    }
    setIsSubmitting(false)
  }

  const handleLogout = async () => {
    if (!supabase) {
      return
    }
    await supabase.auth.signOut()
  }

  if (sessionState === "loading") {
    return (
      <div className="flex h-dvh items-center justify-center">
        <p className="text-sm text-muted-foreground">Session wird geladen…</p>
      </div>
    )
  }

  if (sessionState === "authenticated") {
    return <ChatPage userEmail={userEmail} onLogout={handleLogout} />
  }

  return (
    <div className="flex h-dvh items-center justify-center px-4">
      <div className="w-full max-w-md rounded-xl border border-border bg-card p-6">
        <h1 className="mb-2 text-xl font-semibold text-foreground">Moviebot Login</h1>
        <p className="mb-4 text-sm text-muted-foreground">Melde dich mit deinem Supabase-User an.</p>

        {!isSupabaseConfigured && (
          <div className="mb-4 rounded-md border border-border bg-secondary p-3 text-xs text-muted-foreground">
            Supabase ist noch nicht vollständig konfiguriert. Setze in `frontend/web/.env` folgende Variablen: {missingSupabaseVars.join(", ")}
          </div>
        )}

        <form className="space-y-3" onSubmit={handleLogin}>
          <div>
            <label className="mb-1 block text-xs text-muted-foreground">E-Mail</label>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground"
              style={{ color: "hsl(var(--background))", caretColor: "hsl(var(--background))", WebkitTextFillColor: "hsl(var(--background))" }}
              placeholder="you@example.com"
              required
            />
          </div>

          <div>
            <label className="mb-1 block text-xs text-muted-foreground">Passwort</label>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground"
              style={{ color: "hsl(var(--background))", caretColor: "hsl(var(--background))", WebkitTextFillColor: "hsl(var(--background))" }}
              placeholder="••••••••"
              required
            />
          </div>

          {authError && <p className="text-xs text-red-400">{authError}</p>}

          <button
            type="submit"
            disabled={isSubmitting || !isSupabaseConfigured}
            className="w-full rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? "Anmeldung läuft…" : "Einloggen"}
          </button>
        </form>
      </div>
    </div>
  )
}
