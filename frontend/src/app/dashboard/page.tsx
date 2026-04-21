'use client'

import DashboardSidebar from "@/components/ui/DashboardSidebar";
import { Group } from "react-resizable-panels";

export default function Dashboard() {
  return (
    <main className="flex flex-row h-screen w-full bg-primary-bg overflow-hidden font-sans text-primary-text">
        <Group orientation="horizontal" id="main-layout">
        {/* Left: Section Sidebar */}
        <DashboardSidebar />
        </Group> 
    </main>
  );
}