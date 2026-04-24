# Deployment (Dokploy)

Single-app deployment: one public route (the web UI). The API and Ollama stay entirely internal to the compose network. Dokploy's Traefik fronts everything.

## Architecture in production

```
┌──── user's browser ────┐
│ https://krr.example... │
└──────────┬─────────────┘
           │ (HTTPS via Dokploy Traefik)
           ▼
┌─────────── web (Next.js :3000, internal only) ───────────┐
│ - Static assets + SSR served directly                    │
│ - `/api/*` rewritten server-side to the api container    │
└──────────┬───────────────────────────────────────────────┘
           │ (Docker network, http://api:8000)
           ▼
┌─────────── api (FastAPI :8000, internal only) ───────────┐
│ - Judge / Style / Knowledge orchestrator                 │
│ - FAISS index is baked into the image at build time      │
└──────────┬───────────────────────────────────────────────┘
           │ (Docker network, http://ollama:11434)
           ▼
┌─────────── ollama (:11434, internal only) ───────────────┐
│ - Model weights in named volume `ollama-models`          │
└──────────────────────────────────────────────────────────┘
```

Browser only ever sees one origin. `/api/generate/judge` SSE streams pass through Next.js rewrites unbuffered.

## Quick start on Dokploy

1. **Create a new Docker Compose application** in Dokploy. Point it at this repo + branch.
2. **Environment variables** — set these in the Dokploy UI (Application → Environment):

   ```
   KNOWLEDGE_MODEL=gemma4:latest
   STYLE_MODEL=gemma4:latest
   JUDGE_MODEL=rnj-1:latest
   MAX_NEW_TOKENS=768
   ALLOWED_ORIGINS=https://krr.example.com
   ```

   Adjust model names to whatever you've pulled in Ollama. Set `ALLOWED_ORIGINS` to the public domain you'll assign to the web service.

3. **Assign a domain to the `web` service** in Dokploy (Application → Domains → Add). Dokploy generates the Traefik route automatically; the service exposes port `3000` internally.

4. **Deploy**. Dokploy builds both Dockerfiles, pulls the ollama image, creates the volumes.

5. **Pull the Ollama models** (one-time, after first deploy):
   ```bash
   docker compose -p <dokploy-project> exec ollama ollama pull gemma4:latest
   docker compose -p <dokploy-project> exec ollama ollama pull rnj-1:latest
   ```
   Or from Dokploy's terminal shortcut for the ollama service. Whatever models you pull must match the `*_MODEL` env vars above.

   Model weights persist in the named `ollama-models` volume across redeploys.

6. **Verify.** Hit `https://krr.example.com/` — the Playground. The health dot in the sidebar goes green once Ollama + the FAISS index are both reachable. `/styles` shows the 8 style cards. Run a query; the SSE stream works.

## Using an external Ollama host

If you have a GPU box, you probably don't want Ollama in the same compose. Two changes:

- Remove the `ollama` service (and the `depends_on.ollama` block under `api`) from `docker-compose.yml`.
- Set `OLLAMA_HOST=https://ollama.your-gpu-host.example` in Dokploy env.

Pulling models happens on the GPU host, not the Dokploy deployment.

## What's NOT exposed to the host

- API (`:8000`), ollama (`:11434`), web (`:3000`) — internal to the compose network only. Dokploy's Traefik connects into the network by joining it; no host ports are published. If you need to poke at the API directly during debugging, `docker compose exec api curl -fs http://localhost:8000/api/health`.

## What persists across redeploys

- `ollama-models` — pulled model weights (important — pulling `gemma4:latest` is 9.6 GB).
- `api-results` — evaluation traces (optional; only matters if you run `python judge/run_pipeline.py --step evaluate` in the container).

Code + FAISS index rebuild from scratch on every redeploy.

## Scaling notes

- The FAISS `IndexFlatIP` is exact and fits in memory for bank sizes < ~100k cards. Beyond that, switch to IVF-PQ.
- `MAX_CONCURRENT_JUDGE_RUNS` (default 2) bounds in-flight SSE streams per api instance. The orchestrator loop holds a thread per run via `asyncio.to_thread`. If you horizontally scale the api service, each replica gets its own semaphore.
- Ollama throughput is the real bottleneck. For concurrent users, either scale Ollama vertically (GPU) or stand up a pool behind a load balancer and point `OLLAMA_HOST` at it.
