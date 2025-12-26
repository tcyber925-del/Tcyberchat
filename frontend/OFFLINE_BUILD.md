Offline Frontend Build (for air-gapped / restricted networks)
=============================================================

Overview
--------
If your environment cannot access the public npm registry, you can build the frontend offline by providing two artifacts in `frontend/offline/`:

1) `pnpm.tgz` — a packed pnpm release
   - Create on a machine with network access: `npm pack pnpm@<version>`
   - Example:
     - `npm pack pnpm@8.12.1`
     - Rename the produced `pnpm-8.12.1.tgz` to `pnpm.tgz` and place in `frontend/offline/pnpm.tgz`

2) `prebuilt.tar.gz` — a tarball containing the built standalone output
   - On a machine with network access and the same Node major architecture, from repo root:
     - cd frontend
     - pnpm install --no-frozen-lockfile
     - pnpm build
     - cd ..
     - tar -czf frontend/offline/prebuilt.tar.gz -C frontend .next public
   - The tar should contain `.next/standalone/frontend` (the Next standalone build folder) and any static/public files you need at runtime.

Building the image (offline)
----------------------------
From the repo root (no network required during Docker build after the artifacts are present):

# Build using the offline Dockerfile
docker build -f frontend/Dockerfile.offline -t tcyber_frontend:offline .

# Or build with docker compose directly (use -f and an override if desired):
docker compose -f docker-compose.yml -f docker-compose.yml build --no-cache --progress=plain frontend

Notes and caveats
-----------------
- The offline workflow assumes you provide a prebuilt Next standalone output. This is simpler and more reliable than attempting to fully reproduce pnpm install offline.
- If you want to run pnpm install offline inside the container, ensure the prebuilt archive includes `node_modules` compatible with the container's OS and Node version.
- The `frontend/Dockerfile.offline` will fail if either `frontend/offline/pnpm.tgz` or `frontend/offline/prebuilt.tar.gz` are missing — this is by design to fail early.

If you want, I can also add a convenience script to validate the offline artifacts before the Docker build; let me know.