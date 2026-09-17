import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useExperimentConfig } from "../state/ExperimentContext.jsx";
import UnlearningStepper from "../components/UnlearningStepper.jsx";
import GradientAscentPanel from "../components/GradientAscentPanel.jsx";
import KnowledgeDistillationPanel from "../components/KnowledgeDistillationPanel.jsx";
import ClientInfluenceBars from "../components/ClientInfluenceBars.jsx";

// Page 6 -- Unlearning (Dashboard Spec Ch.13-20, Ch.32 Page 6).
//
// Mirrors Phase 06's replay strategy (see FederatedLearning.jsx): the
// backend runs both stages -- Gradient Ascent (Phase 08) then
// Knowledge Distillation (Phase 09) -- synchronously and returns the
// complete, real per-step/per-epoch history at once (Ch.37: "prefer
// live execution" for unlearning). "Live" animation here means
// revealing that real history progressively, never fabricating values
// with a timer (Phase 09 acceptance criterion).

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export default function Unlearning() {
  const { config } = useExperimentConfig();

  const [gateStatus, setGateStatus] = useState("loading"); // loading | ready | missing
  const [runStatus, setRunStatus] = useState("idle"); // idle | loading | error | ready
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [resultKind, setResultKind] = useState(null); // "measured" | "stored"

  const [elapsedMs, setElapsedMs] = useState(0);
  useEffect(() => {
    if (runStatus !== "loading") return;
    const startedAt = Date.now();
    setElapsedMs(0);
    const id = setInterval(() => setElapsedMs(Date.now() - startedAt), 200);
    return () => clearInterval(id);
  }, [runStatus]);

  // A trained checkpoint is required before unlearning can run at all.
  useEffect(() => {
    if (!config.experiment_id) return;
    let ignore = false;
    fetch(`/api/training/${encodeURIComponent(config.experiment_id)}`)
      .then((res) => {
        if (!ignore) setGateStatus(res.ok ? "ready" : "missing");
      })
      .catch(() => {
        if (!ignore) setGateStatus("missing");
      });
    return () => {
      ignore = true;
    };
  }, [config.experiment_id]);

  // If this experiment already has a persisted unlearning result,
  // load and replay it (a "stored" replay, same as Phase 06's loaded
  // runs -- never presented as if it were live).
  useEffect(() => {
    if (!config.experiment_id || gateStatus !== "ready") return;
    let ignore = false;
    fetch(`/api/unlearning/${encodeURIComponent(config.experiment_id)}`)
      .then(async (res) => {
        if (ignore || !res.ok) return;
        const data = await res.json();
        if (data.status && data.status.status === "complete") {
          setResultKind("stored");
          setResult(data.status);
          setRunStatus("ready");
        }
      })
      .catch(() => {});
    return () => {
      ignore = true;
    };
  }, [config.experiment_id, gateStatus]);

  async function runUnlearning() {
    setRunStatus("loading");
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/api/unlearning", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          experiment_id: config.experiment_id,
          client_id: config.target_client_id,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || `Request failed: ${res.status}`);
      }
      const data = await res.json();
      setResultKind("measured");
      setResult(data.status);
      setRunStatus("ready");
    } catch (err) {
      setError(err.message);
      setRunStatus("error");
    }
  }

  // -- Two-stage replay animation ------------------------------------
  const [phase, setPhase] = useState("idle"); // idle | ascent | distillation | done
  const [gaRevealed, setGaRevealed] = useState(0);
  const [kdRevealed, setKdRevealed] = useState(0);
  const cancelRef = useRef(false);

  useEffect(() => {
    if (!result) return;
    cancelRef.current = false;
    setGaRevealed(0);
    setKdRevealed(0);
    setPhase("ascent");

    const ga = result.gradient_ascent;
    const kd = result.knowledge_distillation;

    async function play() {
      for (let i = 1; i <= ga.step_history.length; i++) {
        if (cancelRef.current) return;
        setGaRevealed(i);
        await sleep(45);
      }
      if (cancelRef.current) return;
      await sleep(400);
      setPhase("distillation");
      for (let i = 1; i <= kd.epoch_history.length; i++) {
        if (cancelRef.current) return;
        setKdRevealed(i);
        await sleep(220);
      }
      if (cancelRef.current) return;
      setPhase("done");
    }

    play();
    return () => {
      cancelRef.current = true;
    };
  }, [result]);

  function skipAnimation() {
    if (!result) return;
    cancelRef.current = true;
    setGaRevealed(result.gradient_ascent.step_history.length);
    setKdRevealed(result.knowledge_distillation.epoch_history.length);
    setPhase("done");
  }

  const stageStatus = {
    model_loaded: result ? "done" : "waiting",
    target_client: result ? "done" : config.target_client_id !== null ? "done" : "waiting",
    gradient_ascent: !result ? "waiting" : phase === "ascent" ? "running" : "done",
    knowledge_distillation: !result ? "waiting" : phase === "distillation" ? "running" : phase === "done" ? "done" : "waiting",
    final_results: phase === "done" ? "done" : "waiting",
  };

  const hasTarget = config.target_client_id !== null && config.target_client_id !== undefined;
  const isAnimating = Boolean(result) && phase !== "done";

  return (
    <section className="space-y-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Unlearning</h1>
          <p className="mt-1 text-sm text-gray-500">
            Gradient Ascent forgets the target client; Knowledge Distillation repairs everyone
            else&rsquo;s accuracy.
          </p>
        </div>
        {resultKind && (
          <span
            className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${
              resultKind === "measured" ? "bg-indigo-100 text-indigo-800" : "bg-amber-100 text-amber-800"
            }`}
          >
            {resultKind === "measured" ? "Measured" : "Stored Experiment"}
          </span>
        )}
      </div>

      {gateStatus === "missing" && (
        <p role="alert" className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
          No trained model found for this experiment yet — run{" "}
          <Link to="/training" className="font-medium underline">
            Federated Learning
          </Link>{" "}
          first.
        </p>
      )}

      {gateStatus === "ready" && !hasTarget && (
        <p role="alert" className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
          No target client selected yet — choose one on{" "}
          <Link to="/client-selection" className="font-medium underline">
            Client Selection
          </Link>{" "}
          first.
        </p>
      )}

      {gateStatus === "ready" && hasTarget && (
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <p className="text-sm text-gray-700">
            Run Gradient Ascent + Knowledge Distillation for experiment{" "}
            <strong className="font-semibold">{config.experiment_id}</strong>, forgetting{" "}
            <strong className="font-semibold">Client {config.target_client_id}</strong>.
          </p>
          <button
            onClick={runUnlearning}
            disabled={runStatus === "loading"}
            className="mt-4 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {runStatus === "loading" ? "Unlearning…" : "Run Unlearning"}
          </button>
          {runStatus === "loading" && (
            <div className="mt-3 flex items-center gap-2 text-xs font-medium text-rose-600">
              <svg className="h-4 w-4 animate-spin text-rose-500" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
              </svg>
              <span>
                Live — running Gradient Ascent + Knowledge Distillation on the server (
                {(elapsedMs / 1000).toFixed(0)}s elapsed).
              </span>
            </div>
          )}
        </div>
      )}

      {error && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {result && (
        <>
          <UnlearningStepper stageStatus={stageStatus} />

          {isAnimating && (
            <div className="flex justify-end">
              <button
                onClick={skipAnimation}
                className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50"
              >
                Skip to final result
              </button>
            </div>
          )}

          {(phase === "ascent" || phase === "distillation" || phase === "done") && (
            <GradientAscentPanel
              targetClientId={result.target_client_id}
              currentStep={gaRevealed}
              totalSteps={result.gradient_ascent.steps_requested}
              revealedHistory={result.gradient_ascent.step_history.slice(0, gaRevealed)}
            />
          )}

          {(phase === "distillation" || phase === "done") && (
            <KnowledgeDistillationPanel
              temperature={result.knowledge_distillation.temperature}
              alpha={result.knowledge_distillation.alpha}
              currentEpoch={kdRevealed}
              totalEpochs={result.knowledge_distillation.epochs_requested}
              revealedHistory={result.knowledge_distillation.epoch_history.slice(0, kdRevealed)}
            />
          )}

          {phase === "done" && (
            <>
              <ClientInfluenceBars
                targetClientId={result.target_client_id}
                targetBefore={result.gradient_ascent.initial_accuracy}
                targetAfter={result.gradient_ascent.final_accuracy}
                retainedBefore={result.knowledge_distillation.per_client_accuracy_before}
                retainedAfter={result.knowledge_distillation.per_client_accuracy_after}
              />

              <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                <h2 className="text-base font-semibold text-gray-900">Unlearning Complete</h2>
                <p className="mt-1 text-sm text-gray-500">
                  Original Model → Gradient Ascent → Knowledge Distillation → Unlearned Model
                </p>
                <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-4">
                  <div>
                    <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Model / Dataset</dt>
                    <dd className="mt-0.5 text-sm font-semibold text-gray-900">
                      {result.model} · {result.dataset}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Retained Accuracy</dt>
                    <dd className="mt-0.5 text-sm font-semibold text-gray-900">
                      {(result.knowledge_distillation.initial_retained_accuracy * 100).toFixed(1)}% →{" "}
                      {(result.knowledge_distillation.final_retained_accuracy * 100).toFixed(1)}%
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Total Unlearning Time</dt>
                    <dd className="mt-0.5 text-sm font-semibold text-gray-900">
                      {result.duration_seconds.toFixed(1)}s
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Checkpoint</dt>
                    <dd className="mt-0.5 text-sm font-semibold text-green-700">✓ Saved</dd>
                  </div>
                </dl>
              </div>
            </>
          )}
        </>
      )}
    </section>
  );
}
