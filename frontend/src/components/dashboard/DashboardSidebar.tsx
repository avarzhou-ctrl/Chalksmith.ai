'use client'

import { Folder, Bookmark, Search, PanelLeft } from "lucide-react"
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
                        <div className="flex items-center min-w-0">
                            <div className="w-10 h-10 rounded-xl flex items-center justify-center overflow-hidden mr-3 shrink-0">
                                <img src="/logo.png" alt="Logo" className="w-8 h-8 object-contain" />
                            </div>
                            <h1 className="text-xl font-bold tracking-tight text-primary-text truncate animate-in fade-in duration-300">Chalksmith.ai</h1>
                        </div>
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
                    href="/favorites"
                    className={`flex items-center rounded-xl text-secondary-text hover:bg-accent hover:text-primary-text transition-all duration-200 group w-full ${isCollapsed ? 'justify-center p-3' : 'px-3 py-3'}`}
                    title={isCollapsed ? "Favorites" : ""}
                >
                    <Bookmark size={20} className={`${!isCollapsed ? 'mr-3' : ''} group-hover:scale-110 transition-transform`} />
                    {!isCollapsed && <span className="text-sm font-medium">Favorites</span>}
                </Link>

                <Link
                    href="/search"
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
