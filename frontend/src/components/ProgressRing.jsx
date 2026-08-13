import './ProgressRing.css';

/**
 * ProgressRing Component
 * 
 * SVG circular progress indicator with animated stroke and percentage display.
 * 
 * @param {Object} props
 * @param {number} props.percentage - Progress percentage (0-100)
 * @param {number} [props.size=120] - SVG size in pixels
 * @param {number} [props.strokeWidth=10] - Stroke width in pixels
 * @param {string} [props.color] - Progress color (CSS variable or hex)
 */
export default function ProgressRing({
  percentage = 0,
  size = 120,
  strokeWidth = 10,
  color
}) {
  // Calculate circle properties
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  // Center position
  const cx = size / 2;
  const cy = size / 2;

  // Use provided color or default to accent
  const progressColor = color || 'var(--accent)';

  return (
    <div className="progress-ring-container" style={{ width: size, height: size }}>
      <svg
        className="progress-ring-svg"
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
      >
        {/* Background circle */}
        <circle
          className="progress-ring-background"
          cx={cx}
          cy={cy}
          r={radius}
          fill="none"
          stroke="var(--border)"
          strokeWidth={strokeWidth}
        />

        {/* Progress circle */}
        <circle
          className="progress-ring-progress"
          cx={cx}
          cy={cy}
          r={radius}
          fill="none"
          stroke={progressColor}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${cx} ${cy})`}
        />
      </svg>

      {/* Percentage text */}
      <div className="progress-ring-text">
        <span className="progress-percentage">{Math.round(percentage)}%</span>
      </div>
    </div>
  );
}
