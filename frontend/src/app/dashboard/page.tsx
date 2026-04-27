'use client'

import { useState, useRef } from "react";
import DashboardSidebar from "@/components/ui/DashboardSidebar";
import { Group, Panel, Separator } from "react-resizable-panels";

export default function Dashboard() {
  const panelRef = useRef<any>(null);
  const [isCollapsed, setIsCollapsed] = useState(false);

  const togglePanel = () => {
    // Imperative API for react-resizable-panels to handle manual collapse/expand
    const panel = panelRef.current;
    if (panel) {
      if (panel.isCollapsed()) {
        panel.expand();
      } else {
        panel.collapse();
      }
    }
  }

  return (
    <main className="flex flex-row h-screen w-full bg-primary-bg overflow-hidden font-sans text-primary-text">
        <Group orientation="horizontal" id="main-layout">
        {/* Left: Section Sidebar */}
        <Panel 
          panelRef={panelRef}
          collapsible={true} 
          collapsedSize="80px"
          onResize={(size) => {
            if (size.asPercentage < 15) {
              setIsCollapsed(true);
            } else {
              setIsCollapsed(false);
            }
          }}
          minSize="20%" 
          maxSize="20%" 
          defaultSize="20%"
          id="left-panel"
          className="bg-secondary-bg border-r border-border h-full flex flex-col"
          >
          <DashboardSidebar isCollapsed={isCollapsed} onToggle={togglePanel} />
        </Panel>

        <Separator className="w-1 bg-border/20 hover:bg-accent/40 transition-colors cursor-col-resize shadow-[inset_0_0_1px_rgba(255,255,255,0.05)]" />

        {/* Right: Main Content */}
        <Panel minSize="50%" defaultSize="80%" id="content-panel">
            <div className="flex flex-col h-full bg-primary-bg p-8 overflow-y-auto">
                <header className="mb-8">
                    <h2 className="text-3xl font-bold tracking-tight text-primary-text mb-2">Lessons</h2>
                </header>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {/* Placeholder for lesson cards */}
                    <div className="h-64 rounded-3xl border border-border bg-surface/30 border-dashed flex flex-col items-center justify-center p-6 text-center">
                        <p className="text-secondary-text mb-4 italic">No lessons yet.</p>
                        <a 
                          href="/generation" 
                          className="px-6 py-2.5 bg-accent text-primary-text rounded-xl font-semibold shadow-lg shadow-accent/20 hover:bg-amber-700 transition-all duration-300 transform hover:-translate-y-1"
                        >
                          Create First Lesson
                        </a>
                    </div>
                </div>
            </div>
        </Panel>
      </Group>
    </main>
    );
  }
