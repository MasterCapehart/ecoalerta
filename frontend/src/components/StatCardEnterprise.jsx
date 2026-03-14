import { AreaChart, Area, ResponsiveContainer } from 'recharts'

const Sparkline = ({ data, color }) => (
  <div className="sparkline-container">
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id={`grad-${color}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.3}/>
            <stop offset="95%" stopColor={color} stopOpacity={0}/>
          </linearGradient>
        </defs>
        <Area 
          type="monotone" 
          dataKey="value" 
          stroke={color} 
          strokeWidth={2} 
          fillOpacity={1} 
          fill={`url(#grad-${color})`} 
        />
      </AreaChart>
    </ResponsiveContainer>
  </div>
)

const StatCardEnterprise = ({ 
  title, 
  value, 
  subtext, 
  icon: Icon, 
  trend, 
  trendLabel, 
  colorClass, 
  bgIconClass, 
  sparkColor,
  sparkData 
}) => {
  const trendIsPositive = trend > 0
  const trendAbs = Math.abs(trend)

  return (
    <div className="stat-card-enterprise">
      <div className="stat-card-header">
        <div className={`stat-icon-wrapper ${bgIconClass}`}>
          {Icon && (typeof Icon === 'function' ? <Icon size={20} strokeWidth={2} /> : Icon)}
        </div>
        <div className={`trend-badge ${trendIsPositive ? 'trend-up' : trend === 0 ? 'trend-neutral' : 'trend-down'}`}>
          {trendIsPositive ? '↑' : trend === 0 ? '→' : '↓'} {trendAbs}%
        </div>
      </div>
      
      <div className="stat-card-body">
        <div className="stat-card-main">
          <h3 className="stat-value">{value}</h3>
          <p className="stat-title">{title}</p>
        </div>
        {sparkData && <Sparkline data={sparkData} color={sparkColor} />}
      </div>
      
      <div className="stat-card-footer">
        <span className="trend-label">{trendLabel}</span>
        <span className="stat-subtext">{subtext}</span>
      </div>
    </div>
  )
}

export default StatCardEnterprise

