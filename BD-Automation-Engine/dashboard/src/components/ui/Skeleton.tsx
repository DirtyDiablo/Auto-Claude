/**
 * Skeleton Components
 *
 * Reusable loading skeleton components with shimmer animation.
 */

import { ReactNode } from 'react';

interface SkeletonProps {
  className?: string;
  animate?: boolean;
}

// Base skeleton with shimmer animation
export function Skeleton({ className = '', animate = true }: SkeletonProps) {
  return (
    <div
      className={`bg-slate-200 rounded ${animate ? 'animate-pulse' : ''} ${className}`}
    />
  );
}

// Text line skeleton
export function SkeletonText({ lines = 1, className = '' }: { lines?: number; className?: string }) {
  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className={`h-4 ${i === lines - 1 && lines > 1 ? 'w-3/4' : 'w-full'}`}
        />
      ))}
    </div>
  );
}

// Avatar/circle skeleton
export function SkeletonAvatar({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
  };
  return <Skeleton className={`${sizeClasses[size]} rounded-full`} />;
}

// Card skeleton
export function SkeletonCard({ className = '' }: { className?: string }) {
  return (
    <div className={`bg-white rounded-xl shadow-sm border border-slate-200 p-6 ${className}`}>
      <div className="flex items-center gap-4 mb-4">
        <SkeletonAvatar size="md" />
        <div className="flex-1">
          <Skeleton className="h-5 w-32 mb-2" />
          <Skeleton className="h-4 w-48" />
        </div>
      </div>
      <SkeletonText lines={3} />
    </div>
  );
}

// Stat card skeleton
export function SkeletonStatCard() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <Skeleton className="h-4 w-24 mb-2" />
          <Skeleton className="h-8 w-16 mb-1" />
          <Skeleton className="h-3 w-20" />
        </div>
        <Skeleton className="w-12 h-12 rounded-xl" />
      </div>
    </div>
  );
}

// Table row skeleton
export function SkeletonTableRow({ columns = 4 }: { columns?: number }) {
  return (
    <tr>
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <Skeleton className="h-4 w-full" />
        </td>
      ))}
    </tr>
  );
}

// List item skeleton
export function SkeletonListItem() {
  return (
    <div className="flex items-center gap-3 p-3 border-b border-slate-100 last:border-0">
      <SkeletonAvatar size="sm" />
      <div className="flex-1">
        <Skeleton className="h-4 w-32 mb-1" />
        <Skeleton className="h-3 w-48" />
      </div>
      <Skeleton className="h-6 w-16 rounded-full" />
    </div>
  );
}

// Chart skeleton
export function SkeletonChart({ height = 200 }: { height?: number }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <Skeleton className="h-5 w-40 mb-4" />
      <div className="flex items-end gap-2" style={{ height }}>
        {Array.from({ length: 7 }).map((_, i) => (
          <Skeleton
            key={i}
            className="flex-1 rounded-t"
            style={{ height: `${30 + Math.random() * 70}%` }}
          />
        ))}
      </div>
    </div>
  );
}

// Search result skeleton
export function SkeletonSearchResult() {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4">
      <div className="flex items-start gap-3">
        <Skeleton className="w-10 h-10 rounded-lg flex-shrink-0" />
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-16 rounded-full" />
          </div>
          <SkeletonText lines={2} />
        </div>
      </div>
    </div>
  );
}

// Grid of skeleton cards
export function SkeletonGrid({ count = 4, columns = 2 }: { count?: number; columns?: number }) {
  const gridClass = columns === 2 ? 'grid-cols-1 md:grid-cols-2' :
                    columns === 3 ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3' :
                    columns === 4 ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4' : 'grid-cols-1';
  return (
    <div className={`grid ${gridClass} gap-4`}>
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}

// Page loading skeleton wrapper
export function SkeletonPage({ children }: { children: ReactNode }) {
  return (
    <div className="p-6 space-y-6 animate-pulse">
      {children}
    </div>
  );
}

// Hub stats bar skeleton
export function SkeletonHubStats() {
  return (
    <div className="bg-gradient-to-r from-slate-800 to-slate-900 rounded-xl p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Skeleton className="w-10 h-10 rounded-lg bg-slate-700" />
          <div>
            <Skeleton className="h-4 w-24 mb-1 bg-slate-700" />
            <Skeleton className="h-3 w-32 bg-slate-700" />
          </div>
        </div>
        <div className="flex gap-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="text-center">
              <Skeleton className="h-6 w-12 mb-1 bg-slate-700 mx-auto" />
              <Skeleton className="h-3 w-16 bg-slate-700" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Skeleton;
