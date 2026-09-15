const STRATEGY_LABEL = {
  iid: "IID",
  non_iid: "Non-IID",
};

// Top classes by sample count for this client (Dashboard Spec Ch.7.1
// "Dominant Classes"). class_counts is keyed by class id -> sample count.
function dominantClasses(classCounts, limit = 3) {
  return Object.entries(classCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([classId]) => Number(classId));
}

export default function ClientCard({ client, strategy }) {
  const dominant = dominantClasses(client.class_counts);

  return (
    <article
      aria-label={`Client ${client.client_id}`}
      style={{ border: "1px solid #ccc", borderRadius: "6px", padding: "0.75rem" }}
    >
      <h3 style={{ marginTop: 0 }}>Client {client.client_id}</h3>
      <dl style={{ margin: 0 }}>
        <dt>Samples</dt>
        <dd>{client.num_samples.toLocaleString()}</dd>

        <dt>Classes</dt>
        <dd>{client.num_classes_present}</dd>

        <dt>Dominant Classes</dt>
        <dd>
          {dominant.length ? (
            <ul style={{ margin: 0, paddingLeft: "1.1rem" }}>
              {dominant.map((c) => (
                <li key={c}>Class {c}</li>
              ))}
            </ul>
          ) : (
            "None"
          )}
        </dd>

        <dt>Distribution</dt>
        <dd>{STRATEGY_LABEL[strategy] || strategy}</dd>
      </dl>
    </article>
  );
}
