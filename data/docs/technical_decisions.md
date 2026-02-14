# Technical Decisions Log

**Updated:** Week 12  
**Maintainer:** Engineering Lead

---

## TD-001: Database Migration Approach
We are migrating from MySQL to PostgreSQL to support analytics workloads and scaling.

---

## TD-002: Analytics Delivery Approach Options

### Option A: Build Analytics In-House
**Pros**
- Full control over data model and UX
- Lower long-term licensing cost
- Tight integration with our product workflows

**Cons**
- Slower initial delivery
- Requires maintenance and dedicated engineering capacity

---

### Option B: Use a Third-Party BI Tool
**Pros**
- Fastest time-to-market
- Mature charting and exports

**Cons**
- Vendor lock-in
- Per-seat licensing cost
- Limited customization for our workflow-specific reporting

---

## Current Recommendation (Week 12)
Proceed with **Option A (In-House)** for the MVP because analytics is strategic differentiation, but keep Option B as contingency if Week 16 timeline slips.

---

## TD-003: Vector Search for Internal Docs
For internal assistant docs:
- Use chunking + embeddings
- Store in FAISS for local prototype
- Enforce citations for all claims
