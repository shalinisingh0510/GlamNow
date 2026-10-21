import { Card, CardHeader, CardContent, CardFooter } from "./card";
import { Badge } from "./badge";
import { Rating } from "./rating";
import { Button } from "./button";

export interface ProfessionalCardProps {
  id: string;
  name: string;
  title: string;
  experienceYears: number;
  ratingScore: number;
  reviewCount: number;
  etaMinutes: number;
  specialties: string[];
  startingPricePaise: number;
  avatarText?: string;
  isVerified?: boolean;
  isSelected?: boolean;
  onSelect?: () => void;
  className?: string;
}

export function ProfessionalCard({
  name,
  title,
  experienceYears,
  ratingScore,
  reviewCount,
  etaMinutes,
  specialties,
  startingPricePaise,
  avatarText,
  isVerified = true,
  isSelected = false,
  onSelect,
  className = "",
}: ProfessionalCardProps) {
  const priceRupees = Math.round(startingPricePaise / 100);
  const initials = avatarText || name.split(" ").map((n) => n[0]).join("").slice(0, 2);

  return (
    <Card
      hover
      onClick={onSelect}
      className={`
        cursor-pointer transition-all duration-[var(--gn-transition-base)] bg-gn-bg-card
        ${isSelected ? "ring-2 ring-gn-accent-primary shadow-gn-md border-transparent" : "border-gn-border-default"}
        ${className}
      `}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            {/* Avatar */}
            <div className="h-12 w-12 rounded-full bg-gn-accent-primary-subtle text-gn-accent-primary font-serif font-bold text-lg flex items-center justify-center shrink-0 shadow-xs">
              {initials}
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h4 className="font-semibold text-gn-text-primary text-base">{name}</h4>
                {isVerified && (
                  <span
                    className="inline-flex items-center justify-center h-4 w-4 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold"
                    title="Background-checked & certified"
                  >
                    ✓
                  </span>
                )}
              </div>
              <p className="text-xs text-gn-text-tertiary">{title}</p>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pb-4">
        {/* Rating and ETA badge strip */}
        <div className="flex items-center justify-between text-xs py-2 px-3 rounded-gn-sm bg-gn-bg-secondary">
          <Rating score={ratingScore} reviewCount={reviewCount} size="sm" />
          <span className="font-semibold text-emerald-700 flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 gn-pulse" />
            {etaMinutes}m ETA
          </span>
        </div>

        {/* Experience and Specialties */}
        <div className="space-y-1.5">
          <span className="text-[11px] text-gn-text-muted">
            {experienceYears}+ years exp • Specialties:
          </span>
          <div className="flex flex-wrap gap-1">
            {specialties.map((s) => (
              <Badge key={s} variant="outline" className="text-[10px] py-0 px-2 font-normal">
                {s}
              </Badge>
            ))}
          </div>
        </div>
      </CardContent>

      <CardFooter className="pt-3 border-t border-gn-border-default/60 flex items-center justify-between">
        <div>
          <span className="text-[10px] text-gn-text-tertiary uppercase tracking-wide block">Starting at</span>
          <span className="text-base font-bold font-serif text-gn-text-primary">₹{priceRupees}</span>
        </div>

        <Button
          variant={isSelected ? "primary" : "ghost"}
          size="sm"
          className={isSelected ? "" : "border border-gn-border-default text-xs"}
        >
          {isSelected ? "Selected ✓" : "Choose Pro"}
        </Button>
      </CardFooter>
    </Card>
  );
}
