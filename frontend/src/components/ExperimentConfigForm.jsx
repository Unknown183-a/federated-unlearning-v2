import { useState } from "react";
import { useExperimentConfig } from "../state/ExperimentContext.jsx";

const PARTITION_STRATEGIES = [
  { value: "iid", label: "IID" },
  { value: "non_iid", label: "Non-IID" },
];

const MODELS = [
  { value: "cnn", label: "CNN" },
  { value: "resnet", label: "ResNet" },
];

const TRAINING_MODES = [
  { value: "load_existing", label: "Load Existing Experiment" },
  { value: "run_federated_training", label: "Run Federated Training" },
];

function validate(config) {
  const errors = {};
  if (!config.dataset) {
    errors.dataset = "Select a dataset first.";
  }
  if (!Number.isInteger(config.num_clients) || config.num_clients < 2) {
    errors.num_clients = "Number of clients must be an integer of at least 2.";
  }
  if (!Number.isInteger(config.federated_rounds) || config.federated_rounds < 1) {
    errors.federated_rounds = "Federated rounds must be an integer of at least 1.";
  }
  if (!Number.isInteger(config.local_epochs) || config.local_epochs < 1) {
    errors.local_epochs = "Local epochs must be an integer of at least 1.";
  }
  if (!Number.isInteger(config.seed)) {
    errors.seed = "Seed must be an integer.";
  }
  return errors;
}

function toInt(value) {
  const n = parseInt(value, 10);
  return Number.isNaN(n) ? value : n;
}

const inputClass =
  "mt-1 block w-full max-w-xs rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500";
const labelClass = "block text-sm font-medium text-gray-700";
const errorClass = "mt-1 text-sm text-red-600";

export default function ExperimentConfigForm() {
  const { config, updateConfig } = useExperimentConfig();
  const [touched, setTouched] = useState(false);

  const errors = validate(config);
  const hasErrors = Object.keys(errors).length > 0;

  return (
    <form
      onSubmit={(e) => e.preventDefault()}
      onBlur={() => setTouched(true)}
      className="space-y-5"
    >
      <div>
        <label htmlFor="num_clients" className={labelClass}>
          Number of Clients
        </label>
        <input
          id="num_clients"
          type="number"
          min={2}
          step={1}
          value={config.num_clients}
          onChange={(e) => updateConfig({ num_clients: toInt(e.target.value) })}
          className={inputClass}
        />
        {touched && errors.num_clients && <p role="alert" className={errorClass}>{errors.num_clients}</p>}
      </div>

      <div>
        <label htmlFor="partition_strategy" className={labelClass}>
          Partition Strategy
        </label>
        <select
          id="partition_strategy"
          value={config.partition_strategy}
          onChange={(e) => updateConfig({ partition_strategy: e.target.value })}
          className={inputClass}
        >
          {PARTITION_STRATEGIES.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="federated_rounds" className={labelClass}>
          Federated Rounds
        </label>
        <input
          id="federated_rounds"
          type="number"
          min={1}
          step={1}
          value={config.federated_rounds}
          onChange={(e) => updateConfig({ federated_rounds: toInt(e.target.value) })}
          className={inputClass}
        />
        {touched && errors.federated_rounds && <p role="alert" className={errorClass}>{errors.federated_rounds}</p>}
      </div>

      <div>
        <label htmlFor="local_epochs" className={labelClass}>
          Local Epochs
        </label>
        <input
          id="local_epochs"
          type="number"
          min={1}
          step={1}
          value={config.local_epochs}
          onChange={(e) => updateConfig({ local_epochs: toInt(e.target.value) })}
          className={inputClass}
        />
        {touched && errors.local_epochs && <p role="alert" className={errorClass}>{errors.local_epochs}</p>}
      </div>

      <div>
        <label htmlFor="model" className={labelClass}>
          Model
        </label>
        <select
          id="model"
          value={config.model}
          onChange={(e) => updateConfig({ model: e.target.value })}
          className={inputClass}
        >
          {MODELS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="seed" className={labelClass}>
          Random Seed
        </label>
        <input
          id="seed"
          type="number"
          step={1}
          value={config.seed}
          onChange={(e) => updateConfig({ seed: toInt(e.target.value) })}
          className={inputClass}
        />
        {touched && errors.seed && <p role="alert" className={errorClass}>{errors.seed}</p>}
      </div>

      <fieldset>
        <legend className={labelClass}>Training Mode</legend>
        <div className="mt-2 space-y-2">
          {TRAINING_MODES.map((opt) => (
            <label key={opt.value} className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="radio"
                name="training_mode"
                value={opt.value}
                checked={config.training_mode === opt.value}
                onChange={(e) => updateConfig({ training_mode: e.target.value })}
                className="h-4 w-4 border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              {opt.label}
            </label>
          ))}
        </div>
      </fieldset>

      {touched && !config.dataset && <p role="alert" className={errorClass}>{errors.dataset}</p>}
      {!hasErrors && config.dataset && (
        <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">
          Configuration is valid.
        </p>
      )}
    </form>
  );
}
