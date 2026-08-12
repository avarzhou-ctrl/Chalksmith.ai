'use client';

import type { ReactNode } from 'react';
import { useRef, useState } from 'react';
import { Group, Panel, Separator, type PanelImperativeHandle } from 'react-resizable-panels';

import { AuthButton } from '@/components/auth/AuthButton';
import { RequireAuth } from '@/components/auth/RequireAuth';
import DashboardSidebar from '@/components/dashboard/DashboardSidebar';

interface DashboardShellProps {
  children: ReactNode;
  layoutId: string;
}

export default function DashboardShell({ children, layoutId }: DashboardShellProps) {
  const panelRef = useRef<PanelImperativeHandle | null>(null);
  const [isCollapsed, setIsCollapsed] = useState(false);

  function togglePanel() {
    const panel = panelRef.current;
    if (panel) panel.isCollapsed() ? panel.expand() : panel.collapse();
  }

  return (
    <RequireAuth>
      <main className="app-route-without-site-header flex h-screen w-full overflow-hidden bg-primary-bg font-sans text-primary-text">
        <Group orientation="horizontal" id={layoutId}>
          <Panel
            panelRef={panelRef}
            collapsible
            collapsedSize="80px"
            minSize="20%"
            maxSize="20%"
            defaultSize="20%"
            onResize={(size) => setIsCollapsed(size.asPercentage < 15)}
            className="flex h-full flex-col border-r border-border bg-secondary-bg"
          >
            <DashboardSidebar isCollapsed={isCollapsed} onToggle={togglePanel} />
            <section className="mt-auto p-4">
              <AuthButton />
            </section>
          </Panel>
          <Separator className="w-1 cursor-col-resize bg-border/20 transition-colors hover:bg-accent/40" />
          <Panel minSize="50%" defaultSize="80%">
            {children}
          </Panel>
        </Group>
      </main>
    </RequireAuth>
  );
}
