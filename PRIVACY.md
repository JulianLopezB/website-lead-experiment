# Privacy & data handling

This document explains the legal basis and operational rules for processing
business contact data in this project. It is internal documentation, not a
public privacy notice — that comes later, once a domain is purchased.

## Scope

B2B outreach to small businesses physically located in Madrid, Spain, that do
not currently have a website. All contact information is sourced from publicly
published business listings (Google Places).

## Legal basis (GDPR)

Processing is performed under **Article 6(1)(f) GDPR — legitimate interests**.

**Legitimate interest**: offering a relevant commercial service (a website) to
businesses whose own published information demonstrates they would benefit from
it. The offer is narrowly targeted (small local businesses with no current web
presence) and uses contact channels the business has itself made public for the
purpose of being contacted by customers and partners.

**Necessity**: there is no less intrusive way to reach a self-employed
restaurateur or shopkeeper to propose a B2B service than the contact methods
they themselves publish.

**Balancing test**: the data subject is acting in a commercial capacity, not a
personal one. The data is already public. Outreach volume per business is
strictly capped (see "Operational rules" below). An opt-out is honored
immediately and permanently. On balance, the data subject's interests are not
overridden.

## Data we store

- Business name, address, neighborhood, geo coordinates
- Business phone number (as published)
- Public ratings and review counts
- Full Google Places API response (`raw jsonb`) for re-scoring without re-querying
- Internal status, score, and contact timestamps

We do **not** store: employee names beyond what Google Places publishes as
business owner/contact, reviewer names, or any data scraped outside the Places
API.

## Data subject rights

- **Access / erasure**: any business that requests it has its `leads` row
  hard-deleted (cascades to `demos`).
- **Objection (opt-out)**: any reply containing opt-out keywords (`baja`,
  `no contactar`, `unsubscribe`, `dar de baja`) sets `leads.opt_out = true`.
  No further outreach, ever. Enforced in `pipeline/outreach.py` (phase 5).
- **Rectification**: handled ad-hoc; volume is too low to justify a portal.

## Operational rules

- Maximum **2 outreach touches per business**, minimum 7 days apart. Enforced in
  outreach code, not just in process.
- `opt_out = true` is checked before every send. No exceptions.
- 180-day retention for `leads` with `status IN ('rejected', 'dead')`. See
  `PREREQUISITES.md` TODO.
- Secrets (`ANTHROPIC_API_KEY`, `RESEND_API_KEY`, `GOOGLE_PLACES_API_KEY`,
  `DATABASE_URL*`) are never committed; `.env` is gitignored.

## Data processors

- Supabase (EU region) — primary database
- Google (Places API) — data source
- Anthropic — content generation (no PII sent; only business name, category, neighborhood)
- Resend — email delivery
- Vercel — hosting of generated demo pages

A formal Record of Processing Activities (RoPA) and DPA links will be added
once a domain and contact email exist.
