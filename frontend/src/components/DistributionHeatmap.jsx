// Class distribution heatmap (Dashboard Spec Ch.7.2). Columns beyond
// this width are grouped into labeled blocks with a scrollable
// container, which is what keeps a 100-class dataset like CIFAR-100
// readable (Phase 04 "grouping/scroll" requirement).
const GROUP_SIZE = 10;

function cellColor(count, maxCount) {
  if (!count) return "transparent";
  const alpha = 0.15 + 0.85 * (count / maxCount);
  return `rgba(37, 99, 235, ${alpha.toFixed(2)})`;
}

export default function DistributionHeatmap({ partition }) {
  const { clients, num_classes } = partition;
  const classes = Array.from({ length: num_classes }, (_, i) => i);
  const maxCount = Math.max(
    1,
    ...clients.flatMap((c) => Object.values(c.class_counts))
  );
  const grouped = num_classes > GROUP_SIZE;

  return (
    <section aria-labelledby="heatmap-heading">
      <h2 id="heatmap-heading">Class Distribution Heatmap</h2>
      <p>
        Each cell is one client&rsquo;s sample count for one class &mdash;
        darker means more samples. Hover a cell for the exact count.
        {grouped &&
          ` Classes are grouped in blocks of ${GROUP_SIZE}; scroll horizontally to see them all.`}
      </p>
      <div style={{ overflowX: "auto", maxWidth: "100%" }}>
        <table style={{ borderCollapse: "collapse", fontSize: "0.75rem" }}>
          <thead>
            {grouped && (
              <tr>
                <th scope="col"></th>
                {classes
                  .filter((c) => c % GROUP_SIZE === 0)
                  .map((c) => (
                    <th
                      key={`group-${c}`}
                      colSpan={Math.min(GROUP_SIZE, num_classes - c)}
                      style={{
                        textAlign: "left",
                        borderLeft: "2px solid #999",
                        padding: "0.2rem 0.35rem",
                        whiteSpace: "nowrap",
                      }}
                    >
                      Classes {c}&ndash;{Math.min(c + GROUP_SIZE, num_classes) - 1}
                    </th>
                  ))}
              </tr>
            )}
            <tr>
              <th scope="col">Client</th>
              {classes.map((c) => (
                <th
                  key={c}
                  scope="col"
                  style={{
                    borderLeft: grouped && c % GROUP_SIZE === 0 ? "2px solid #999" : undefined,
                    padding: "0.15rem",
                    fontWeight: "normal",
                  }}
                >
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {clients.map((client) => (
              <tr key={client.client_id}>
                <th scope="row" style={{ padding: "0.2rem 0.5rem", whiteSpace: "nowrap", textAlign: "left" }}>
                  Client {client.client_id}
                </th>
                {classes.map((c) => {
                  const count = client.class_counts[c] ?? 0;
                  return (
                    <td
                      key={c}
                      title={`Client ${client.client_id}, Class ${c}: ${count.toLocaleString()} samples`}
                      style={{
                        width: "1.15rem",
                        height: "1.15rem",
                        backgroundColor: cellColor(count, maxCount),
                        borderLeft:
                          grouped && c % GROUP_SIZE === 0 ? "2px solid #999" : "1px solid #eee",
                        borderBottom: "1px solid #eee",
                      }}
                    />
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
