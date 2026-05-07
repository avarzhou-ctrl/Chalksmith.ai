'use client'

import { useState, useRef, useEffect } from "react";
import DashboardSidebar from "@/components/dashboard/DashboardSidebar";
import { Group, Panel, Separator } from "react-resizable-panels";
import { CirclePlus } from "lucide-react";

export default function Dashboard() {
  const panelRef = useRef<any>(null);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [lessons, storeLessons] = useState<any[]>([]);

  useEffect(() => {
    // Fetch lessons from the backend API when the component mounts
    const fetchLessons = async () => {
      try {
        const response = await fetch('/api/lessons');
        if (!response.ok) {
          throw new Error('Failed to fetch lessons');
        }
        const data = await response.json();
        storeLessons(data);
      } catch (error) {
        console.error('Error fetching lessons:', error);
      }
    };
    fetchLessons();
  }, []);

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
                <header className="mb-2">
                    <h2 className="text-3xl font-bold tracking-tight text-primary-text mb-2">Lessons</h2>
                </header>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {/* Placeholder for lesson cards */}
                    <div 
                      onClick={() => (window.location.href = "/generation")}
                      className="h-50 w-75 rounded-3xl border border-border hover:border-accent bg-surface/30 border-dashed flex flex-col items-center justify-center p-6 text-center cursor-pointer transition-all duration-300 ease-in-out hover:bg-surface/40 group"
                    >
                      <CirclePlus className="text-accent/80 group-hover:text-accent transition-all duration-300 ease-in-out" size={55} />
                      <p className="mt-4 text-lg text-primary-text/80 group-hover:text-primary-text transition-all duration-300 ease-in-out">Create New Lesson</p>
                    </div>
                </div>
            </div>
        </Panel>
      </Group>
    </main>
    );
  }
