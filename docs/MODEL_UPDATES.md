# Model Updates: unlearning a model that devices already installed (Phase 16)

Unlearning happens on the server. A device that downloaded the old model still has a copy that contains the
forgotten client's influence, and the server cannot edit that copy. What the server can do is publish the
unlearned model as a **new version**, ask devices to switch, and stop allowing the old version.

Open **Model Updates** (left menu, Research mode) to try it.

## The two policies
| | Auto update | Request, then force |
|---|---|---|
| Online devices | Updated immediately | Asked to update; may accept any time before the deadline |
| Offline devices | Updated the moment they reconnect | Asked when they reconnect. If the deadline has passed they are updated then |
| Old version | Revoked at once | Allowed until the deadline, revoked after |
| After the deadline | n/a | Online devices still on the old version are updated automatically **at the deadline** |

The deadline is the publish time plus the hours you choose (1 to 8760).

## Steps in the dashboard
1. **Release the original model** (v1). It is the trained global model, and is what devices install first.
2. **Add simulated devices** (up to 100). They start on the latest version.
3. **Publish the unlearned model** with a policy. It needs a finished unlearning run, and the same unlearned model
   cannot be published twice (re-run unlearning to make a new one).
4. Use **+1 hour / +1 day / +3 days** to move the simulated clock, take devices offline, accept requests, and watch
   the event log.

## What is stored
`experiments/<id>/model_releases.json` holds releases, devices, the simulated clock and the event log. Each
release's model is copied to `experiments/<id>/releases/model_v<N>.pt` and its SHA-256 is recorded, so a release
stays identical even if unlearning is re-run later.

## Limits (read before presenting)
- **Devices and the clock are simulated.** No app is installed anywhere. The page is labelled *Illustrative*.
- **Old copies are not deleted.** Someone who keeps the old model file, or blocks the update, still has a model that
  remembers the forgotten client. "Revoked" only means apps that follow the policy refuse to run it.
- **Integrity is a hash, not a signature.** A real deployment needs signed manifests (asymmetric keys) so devices
  can check a release really came from you.
- The strongest protection is not to ship weights at all: if devices only call a prediction API, unlearning on the
  server covers everyone.

## Code
`core/distribution/releases.py` (rules, standard library only), `core/distribution/cli.py`,
`backend/src/routes/releases.js` (`/api/releases/:experimentId/...`), `frontend/src/pages/ModelUpdates.jsx`,
tests in `tests/test_releases.py`.
