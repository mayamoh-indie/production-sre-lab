# Security scope

The current demo binds the host port to loopback. It has no authentication, TLS termination, rate limiting, or multi-tenant isolation. Catalog data is synthetic. Never put deployment credentials or personal/customer data in it. Before public or shared access, implement the ingress trust boundary and restrict health/metrics exposure.

Input validation is strict, unknown fields are rejected, and catalog failures prevent startup. Request events avoid raw paths and query values; default access logging is disabled in documented launch commands. Validation responses may echo rejected caller input to that caller. Server exception tracebacks require normal log-access controls. Startup schema errors suppress raw validation causes to avoid printing catalog values.

Docker configuration selects a non-root user, read-only filesystem, dropped capabilities, and no privilege escalation. Python dependencies are version-pinned, not hash-locked; the base image and GitHub Actions references use tags, not immutable digests/SHAs yet. Package build tooling is not fully pinned. These are documented supply-chain limitations for the next delivery milestone, not a claim of hardened production supply-chain security.

Bandit scans application Python in Phase 1. It cannot prove the absence of vulnerabilities. Incrementally add Gitleaks before publishing/history review, Trivy image/filesystem scans and a CycloneDX or SPDX SBOM in Phase 2, and Checkov when Terraform/Kubernetes configuration exists. Record findings, severity gates and justified exceptions; do not hide failures with blanket ignores. Add Terraform validation and Helm lint as those artifacts arrive. Cloud CI should use scoped OIDC federation rather than static AWS keys.

No cloud credentials, resource provisioning, image publishing or public GitHub publication is part of Phase 1.
