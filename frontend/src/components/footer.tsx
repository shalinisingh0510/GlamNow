import Link from "next/link";

export function Footer() {
  return (
    <footer className="bg-gn-text-primary text-gn-bg-primary pt-16 pb-12 border-t border-gn-border-default">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-10 pb-12 border-b border-gn-text-secondary/40">
          {/* Brand info */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="h-10 w-10 rounded-gn-md bg-gradient-to-tr from-gn-accent-primary to-gn-accent-secondary flex items-center justify-center">
                <span className="text-white font-serif text-2xl font-bold">G</span>
              </div>
              <span className="text-2xl font-bold font-serif text-white tracking-tight">
                Glam<span className="text-gn-accent-primary">Now</span>
              </span>
            </div>
            <p className="text-sm text-gn-text-muted max-w-sm leading-relaxed">
              India&apos;s premier quick commerce platform for verified at-home salon, grooming, therapeutic massage,
              and bespoke doorstep custom tailoring &amp; alterations.
            </p>
            <div className="flex items-center gap-3 text-xs text-gn-accent-secondary font-medium">
              <span className="inline-block h-2 w-2 rounded-full bg-emerald-400" />
              <span>Operating in Bengaluru, Mumbai, Delhi NCR, and Hyderabad</span>
            </div>
          </div>

          {/* Column 1: Beauty & Grooming */}
          <div>
            <h4 className="text-sm font-semibold uppercase tracking-wider text-white mb-4">Services</h4>
            <ul className="space-y-2.5 text-sm text-gn-text-muted">
              <li><Link href="#services" className="hover:text-white transition-colors">Hair Styling &amp; Spa</Link></li>
              <li><Link href="#services" className="hover:text-white transition-colors">Facials &amp; Cleanups</Link></li>
              <li><Link href="#services" className="hover:text-white transition-colors">Manicure &amp; Pedicure</Link></li>
              <li><Link href="#services" className="hover:text-white transition-colors">Men&apos;s Grooming &amp; Beard</Link></li>
              <li><Link href="#services" className="hover:text-white transition-colors">Therapeutic Massage</Link></li>
              <li><Link href="#services" className="hover:text-white transition-colors">Bridal &amp; Event Makeover</Link></li>
            </ul>
          </div>

          {/* Column 2: Custom Tailoring & Alterations */}
          <div>
            <h4 className="text-sm font-semibold uppercase tracking-wider text-white mb-4">Tailoring Studio</h4>
            <ul className="space-y-2.5 text-sm text-gn-text-muted">
              <li><Link href="#tailoring" className="hover:text-white transition-colors">Saree Draping &amp; Ironing</Link></li>
              <li><Link href="#tailoring" className="hover:text-white transition-colors">Pico &amp; Fall Stitching</Link></li>
              <li><Link href="#tailoring" className="hover:text-white transition-colors">Blouse &amp; Kurti Tailoring</Link></li>
              <li><Link href="#tailoring" className="hover:text-white transition-colors">Pant &amp; Suit Alterations</Link></li>
              <li><Link href="#tailoring" className="hover:text-white transition-colors">Home Measurement Visit</Link></li>
              <li><Link href="#tailoring" className="hover:text-white transition-colors">Doorstep Fabric Pickup</Link></li>
            </ul>
          </div>

          {/* Column 3: Trust & Safety */}
          <div>
            <h4 className="text-sm font-semibold uppercase tracking-wider text-white mb-4">Trust &amp; Safety</h4>
            <ul className="space-y-2.5 text-sm text-gn-text-muted">
              <li><span className="text-white">✓ Background-checked</span> pros</li>
              <li><span className="text-white">✓ Sanitized</span> single-use kits</li>
              <li><span className="text-white">✓ Transparent</span> upfront pricing</li>
              <li><span className="text-white">✓ 100%</span> satisfaction rework</li>
              <li><Link href="#support" className="hover:text-white transition-colors">24/7 Dedicated Support</Link></li>
            </ul>
          </div>
        </div>

        {/* Bottom copyright */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between text-xs text-gn-text-muted gap-4">
          <p>© 2026 GlamNow Technologies Pvt. Ltd. All rights reserved.</p>
          <div className="flex items-center gap-6">
            <Link href="#terms" className="hover:text-white transition-colors">Terms of Service</Link>
            <Link href="#privacy" className="hover:text-white transition-colors">Privacy Policy</Link>
            <Link href="#cancellation" className="hover:text-white transition-colors">Refund &amp; Reschedule Policy</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
