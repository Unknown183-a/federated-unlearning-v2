import { ComputeBackend } from "./ComputeBackend.js";

/**
 * DemoBackend — the "guaranteed presentation fallback" (Ch. 71.16).
 * Will eventually load precomputed experiment artifacts from
 * experiments/ instead of running anything live.
 *
 * TODO (later phase): read JSON artifacts under experiments/<name>/
 * and return them from these methods instead of throwing.
 */
export class DemoBackend extends ComputeBackend {
  async getStatus() {
    return { name: "demo", available: true };
  }

  async loadExperiment(experimentId) {
    throw new Error(`loadExperiment() not implemented yet for experiment "${experimentId}"`);
  }

  async getClientDistribution(experimentId, clientId) {
    throw new Error("getClientDistribution() not implemented yet");
  }

  async getFlHistory(experimentId) {
    throw new Error("getFlHistory() not implemented yet");
  }

  async startUnlearning(experimentId, clientId) {
    throw new Error("startUnlearning() not implemented yet");
  }

  async getUnlearningStatus(experimentId) {
    throw new Error("getUnlearningStatus() not implemented yet");
  }

  async getResults(experimentId) {
    throw new Error("getResults() not implemented yet");
  }
}
