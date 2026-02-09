import { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';
import { hubApiClient } from '../services/hubApi';

interface PageFreshnessBadgeProps {
  collection?: string;
}

export function PageFreshnessBadge({ collection }: PageFreshnessBadgeProps) {
  const [lastRefreshed, setLastRefreshed] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function fetchFreshness() {
      try {
        const data = await hubApiClient.getDataFreshness();
        if (!mounted) return;
        if (collection && data.collections[collection]?.last_indexed) {
          setLastRefreshed(data.collections[collection].last_indexed);
        } else {
          setLastRefreshed(data.timestamp);
        }
      } catch {
        // API not available
      }
    }
    fetchFreshness();
    return () => { mounted = false; };
  }, [collection]);

  if (!lastRefreshed) return null;

  const date = new Date(lastRefreshed);
  const diff = Date.now() - date.getTime();
  const hours = Math.floor(diff / 3600000);
  const label =
    hours < 1 ? 'just now' :
    hours < 24 ? `${hours}h ago` :
    `${Math.floor(hours / 24)}d ago`;

  const color =
    hours < 1 ? 'text-green-600 bg-green-50 dark:text-green-400 dark:bg-green-900/30' :
    hours < 24 ? 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/30' :
    hours < 168 ? 'text-amber-600 bg-amber-50 dark:text-amber-400 dark:bg-amber-900/30' :
    'text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-900/30';

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium ${color}`}>
      <Clock className="h-3 w-3" />
      Last Refreshed: {label}
    </span>
  );
}
