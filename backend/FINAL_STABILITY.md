# AURA 3.0 — Final Stability Contract

AURA is designed so future changes fail safely rather than silently corrupting scientific truth.

## Guarantees by design
- Dynamic capability registry: no completion logic depends on one project domain.
- Dynamic data and evaluation contracts.
- Generated / implemented / tested / executed / measured / validated / completed are separate states.
- Completion requires required gates, evidence, validation and human approval.
- Controlled execution uses an allowlist, subprocess isolation, path protection and timeouts.
- Project state persists through the existing durable snapshot store.
- Health and completion endpoints expose regressions and blockers.
- Truth boundary prevents synthetic smoke tests from becoming scientific evidence.

## Operational rule
Every future release should run backend compilation, API tests, frontend TypeScript/build, execution smoke tests, truth-boundary tests and an end-to-end project lifecycle test before deployment.

No software release can honestly promise zero future defects. AURA instead makes defects observable, bounded, auditable and recoverable.
