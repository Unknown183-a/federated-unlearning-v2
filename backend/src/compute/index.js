import { DemoBackend } from "./DemoBackend.js";
import { LocalBackend } from "./LocalBackend.js";
import { ColabBackend } from "./ColabBackend.js";
import { CollegeGPUBackend } from "./CollegeGPUBackend.js";

/**
 * ComputeManager — picks a backend by name (env: COMPUTE_BACKEND).
 * "auto" priority per Ch. 71.16: college-gpu -> colab -> local -> demo.
 * Phase 00: only "demo" is actually usable; the rest are stubs that
 * report unavailable until their real implementations land.
 */
const BACKENDS = {
  demo: DemoBackend,
  local: LocalBackend,
  colab: ColabBackend,
  "college-gpu": CollegeGPUBackend,
};

export function getComputeBackend(name = process.env.COMPUTE_BACKEND || "demo") {
  const BackendClass = BACKENDS[name] || DemoBackend;
  return new BackendClass();
}
