# AWS estimate and shutdown plan — proposal only

Checked **2026-09-26** against official AWS pages. Budget in **USD**, target **us-east-1 (N. Virginia)**, no free-tier credits assumed. Monthly comparison uses **730 hours**. No AWS resources were created or priced through an authenticated account. Recheck the region-specific plan before any apply.

| Option | Planning cost | What this means |
|---|---|---|
| Native Python / local Docker / local kind | $0 AWS | Uses your machine; Docker licensing and local hardware are separate |
| Lightsail Linux micro, public IPv4 | $7/month bundle cap | 1 GB memory, 40 GB SSD; application-only demo, not HA and not the full telemetry stack |
| Lightsail Linux micro, IPv6-only | $5/month bundle cap | Lower cost if client/network IPv6 support is confirmed; IPv4 bundle is simpler for this exercise |
| EKS standard-support cluster | $0.10/hour; $73 at 730 hours | Control plane only; an 8-hour exercise is $0.80 control-plane cost plus workers and other resources |

Bundle specifications and hourly billing with a monthly cap come from [AWS Lightsail bundle documentation](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-bundles.html). EKS bills the control plane separately from worker resources; see [AWS EKS pricing](https://aws.amazon.com/eks/pricing/). These are component estimates, not an EKS total-cost quote.

The cheapest reasonable general-access demo is the $7 IPv4 VM. The $5 IPv6-only alternative is viable with verified connectivity. Neither is EKS. Running self-managed k3s on a VM would also not be EKS and is unnecessary for Phase 1. Local kind is the economical Kubernetes/GitOps learning environment. A real EKS deployment is optional and should be time-boxed, not left running for a portfolio link.

Excluded: tax, paid support, domain, snapshots, extra disks, excess data transfer, registry storage, log/trace ingestion or retention, load balancers, NAT, additional addresses, and all EKS workers/network/storage. A VM bundle's included storage/IP should not be counted twice. No claim is made that 1 GB supports Prometheus/Grafana/ArgoCD alongside the app. Exact EKS totals require a selected instance type/count, storage size, traffic and network plan; do not approve deployment from the control-plane subtotal.

## Before any later paid deployment

Record the approved runtime cap and resource inventory in the Terraform plan. Use tags including project/owner/expiry and an AWS budget notification; budget alerts do not automatically stop spending. Prefer one short session with teardown while still present. No cloud apply is included in Phase 1.

## Shutdown strategy

1. Capture the evidence needed for the portfolio, excluding credentials and account identifiers.
2. For Kubernetes, delete Service/Ingress resources and wait for controller-managed load balancers to disappear before destroying the cluster.
3. Review and execute Terraform destroy for the project. Do not treat stopping a VM or scaling workers to zero as teardown.
4. Check the region and billing/resource inventory for remaining instances, disks, snapshots, public/static addresses, load balancers, NAT gateways, registry images, log groups and cluster resources. Delete only this project's resources; preserve state until cleanup is verified.
5. Review cost data when it updates. Record the final inventory and remaining charges. EKS control-plane fees continue while the cluster exists; retained data/network resources can bill after compute deletion.

Lightsail stopped instances still incur charges until deletion, and unattached static IPs can bill; consult [AWS Lightsail FAQs](https://aws.amazon.com/lightsail/faq/). Keep the shutdown verification as evidence, not just a `terraform destroy` command in a README.
