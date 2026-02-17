import { CreditCard, Monitor, ShoppingCart, Tv } from "lucide-react"

import { cn } from "@/lib/utils"

const STREAMING_PROVIDERS = [
  { id: "netflix", name: "Netflix", color: "#E50914" },
  { id: "disney-plus", name: "Disney+", color: "#113CCF" },
  { id: "amazon", name: "Amazon", color: "#00A8E1" },
  { id: "wow", name: "WOW", color: "#6B21A8" },
  { id: "paramount-plus", name: "Paramount+", color: "#0064FF" },
  { id: "apple-tv", name: "Apple TV+", color: "#A3A3A3" },
  { id: "magenta-tv", name: "Magenta TV", color: "#E20074" },
] as const

export type FilterSource = "streaming" | "mediathek"
export type PaymentType = "flatrate" | "rent"

export interface Filters {
  source: FilterSource
  providers: string[]
  paymentTypes: PaymentType[]
}

interface FilterPanelProps {
  filters: Filters
  onFiltersChange: (filters: Filters) => void
}

export function FilterPanel({ filters, onFiltersChange }: FilterPanelProps) {
  const AUSLEIHEN_PAYMENT_TYPES: PaymentType[] = ["flatrate", "rent"]
  const FLATRATE_COLOR = "#22C55E"
  const AUSLEIHEN_COLOR = "#F59E0B"

  const toggleProvider = (providerId: string) => {
    const newProviders = filters.providers.includes(providerId)
      ? filters.providers.filter((provider) => provider !== providerId)
      : [...filters.providers, providerId]

    onFiltersChange({ ...filters, providers: newProviders })
  }

  const setSource = (source: FilterSource) => {
    onFiltersChange({
      source,
      providers: [],
      paymentTypes: source === "streaming" ? AUSLEIHEN_PAYMENT_TYPES : [],
    })
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setSource("streaming")}
          className={cn(
            "flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-all",
            filters.source === "streaming"
              ? "bg-primary text-primary-foreground"
              : "bg-secondary text-muted-foreground hover:text-foreground hover:bg-secondary/80"
          )}
        >
          <Tv className="h-4 w-4" />
          Streaming
        </button>
        <button
          type="button"
          onClick={() => setSource("mediathek")}
          className={cn(
            "flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-all",
            filters.source === "mediathek"
              ? "bg-primary text-primary-foreground"
              : "bg-secondary text-muted-foreground hover:text-foreground hover:bg-secondary/80"
          )}
        >
          <Monitor className="h-4 w-4" />
          Mediatheken
        </button>
      </div>

      {filters.source === "streaming" && (
        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap gap-2">
            {STREAMING_PROVIDERS.map((provider) => {
              const isSelected = filters.providers.includes(provider.id)
              return (
                <button
                  key={provider.id}
                  type="button"
                  onClick={() => toggleProvider(provider.id)}
                  className={cn(
                    "rounded-lg px-3 py-2 text-sm font-medium transition-all border",
                    isSelected
                      ? "border-transparent text-foreground"
                      : "border-border text-muted-foreground hover:text-foreground hover:border-muted-foreground/40"
                  )}
                  style={
                    isSelected
                      ? {
                          backgroundColor: `${provider.color}20`,
                          borderColor: provider.color,
                          color: provider.color,
                        }
                      : undefined
                  }
                >
                  {provider.name}
                </button>
              )
            })}
          </div>

          {filters.providers.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground mr-1">Bezahlmodell:</span>
              {(() => {
                const isFlatrateSelected = filters.paymentTypes.includes("flatrate")
                const isAusleihenSelected =
                  filters.paymentTypes.includes("flatrate") && filters.paymentTypes.includes("rent")

                return (
                  <>
              <button
                type="button"
                onClick={() => onFiltersChange({ ...filters, paymentTypes: ["flatrate"] })}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all border",
                  isFlatrateSelected
                    ? "border-transparent"
                    : "border-border bg-secondary text-muted-foreground hover:text-foreground hover:border-muted-foreground/40"
                )}
                style={
                  isFlatrateSelected
                    ? {
                        backgroundColor: `${FLATRATE_COLOR}20`,
                        borderColor: FLATRATE_COLOR,
                        color: FLATRATE_COLOR,
                      }
                    : undefined
                }
              >
                <CreditCard className="h-3.5 w-3.5" />
                Flatrate
              </button>
              <button
                type="button"
                onClick={() => onFiltersChange({ ...filters, paymentTypes: AUSLEIHEN_PAYMENT_TYPES })}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all border",
                  isAusleihenSelected
                    ? "border-transparent"
                    : "border-border bg-secondary text-muted-foreground hover:text-foreground hover:border-muted-foreground/40"
                )}
                style={
                  isAusleihenSelected
                    ? {
                        backgroundColor: `${AUSLEIHEN_COLOR}20`,
                        borderColor: AUSLEIHEN_COLOR,
                        color: AUSLEIHEN_COLOR,
                      }
                    : undefined
                }
              >
                <ShoppingCart className="h-3.5 w-3.5" />
                Ausleihen
              </button>
                  </>
                )
              })()}
            </div>
          )}
        </div>
      )}

      {filters.source === "mediathek" && (
        <p className="text-xs text-muted-foreground leading-relaxed">
          Suche in den Mediatheken von ARD, ZDF, Arte, 3sat und weiteren öffentlich-rechtlichen Sendern.
        </p>
      )}
    </div>
  )
}
