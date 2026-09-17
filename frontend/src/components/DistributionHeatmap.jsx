// Class distribution heatmap (Dashboard Spec Ch.7.2). Columns beyond
// this width are grouped into labeled blocks with a scrollable
// container, which is what keeps a 100-class dataset like CIFAR-100
// readable (Phase 04 "grouping/scroll" requirement).
const GROUP_SIZE = 10;

function cellColor(count, maxCount) {
  if (!count) return "transparent";
  const alpha = 0.15 + 0.85 * (count / maxCount);
  return `rgba(79, 70, 229, ${alpha.toFixed(2)})`;
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
    <section
      aria-labelledby="heatmap-heading"
      className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm"
    >
      <h2 id="heatmap-heading" className="text-base font-semibold text-gray-900">
        Class Distribution Heatmap
      </h2>
      <p className="mt-1 text-sm text-gray-500">
        Each cell is one client&rsquo;s sample count for one class &mdash;
        darker means more samples. Hover a cell for the exact count.
        {grouped &&
          ` Classes are grouped in blocks of ${GROUP_SIZE}; scroll horizontally to see them all.`}
      </p>
      <div className="mt-4 max-w-full overflow-x-auto">
        <table className="border-collapse text-xs">
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
                      className="whitespace-nowrap border-l-2 border-gray-300 px-1.5 py-1 text-left font-medium text-gray-600"
                    >
                      Classes {c}&ndash;{Math.min(c + GROUP_SIZE, num_classes) - 1}
                    </th>
                  ))}
              </tr>
            )}
            <tr>
              <th scope="col" className="px-2 py-1 text-left font-medium text-gray-600">
                Client
              </th>
              {classes.map((c) => (
                <th
                  key={c}
                  scope="col"
                  className={`p-1 font-normal text-gray-500 ${
                    grouped && c % GROUP_SIZE === 0 ? "border-l-2 border-gray-300" : ""
                  }`}
                >
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {clients.map((client) => (
              <tr key={client.client_id}>
                <th
                  scope="row"
                  className="whitespace-nowrap px-2 py-1 text-left font-medium text-gray-700"
                >
                  Client {client.client_id}
                </th>
                {classes.map((c) => {
                  const count = client.class_counts[c] ?? 0;
                  return (
                    <td
                      key={c}
                      title={`Client ${client.client_id}, Class ${c}: ${count.toLocaleString()} samples`}
                      className={`h-[1.15rem] w-[1.15rem] border-b ${
                        grouped && c % GROUP_SIZE === 0 ? "border-l-2 border-l-gray-300" : "border-l border-l-gray-100"
                      } border-b-gray-100`}
                      style={{ backgroundColor: cellColor(count, maxCount) }}
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
