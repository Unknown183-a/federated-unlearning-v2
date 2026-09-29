// Original vs Unlearned vs Retrained grouped bars (Page 8, Ch.24).
// Plain inline SVG, same pattern as MetricLineChart.jsx /
// DistributionHeatmap.jsx -- this project has no charting library.

const WIDTH = 640;
const ROW_HEIGHT = 64;
const PADDING = { top: 8, right: 90, bottom: 8, left: 170 };

const SERIES = [
  { key: "original", label: "Original", color: "#9ca3af" },
  { key: "unlearned", label: "Unlearned (GA + KD)", color: "#6366f1" },
  { key: "retrained", label: "Retrained", color: "#059669" },
];

function pct(value) {
  return `${(value * 100).toFixed(1)}%`;
}

export default function RetrainingComparisonChart({ metrics }) {
  const plotWidth = WIDTH - PADDING.left - PADDING.right;
  const height = PADDING.top + PADDING.bottom + metrics.length * ROW_HEIGHT;
  const barHeight = 14;
  const barGap = 4;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-gray-900">Original vs Unlearned vs Retrained</h3>
        <ul className="flex items-center gap-4 text-xs text-gray-500">
          {SERIES.map((s) => (
            <li key={s.key} className="flex items-center gap-1.5">
              <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: s.color }} />
              {s.label}
            </li>
          ))}
        </ul>
      </div>

      <svg viewBox={`0 0 ${WIDTH} ${height}`} className="mt-4 w-full" role="img" aria-label="Comparison chart">
        {metrics.map((metric, rowIndex) => {
          const rowTop = PADDING.top + rowIndex * ROW_HEIGHT;
          const groupHeight = SERIES.length * (barHeight + barGap) - barGap;
          const groupTop = rowTop + (ROW_HEIGHT - groupHeight) / 2;

          return (
            <g key={metric.key}>
              <text
                x={PADDING.left - 12}
                y={rowTop + ROW_HEIGHT / 2}
                textAnchor="end"
                dominantBaseline="middle"
                fontSize="11"
                fontWeight="600"
                fill="#374151"
              >
                {metric.label}
              </text>
              {SERIES.map((s, seriesIndex) => {
                const value = metric[s.key];
                const barWidth = Math.max(value, 0) * plotWidth;
                const y = groupTop + seriesIndex * (barHeight + barGap);
                return (
                  <g key={s.key}>
                    <rect
                      x={PADDING.left}
                      y={y}
                      width={plotWidth}
                      height={barHeight}
                      fill="#f3f4f6"
                    />
                    <rect x={PADDING.left} y={y} width={barWidth} height={barHeight} fill={s.color} rx="2" />
                    <text
                      x={PADDING.left + plotWidth + 8}
                      y={y + barHeight / 2}
                      dominantBaseline="middle"
                      fontSize="10"
                      fontWeight="600"
                      fill="#374151"
                    >
                      {pct(value)}
                    </text>
                  </g>
                );
              })}
              {rowIndex < metrics.length - 1 && (
                <line
                  x1={PADDING.left}
                  x2={WIDTH - PADDING.right}
                  y1={rowTop + ROW_HEIGHT}
                  y2={rowTop + ROW_HEIGHT}
                  stroke="#f3f4f6"
                  strokeWidth="1"
                />
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
