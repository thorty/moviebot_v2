import { Clapperboard, Laugh, Mountain, Music, Rocket, Search, Swords } from "lucide-react"

const EXAMPLE_PROMPTS = [
  { icon: Laugh, text: "Ein lustiger Film für den Abend mit Freunden", color: "#39ff14" },
  { icon: Rocket, text: "Die besten Sci-Fi Serien der letzten 5 Jahre", color: "#00f5ff" },
  { icon: Search, text: "Eine Krimiserie wie \"Death in Paradise\"", color: "#ff3131" },
  { icon: Swords, text: "Spannende Abenteuerfilme für die ganze Familie mit Piraten", color: "#ff00ff" },
  { icon: Mountain, text: "Eine Dokumentation über das Extrembergsteigen", color: "#b026ff" },
  { icon: Music, text: "Eine Dokumentation über Rockmusik", color: "#fff700" },
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
          Beschreibe mir, wonach dir heute ist, und ich empfehle dir Filme und Serien, die zu deinen Vorlieben passen. Je mehr Details du mir gibst, desto besser kann ich suchen!
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
              <Icon className="h-4 w-4 shrink-0 transition-colors" color={prompt.color} />
              <span className="leading-snug">{prompt.text}</span>
            </button>
          )
        })}
      </div>
      <div>
        <p className="max-w-md text-sm text-muted-foreground leading-relaxed">
        Du kannst deine Suche auch über den 'Filtern' anpassen!
        </p>
      </div>
    </div>
  )
}
