import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";

// Central experiment state (Dashboard Spec Ch.34).
// Every later phase (partitioning, training, unlearning, evaluation)
// reads/extends this instead of keeping its own copy.
const DEFAULT_CONFIG = {
  dataset: null, // dataset id, e.g. "cifar10" -- set from the Phase 01 picker
  num_clients: 10, // free numeric input -- never a fixed set of options (Ch.4)
  partition_strategy: "non_iid", // "iid" | "non_iid"
  model: "cnn", // "cnn" | "resnet"
  federated_rounds: 20,
  local_epochs: 1,
  seed: 42,
  training_mode: "load_existing", // "load_existing" | "run_federated_training"
  target_client_id: null, // set on Phase 07's Client Selection page -- the client to unlearn
  // Phase 14: which compute backend runs training/unlearning/evaluation.
  // "auto" walks College GPU -> Colab -> Local -> Demo; a specific kind
  // pins that backend and fails loudly if it's unavailable. This is a
  // UI preference only -- no credential or endpoint ever lives here.
  compute_backend: "auto", // "auto" | "college_gpu" | "colab" | "local" | "demo"
};

const EMPTY_STAGES = {
  partitioned: false,
  trained: false,
  unlearned: false,
  evaluated: false,
  compared: false,
};

function generateExperimentId() {
  return `exp-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

const ExperimentContext = createContext(null);

export function ExperimentProvider({ children }) {
  // experiment_id (Ch.34 state model) identifies this draft experiment's
  // artifacts on disk, e.g. experiments/<experiment_id>/partition.json.
  const [config, setConfigState] = useState(() => ({
    ...DEFAULT_CONFIG,
    experiment_id: generateExperimentId(),
  }));

  // Phase 13: how far the *current* experiment_id has actually gotten,
  // read from the Phase 12 registry (GET /api/experiments/:id) rather
  // than re-derived separately by the nav stepper and the pipeline
  // mini-map -- both read this one value, so they can never disagree
  // about what stage the experiment is at ("consolidate page state
  // into one central store"). This is read-only progress, not
  // editable config, so it lives alongside `config` rather than in it.
  const [stages, setStages] = useState(EMPTY_STAGES);
  const [stagesStatus, setStagesStatus] = useState("idle"); // idle | loading | ready

  // Always holds the *current* experiment_id, independent of which
  // render's refreshStages closure is running -- a plain dependency
  // comparison inside the fetch callback would compare `id` against
  // whatever config.experiment_id that specific closure captured,
  // which is always equal to `id` itself and so never actually
  // detects that the user has since switched experiments.
  const activeExperimentIdRef = useRef(config.experiment_id);
  activeExperimentIdRef.current = config.experiment_id;

  const refreshStages = useCallback((experimentId) => {
    const id = experimentId ?? activeExperimentIdRef.current;
    if (!id) return;
    setStagesStatus("loading");
    fetch(`/api/experiments/${encodeURIComponent(id)}`)
      .then(async (res) => {
        if (id !== activeExperimentIdRef.current) return; // stale response -- experiment changed since this call
        if (!res.ok) {
          setStages(EMPTY_STAGES);
          setStagesStatus("ready");
          return;
        }
        const data = await res.json();
        setStages(data.experiment?.stages ?? EMPTY_STAGES);
        setStagesStatus("ready");
      })
      .catch(() => {
        if (id !== activeExperimentIdRef.current) return;
        setStages(EMPTY_STAGES);
        setStagesStatus("ready");
      });
  }, []);

  // Re-read stage completion every time the active experiment changes
  // -- including when navigating back to a page after a stage
  // finished, so the stepper/mini-map never show stale progress.
  useEffect(() => {
    setStages(EMPTY_STAGES);
    refreshStages(config.experiment_id);
  }, [config.experiment_id, refreshStages]);

  function updateConfig(patch) {
    setConfigState((prev) => {
      const next = { ...prev, ...patch };
      // Changing dataset invalidates anything downstream that assumed
      // the old dataset's shape (Ch.34: "Changing the dataset should
      // reset incompatible experiment state").
      if ("dataset" in patch && patch.dataset !== prev.dataset) {
        next.training_mode = DEFAULT_CONFIG.training_mode;
        next.target_client_id = null;
      }
      return next;
    });
  }

  // Phase 12: point this context at an already-persisted experiment
  // (from the Model Library or Experiment History) instead of the
  // fresh draft one started with. Used by both entry points so a
  // stored experiment is loaded identically either way -- every
  // field this config carries is overwritten from the artifact
  // summary, not merged, since the two experiments are unrelated.
  function loadExperiment(summary) {
    setConfigState((prev) => ({
      ...DEFAULT_CONFIG,
      compute_backend: prev.compute_backend, // a backend choice is a session preference, not per-experiment
      experiment_id: summary.experiment_id,
      dataset: summary.dataset,
      num_clients: summary.num_clients ?? DEFAULT_CONFIG.num_clients,
      partition_strategy: summary.partition_strategy ?? DEFAULT_CONFIG.partition_strategy,
      model: summary.model ?? DEFAULT_CONFIG.model,
      federated_rounds: summary.federated_rounds ?? DEFAULT_CONFIG.federated_rounds,
      seed: summary.seed ?? DEFAULT_CONFIG.seed,
      training_mode: "load_existing",
      target_client_id: summary.target_client_id ?? null,
    }));
    // summary already carries a `stages` object (it came from the same
    // registry endpoint) -- seed it immediately instead of waiting on
    // a round trip, since loadExperiment is always immediately
    // followed by a navigation.
    if (summary.stages) setStages(summary.stages);
  }

  return (
    <ExperimentContext.Provider
      value={{ config, updateConfig, loadExperiment, stages, stagesStatus, refreshStages }}
    >
      {children}
    </ExperimentContext.Provider>
  );
}

export function useExperimentConfig() {
  const ctx = useContext(ExperimentContext);
  if (!ctx) {
    throw new Error("useExperimentConfig must be used within an ExperimentProvider");
  }
  return ctx;
}
