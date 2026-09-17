export default function DatasetCard({ dataset, selected, onSelect }) {
  return (
    <button
      type="button"
      onClick={() => onSelect(dataset.id)}
      aria-pressed={selected}
      className={`w-56 rounded-lg border p-4 text-left transition-colors ${
        selected
          ? "border-indigo-500 bg-indigo-50 ring-1 ring-indigo-500"
          : "border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50"
      }`}
    >
      <h3 className="text-sm font-semibold text-gray-900">{dataset.name}</h3>
      <p className="mt-1 text-sm text-gray-500">{dataset.description}</p>
      <dl className="mt-3 space-y-1 text-xs text-gray-600">
        <div>
          <dt className="inline font-medium text-gray-700">Image size: </dt>
          <dd className="inline">
            {dataset.image_size}×{dataset.image_size}
          </dd>
        </div>
        <div>
          <dt className="inline font-medium text-gray-700">Channels: </dt>
          <dd className="inline">{dataset.channels}</dd>
        </div>
        <div>
          <dt className="inline font-medium text-gray-700">Classes: </dt>
          <dd className="inline">{dataset.num_classes}</dd>
        </div>
        <div>
          <dt className="inline font-medium text-gray-700">Train / Test: </dt>
          <dd className="inline">
            {dataset.num_train.toLocaleString()} / {dataset.num_test.toLocaleString()}
          </dd>
        </div>
      </dl>
    </button>
  );
}
