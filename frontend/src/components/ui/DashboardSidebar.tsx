'use client'

import { Folder, Bookmark, Search } from "lucide-react"
import Link from "next/link";

export default function DashboardSidebar() {
    return (
        <div className="w-64 bg-secondary-bg p-4 border-r border-border">
            <div className="flex flex-row items-center mb-6">
                <div className="w-10 h-10 bg-accent rounded-xl flex items-center justify-center shadow-lg shadow-accent/20 overflow-hidden mb-1">
                    <img src="/logo.png" alt="Logo" className="w-8 h-8 object-contain" />
                </div>
                <h1 className="text-lg font-semibold mb-4">Chalksmith.ai</h1>
            </div>
            <nav className="flex flex-col space-y-2">
                <Link
                    href="/dashboard"
                    className="flex flex_row items-center mb-6 px-3 py-2 rounded-xl text-sm font-medium text-secondary-text hover:bg-accent hover:text-primary-text transition-colors duration-200"
                >
                    <Folder size={24} />
                    <span className="ml-2">Lessons</span>
                </Link>
                <Link
                    href="/favorites"
                    className="flex flex_row items-center mb-6 px-3 py-2 rounded-xl text-sm font-medium text-secondary-text hover:bg-accent hover:text-primary-text transition-colors duration-200"
                >
                    <Bookmark size={24} />
                    <span className="ml-2">Favorites</span>
                </Link>
                <Link
                    href="/search"
                    className="flex flex_row items-center mb-6 px-3 py-2 rounded-xl text-sm font-medium text-secondary-text hover:bg-accent hover:text-primary-text transition-colors duration-200"
                >
                    <Search size={24} />
                    <span className="ml-2">Search</span>
                </Link>
            </nav>
        </div>
    );
}