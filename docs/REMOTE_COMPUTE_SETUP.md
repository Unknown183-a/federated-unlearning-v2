# Connecting the College GPU and Google Colab (Phase 14b)

Both backends are the same program: `python -m core.compute.server`, started on the remote machine and
reached from your Mac over HTTP. Only the way you reach it differs.

## What happens on a remote run
1. The dashboard calls the remote server's HTTP endpoints (`docs/COMPUTE_BACKENDS.md` lists them).
2. Before training / unlearning / evaluation, your Mac sends `experiments/<id>/` (partition, checkpoints) up.
3. The server runs the same `core/` code on its GPU. One job at a time; a second gets HTTP 409.
4. When it finishes, the server's `experiments/<id>/` is downloaded back, so the UI and the acceptance checker
   see the new files locally. (Disable with `REMOTE_SYNC=0` only if the folder is already shared.)

Retraining (Phase 11) is **not** routed through compute backends yet; it still runs on your Mac.

## A. Google Colab
1. Open `colab/remote_compute_server.ipynb` in Colab (File > Open notebook > GitHub, paste the repo URL).
2. Runtime > Change runtime type > GPU. Run the cells in order; leave the last one running.
3. It prints two lines. Put them in `backend/.env` on your Mac:
   ```
   COLAB_BASE_URL=https://something.trycloudflare.com
   COLAB_API_KEY=...
   ```
4. Restart the backend (`npm start` in `backend/`). On Overview press **Refresh**: Google Colab should show
   **available** (with the GPU device). Select **Google Colab** or **Auto**.

The tunnel URL and key change whenever the notebook restarts, so repeat step 3 each session. Free Colab
sessions end after idle time or about 12 h: runs are brought back to your Mac when they finish, so a
finished run is never stranded, but a run in progress is lost if the session dies.

## B. College GPU (over SSH, recommended)
Keep the server bound to `127.0.0.1` on the GPU machine and reach it with an SSH port-forward, so the API key
never crosses the network in plain text.

On the GPU machine (once):
```bash
git clone https://github.com/Unknown183-a/federated-unlearning-v2.git
cd federated-unlearning-v2
python3 -m venv .venv && source .venv/bin/activate
nvidia-smi                      # note the CUDA version, install the matching torch from pytorch.org
pip install -r core/requirements.txt
export COMPUTE_API_KEY="$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')"
echo "$COMPUTE_API_KEY"         # copy this
python -m core.compute.server --host 127.0.0.1 --port 8000     # use tmux/screen so it survives logout
```
On your Mac, in a separate terminal (leave it open):
```bash
ssh -N -L 8000:127.0.0.1:8000 YOUR_USER@GPU_HOST
```
Then in `backend/.env`:
```
COLLEGE_GPU_BASE_URL=http://127.0.0.1:8000
COLLEGE_GPU_API_KEY=<the key you copied>
```
Restart the backend and press **Refresh** on Overview. If the college only exposes a direct URL (no SSH), use
HTTPS in front of the server; do not send the key over plain `http://` across a network.

## Troubleshooting
| Symptom on the status panel | Meaning |
|---|---|
| `Not configured (...BASE_URL is not set)` | `.env` is missing the line, or the backend was not restarted after editing it |
| `rejected the API key (HTTP 401)` | Key in `.env` differs from the server's `COMPUTE_API_KEY` |
| `URLError while reaching the remote backend` | Server or tunnel/SSH forward is not running |
| `HTTP 530` / `1033` | The Cloudflare tunnel is down: re-run the notebook's tunnel cell, update `COLAB_BASE_URL` |
| `Another job is already running` | The server is busy; wait for it to finish |

A run longer than 15 minutes is also cut off by the Express layer: raise `ENGINE_TIMEOUT_MS` in `backend/.env`
(milliseconds) for long CIFAR runs.
