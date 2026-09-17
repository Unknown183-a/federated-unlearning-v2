import { ComputeBackend } from "./ComputeBackend.js";

/**
 * LocalBackend — Mac MPS/CPU fallback (Ch. 71.16, "LOCAL FALLBACK").
 * TODO (later phase): shell out to / call the Python core/ ML code
 * running on this machine.
 */
export class LocalBackend extends ComputeBackend {
  async getStatus() {
    return { name: "local", available: false };
  }
}
