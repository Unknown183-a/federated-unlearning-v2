import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useExperimentConfig } from "../state/ExperimentContext.jsx";
import FedAvgDiagram from "../components/FedAvgDiagram.jsx";
import RoundProgress from "../components/RoundProgress.jsx";
import MetricLineChart from "../components/MetricLineChart.jsx";

// Page 4 -- Federated Learning (Dashboard Spec Ch.8-10, Ch.37/46).
//
// Both training modes (Ch.34's training_mode: "run_federated_training"
// vs "load_existing") end up with the same shape of data -- an
// fl_history from Phase 05's get_fl_history() -- and are replayed
// through the same client-side round-by-round animation. What differs
// is only the label: a freshly-run experiment is "Measured", a loaded
// one is "Stored Experiment" (never presented as if it were live).

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function stageProgress(stage, clientsRevealed, totalClients) {
  if (stage === "clients") return 0.7 * (totalClients ? clientsRevealed / totalClients : 0);
  if (stage === "aggregating") return 0.85;
  if (stage === "updated" || stage === "done") return 1;
  return 0;
}

function averageLocalLoss(round) {
  const losses = round.clients.map((c) => c.local_loss).filter((v) => v !== null && v !== undefined);
  if (!losses.length) return null;
  return losses.reduce((a, b) => a + b, 0) / losses.length;
}

export default function FederatedLearning() {
  const { config } = useExperimentConfig();
  const isLiveMode = config.training_mode === "run_federated_training";

  const [loadExperimentId, setLoadExperimentId] = useState(config.experiment_id);
  const [partitionReady, setPartitionReady] = useState(null); // null = unknown

  const [status, setStatus] = useState("idle"); // idle | loading | error | ready
  const [error, setError] = useState(null);
  const [history, setHistory] = useState(null);
  const [resultKind, setResultKind] = useState(null); // "measured" | "precomputed"

  const [animRoundIdx, setAnimRoundIdx] = useState(0);
  const [animClientsRevealed, setAnimClientsRevealed] = useState(0);
  const [animStage, setAnimStage] = useState("idle"); // idle | clients | aggregating | updated | done
  const [revealedRounds, setRevealedRounds] = useState([]);
  const cancelRef = useRef(false);

  // Elapsed-time readout while the synchronous /api/training request is in
  // flight -- Phase 05 returns the whole history at once, so there's no real
  // per-round progress to show yet; a ticking clock is an honest substitute
  // for a progress bar we can't back with real data.
  const [elapsedMs, setElapsedMs] = useState(0);
  useEffect(() => {
    if (status !== "loading") return;
    const startedAt = Date.now();
    setElapsedMs(0);
    const id = setInterval(() => setElapsedMs(Date.now() - startedAt), 200);
    return () => clearInterval(id);
  }, [status]);

  // Check whether Phase 04's partitioning already ran for this
  // experiment -- the training CLI requires a saved partition.
  useEffect(() => {
    if (!isLiveMode || !config.experiment_id) {
      setPartitionReady(null);
      return;
    }
    let ignore = false;
    fetch(`/api/partition/${config.experiment_id}`)
      .then((res) => {
        if (!ignore) setPartitionReady(res.ok);
      })
      .catch(() => {
        if (!ignore) setPartitionReady(false);
      });
    return () => {
      ignore = true;
    };
  }, [isLiveMode, config.experiment_id]);

  // Client-side round-by-round replay. The backend always returns the
  // complete history at once (Phase 05 is synchronous), so "live"
  // animation here means revealing it progressively rather than
  // streaming it -- true for both a just-measured run and a replayed
  // stored one (Ch.9: "the dashboard should replay the training
  // progression from stored metrics").
  useEffect(() => {
    if (!history) return;
    cancelRef.current = false;
    setRevealedRounds([]);
    setAnimRoundIdx(0);
    setAnimClientsRevealed(0);
    setAnimStage("clients");

    const rounds = history.round_history;
    const numClients = rounds[0]?.clients.length || 1;
    const clientDelay = Math.max(35, Math.min(160, 900 / numClients));
    const stageDelay = 260;
    const roundGap = 200;

    async function play() {
      for (let i = 0; i < rounds.length; i++) {
        if (cancelRef.current) return;
        setAnimRoundIdx(i);
        setAnimStage("clients");
        setAnimClientsRevealed(0);
        const total = rounds[i].clients.length;
        for (let c = 1; c <= total; c++) {
          if (cancelRef.current) return;
          setAnimClientsRevealed(c);
          await sleep(clientDelay);
        }
        if (cancelRef.current) return;
        setAnimStage("aggregating");
        await sleep(stageDelay);
        if (cancelRef.current) return;
        setAnimStage("updated");
        await sleep(stageDelay);
        if (cancelRef.current) return;
        setRevealedRounds((prev) => [...prev, rounds[i]]);
        await sleep(roundGap);
      }
      if (!cancelRef.current) setAnimStage("done");
    }

    play();
    return () => {
      cancelRef.current = true;
    };
  }, [history]);

  async function runLiveTraining() {
    setStatus("loading");
    setError(null);
    setHistory(null);
    try {
      const res = await fetch("/api/training", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          experiment_id: config.experiment_id,
          model: config.model,
          federated_rounds: config.federated_rounds,
          local_epochs: config.local_epochs,
          seed: config.seed,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || `Request failed: ${res.status}`);
      }
      const data = await res.json();
      setResultKind("measured");
      setHistory(data.history);
      setStatus("ready");
    } catch (err) {
      setError(err.message);
      setStatus("error");
    }
  }

  async function loadStoredExperiment() {
    const id = loadExperimentId.trim();
    if (!id) {
      setError("Enter an experiment ID to load.");
      setStatus("error");
      return;
    }
    setStatus("loading");
    setError(null);
    setHistory(null);
    try {
      const res = await fetch(`/api/training/${encodeURIComponent(id)}`);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || `Request failed: ${res.status}`);
      }
      const data = await res.json();
      setResultKind("precomputed");
      setHistory(data.history);
      setStatus("ready");
    } catch (err) {
      setError(err.message);
      setStatus("error");
    }
  }

  function skipAnimation() {
    if (!history) return;
    cancelRef.current = true;
    const rounds = history.round_history;
    setRevealedRounds(rounds);
    setAnimRoundIdx(rounds.length - 1);
    setAnimClientsRevealed(rounds[rounds.length - 1].clients.length);
    setAnimStage("done");
  }

  const currentRound = history ? history.round_history[animRoundIdx] : null;
  const totalRounds = history ? history.rounds : config.federated_rounds;
  const isAnimating = Boolean(history) && animStage !== "done";

  const clientsForChecklist = currentRound
    ? currentRound.clients.map((c, i) => ({
        client_id: c.client_id,
        completed: animStage !== "clients" || i < animClientsRevealed,
      }))
    : [];

  const progress = currentRound
    ? (animRoundIdx + stageProgress(animStage, animClientsRevealed, currentRound.clients.length)) /
      Math.max(totalRounds, 1)
    : 0;

  const accuracyData = revealedRounds.map((r) => ({ round: r.round, value: r.accuracy }));
  const lossData = revealedRounds.map((r) => ({ round: r.round, value: r.loss }));
  const totalElapsed = revealedRounds.reduce((sum, r) => sum + (r.duration_seconds || 0), 0);
  const latestRound = revealedRounds[revealedRounds.length - 1];
  const latestLocalLoss = latestRound ? averageLocalLoss(latestRound) : null;

  return (
    <section className="space-y-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Federated Learning</h1>
          <p className="mt-1 text-sm text-gray-500">
            The FedAvg loop: every client trains locally, the server aggregates, and the global
            model improves round by round.
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

      {!config.dataset && (
        <p role="alert" className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
          Choose a dataset on Experiment Setup first.
        </p>
      )}

      {isLiveMode ? (
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <p className="text-sm text-gray-700">
            Run federated training for experiment{" "}
            <strong className="font-semibold">{config.experiment_id}</strong>: {config.model} on{" "}
            {config.dataset || "—"}, {config.federated_rounds} rounds × {config.local_epochs} local
            epoch(s), seed {config.seed}.
          </p>
          {partitionReady === false && (
            <p role="alert" className="mt-3 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
              No saved partition found for this experiment yet — run{" "}
              <Link to="/distribution" className="font-medium underline">
                Data Distribution
              </Link>{" "}
              first.
            </p>
          )}
          <button
            onClick={runLiveTraining}
            disabled={!config.dataset || status === "loading" || partitionReady === false}
            className="mt-4 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {status === "loading" ? "Training…" : "Run Federated Training"}
          </button>
          {status === "loading" && (
            <div className="mt-3 flex items-center gap-2 text-xs font-medium text-rose-600">
              <svg
                className="h-4 w-4 animate-spin text-rose-500"
                viewBox="0 0 24 24"
                fill="none"
                aria-hidden="true"
              >
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                />
              </svg>
              <span>
                Live — currently calculating on the server ({(elapsedMs / 1000).toFixed(0)}s elapsed).
                This can take a while for larger models or many rounds.
              </span>
            </div>
          )}
        </div>
      ) : (
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <p className="text-sm text-gray-700">
            Load a previously computed training run and replay it round by round.
          </p>
          <div className="mt-4 flex flex-wrap items-end gap-3">
            <div>
              <label htmlFor="load-experiment-id" className="block text-sm font-medium text-gray-700">
                Experiment ID
              </label>
              <input
                id="load-experiment-id"
                type="text"
                value={loadExperimentId}
                onChange={(e) => setLoadExperimentId(e.target.value)}
                className="mt-1 block w-64 rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <button
              onClick={loadStoredExperiment}
              disabled={status === "loading"}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {status === "loading" ? "Loading…" : "Load Stored Experiment"}
            </button>
          </div>
        </div>
      )}

      {error && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {history && (
        <>
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

          <FedAvgDiagram clients={clientsForChecklist} stage={animStage} />

          <RoundProgress
            currentRound={currentRound ? currentRound.round : 0}
            totalRounds={totalRounds}
            clients={clientsForChecklist}
            stage={animStage}
            progress={Math.min(progress, 1)}
            replay={resultKind === "precomputed"}
          />

          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-base font-semibold text-gray-900">Metrics</h2>
            <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-4">
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Global Accuracy</dt>
                <dd className="mt-0.5 text-sm font-semibold text-gray-900">
                  {latestRound ? `${(latestRound.accuracy * 100).toFixed(1)}%` : "—"}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Global Loss</dt>
                <dd className="mt-0.5 text-sm font-semibold text-gray-900">
                  {latestRound ? latestRound.loss.toFixed(3) : "—"}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Client Participation</dt>
                <dd className="mt-0.5 text-sm font-semibold text-gray-900">
                  {clientsForChecklist.filter((c) => c.completed).length} / {clientsForChecklist.length}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Avg. Local Training Loss</dt>
                <dd className="mt-0.5 text-sm font-semibold text-gray-900">
                  {latestLocalLoss !== null ? latestLocalLoss.toFixed(3) : "—"}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Round</dt>
                <dd className="mt-0.5 text-sm font-semibold text-gray-900">
                  {currentRound ? currentRound.round : 0} / {totalRounds}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Aggregation</dt>
                <dd className="mt-0.5 text-sm font-semibold text-gray-900">FedAvg</dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Total Training Time</dt>
                <dd className="mt-0.5 text-sm font-semibold text-gray-900">{totalElapsed.toFixed(1)}s</dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Model / Clients</dt>
                <dd className="mt-0.5 text-sm font-semibold text-gray-900">
                  {history.model} · {history.num_clients}
                </dd>
              </div>
            </dl>
          </div>

          <div className="grid gap-6 sm:grid-cols-2">
            <MetricLineChart
              title="Global Accuracy vs Round"
              data={accuracyData}
              totalRounds={totalRounds}
              color="#4f46e5"
              yDomain={[0, 1]}
              formatY={(v) => `${Math.round(v * 100)}%`}
              yLabel="accuracy"
            />
            <MetricLineChart
              title="Global Loss vs Round"
              data={lossData}
              totalRounds={totalRounds}
              color="#dc2626"
              formatY={(v) => v.toFixed(2)}
              yLabel="loss"
            />
          </div>
        </>
      )}
    </section>
  );
}
