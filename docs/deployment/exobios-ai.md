# Deploying the landing page + AI chatbot to exobios.in

Scope: the public landing page (`exobios-frontend`) and its Biochemistry RAG
chatbot, calling `exobios-ai`'s `/chat` endpoint directly from the browser.
**`exobios-backend` is not part of this path** — the chatbot bypasses it
entirely (see `src/shared/services/aiAssistantService.js`), and the
frontend's login/dashboard flows still run against a local mock store, not a
real backend. Deploying those is a separate, larger project.

## Prerequisites (accounts you'll need)

- [Qdrant Cloud](https://cloud.qdrant.io) — free tier (1GB) is enough for the
  ~2,900-point Biochemistry corpus.
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) — free M0 tier.
  `/chat` itself never touches Mongo, but the app won't boot without
  `MONGO__URI` set (required field, no default — see `config/settings.py`),
  and `/health/ready` checks it.
- [Railway](https://railway.app) — hosts the `exobios-ai` container.
- Existing Vercel project for `exobios-frontend` (already deployed, per repo
  history) and whatever registrar/DNS manages `exobios.in` — both outside
  this repo, no in-repo config exists for either.

## 1. Qdrant Cloud — migrate the existing corpus

Don't re-run ingestion (it costs real HF API calls and time) — snapshot the
local `corpus` collection and restore it to the cloud cluster.

**Version gap gotcha (hit this for real doing the 2026-08 migration):**
local Qdrant was pinned to `v1.12.4` (see `docker-compose.yml`'s history);
Qdrant Cloud runs a current version (`v1.19.0` as of this migration). A
snapshot taken on `v1.12.4` fails to restore directly on `v1.19.0` —
`Failed to deserialize .../segment.json: unknown variant \`on_disk\`,
expected \`mmap\` or \`in_ram_mmap\``. Qdrant's on-disk segment format isn't
forward-compatible across that many minor versions in one jump. Fix: upgrade
the *local* Qdrant to match the cloud version first, stepping through a
couple of intermediate versions against the same volume so each hop can
migrate the format incrementally (jumping straight to the target version
panics the same way the cloud restore did):

```bash
docker compose stop qdrant && docker compose rm -f qdrant
# Step through intermediate versions against the SAME volume — confirm each
# one loads (GET :6333/collections/corpus returns "status":"green") before
# moving to the next. This exact sequence worked for the 1.12.4 -> 1.19.0 gap:
docker run -d --name exobios-qdrant -p 6333:6333 -p 6334:6334 \
  -v exobios-ai_qdrant_data:/qdrant/storage qdrant/qdrant:v1.13.6
# ... confirm green, then:
docker rm -f exobios-qdrant
docker run -d --name exobios-qdrant -p 6333:6333 -p 6334:6334 \
  -v exobios-ai_qdrant_data:/qdrant/storage qdrant/qdrant:v1.16.1
# ... confirm green, then finally:
docker rm -f exobios-qdrant
docker run -d --name exobios-qdrant -p 6333:6333 -p 6334:6334 \
  -v exobios-ai_qdrant_data:/qdrant/storage qdrant/qdrant:v1.19.0
```

`docker-compose.yml` is now pinned to `v1.19.0` going forward, so this
particular gap shouldn't recur for anyone starting fresh — this only bites
if you're migrating an *old* existing local volume.

Once local is on the same version as the cloud cluster, snapshot and
restore:

```bash
curl -X POST http://localhost:6333/collections/corpus/snapshots
# -> returns a snapshot name; download it:
curl -o corpus.snapshot http://localhost:6333/collections/corpus/snapshots/<name>

# Create a free cluster at cloud.qdrant.io, then restore into it:
curl -X POST "https://<your-cluster-url>/collections/corpus/snapshots/upload?wait=true" \
  -H "api-key: <cloud-api-key>" \
  -F "snapshot=@corpus.snapshot"
```

Verify: `GET https://<cluster-url>/collections/corpus` with the `api-key`
header should show `"status":"green"` and `points_count: 2853`.

## 2. MongoDB Atlas

Create a free M0 cluster, a DB user, and allow network access from `0.0.0.0/0`
(Railway doesn't have static egress IPs on standard plans — use a strong
generated DB password to compensate). Grab the `mongodb+srv://...`
connection string.

## 3. Railway — deploy exobios-ai

Actually deployed 2026-08-18 via `railway up` (CLI) from `exobios-ai/app/` —
if using the dashboard's "Deploy from GitHub repo" flow instead, set **Root
Directory** to `exobios-ai/app` (the `Dockerfile` lives there, not at the
repo root or `exobios-ai/`).

**Two Railway-specific Dockerfile gotchas hit for real, both already fixed
in the committed `Dockerfile` — flagging in case they resurface:**

1. Railway's build backend ("Metal builder") rejects
   `RUN --mount=type=cache,target=...` without an explicit `id=`, and then
   *also* rejects an explicit `id=` without an undocumented "cacheKey
   prefix" it never specifies — a stricter/different BuildKit frontend than
   plain Docker (which accepts the bare mount with no `id` at all). Fix
   here: dropped the cache mount from both `uv sync` steps entirely. Slower
   cold builds, but the Dockerfile now builds identically on local Docker,
   the existing `docker-build` GitHub Actions job, and Railway — no
   builder-specific syntax anywhere.
2. A freshly created Railway domain shows **`Target port: -`** and returns
   `502 Application failed to respond` even though the container is up and
   `EXPOSE 8000` is in the Dockerfile — Railway doesn't reliably infer the
   port from `EXPOSE`. Fix: `railway domain update <domain-id> --port 8000`
   (or the equivalent "Settings → Networking → target port" field in the
   dashboard) immediately after generating the domain.

Environment variables (mirrors `exobios-ai/app/.env.example`):

   | Variable | Value |
   |---|---|
   | `AI_API_KEY` | a new, strong random secret — **do not reuse** `local-dev-api-key` |
   | `CORS_ALLOWED_ORIGINS` | `https://exobios.in,https://www.exobios.in` (add the Vercel preview domain too if you want previews to work) |
   | `QDRANT__URL` | your Qdrant Cloud cluster URL |
   | `QDRANT__API_KEY` | your Qdrant Cloud API key |
   | `QDRANT__COLLECTION_NAME` | `corpus` |
   | `EMBEDDING__HF_TOKEN` | your HF token |
   | `RERANKER__HF_TOKEN` | same HF token (reused) |
   | `RERANKER__ENABLED` | `false` (HF has no working hosted reranker as of the 2026-08 audit — see `docs/ARCHITECTURE.md`) |
   | `LLM__GROQ_API_KEY` | your Groq key |
   | `LLM__MODEL` | `openai/gpt-oss-120b` (see the note in `.env.example` on why the old default is dead) |
   | `MONGO__URI` | your Atlas `mongodb+srv://...` string |
   | `RATE_LIMIT__ENABLED` | `true` |

4. Set the healthcheck path to `/health` (not `/health/ready` — that one
   legitimately returns 503 if a dependency is briefly unreachable, which
   would flap Railway's health status for no real reason).
5. Deploy, then generate a domain and set its target port to 8000 (see
   gotcha #2 above) — `https://<something>.up.railway.app`, that's what the
   frontend calls; no custom subdomain needed unless you want one.
6. Verify: `GET https://<railway-domain>/health/ready` → `"status": "UP"`
   with `mongo: ok`, `qdrant: ok`.

**Live production URL** (as of 2026-08-18): `https://exobios-ai-production.up.railway.app`

## 4. Vercel — point the frontend at production

Set these as production environment variables on the Vercel project, then
redeploy:

```
VITE_AI_SERVICE_URL=https://<your-railway-domain>
VITE_AI_API_KEY=<the same AI_API_KEY you set in Railway>
```

Confirm `exobios.in` is attached as the project's production domain in the
Vercel dashboard (not verified here — no DNS/domain config exists in this
repo, so this is a dashboard-only check).

## 5. Verify end-to-end on the real domain

Visit `https://exobios.in`, ask a question (e.g. "Explain glycolysis"),
confirm a grounded answer with expandable Sources appears. Check the browser
console for CORS errors — if you see one, the origin hitting the site
doesn't match `CORS_ALLOWED_ORIGINS` exactly (scheme + host, no trailing
slash).

## Known limitations to be aware of, not fixed here

- **`X-Api-Key` is visible in the browser bundle.** `VITE_AI_API_KEY` ships
  in client-side JS — anyone can read it via devtools and call `/chat`
  directly, bypassing the site. It stops casual abuse, not a determined one.
  The existing in-process rate limiter (`RATE_LIMIT__REQUESTS=60`/min per
  key) and Groq's own per-minute token cap are the actual ceilings on that.
  If this becomes a real problem, the fix is moving the Groq call behind a
  server-side proxy the browser never holds credentials for — not built
  today, since scope was "landing + chatbot only."
- **Groq free-tier ceiling**: ~8,000 tokens/minute on `gpt-oss-120b`, and a
  typical `/chat` call costs ~2,000 tokens — roughly 3-4 questions/minute
  before requests start 502'ing. Fine for a demo; upgrade the Groq plan if
  you expect concurrent real users.
- **Rate limiter is per-process** (`core/rate_limit.py`'s own docstring) —
  fine on Railway's default single instance; would silently under-enforce if
  you ever scale to multiple replicas.
- `exobios-backend/docker-compose.yml` has a broken Dockerfile path
  (`context: ../exobios-ai`, but the Dockerfile is at
  `exobios-ai/app/Dockerfile`) — irrelevant to this deploy since the backend
  isn't involved, but worth fixing whenever the backend actually gets
  deployed.
