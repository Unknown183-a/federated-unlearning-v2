import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import { getComputeBackend } from "./compute/index.js";
import datasetsRouter from "./routes/datasets.js";
import partitionRouter from "./routes/partition.js";
import trainingRouter from "./routes/training.js";
import unlearningRouter from "./routes/unlearning.js";
import evaluationRouter from "./routes/evaluation.js";
import retrainingRouter from "./routes/retraining.js";
import experimentsRouter from "./routes/experiments.js";
import computeRouter from "./routes/compute.js";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 4000;
const backend = getComputeBackend();

app.use("/api/datasets", datasetsRouter);
app.use("/api/partition", partitionRouter);
app.use("/api/training", trainingRouter);
app.use("/api/unlearning", unlearningRouter);
app.use("/api/evaluation", evaluationRouter);
app.use("/api/retraining", retrainingRouter);
app.use("/api/experiments", experimentsRouter);
app.use("/api/compute", computeRouter);

// Health-check route (Phase 00 deliverable).
app.get("/status", async (_req, res) => {
  const backendStatus = await backend.getStatus();
  res.status(200).json({
    status: "ok",
    service: "federated-unlearning-backend",
    computeBackend: backendStatus,
  });
});

// Phase 15: every failure answers in JSON, never Express's default HTML
// error page -- the dashboard parses a response body on every failed
// request and a stray HTML page used to surface as "Unexpected token <".
app.use("/api", (_req, res) => {
  res.status(404).json({ error: "That API route does not exist.", code: "NOT_FOUND", retryable: false });
});

// eslint-disable-next-line no-unused-vars
app.use((err, _req, res, _next) => {
  if (res.headersSent) return;
  if (err && err.type === "entity.parse.failed") {
    return res.status(400).json({ error: "The request body is not valid JSON.", code: "INVALID_REQUEST", retryable: false });
  }
  console.error("Unhandled backend error:", err && err.message);
  res.status(500).json({
    error: "Something went wrong on the server.",
    code: "SERVER_ERROR",
    detail: err && err.message ? String(err.message).slice(0, 300) : "",
    retryable: true,
  });
});

app.listen(PORT, () => {
  console.log(`Backend listening on http://localhost:${PORT}`);
});
