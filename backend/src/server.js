import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import { getComputeBackend } from "./compute/index.js";
import datasetsRouter from "./routes/datasets.js";
import partitionRouter from "./routes/partition.js";
import trainingRouter from "./routes/training.js";
import unlearningRouter from "./routes/unlearning.js";

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

// Health-check route (Phase 00 deliverable).
app.get("/status", async (_req, res) => {
  const backendStatus = await backend.getStatus();
  res.status(200).json({
    status: "ok",
    service: "federated-unlearning-backend",
    computeBackend: backendStatus,
  });
});

app.listen(PORT, () => {
  console.log(`Backend listening on http://localhost:${PORT}`);
});
