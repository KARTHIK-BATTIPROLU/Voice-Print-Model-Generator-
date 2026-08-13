import './ScoreGauge.css';

/**
 * ScoreGauge Component
 * 
 * SVG semicircular arc gauge with color gradient and threshold indicator.
 * Displays verification scores with a needle pointing to the current value.
 * 
 * @param {Object} props
 * @param {number} props.score - Score value (0.0-1.0)
 * @param {number} props.threshold - Threshold value (0.0-1.0)
 * @param {number} [props.size=200] - Gauge size in pixels
 */
export default function ScoreGauge({
  score = 0,
  threshold = 0.7,
  size = 200
}) {
  // Clamp score and threshold to valid range
  const clampedScore = Math.max(0, Math.min(1, score));
  const clampedThreshold = Math.max(0, Math.min(1, threshold));

  // SVG dimensions
  const width = size;
  const height = size * 0.65; // Semicircle takes less vertical space
  const cx = width / 2;
  const cy = height * 0.9; // Position circle center near bottom
  const radius = Math.min(width, height * 1.3) * 0.35;
  const strokeWidth = radius * 0.25;

  // Arc path for the gauge background (180° semicircle)
  const startAngle = 180;
  const endAngle = 0;
  const arcPath = describeArc(cx, cy, radius, startAngle, endAngle);

  // Calculate needle angle (-90° to 90° for semicircle)
  const needleAngle = -90 + (clampedScore * 180);
  const needleLength = radius * 0.85;

  // Calculate threshold indicator position
  const thresholdAngle = -90 + (clampedThreshold * 180);
  const thresholdRadius = radius + strokeWidth / 2;

  // Helper function to convert polar to cartesian
  function polarToCartesian(centerX, centerY, r, angleInDegrees) {
    const angleInRadians = (angleInDegrees * Math.PI) / 180;
    return {
      x: centerX + r * Math.cos(angleInRadians),
      y: centerY + r * Math.sin(angleInRadians)
    };
  }

  // Helper function to create arc path
  function describeArc(x, y, r, startAngleDeg, endAngleDeg) {
    const start = polarToCartesian(x, y, r, endAngleDeg);
    const end = polarToCartesian(x, y, r, startAngleDeg);
    const largeArcFlag = endAngleDeg - startAngleDeg <= 180 ? '0' : '1';
    return [
      'M', start.x, start.y,
      'A', r, r, 0, largeArcFlag, 0, end.x, end.y
    ].join(' ');
  }

  // Calculate needle endpoint
  const needleEnd = polarToCartesian(cx, cy, needleLength, needleAngle);

  // Calculate threshold indicator endpoints
  const thresholdInner = polarToCartesian(cx, cy, radius - strokeWidth / 2, thresholdAngle);
  const thresholdOuter = polarToCartesian(cx, cy, thresholdRadius + 5, thresholdAngle);

  // Determine color based on score
  function getScoreColor(value) {
    if (value < 0.33) return 'var(--error)'; // Red
    if (value < 0.67) return 'var(--warning)'; // Yellow
    return 'var(--success)'; // Green
  }

  return (
    <div className="score-gauge-container" style={{ width, height: height + 40 }}>
      <svg
        className="score-gauge-svg"
        width={width}
        height={height + 40}
        viewBox={`0 0 ${width} ${height + 40}`}
      >
        {/* Define gradient */}
        <defs>
          <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="var(--error)" />
            <stop offset="50%" stopColor="var(--warning)" />
            <stop offset="100%" stopColor="var(--success)" />
          </linearGradient>
        </defs>

        {/* Arc background */}
        <path
          className="gauge-arc-background"
          d={arcPath}
          fill="none"
          stroke="var(--border)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />

        {/* Arc gradient */}
        <path
          className="gauge-arc-gradient"
          d={arcPath}
          fill="none"
          stroke="url(#gaugeGradient)"
          strokeWidth={strokeWidth * 0.8}
          strokeLinecap="round"
        />

        {/* Threshold indicator line */}
        <line
          className="gauge-threshold-line"
          x1={thresholdInner.x}
          y1={thresholdInner.y}
          x2={thresholdOuter.x}
          y2={thresholdOuter.y}
          stroke="var(--accent)"
          strokeWidth="3"
          strokeLinecap="round"
        />

        {/* Needle */}
        <line
          className="gauge-needle"
          x1={cx}
          y1={cy}
          x2={needleEnd.x}
          y2={needleEnd.y}
          stroke={getScoreColor(clampedScore)}
          strokeWidth="3"
          strokeLinecap="round"
        />

        {/* Needle center dot */}
        <circle
          className="gauge-needle-center"
          cx={cx}
          cy={cy}
          r="6"
          fill={getScoreColor(clampedScore)}
        />

        {/* Scale labels */}
        <text
          x={cx - radius * 1.1}
          y={cy + 5}
          className="gauge-label"
          textAnchor="middle"
          fill="var(--text-secondary)"
        >
          0.0
        </text>

        <text
          x={cx}
          y={cy - radius * 0.95}
          className="gauge-label"
          textAnchor="middle"
          fill="var(--text-secondary)"
        >
          0.5
        </text>

        <text
          x={cx + radius * 1.1}
          y={cy + 5}
          className="gauge-label"
          textAnchor="middle"
          fill="var(--text-secondary)"
        >
          1.0
        </text>

        {/* Score value text */}
        <text
          x={cx}
          y={height + 25}
          className="gauge-score-text"
          textAnchor="middle"
          fill="var(--text-primary)"
        >
          {clampedScore.toFixed(3)}
        </text>
      </svg>
    </div>
  );
}
