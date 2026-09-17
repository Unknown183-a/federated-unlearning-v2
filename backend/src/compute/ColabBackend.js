import { ComputeBackend } from "./ComputeBackend.js";

/**
 * ColabBackend — Google Colab GPU, used as a temporary/backup backend
 * (Ch. 71.16, "BACKUP"). TODO (later phase): implement the connection
 * to a Colab-hosted training/unlearning session.
 */
export class ColabBackend extends ComputeBackend {
  async getStatus() {
    return { name: "colab", available: false };
  }
}
