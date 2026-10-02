import { createContext, useContext, useState } from "react";

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
    setConfigState({
      ...DEFAULT_CONFIG,
      experiment_id: summary.experiment_id,
      dataset: summary.dataset,
      num_clients: summary.num_clients ?? DEFAULT_CONFIG.num_clients,
      partition_strategy: summary.partition_strategy ?? DEFAULT_CONFIG.partition_strategy,
      model: summary.model ?? DEFAULT_CONFIG.model,
      federated_rounds: summary.federated_rounds ?? DEFAULT_CONFIG.federated_rounds,
      seed: summary.seed ?? DEFAULT_CONFIG.seed,
      training_mode: "load_existing",
      target_client_id: summary.target_client_id ?? null,
    });
  }

  return (
    <ExperimentContext.Provider value={{ config, updateConfig, loadExperiment }}>
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
