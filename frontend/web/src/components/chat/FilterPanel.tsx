import type { CSSProperties } from "react"
import { CreditCard, Monitor, ShoppingCart, Tv } from "lucide-react"

import { cn } from "@/lib/utils"

const STREAMING_PROVIDERS = [
  { id: "Netflix", name: "Netflix", color: "#FF3B3B" },
  { id: "Disney Plus", name: "Disney Plus", color: "#5E82FF" },
  { id: "Amazon", name: "Amazon", color: "#FF8A1F" },
  { id: "WOW", name: "WOW", color: "#8B5CF6" },
  { id: "Paramount Plus", name: "Paramount Plus", color: "#3B82F6" },
  { id: "Apple TV", name: "Apple TV", color: "#D1D5DB" },
  { id: "Magenta TV", name: "Magenta TV", color: "#F02D9E" },
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

  const togglePaymentType = (paymentType: PaymentType) => {
    const nextPaymentTypes = filters.paymentTypes.includes(paymentType)
      ? filters.paymentTypes.filter((currentType) => currentType !== paymentType)
      : [...filters.paymentTypes, paymentType]

    onFiltersChange({
      ...filters,
      paymentTypes: nextPaymentTypes.length > 0 ? nextPaymentTypes : DEFAULT_STREAMING_PAYMENT_TYPES,
    })
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col items-center gap-3">
      <div className="flex w-full flex-wrap justify-center gap-2.5">
        {STREAMING_PROVIDERS.map((provider) => {
          const isSelected = filters.providers.includes(provider.id)
          return (
            <button
              key={provider.id}
              type="button"
              onClick={() => toggleProvider(provider.id)}
              className={cn(
                "moviebot-filter-chip min-h-11",
                isSelected ? "is-selected" : "text-muted-foreground"
              )}
              style={
                {
                  "--chip-color": provider.color,
                } as CSSProperties
              }
            >
              <Tv className="h-4 w-4" />
              {provider.name}
            </button>
          )
        })}
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
            "moviebot-filter-chip min-h-11",
            filters.includeMediatheken ? "is-selected" : "text-muted-foreground"
          )}
          style={
            {
              "--chip-color": "#6EC7FF",
            } as CSSProperties
          }
        >
          <Monitor className="h-4 w-4" />
          Mediatheken
        </button>
      </div>
      <div className="flex flex-wrap justify-center gap-2.5">
        <button
          type="button"
          onClick={() => togglePaymentType("free")}
          className={cn(
            "moviebot-filter-chip min-h-10",
            filters.paymentTypes.includes("free") ? "is-selected" : "text-muted-foreground"
          )}
          style={
            {
              "--chip-color": FLATRATE_COLOR,
            } as CSSProperties
          }
        >
          <CreditCard className="h-4 w-4" />
          Flatrate
        </button>
        <button
          type="button"
          onClick={() => togglePaymentType("rent")}
          className={cn(
            "moviebot-filter-chip min-h-10",
            filters.paymentTypes.includes("rent") ? "is-selected" : "text-muted-foreground"
          )}
          style={
            {
              "--chip-color": AUSLEIHEN_COLOR,
            } as CSSProperties
          }
        >
          <ShoppingCart className="h-4 w-4" />
          Ausleihen
        </button>
      </div>
    </div>
  )
}
