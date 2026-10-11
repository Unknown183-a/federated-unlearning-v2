import { Router } from "express";
import { validateExperimentIdParam } from "../artifacts.js";
import { runEngine } from "../runEngine.js";
import { sendInvalidRequest } from "../errors.js";

// Phase 16 -- model releases and the auto / request-then-force update
// policy for devices that already installed a model.
//
// All the rules live in Python (core/distribution/); these routes only
// check the shape of the request, hand it to the CLI, and pass its JSON
// back. The CLI reports input mistakes as {"error": "..."} (exit 0), which
// becomes a plain 400 here.

const router = Router();
router.param("experimentId", validateExperimentIdParam);

const DEVICE_ID = /^device-\d{2,3}$/;

function call(res, experimentId, subcommand, extraArgs = []) {
  runEngine({
    args: ["-m", "core.distribution.cli", subcommand, "--experiment-id", String(experimentId), ...extraArgs],
    stage: "release",
    res,
    experimentId: String(experimentId),
    onSuccess: (parsed) => {
      if (parsed && parsed.error) return sendInvalidRequest(res, parsed.error);
      res.status(200).json(parsed);
    },
  });
}

function deviceIdFrom(body, res, { required }) {
  const { device_id } = body || {};
  if (device_id === undefined || device_id === null) {
    if (required) sendInvalidRequest(res, "device_id is required");
    return required ? false : null;
  }
  if (typeof device_id !== "string" || !DEVICE_ID.test(device_id)) {
    sendInvalidRequest(res, "That device id is not valid.");
    return false;
  }
  return device_id;
}

// GET /api/releases/:experimentId -> releases, devices, simulated clock, events.
router.get("/:experimentId", (req, res) => call(res, req.params.experimentId, "state"));

// POST .../original -> release v1 (the trained global model devices install first).
router.post("/:experimentId/original", (req, res) => call(res, req.params.experimentId, "release-original"));

// POST .../publish { mode: "auto" | "request", grace_hours?, note? }
router.post("/:experimentId/publish", (req, res) => {
  const { mode, grace_hours, note } = req.body || {};
  if (mode !== "auto" && mode !== "request") {
    return sendInvalidRequest(res, "mode must be 'auto' or 'request'.");
  }
  const args = [`--mode=${mode}`];
  if (mode === "request") {
    const hours = Number(grace_hours);
    if (grace_hours === undefined || grace_hours === "" || !Number.isFinite(hours)) {
      return sendInvalidRequest(res, "grace_hours must be a number.");
    }
    args.push(`--grace-hours=${hours}`);
  }
  if (note !== undefined && note !== null) {
    if (typeof note !== "string") return sendInvalidRequest(res, "note must be text.");
    args.push(`--note=${note}`);
  }
  call(res, req.params.experimentId, "publish", args);
});

// POST .../devices { count } -> add simulated devices on the latest version.
router.post("/:experimentId/devices", (req, res) => {
  const count = Number((req.body || {}).count);
  if (!Number.isInteger(count) || count < 1) {
    return sendInvalidRequest(res, "count must be a whole number of at least 1.");
  }
  call(res, req.params.experimentId, "devices", [`--count=${count}`]);
});

// POST .../check-in { device_id? } -> one device, or all when omitted.
router.post("/:experimentId/check-in", (req, res) => {
  const device = deviceIdFrom(req.body, res, { required: false });
  if (device === false) return;
  call(res, req.params.experimentId, "check-in", device ? [`--device=${device}`] : []);
});

// POST .../accept { device_id } -> a device accepts the update request.
router.post("/:experimentId/accept", (req, res) => {
  const device = deviceIdFrom(req.body, res, { required: true });
  if (device === false) return;
  call(res, req.params.experimentId, "accept", [`--device=${device}`]);
});

// POST .../online { device_id, online } -> take a device offline / back online.
router.post("/:experimentId/online", (req, res) => {
  const device = deviceIdFrom(req.body, res, { required: true });
  if (device === false) return;
  const { online } = req.body || {};
  if (typeof online !== "boolean") return sendInvalidRequest(res, "online must be true or false.");
  call(res, req.params.experimentId, "online", [`--device=${device}`, `--value=${online}`]);
});

// POST .../advance-clock { hours } -> move the simulated clock forward.
router.post("/:experimentId/advance-clock", (req, res) => {
  const hours = Number((req.body || {}).hours);
  if (!Number.isFinite(hours)) return sendInvalidRequest(res, "hours must be a number.");
  call(res, req.params.experimentId, "advance-clock", [`--hours=${hours}`]);
});

// DELETE /api/releases/:experimentId -> clear releases and devices for this experiment.
router.delete("/:experimentId", (req, res) => call(res, req.params.experimentId, "reset"));

export default router;
