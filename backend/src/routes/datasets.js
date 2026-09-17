import { Router } from "express";
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));

// Single source of truth shared with core/datasets/base.py -- the
// Python loaders and this route both read the same manifest.json so
// metadata can never drift between the two layers.
const MANIFEST_PATH = join(__dirname, "..", "..", "..", "core", "datasets", "manifest.json");

function loadManifest() {
  const raw = readFileSync(MANIFEST_PATH, "utf-8");
  return JSON.parse(raw);
}

const router = Router();

// GET /api/datasets -> list of all dataset metadata (Ch.3, Ch.32 Page 2)
router.get("/", (_req, res) => {
  const manifest = loadManifest();
  res.status(200).json({ datasets: Object.values(manifest) });
});

// GET /api/datasets/:id -> single dataset's metadata
router.get("/:id", (req, res) => {
  const manifest = loadManifest();
  const dataset = manifest[req.params.id];
  if (!dataset) {
    return res.status(404).json({ error: `Unknown dataset id "${req.params.id}"` });
  }
  res.status(200).json({ dataset });
});

export default router;
