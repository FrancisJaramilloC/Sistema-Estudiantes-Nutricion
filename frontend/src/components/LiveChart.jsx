import React from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

function formatTime(isoString) {
  try {
    const d = new Date(isoString);
    return d.toLocaleTimeString('es-EC', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch {
    return '';
  }
}

export default function LiveChart({ readings }) {
  if (!readings || readings.length === 0) {
    return (
      <div className="live-chart-empty">
        <p>Esperando lecturas en vivo...</p>
      </div>
    );
  }

  const data = readings.map((r, i) => ({
    time: formatTime(r.timestamp),
    bpm: r.bpm,
    index: i,
  }));

  const yMin = Math.max(30, Math.min(...data.map((d) => d.bpm)) - 10);
  const yMax = Math.min(220, Math.max(...data.map((d) => d.bpm)) + 10);

  return (
    <div className="live-chart">
      <h3 className="chart-title">Tendencia en Vivo</h3>
      <ResponsiveContainer width="100%" height={180}>
        <AreaChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
          <defs>
            <linearGradient id="bpmGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="index" hide />
          <YAxis
            domain={[yMin, yMax]}
            tick={{ fontSize: 11, fill: 'hsl(var(--text-secondary))' }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            contentStyle={{
              background: 'hsl(var(--card-bg))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '6px',
              fontSize: '12px',
            }}
            labelFormatter={() => ''}
            formatter={(value) => [`${value} BPM`]}
          />
          <ReferenceLine y={60} stroke="#3b82f6" strokeDasharray="3 3" strokeOpacity={0.5} />
          <ReferenceLine y={100} stroke="#eab308" strokeDasharray="3 3" strokeOpacity={0.5} />
          <Area
            type="monotone"
            dataKey="bpm"
            stroke="#22c55e"
            strokeWidth={2}
            fill="url(#bpmGradient)"
            animationDuration={300}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
      <div className="chart-ref-lines">
        <span className="ref-line ref-brady">— Bradicardia (60)</span>
        <span className="ref-line ref-tachy">— Taquicardia (100)</span>
      </div>
    </div>
  );
}
