import type { CSSProperties } from "react"
import { Heart, Laugh, Music, Rocket, Search, Swords } from "lucide-react"

const EXAMPLE_PROMPTS = [
  {
    icon: Music,
    text: "Eine Dokumentation über Musik",
    accent: "#8B5CF6",
    glow: "rgba(124, 58, 237, 0.42)",
    backdrop: "radial-gradient(circle at 78% 54%, rgba(244, 190, 92, 0.8), transparent 12%), linear-gradient(135deg, rgba(68, 22, 114, 0.96), rgba(18, 12, 42, 0.94))",
  },
  {
    icon: Laugh,
    text: "Ein lustiger Film für den Abend mit Freunden",
    accent: "#2DD4BF",
    glow: "rgba(20, 184, 166, 0.32)",
    backdrop: "radial-gradient(circle at 74% 60%, rgba(25, 36, 34, 0.34), transparent 24%), linear-gradient(135deg, rgba(12, 83, 88, 0.94), rgba(4, 30, 38, 0.96))",
  },
  {
    icon: Rocket,
    text: "Die besten Sci-Fi Serien der letzten 5 Jahre",
    accent: "#F59E0B",
    glow: "rgba(245, 158, 11, 0.34)",
    backdrop: "radial-gradient(circle at 78% 62%, rgba(249, 115, 22, 0.72), transparent 22%), linear-gradient(135deg, rgba(86, 41, 5, 0.94), rgba(29, 18, 8, 0.96))",
  },
  {
    icon: Heart,
    text: "Etwas Romantisches ohne Drama mit Happy End",
    accent: "#EC4899",
    glow: "rgba(236, 72, 153, 0.34)",
    backdrop: "radial-gradient(circle at 74% 54%, rgba(244, 114, 182, 0.68), transparent 16%), linear-gradient(135deg, rgba(103, 24, 72, 0.96), rgba(37, 13, 34, 0.96))",
  },
  {
    icon: Swords,
    text: "Spannende Abenteuerfilme für die ganze Familie mit Piraten",
    accent: "#38BDF8",
    glow: "rgba(14, 165, 233, 0.34)",
    backdrop: "radial-gradient(circle at 76% 54%, rgba(56, 189, 248, 0.42), transparent 24%), linear-gradient(135deg, rgba(14, 74, 114, 0.94), rgba(8, 31, 59, 0.96))",
  },
  {
    icon: Search,
    text: "Eine Krimiserie wie \"Death in Paradise\"",
    accent: "#22C55E",
    glow: "rgba(34, 197, 94, 0.3)",
    backdrop: "radial-gradient(circle at 78% 56%, rgba(34, 197, 94, 0.34), transparent 24%), linear-gradient(135deg, rgba(21, 83, 45, 0.94), rgba(8, 35, 25, 0.96))",
  },
]

interface ExamplePromptsProps {
  onSelect: (prompt: string) => void
}

export function ExamplePrompts({ onSelect }: ExamplePromptsProps) {
  return (
    <div className="flex flex-col items-center gap-8 py-5 md:gap-10 md:py-7">
      <div className="flex flex-col items-center gap-3 text-center">
        <h1 className="moviebot-hero-title text-3xl font-black tracking-normal text-foreground sm:text-5xl lg:text-6xl">
          Was möchtest du schauen?
        </h1>
        <p className="max-w-3xl text-sm leading-relaxed text-muted-foreground sm:text-base md:text-lg">
          Erzähl mir, wonach dir ist - ich finde den perfekten Film oder die perfekte Serie für dich.
        </p>
      </div>

      <div className="hidden w-full max-w-5xl grid-cols-1 gap-4 sm:grid sm:grid-cols-2 lg:grid-cols-3">
        {EXAMPLE_PROMPTS.map((prompt) => {
          const Icon = prompt.icon
          return (
            <button
              key={prompt.text}
              onClick={() => onSelect(prompt.text)}
              className="moviebot-prompt-card group"
              style={
                {
                  "--prompt-accent": prompt.accent,
                  "--prompt-glow": prompt.glow,
                  background: prompt.backdrop,
                } as CSSProperties
              }
            >
              <span className="relative z-10 max-w-[12rem] text-balance text-left text-base font-semibold leading-snug text-white sm:text-xl md:text-2xl">
                {prompt.text}
              </span>
              <span className="moviebot-prompt-icon" aria-hidden="true">
                <Icon className="h-12 w-12" />
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
