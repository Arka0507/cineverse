# Security and operational boundaries

## Implemented

- Signed, expiring, issuer/audience-bound profile tokens; subject checked against requested user ID.
- No client-supplied access to another profile. Demo dataset identities restricted to development.
- Production rejects the development signing secret and wildcard CORS.
- Strict Pydantic bodies, finite bounded ratings, bounded queries and pagination.
- Parameterized SQLite queries and atomic feedback/event writes.
- Trusted artifact checksums at startup, non-root containers, backend private network port.
- Same-origin production API, security headers, request IDs, bounded TMDB concurrency and timeouts.
- Per-client Nginx request limits, shared aggregate API limit, max ingress body size.
- TMDB key stays server-side; logger does not expose upstream request URLs.

## Actual dependency finding

The requested Next.js 14.2.35 is an old release line and npm audit reports a critical severity package finding. Patching PostCSS removes its separate findings, but cannot fix unsupported Next.js server releases. The production frontend is therefore a static export copied into Nginx: Node.js, Next.js server code, image optimization and server action endpoints are absent at runtime. All dynamic behavior uses the FastAPI API.

This reduces applicability of server-specific advisories; it is not an audit pass, a blanket security guarantee, or justification for using next dev in production. A current framework upgrade is required if your organization rejects the build dependency or needs Next.js server functionality. Review the saved npm audit report and the official advisory before release.

The security posture of a deployed system also depends on approved image digests, operating system patches, ingress and credentials. No container scanner, penetration test or hosted security assessment ran here.

## Enterprise identity and scaling

Profiles are signed anonymous sessions. They are not corporate employee identities, SSO, subscription accounts or an authorization model for premium video. If this is an internal enterprise service, place it behind your approved identity-aware gateway and integrate stable employee subjects before associating it with corporate personal data.

The browser uses local storage to retain a token. Nginx restricts content sources, but inline scripts/styles are allowed for Next.js export bootstrapping; this is not a nonce-based CSP. Do not render untrusted HTML or embed user-supplied scripts. Use an HttpOnly session architecture if your identity requirements demand it.

SQLite is single-host persistence. Use a distributed database, limiter and cache before adding independent replicas. Metadata warming is best effort; critical rating writes commit synchronously. There is no distributed durable background queue in this release because no critical task depends on one.

A model manifest detects accidental corruption, not a hostile model publisher. Restrict artifact write access and promote signed releases. Never unpickle an untrusted upload.

## Dataset and metadata

MovieLens inputs and TMDB assets retain their own usage terms. This source package does not grant rights to films, artwork or third-party datasets. The app plays verified trailers, not complete films. TMDB production metadata calls remain unverified without your API key.
