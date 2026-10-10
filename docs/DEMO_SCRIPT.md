# Professor Demo Script (about 10 minutes)

This is a speaking guide for presenting the Federated Unlearning Lab. It uses
**Professor Demo Mode**, which only replays a *stored* experiment. It never
trains anything, so it works with no GPU and no live backend.

## Before you present (5 minutes, once)

1. Start the backend: `cd backend && npm start` (it listens on port 4000).
2. Start the frontend: `cd frontend && npm run dev`, then open the address it prints.
3. Check the experiment is complete and consistent:
   `python -m core.acceptance.cli --all`
   Every experiment you plan to show should end with `0 failed`.
4. Open **Professor Demo** in the left menu. You should see at least one
   experiment card. If you see "No complete stored experiment found", run one
   full experiment in Research Mode first (see the README, "Make a demo experiment").
5. Pick the experiment and press **START DEMO** once to rehearse, then **Exit demo**.

Tip: unplug the network or stop any remote GPU before you start. Nothing in
Demo Mode needs them, and seeing it work offline is a good test.

## The walkthrough

Press **START DEMO**. A blue bar at the top shows the step and a time hint.
Use its **Next** button to move through the story.

| Step | Page | Time | What to say |
|------|------|------|-------------|
| 1 | Data Distribution | 1 min | "The dataset is split across several clients. Each card is one client. The heatmap shows which classes each client holds. Non-IID means clients see different mixes of classes, as in real life." |
| 2 | Federated Learning | 2 min | "Each round, every client trains locally, the server averages the updates (FedAvg), and the global model improves. This is a replay of a stored run, and the badge says so." |
| 3 | Client Selection | 1 min | "Now one client asks to be forgotten. This is the target client." Point at the **Remove Influence** button. |
| 4 | Unlearning | 2 min | "Stage one, Gradient Ascent, pushes the model away from that client's data. Stage two, Knowledge Distillation, repairs the model using the other clients." |
| 5 | Results | 2 min | "Before and after: accuracy on the forgotten client should drop, accuracy on the others should stay high, and the Membership Inference Attack should find it harder to tell that client's data was used." |
| 6 | Retraining Comparison | 2 min | "The gold standard is retraining from scratch without that client. Unlearning should land close to it, in much less time. Both runtimes here are measured." |

At any step, open **Experiment Configuration & Seed** at the bottom of the page
to show exactly which dataset, partition, seed, model and unlearning settings
produced the numbers.

## Reading the labels aloud

| Label | Meaning |
|-------|---------|
| Measured | Computed by a real run in this session |
| Precomputed · Stored Experiment | Replayed from an earlier real run |
| Live | A run happening right now |
| Illustrative | A diagram only, never a result |

In Demo Mode almost everything is **Precomputed**. Say so out loud. It is
honest, and it is what the labels are for.

## Questions you may get

- **"Did you just make those numbers up?"** No. Open Experiment Configuration
  and show the seed. Every number comes from a stored run. The checker
  (`python -m core.acceptance.cli`) confirms the files are complete and
  consistent, and the app refuses to show an unfinished evaluation as a result.
- **"Is the unlearning live?"** In Demo Mode it is a replay. To show a live run,
  switch to Research Mode with a GPU or Local backend available.
- **"Why not just retrain?"** Step 6. Retraining is the reference answer but costs
  about as much as the original training. Unlearning is the cheap approximation.

## If something goes wrong on the day

| What you see | What to do |
|--------------|------------|
| "The dashboard server is not reachable" | Start the backend (step 1 above) and press **Retry**. |
| "No complete stored experiment found" | Switch to Research Mode and run one experiment, or open Experiment History and pick a finished one. |
| "This stored result is incomplete" or "unreadable" | That experiment's file was damaged. Pick another experiment on the Professor Demo page. |
| A page says "could not be displayed" | Nothing was changed. Click another page, or press **Exit demo** and start again. |
| The compute panel says the status check failed | Ignore it. Stored experiments do not need a backend. |
