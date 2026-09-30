# ReServeAI — User Roles & Permissions Matrix

## 1. Overview
ReServeAI implements strict, server-side Role-Based Access Control (RBAC). Ten distinct roles govern tenant boundaries and operational access.

---

## 2. Role Definitions

| Role Identifier | Typical User Profile | Core Permissions |
| :--- | :--- | :--- |
| `SUPER_ADMIN` | Platform DevOps / Site Reliability Engineers | Unrestricted multi-tenant access, system health, user administration, global analytics. |
| `ORG_ADMIN` | Organization Executive / Enterprise Director | Full management of organization kitchens, users, inventories, and redistribution offers. |
| `KITCHEN_MANAGER` | Executive Chef / Commercial Kitchen Supervisor | Meal demand forecasting, surplus batch creation, inventory logging, internal kitchen operations. |
| `QUALITY_INSPECTOR` | Food Safety Specialist / QA Officer | Computer vision freshness screening, IoT sensor review, human verification sign-off. |
| `LOGISTICS_COORDINATOR` | Fleet Dispatcher / Supply Chain Manager | Route generation, VRP optimization, vehicle/driver assignment, delivery tracking. |
| `LOGISTICS_DRIVER` | Cold-Chain Vehicle Operator | Viewing assigned routes, stop navigation, proof-of-delivery OTP confirmation. |
| `NGO_REP` | Food Bank / Relief Agency Representative | Surplus discovery, meal reservation, delivery receipt verification. |
| `NGO_COORDINATOR` | NGO Regional Director | Multi-site surplus allocation and partner coordination. |
| `ESG_AUDITOR` | Sustainability Assessor / Compliance Officer | Poore & Nemecek LCA reports, carbon offset verification, ESG export data. |
| `PUBLIC_USER` | Self-registered Citizen / Beneficiary | Public platform browsing, transparency reports; strictly barred from administrative endpoints. |

---

## 3. Route Authorization Matrix

| Endpoint Group | Allowed Roles | Default Unauthorized Response |
| :--- | :--- | :--- |
| `/api/v1/users/*` | `SUPER_ADMIN`, `ORG_ADMIN` | `403 Forbidden` |
| `/api/v1/organizations/*` | `SUPER_ADMIN`, `ORG_ADMIN` | `403 Forbidden` |
| `/api/v1/kitchens/*` | `SUPER_ADMIN`, `ORG_ADMIN`, `KITCHEN_MANAGER` | `403 Forbidden` |
| `/api/v1/inventory/*` | `SUPER_ADMIN`, `ORG_ADMIN`, `KITCHEN_MANAGER` | `403 Forbidden` |
| `/api/v1/quality/*` | `SUPER_ADMIN`, `QUALITY_INSPECTOR`, `KITCHEN_MANAGER` | `403 Forbidden` |
| `/api/v1/logistics/*` | `SUPER_ADMIN`, `LOGISTICS_COORDINATOR`, `LOGISTICS_DRIVER` | `403 Forbidden` |
| `/api/v1/sustainability/*` | `SUPER_ADMIN`, `ORG_ADMIN`, `ESG_AUDITOR`, `KITCHEN_MANAGER` | `403 Forbidden` |
| `/api/v1/auth/me` | All Authenticated Users | `401 Unauthorized` (if no JWT) |
| `/health`, `/health/live`, `/health/ready` | Unauthenticated (Public / Orchestrators) | `200 OK` / `503 Unavailable` |
