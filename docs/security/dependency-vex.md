# Dependency vulnerability VEX

Date: 2026-07-18  
Scope: production dependencies in `backend/requirements.txt`  
Owner: release engineering

## Decision

The package index available to this build currently resolves FastAPI to `0.128.8`, Starlette to `0.49.3`, and Click to `8.1.8`. The fixed Starlette releases are 1.x and are outside FastAPI's current `<0.50` compatibility range in this environment. These advisories are therefore acknowledged by exact ID in `security-ci.yml`; they are not silently suppressed. Remove each exception as soon as a compatible fixed dependency is resolvable.

| Advisory | Status | Rationale and compensating control | Revalidation |
|---|---|---|---|
| [PYSEC-2026-161](https://osv.dev/vulnerability/PYSEC-2026-161) | affected, mitigated | Starlette does not validate Host before reconstructing request URLs. `RequestBoundaryMiddleware` rejects missing or ambiguous Host values before routing. | `test_ambiguous_host_authorities_are_rejected` |
| [PYSEC-2026-248](https://osv.dev/vulnerability/PYSEC-2026-248) | affected, mitigated | A non-slash path can move the reconstructed authority boundary. The request boundary rejects every raw HTTP path not beginning with `/`. | `test_non_slash_request_target_is_rejected_before_routing` |
| [PYSEC-2026-249](https://osv.dev/vulnerability/PYSEC-2026-249) | affected, mitigated | URL-encoded form parser limits can be bypassed. The application does not expose form-upload routes and enforces both declared and streamed request-body limits (default 5 MiB) before handler parsing. | `test_declared_and_streamed_body_limits_are_enforced` |
| [PYSEC-2026-2280](https://osv.dev/vulnerability/PYSEC-2026-2280) | not affected by application usage | The issue requires an unconstrained Starlette `HTTPEndpoint` subclass. The application registers FastAPI function routes and has no `HTTPEndpoint` subclass. | CI source search plus route tests |
| [PYSEC-2026-2281](https://osv.dev/vulnerability/PYSEC-2026-2281) | not affected by deployment or usage | The issue is Windows-only `StaticFiles` UNC handling. The production image is Linux and the backend does not mount Starlette `StaticFiles`. | Docker image and source review |
| [PYSEC-2026-2132](https://osv.dev/vulnerability/PYSEC-2026-2132) | not affected by application usage | The vulnerable surface is `click.edit()`. Neither the application nor its startup path calls it. | CI source search and startup smoke |

`pytest` is intentionally in `requirements-dev.txt`, not the production image. [PYSEC-2026-1845](https://osv.dev/vulnerability/PYSEC-2026-1845) affects its Unix temporary-directory handling through 9.0.2. The available index provides 8.4.2 only, so CI must run in an isolated ephemeral runner without untrusted local users until 9.0.3 is available. It is not an exception in the production dependency audit because it is not a production dependency.

## Operational requirements

- Keep `MAX_REQUEST_BODY_BYTES` at or below 5 MiB unless a reviewed route requires more.
- Terminate public traffic at a reverse proxy that validates request targets and Host.
- Do not add `HTTPEndpoint`, backend `StaticFiles`, `click.edit()`, or form-upload routes without revisiting this VEX.
- Run the raw unignored audit during dependency upgrade review. The release gate uses only the exact exceptions above.
- Recheck this file whenever FastAPI, Starlette, Click, or pytest changes.

