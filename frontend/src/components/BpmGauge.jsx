import React from 'react';

const RADIUS = 80;
const STROKE_WIDTH = 16;
const CENTER = RADIUS + STROKE_WIDTH;
const SIZE = CENTER * 2;
const ARC_LENGTH = 2 * Math.PI * RADIUS;
const ARC_SWEEP = 270;
const ARC_START_OFFSET = 135;
const ARC_FRACTION = ARC_SWEEP / 360;

function polarToCartesian(cx, cy, r, angleDeg) {
  const rad = ((angleDeg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function describeArc(cx, cy, r, startAngle, endAngle) {
  const start = polarToCartesian(cx, cy, r, endAngle);
  const end = polarToCartesian(cx, cy, r, startAngle);
  const largeArc = endAngle - startAngle > 180 ? 1 : 0;
  return [`M ${start.x} ${start.y}`, `A ${r} ${r} 0 ${largeArc} 0 ${end.x} ${end.y}`].join(' ');
}

function getBpmColor(bpm) {
  if (bpm < 60) return '#3b82f6';
  if (bpm <= 100) return '#22c55e';
  if (bpm <= 130) return '#eab308';
  return '#ef4444';
}

function getBpmLabel(bpm) {
  if (bpm < 60) return 'Bajo';
  if (bpm <= 100) return 'Normal';
  if (bpm <= 130) return 'Elevado';
  return 'Crítico';
}

export default function BpmGauge({ bpm, isLive, label }) {
  const safeBpm = bpm ?? 0;
  const angle = (safeBpm / 220) * ARC_SWEEP;
  const color = getBpmColor(safeBpm);
  const statusLabel = getBpmLabel(safeBpm);

  const bgArc = describeArc(CENTER, CENTER, RADIUS, ARC_START_OFFSET, ARC_START_OFFSET + ARC_SWEEP);
  const valueArc = describeArc(CENTER, CENTER, RADIUS, ARC_START_OFFSET, ARC_START_OFFSET + angle);

  const needleLen = RADIUS - 12;
  const needleEnd = polarToCartesian(CENTER, CENTER, needleLen, ARC_START_OFFSET + angle);
  const needleBase = RADIUS * 0.15;

  return (
    <div className="bpm-gauge-wrapper">
      <div className="bpm-gauge-label">{label || 'Ritmo Cardíaco'}</div>
      <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`} className="bpm-gauge-svg">
        <path d={bgArc} fill="none" stroke="hsl(var(--border))" strokeWidth={STROKE_WIDTH} strokeLinecap="round" />
        <path
          d={valueArc}
          fill="none"
          stroke={color}
          strokeWidth={STROKE_WIDTH}
          strokeLinecap="round"
          style={{ transition: 'stroke 0.5s, stroke-dashoffset 0.3s' }}
        />
        <circle cx={CENTER} cy={CENTER} r={needleBase} fill={color} style={{ transition: 'fill 0.5s' }} />
        <line
          x1={CENTER}
          y1={CENTER}
          x2={needleEnd.x}
          y2={needleEnd.y}
          stroke={color}
          strokeWidth="3"
          strokeLinecap="round"
          style={{ transition: 'all 0.3s ease-out' }}
        />
      </svg>
      <div className="bpm-gauge-value">
        <span className="bpm-number">{safeBpm}</span>
        <span className="bpm-unit">BPM</span>
        <span className={`bpm-status ${safeBpm < 60 ? 'bpm-low' : safeBpm <= 100 ? 'bpm-normal' : 'bpm-high'}`}>
          {statusLabel}
        </span>
        <span className={`live-indicator ${isLive ? 'live-on' : 'live-off'}`}>
          {isLive ? '● EN VIVO' : '○ DESCONECTADO'}
        </span>
      </div>
    </div>
  );
}
