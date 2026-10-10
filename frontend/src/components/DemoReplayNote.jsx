// Phase 15 -- shown in Professor Demo Mode in place of a "Run ..."
// button. Demo Mode only replays stored results; it never starts a
// computation (Spec Ch.37), and re-running a stage would also overwrite
// the stored artifact the rest of the demo depends on.
export default function DemoReplayNote({ stage, hasResult }) {
  return (
    <p className="rounded-md bg-indigo-50 px-3 py-2 text-sm text-indigo-800">
      {hasResult
        ? `Replaying the stored ${stage} result. Professor Demo Mode never starts a new run.`
        : `No stored ${stage} result for this experiment. Professor Demo Mode never starts a run -- switch to Research Mode to create one.`}
    </p>
  );
}
