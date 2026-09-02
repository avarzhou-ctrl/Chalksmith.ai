import type { ReactNode } from 'react';

export default function ForgeFrame({ children }: { children: ReactNode }) {
  return (
    <div className="relative overflow-hidden rounded-3xl bg-border p-px shadow-2xl shadow-accent/20">
      <span
        aria-hidden="true"
        className="absolute -inset-[180%] animate-forge-border bg-[conic-gradient(from_90deg_at_50%_50%,transparent_0deg,transparent_300deg,#d97706_326deg,#fde68a_340deg,transparent_360deg)] motion-reduce:animate-none"
      />
      <div className="relative overflow-hidden rounded-3xl bg-primary-bg">
        {children}
      </div>
    </div>
  );
}
