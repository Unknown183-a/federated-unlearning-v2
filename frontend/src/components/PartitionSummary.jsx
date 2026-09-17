const STRATEGY_LABEL = {
  iid: "IID",
  non_iid: "Non-IID",
};

export default function PartitionSummary({ partition }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="text-base font-semibold text-gray-900">Partition Summary</h2>
      <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-3">
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Total Samples</dt>
          <dd className="mt-0.5 text-sm font-semibold text-gray-900">
            {partition.total_samples.toLocaleString()}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Clients</dt>
          <dd className="mt-0.5 text-sm font-semibold text-gray-900">{partition.num_clients}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Average Samples / Client</dt>
          <dd className="mt-0.5 text-sm font-semibold text-gray-900">
            {Math.round(partition.average_samples_per_client).toLocaleString()}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Most Imbalanced Client</dt>
          <dd className="mt-0.5 text-sm font-semibold text-gray-900">
            Client {partition.most_imbalanced_client}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Partition</dt>
          <dd className="mt-0.5 text-sm font-semibold text-gray-900">
            {STRATEGY_LABEL[partition.strategy] || partition.strategy}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Random Seed</dt>
          <dd className="mt-0.5 text-sm font-semibold text-gray-900">{partition.seed}</dd>
        </div>
      </dl>

      <div className="mt-6 overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <caption className="mb-2 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
            Samples and classes per client
          </caption>
          <thead>
            <tr>
              <th className="px-3 py-2 text-left font-medium text-gray-500">Client</th>
              <th className="px-3 py-2 text-left font-medium text-gray-500">Samples</th>
              <th className="px-3 py-2 text-left font-medium text-gray-500">Classes Present</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {partition.clients.map((client) => (
              <tr key={client.client_id}>
                <td className="px-3 py-2 text-gray-900">Client {client.client_id}</td>
                <td className="px-3 py-2 text-gray-700">{client.num_samples.toLocaleString()}</td>
                <td className="px-3 py-2 text-gray-700">
                  {client.num_classes_present} / {partition.num_classes}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
