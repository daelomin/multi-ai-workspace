# Host inventory (T0.1) — SCAFFOLD

Status: **scaffold** — every field marked `<fill>` must be captured from the actual target VPS before M0 gates. This file is the §12.1 / WP0 host inventory: one row per co-resident project/service with effective resource limits, storage, growth, backup and ownership, plus ingress, SSH/recovery and the aggregate admission check.

Sources of truth: `spec.md` §12.1 (aggregate capacity + effective limits), §12.2 (storage admission + bounded logging), §4.4 (preserve neighbors), WP0 (shared-host contract).

---

## 1. Host facts

| Field | Value | How to collect |
|---|---|---|
| Provider / region / instance | `<fill>` | provider console |
| Hostname (DNS) | `<fill>` | `hostname -f` |
| CPU cores (vCPU) | `<fill>` | `nproc`, `lscpu` |
| Physical RAM | `<fill>` | `free -h` |
| Swap size + swappiness | `<fill>` | `free -h`, `cat /proc/sys/vm/swappiness` |
| Root disk total / free | `<fill>` | `df -h /` |
| Data-disk(s) total / free | `<fill>` | `df -h` |
| Free inodes | `<fill>` | `df -i /` |
| OS + kernel | `<fill>` | `cat /etc/os-release`, `uname -r` |
| Docker version / Compose version | `<fill>` | `docker version`, `docker compose version` |
| Docker data root (location) | `<fill>` | `docker info --format '{{.DockerRootDir}}'` |

**Reserve policy (§12.1):** host reserve = `max(1 GiB, 20% of physical RAM)` = `<fill>`.

**Swap policy (§12.1):** explicitly choose size + per-container allowance; swap is **not** usable application capacity. Record decision here: `<fill>`.

---

## 2. Co-resident stack inventory (§12.1 table)

One row per **service** (not per stack) — include databases, monitoring, every Tunnel connector and one-shot helpers. Columns are the §12.1 required fields. Memory/CPU/PID are *effective* limits (verify with `docker inspect`, not just the Compose file).

| Project | Service | Kind | Count | Mem limit / observed peak | CPU limit / observed load | PID limit | Storage allocation | Growth estimate | Backup schedule | Maintenance owner |
|---|---|---|---|---|---|---|---|---|---|---|
| *Atlas (planned)* | `atlas-web` | web | 1 | 2 GiB / `<fill>` | 1.5 / `<fill>` | `<fill>` | `<fill>` (§5) | `<fill>` | T4.9 (owner-authorized) | Joe |
| *Atlas (planned)* | `cloudflared` | Tunnel connector | 1 | 256 MiB / `<fill>` | 0.25 / `<fill>` | `<fill>` | `<fill>` | `<fill>` | none (stateless) | Joe |
| *Atlas (planned)* | web tmpfs | tmpfs | 1 | 128 MiB (included in web budget) | — | — | 128 MiB | — | — | Joe |
| `<fill>` | `<fill>` | `<fill>` | `<fill>` | `<fill>` | `<fill>` | `<fill>` | `<fill>` | `<fill>` | `<fill>` | `<fill>` |

> The three "Atlas (planned)" rows are the §12.390–392 starting limits to *tune through measurement*, not final numbers. Rows 4+ are the **existing** co-resident stacks discovered on the host.

### 2.1 Existing stacks discovered (working scratch)

`docker compose ls -a` / `docker ps -a` output: `<paste>`

- [ ] Stack `<name>` → project dir `<fill>`, owner `<fill>`
- [ ] Stack `<name>` → project dir `<fill>`, owner `<fill>`
- [ ] One-shot helpers / cron / systemd units touching Docker: `<fill>`

---

## 3. Public listeners (§4.4 — preserve neighbors)

Inventory **before** touching firewall. Record the owner of every existing public listener and keep every owner-approved one reachable.

| Port | Proto | Owner / stack | Keep? | Notes |
|---|---|---|---|---|
| 80 | TCP | `<fill>` | `<fill>` | `<fill>` |
| 443 | TCP | `<fill>` | `<fill>` | `<fill>` |
| `<fill>` | `<fill>` | `<fill>` | `<fill>` | `<fill>` |

Collect: `ss -tulpn` and cross-check `docker ps -a` published ports (Docker published ports bypass ufw/firewalld).

---

## 4. SSH & recovery access (§4.4)

| Item | Value |
|---|---|
| SSH admin source (approved) | `<fill>` (CIDR / bastion) |
| Provider console recovery available? | `<fill>` |
| Existing SSH config / users | `<fill>` (`/etc/ssh/sshd_config.d/`, `getent passwd`) |
| Key-only auth enforced? | `<fill>` |

Rule: keep provider console recovery available **before** tightening SSH. Public SSH is not part of the application architecture.

---

## 5. Storage inputs (measured dataset sizes)

Snapshot from 22 Oct 2026 (from M0 checklist):

| Item | Size | Notes |
|---|---|---|
| `dist/` (served GeoJSON) | ≈ 674 MB | serving data |
| `REFERENCE` | ≈ 131 MB | fuel station inputs |
| `REFERENCE_EV` | ≈ 275 MB | charger inputs |
| raw US/China PBF | ≈ 13.75 GB | **not** part of the portable serving image; worker/research input only |
| Atlas serving image (planned) | `<fill>` | set after T1.5 build |

**Atlas per-app allocation to define (§12.2):** `<fill>` (e.g. a dedicated `data/` bind or quota). Bind-directory organization alone is **not** a disk quota.

---

## 6. Aggregate admission check (§12.1)

```
Σ (concurrent service mem limits) + host reserve   ≤   physical RAM
Σ = <fill>  (sum of §2 "Mem limit" column)
host reserve = <fill>  (max(1 GiB, 20% RAM))
physical RAM = <fill>
→ <fill> PASS / FAIL
```

Same check for **PID limits** and **CPU** ceilings (record separately — CPU is a scheduler ceiling, not a reservation; do not over-subscribe beyond measured headroom).

> Per-container ceilings do **not** reserve memory/CPU and do **not** enforce a project-wide aggregate. Account every service separately with `mem_limit`, `cpus`, `pids_limit` and supported swap controls; verify with `docker inspect` after startup (T4.4 preflight enforces this — fail, don't silently omit).

---

## 7. Storage admission inputs (§12.2)

Peak additional space to estimate before each pull/load/import/export/backup/restore/update: `compressed archive + extracted files + staging + new image layers + old retained release/image + concurrent jobs`. For `restore`, also `retained current state + active release`.

| Operation | Peak-space formula inputs | Free bytes | Free inodes | Fits? |
|---|---|---|---|---|
| image pull/load | `<fill>` | `<fill>` | `<fill>` | `<fill>` |
| release import | `<fill>` | `<fill>` | `<fill>` | `<fill>` |
| backup | `<fill>` | `<fill>` | `<fill>` | `<fill>` |
| restore | `<fill>` | `<fill>` | `<fill>` | `<fill>` |

Hard rule (§12.2 / A15 / S05): refuse when it cannot fit; **no automatic cleanup/expiration**. Restoring capacity = added storage or explicit item-specific removal authorization.

---

## 8. Backup destination & encryption recipient

| Item | Value |
|---|---|
| Backup destination (off-host) | `<fill>` (path / bucket / host) |
| Encryption recipient (age/gpg key) | `<fill>` |
| Retention policy | `<fill>` (owner-authorized only; no auto-prune) |

This is an **input** to T4.9 (backup), not an implementation here.

---

## 9. Collection commands (run on the target VPS, paste results back)

```bash
nproc; free -h; df -h /; df -i /; cat /proc/sys/vm/swappiness
docker version --format '{{.Server.Version}}'; docker compose version
docker info --format '{{.DockerRootDir}}'
docker compose ls -a
docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
for c in $(docker ps -aq); do echo "== $c =="; docker inspect "$c" --format 'mem={{.HostConfig.Memory}} cpu={{.HostConfig.NanoCpus}} pids={{.HostConfig.PidsLimit}}'; done
ss -tulpn
getent passwd | grep -v nologin
```

---

## 10. Open questions / blockers

- [ ] Target VPS not yet identified (hostname/provider) — **blocks** §1–§4 completion.
- [ ] Existing co-resident stacks unknown — **blocks** the §2 table and the §6 admission check.
- [ ] Backup destination + encryption recipient not chosen — **blocks** T4.9 input.
- [ ] Whether raw PBF (~13.75 GB) lives on this host at all — determines worker-vs-serving disk budget.
