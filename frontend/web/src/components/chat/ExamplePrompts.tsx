import { Clapperboard, Laugh, Mountain, Music, Rocket, Search, Swords } from "lucide-react"

const EXAMPLE_PROMPTS = [
  { icon: Laugh, text: "Ein lustiger Film für den Abend mit Freunden" },
  { icon: Rocket, text: "Die besten Sci-Fi Serien der letzten 5 Jahre" },
  { icon: Search, text: "Eine Krimiserie wie \"Death in Paradise\"" },
  { icon: Swords, text: "Spannende Abenteuerfilme für die ganze Familie mit Piraten" },
  { icon: Mountain, text: "Eine Dokumentation über das Extrembergsteigen" },
  { icon: Music, text: "Eine Dokumentation über Rockmusik" },
]

interface ExamplePromptsProps {
  onSelect: (prompt: string) => void
}

export function ExamplePrompts({ onSelect }: ExamplePromptsProps) {
  return (
    <div className="flex flex-col items-center gap-8 py-8">
      <div className="flex flex-col items-center gap-3 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
          <Clapperboard className="h-8 w-8 text-primary" />
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Was möchtest du schauen?</h1>
        <p className="max-w-md text-sm text-muted-foreground leading-relaxed">
          Beschreibe mir, wonach dir heute ist, und ich finde die passende Empfehlung.
        </p>
      </div>

      <div className="grid w-full max-w-lg grid-cols-1 gap-2 sm:grid-cols-2">
        {EXAMPLE_PROMPTS.map((prompt) => {
          const Icon = prompt.icon
          return (
            <button
              key={prompt.text}
              onClick={() => onSelect(prompt.text)}
              className="group flex items-center gap-3 rounded-xl border border-border bg-secondary/50 px-4 py-3 text-left text-sm text-muted-foreground transition-all hover:border-primary/30 hover:bg-secondary hover:text-foreground"
            >
              <Icon className="h-4 w-4 shrink-0 text-muted-foreground group-hover:text-primary transition-colors" />
              <span className="leading-snug">{prompt.text}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
