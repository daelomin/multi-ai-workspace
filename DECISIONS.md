# Decisions

Record durable decisions here. Do not use this file for temporary discussion.

## Template
### YYYY-MM-DD — Decision title
**Proposed by:**
**Reviewed by:**
**Status:** proposed / accepted / rejected / superseded

**Context**

**Options considered**

**Decision**

**Consequences**

---

### 2026-10-02 — Spécification par phases v1.0 comme feuille de route
**Proposed by:** HUMAN  
**Reviewed by:** CLAUDE  
**Status:** accepted

**Context**  
Le workspace multi-AI n’avait pas encore de projet métier. Une spécification détaillée (phases 0–7) a été fournie.

**Options considered**  
- Adopter `SPEC_PHASES.md` comme feuille de route canonique  
- Réécrire / simplifier avant engagement

**Decision**  
Adopter `SPEC_PHASES.md` v1.0 comme découpage livrable. `MASTER.md` reste l’état courant ; le détail des phases vit dans `SPEC_PHASES.md`.

**Consequences**  
Travail immédiat = Phase 0. Jalons GO/NO-GO humains en fin de chaque phase. Stack figée phases 0–1 (Compose, pas K8s/Kafka).

### 2026-10-02 — Stack technique phases 0–1
**Proposed by:** HUMAN (via SPEC)  
**Reviewed by:** CLAUDE  
**Status:** proposed

**Context**  
Besoin d’un environnement reproductible avant développement fonctionnel.

**Options considered**  
- Compose local (Postgres/PostGIS/TimescaleDB, Redis, Martin) + FastAPI + MapLibre  
- K8s dès le départ

**Decision**  
Stack initiale : Python 3.12, Postgres 16 + PostGIS 3.4 + TimescaleDB 2.15, FastAPI + Pydantic v2, MapLibre GL JS, Redis, Martin ; Docker Compose only. Packaging uv vs poetry encore ouvert.

**Consequences**  
Pas de Kafka/K8s avant phase 3. Choix uv/poetry à trancher en Phase 0.3.

### 2026-10-02 — Axe pilote A11 Nantes–Paris
**Proposed by:** HUMAN (via SPEC)  
**Reviewed by:**  
**Status:** proposed

**Context**  
Phase 1 nécessite un seul axe pour valider la chaîne DATEX → LRS → carte.

**Options considered**  
- A11 Nantes–Paris (~350 km)  
- Autre axe (à proposer si licences/flux A11 insuffisants)

**Decision**  
Pilote proposé : A11 (trafic dense, mix DIR/concessionnaire, incidents fréquents). Validation formelle après inventaire sources.

**Consequences**  
LRS et collecteurs Phase 1 ciblent d’abord A11 ; bascule possible si accès DATEX bloqué.
