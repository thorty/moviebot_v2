import { CreditCard, Monitor, ShoppingCart, Tv } from "lucide-react"

import { cn } from "@/lib/utils"

const STREAMING_PROVIDERS = [
  { id: "Netflix", name: "Netflix", color: "#E50914" },
  { id: "Disney Plus", name: "Disney Plus", color: "#113CCF" },
  { id: "Amazon", name: "Amazon", color: "#00A8E1" },
  { id: "WOW", name: "WOW", color: "#6B21A8" },
  { id: "Paramount Plus", name: "Paramount Plus", color: "#0064FF" },
  { id: "Apple TV", name: "Apple TV", color: "#A3A3A3" },
  { id: "Magenta TV", name: "Magenta TV", color: "#E20074" },
] as const

export type FilterSource = "streaming" | "mediathek"
export type PaymentType = "free" | "rent"

export interface Filters {
  source: FilterSource
  providers: string[]
  paymentTypes: PaymentType[]
  includeMediatheken: boolean
}

interface FilterPanelProps {
  filters: Filters
  onFiltersChange: (filters: Filters) => void
}

export function FilterPanel({ filters, onFiltersChange }: FilterPanelProps) {
  const DEFAULT_STREAMING_PAYMENT_TYPES: PaymentType[] = ["free", "rent"]
  const FLATRATE_COLOR = "#22C55E"
  const AUSLEIHEN_COLOR = "#F59E0B"

  const toggleProvider = (providerId: string) => {
    const newProviders = filters.providers.includes(providerId)
      ? filters.providers.filter((provider) => provider !== providerId)
      : [...filters.providers, providerId]

    onFiltersChange({ ...filters, providers: newProviders })
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        <Tv className="h-4 w-4" />
        Streamingdienste
      </div>

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
              const isFlatrateSelected = filters.paymentTypes.includes("free")
              const isAusleihenSelected = filters.paymentTypes.includes("rent")

              return (
                <>
              <button
                type="button"
                onClick={() => onFiltersChange({ ...filters, paymentTypes: ["free"] })}
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
                onClick={() => onFiltersChange({ ...filters, paymentTypes: ["rent"] })}
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

      <button
        type="button"
        role="switch"
        aria-checked={filters.includeMediatheken}
        onClick={() =>
          onFiltersChange({
            ...filters,
            source: "streaming",
            includeMediatheken: !filters.includeMediatheken,
            paymentTypes: filters.paymentTypes.length > 0 ? filters.paymentTypes : DEFAULT_STREAMING_PAYMENT_TYPES,
          })
        }
        className={cn(
          "flex w-fit items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-all",
          filters.includeMediatheken
            ? "border-primary bg-primary/10 text-primary"
            : "border-border bg-secondary text-muted-foreground hover:text-foreground hover:border-muted-foreground/40"
        )}
      >
        <Monitor className="h-4 w-4" />
        Mediatheken einbeziehen
      </button>

      {filters.includeMediatheken && (
        <p className="text-xs text-muted-foreground leading-relaxed">
          ARD, ZDF, Arte und 3sat werden zusätzlich berücksichtigt.
        </p>
      )}
    </div>
  )
}
