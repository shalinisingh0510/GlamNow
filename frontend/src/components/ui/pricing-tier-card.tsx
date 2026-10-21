import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "./card";
import { Badge, type BadgeVariant } from "./badge";
import { Button } from "./button";

export interface PricingTierCardProps {
  tier: "basic" | "standard" | "premium";
  title: string;
  description: string;
  pricePaise: number;
  durationMinutes: number;
  inclusions: string[];
  brands: string;
  isPopular?: boolean;
  isSelected?: boolean;
  onSelect?: () => void;
  className?: string;
}

export function PricingTierCard({
  tier,
  title,
  description,
  pricePaise,
  durationMinutes,
  inclusions,
  brands,
  isPopular,
  isSelected,
  onSelect,
  className = "",
}: PricingTierCardProps) {
  const badgeVariant: BadgeVariant = tier;
  const priceRupees = Math.round(pricePaise / 100);

  return (
    <Card
      hover
      className={`
        flex flex-col relative transition-all duration-[var(--gn-transition-base)]
        ${isPopular ? "border-gn-accent-primary ring-1 ring-gn-accent-primary/20 shadow-gn-md" : "border-gn-border-default"}
        ${isSelected ? "ring-2 ring-gn-accent-primary shadow-gn-lg" : ""}
        ${tier === "premium" ? "bg-gradient-to-b from-purple-50/40 via-gn-bg-card to-gn-bg-card" : "bg-gn-bg-card"}
        ${className}
      `}
    >
      {isPopular && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <span className="bg-gn-accent-primary text-white text-[11px] font-bold px-3 py-1 rounded-full uppercase tracking-wider shadow-xs">
            Most Popular
          </span>
        </div>
      )}

      <CardHeader className={isPopular ? "pt-8" : "pt-6"}>
        <div className="flex items-center justify-between">
          <Badge variant={badgeVariant}>{tier.toUpperCase()} TIER</Badge>
          <span className="text-xs text-gn-text-tertiary">~{durationMinutes} mins</span>
        </div>
        <CardTitle className="pt-2 text-xl">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>

      <CardContent className="flex-1 space-y-4">
        {/* Price display */}
        <div className="flex items-baseline gap-1.5 pb-2 border-b border-gn-border-default/60">
          <span className="text-3xl font-bold font-serif text-gn-text-primary">
            ₹{priceRupees}
          </span>
          <span className="text-xs text-gn-text-tertiary">/ all inclusive</span>
        </div>

        {/* Branded products tag */}
        <div className="p-2.5 rounded-gn-sm bg-gn-bg-secondary text-xs">
          <span className="font-semibold text-gn-text-primary block mb-0.5">Formulations:</span>
          <span className="text-gn-text-secondary">{brands}</span>
        </div>

        {/* Inclusions list */}
        <div className="space-y-1.5 pt-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-gn-text-tertiary">
            What&apos;s Included:
          </span>
          <ul className="space-y-1.5 text-xs text-gn-text-secondary">
            {inclusions.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-gn-success font-bold mt-0.5">✓</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </CardContent>

      <CardFooter className="pt-4 border-t border-gn-border-default/60">
        <Button
          variant={isSelected ? "primary" : isPopular ? "primary" : "ghost"}
          size="md"
          onClick={onSelect}
          className={`w-full ${!isSelected && !isPopular ? "border border-gn-border-default hover:bg-gn-bg-secondary" : ""}`}
        >
          {isSelected ? "Selected Tier ✓" : `Select ${tier.charAt(0).toUpperCase() + tier.slice(1)}`}
        </Button>
      </CardFooter>
    </Card>
  );
}
