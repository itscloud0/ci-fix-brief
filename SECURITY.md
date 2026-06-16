# Security

## Supported Versions

Security fixes target the latest released version.

## Reporting A Vulnerability

Please report vulnerabilities through GitHub Security Advisories or by opening a minimal public issue that does not include sensitive data.

## Log Safety

`ci-fix-brief` redacts common token and key-value secret shapes before rendering output. This is a safety layer, not a complete secret scanner.

Before sharing a generated brief publicly:

- Review the brief manually.
- Do not paste raw private CI logs into public issues.
- Run a dedicated secret scanner for high-risk logs.

## Scope

In scope:

- Failures to redact common token patterns that the project explicitly claims to handle.
- Bugs that cause the CLI to write output somewhere other than the requested path.

Out of scope:

- Redaction of every possible proprietary identifier.
- Secrets already committed to example logs by downstream users.
- Issues in third-party CI providers.
