import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "./card";
import { Badge } from "./badge";
import { Button } from "./button";

export interface ServiceCardProps {
  id: string;
  category: string;
  name: string;
  description: string;
  durationMinutes: number;
  startingPricePaise: number;
  availableTiers?: ("basic" | "standard" | "premium")[];
  icon?: string;
  onSelectTier?: () => void;
  onQuickBook?: () => void;
  className?: string;
}

export function ServiceCard({
  category,
  name,
  description,
  durationMinutes,
  startingPricePaise,
  availableTiers = ["basic", "standard", "premium"],
  icon = "✨",
  onSelectTier,
  onQuickBook,
  className = "",
}: ServiceCardProps) {
  const priceRupees = Math.round(startingPricePaise / 100);

  return (
    <Card hover className={`flex flex-col bg-gn-bg-card border-gn-border-default ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-2">
          <Badge variant="outline">{category}</Badge>
          <span className="text-xs text-gn-text-tertiary flex items-center gap-1">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {durationMinutes} mins
          </span>
        </div>
        <div className="flex items-center gap-2 pt-2">
          <span className="text-xl">{icon}</span>
          <CardTitle className="text-lg">{name}</CardTitle>
        </div>
        <CardDescription className="line-clamp-2 text-xs sm:text-sm">
          {description}
        </CardDescription>
      </CardHeader>

      <CardContent className="flex-1 pb-4">
        {/* Available tiers chip list */}
        <div className="flex items-center gap-1.5 pt-1">
          <span className="text-[11px] text-gn-text-tertiary">Tiers:</span>
          {availableTiers.map((t) => (
            <Badge key={t} variant={t} className="text-[10px] py-0 px-2">
              {t}
            </Badge>
          ))}
        </div>
      </CardContent>

      <CardFooter className="pt-3 border-t border-gn-border-default/60 flex items-center justify-between gap-2">
        <div>
          <span className="text-[10px] text-gn-text-tertiary uppercase tracking-wide block">Starting at</span>
          <span className="text-lg font-bold font-serif text-gn-text-primary">₹{priceRupees}</span>
        </div>
        <div className="flex items-center gap-2">
          {onSelectTier && (
            <Button variant="ghost" size="sm" onClick={onSelectTier} className="text-xs border border-gn-border-default">
              Compare Tiers
            </Button>
          )}
          <Button variant="primary" size="sm" onClick={onQuickBook} className="text-xs">
            Add Service
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}
