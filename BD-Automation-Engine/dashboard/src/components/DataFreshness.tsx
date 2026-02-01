import { useState, useEffect } from 'react';

interface DataFreshnessInfo {
  last_updated: string;
  pipeline_run_id: string;
  files: Record<string, {
    filename: string;
    size_bytes: number;
    record_count: number;
  }>;
  sources: {
    bullhorn_db: string;
    federal_programs_csv: string;
  };
}

export function DataFreshness() {
  const [freshness, setFreshness] = useState<DataFreshnessInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    fetch('/data/data_freshness.json')
      .then(res => {
        if (!res.ok) throw new Error('Not found');
        return res.json();
      })
      .then(data => {
        setFreshness(data);
        setLoading(false);
      })
      .catch(() => {
        setFreshness(null);
        setLoading(false);
      });
  }, []);

  if (loading || !freshness) return null;

  const lastUpdated = new Date(freshness.last_updated);
  const ageMinutes = Math.floor((Date.now() - lastUpdated.getTime()) / 60000);

  // Freshness indicator: green < 1hr, yellow < 24hr, red > 24hr
  const freshnessColor = ageMinutes < 60 ? '#22c55e' : ageMinutes < 1440 ? '#eab308' : '#ef4444';
  const freshnessLabel = ageMinutes < 60 ? 'Fresh' : ageMinutes < 1440 ? 'Stale' : 'Outdated';
  const freshnessText = ageMinutes < 60
    ? `${ageMinutes}m ago`
    : ageMinutes < 1440
    ? `${Math.floor(ageMinutes / 60)}h ago`
    : `${Math.floor(ageMinutes / 1440)}d ago`;

  const totalFiles = Object.keys(freshness.files).length;
  const totalRecords = Object.values(freshness.files).reduce((sum, f) => sum + f.record_count, 0);

  return (
    <>
      {/* Floating indicator */}
      <div
        onClick={() => setShowDetails(!showDetails)}
        style={{
          position: 'fixed',
          bottom: 16,
          right: 16,
          background: 'rgba(15, 23, 42, 0.9)',
          color: 'white',
          padding: '8px 12px',
          borderRadius: 8,
          fontSize: 12,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          zIndex: 1000,
          cursor: 'pointer',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
          transition: 'transform 0.2s, box-shadow 0.2s',
        }}
        onMouseEnter={e => {
          e.currentTarget.style.transform = 'scale(1.02)';
          e.currentTarget.style.boxShadow = '0 10px 15px -3px rgba(0, 0, 0, 0.1)';
        }}
        onMouseLeave={e => {
          e.currentTarget.style.transform = 'scale(1)';
          e.currentTarget.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
        }}
        title={`Pipeline: ${freshness.pipeline_run_id}\nClick for details`}
      >
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: freshnessColor,
            boxShadow: `0 0 6px ${freshnessColor}`,
          }}
        />
        <span>Data: {freshnessText}</span>
        <span style={{ opacity: 0.6, fontSize: 10 }}>({freshnessLabel})</span>
      </div>

      {/* Details panel */}
      {showDetails && (
        <div
          style={{
            position: 'fixed',
            bottom: 56,
            right: 16,
            background: 'rgba(15, 23, 42, 0.95)',
            color: 'white',
            padding: 16,
            borderRadius: 12,
            fontSize: 12,
            zIndex: 1000,
            minWidth: 280,
            maxWidth: 360,
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>Data Freshness</h3>
            <button
              onClick={() => setShowDetails(false)}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'rgba(255,255,255,0.6)',
                cursor: 'pointer',
                fontSize: 16,
              }}
            >
              ×
            </button>
          </div>

          <div style={{ display: 'grid', gap: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ opacity: 0.7 }}>Last Updated:</span>
              <span>{lastUpdated.toLocaleString()}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ opacity: 0.7 }}>Pipeline Run:</span>
              <span style={{ fontFamily: 'monospace', fontSize: 10 }}>{freshness.pipeline_run_id}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ opacity: 0.7 }}>Data Files:</span>
              <span>{totalFiles} files</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ opacity: 0.7 }}>Total Records:</span>
              <span>{totalRecords.toLocaleString()}</span>
            </div>
          </div>

          <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.1)' }}>
            <div style={{ opacity: 0.7, marginBottom: 8 }}>Files:</div>
            <div style={{ display: 'grid', gap: 4 }}>
              {Object.entries(freshness.files).map(([name, info]) => (
                <div key={name} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                  <span style={{ opacity: 0.8 }}>{name}</span>
                  <span style={{ opacity: 0.6 }}>
                    {info.record_count.toLocaleString()} records ({Math.round(info.size_bytes / 1024)}KB)
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div
            style={{
              marginTop: 12,
              padding: 8,
              background: freshnessColor + '20',
              borderRadius: 6,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: freshnessColor,
              }}
            />
            <span style={{ fontSize: 11 }}>
              {ageMinutes < 60
                ? 'Data is fresh. Pipeline ran recently.'
                : ageMinutes < 1440
                ? 'Data may be stale. Consider running the pipeline.'
                : 'Data is outdated. Run the pipeline to refresh.'}
            </span>
          </div>
        </div>
      )}
    </>
  );
}
