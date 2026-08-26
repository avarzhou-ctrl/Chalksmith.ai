'use client'

import { Folder, Search, PanelLeft } from "lucide-react"
import Link from "next/link";

interface DashboardSidebarProps {
    isCollapsed?: boolean;
    onToggle?: () => void;
}

export default function DashboardSidebar({ isCollapsed, onToggle }: DashboardSidebarProps) {
    return (
        <div className="w-full h-full bg-secondary-bg pt-4 px-4 pb-2 flex flex-col relative">
            {/* Constant Header Area */}
            <div className="h-10 mb-2 flex items-center justify-between">
                {!isCollapsed ? (
                    <>
                        <a
                            href="https://chalksmith.ai/"
                            className="flex min-w-0 items-center"
                            aria-label="Chalksmith.ai home"
                        >
                            <span className="mr-3 flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-xl">
                                <img src="/logo.png" alt="" className="h-8 w-8 object-contain" />
                            </span>
                            <span className="animate-in truncate text-xl font-bold tracking-tight text-primary-text fade-in duration-300">
                                Chalksmith.ai
                            </span>
                        </a>
                        <button 
                            className="p-2 hover:bg-surface/50 rounded-lg text-secondary-text transition-all duration-300 ml-2 shrink-0" 
                            title="Collapse Sidebar"
                            onClick={onToggle}
                        >
                            <PanelLeft size={20} />
                        </button>
                    </>
                ) : (
                    <button 
                        className="p-2 hover:bg-surface/50 rounded-lg text-secondary-text transition-all duration-300 mx-auto shrink-0" 
                        onClick={onToggle}
                    >
                        <PanelLeft size={20} />
                    </button>
                )}
            </div>

            {/* Navigation - Spacing must match exactly for stationary icons */}
            <nav className={`flex flex-col space-y-2 ${isCollapsed ? 'items-center' : ''}`}>
                <Link
                    href="/dashboard"
                    className={`flex items-center rounded-xl text-secondary-text hover:bg-accent hover:text-primary-text transition-all duration-200 group w-full ${isCollapsed ? 'justify-center p-3' : 'px-3 py-3'}`}
                    title={isCollapsed ? "Lessons" : ""}
                >
                    <Folder size={20} className={`${!isCollapsed ? 'mr-3' : ''} group-hover:scale-110 transition-transform`} />
                    {!isCollapsed && <span className="text-sm font-medium">Lessons</span>}
                </Link>

                <Link
                    href="/dashboard/search"
                    className={`flex items-center rounded-xl text-secondary-text hover:bg-accent hover:text-primary-text transition-all duration-200 group w-full ${isCollapsed ? 'justify-center p-3' : 'px-3 py-3'}`}
                    title={isCollapsed ? "Search" : ""}
                >
                    <Search size={20} className={`${!isCollapsed ? 'mr-3' : ''} group-hover:scale-110 transition-transform`} />
                    {!isCollapsed && <span className="text-sm font-medium">Search</span>}
                </Link>
            </nav>
        </div>
    );
}
