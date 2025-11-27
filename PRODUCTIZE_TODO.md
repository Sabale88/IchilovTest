# Productization Considerations

- Add auth: SSO (OIDC) + RBAC so only authorized clinical staff access PHI.
- Automate ingestion: replace manual CSV loaders with S3 event pipeline + worker jobs.
- Schedule snapshot generation, expose health/metrics for the job.
- Harden database: migrations, backups, read replicas, encryption at rest/in transit.
- Observability: structured logging, tracing/metrics, alerting hooks.
- CI/CD: lint/test gates, Docker images, deploy to staging/prod with IaC (Terraform).
- Frontend readiness: automated tests, error tracking, accessibility + i18n audits.
- Compliance: audit logs, retention policies, HIPAA/GDPR data handling review.

