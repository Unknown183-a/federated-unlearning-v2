// Generic round-vs-metric line chart, used for both the accuracy and
// loss curves on Page 4 (Dashboard Spec Ch.10). Plain inline SVG --
// this project has no charting library, and DistributionHeatmap.jsx
// already establishes that pattern for Page 3.
const WIDTH = 600;
const HEIGHT = 200;
const PADDING = { top: 14, right: 16, bottom: 28, left: 46 };

function niceTicks(min, max, count) {
  if (min === max) return [min];
  const step = (max - min) / (count - 1);
  return Array.from({ length: count }, (_, i) => min + step * i);
}

export default function MetricLineChart({
  title,
  data,
  totalRounds,
  color,
  yDomain,
  formatY = (v) => v,
  yLabel,
  emptyHint,
}) {
  const plotWidth = WIDTH - PADDING.left - PADDING.right;
  const plotHeight = HEIGHT - PADDING.top - PADDING.bottom;
  const maxRound = Math.max(totalRounds, 1);

  const values = data.map((d) => d.value);
  const [yMin, yMax] =
    yDomain ||
    (() => {
      if (!values.length) return [0, 1];
      const min = Math.min(...values);
      const max = Math.max(...values);
      if (min === max) return [min - 1, max + 1];
      const pad = (max - min) * 0.1;
      return [min - pad, max + pad];
    })();

  const xFor = (round) =>
    PADDING.left + ((round - 1) / Math.max(maxRound - 1, 1)) * plotWidth;
  const yFor = (value) =>
    PADDING.top + (1 - (value - yMin) / Math.max(yMax - yMin, 1e-9)) * plotHeight;

  const path = data
    .map((d, i) => `${i === 0 ? "M" : "L"} ${xFor(d.round).toFixed(1)} ${yFor(d.value).toFixed(1)}`)
    .join(" ");

  const yTicks = niceTicks(yMin, yMax, 4);
  const xTicks = niceTicks(1, maxRound, Math.min(Math.max(maxRound, 2), 6)).map((v) => Math.round(v));
  const last = data[data.length - 1];

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-baseline justify-between">
        <h3 className="text-base font-semibold text-gray-900">{title}</h3>
        {last && (
          <span className="text-sm font-medium text-gray-500">
            Round {last.round}: <span className="font-semibold text-gray-900">{formatY(last.value)}</span>
          </span>
        )}
      </div>

      {data.length === 0 ? (
        <p className="mt-6 text-sm text-gray-400">{emptyHint || "No rounds completed yet."}</p>
      ) : (
        <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="mt-3 w-full" role="img" aria-label={title}>
          {yTicks.map((t) => (
            <g key={t}>
              <line
                x1={PADDING.left}
                x2={WIDTH - PADDING.right}
                y1={yFor(t)}
                y2={yFor(t)}
                stroke="#e5e7eb"
                strokeWidth="1"
              />
              <text x={PADDING.left - 8} y={yFor(t) + 3} textAnchor="end" fontSize="9" fill="#6b7280">
                {formatY(t)}
              </text>
            </g>
          ))}
          {xTicks.map((t) => (
            <text key={t} x={xFor(t)} y={HEIGHT - 6} textAnchor="middle" fontSize="9" fill="#6b7280">
              {t}
            </text>
          ))}
          <line
            x1={PADDING.left}
            x2={PADDING.left}
            y1={PADDING.top}
            y2={HEIGHT - PADDING.bottom}
            stroke="#9ca3af"
            strokeWidth="1"
          />
          <line
            x1={PADDING.left}
            x2={WIDTH - PADDING.right}
            y1={HEIGHT - PADDING.bottom}
            y2={HEIGHT - PADDING.bottom}
            stroke="#9ca3af"
            strokeWidth="1"
          />
          <path d={path} fill="none" stroke={color} strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
          {data.map((d) => (
            <circle
              key={d.round}
              cx={xFor(d.round)}
              cy={yFor(d.value)}
              r={last && d.round === last.round ? 4 : 2.5}
              fill={color}
            />
          ))}
          <text x={PADDING.left} y={10} fontSize="9" fill="#9ca3af">
            {yLabel}
          </text>
        </svg>
      )}
    </div>
  );
}
