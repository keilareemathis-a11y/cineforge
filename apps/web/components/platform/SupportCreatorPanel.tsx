'use client';
import { useState } from 'react';
import type { CreatorProfile } from '../../types/platform';
import { supportCreator } from '../../lib/api/platform';

interface SupportCreatorPanelProps {
  creator: CreatorProfile;
}

const TIERS = [
  { label: '$1', cents: 100 },
  { label: '$3', cents: 300 },
  { label: '$5', cents: 500 },
];

export default function SupportCreatorPanel({ creator }: SupportCreatorPanelProps) {
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

  const handleSupport = async (cents: number) => {
    setStatus('loading');
    try {
      await supportCreator(creator.id, cents);
      setStatus('success');
    } catch {
      setStatus('error');
    }
  };

  return (
    <div style={{
      background: '#1a1a2e',
      border: '1px solid #2a2a4e',
      borderRadius: '8px',
      padding: '20px',
      marginTop: '20px',
    }}>
      <h3 style={{ margin: '0 0 8px', color: '#e0e0ff', fontSize: '16px' }}>
        Support {creator.display_name}
      </h3>
      <p style={{ color: '#aaa', fontSize: '13px', marginBottom: '14px' }}>
        Help fund their next film
      </p>
      {status === 'success' ? (
        <p style={{ color: '#7c6fff', fontWeight: 600 }}>Thank you for your support! 🎬</p>
      ) : (
        <div style={{ display: 'flex', gap: '10px' }}>
          {TIERS.map((tier) => (
            <button
              key={tier.cents}
              onClick={() => handleSupport(tier.cents)}
              disabled={status === 'loading'}
              style={{
                background: '#7c6fff',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                padding: '10px 18px',
                fontSize: '15px',
                cursor: status === 'loading' ? 'wait' : 'pointer',
                fontWeight: 600,
              }}
            >
              {tier.label}
            </button>
          ))}
        </div>
      )}
      {status === 'error' && (
        <p style={{ color: '#f55', fontSize: '13px', marginTop: '8px' }}>Something went wrong. Please try again.</p>
      )}
    </div>
  );
}
