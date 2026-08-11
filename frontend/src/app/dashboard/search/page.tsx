'use client'

import { useEffect, useRef, useState } from "react";
import { Search, X } from "lucide-react";
import { Group, Panel, Separator, type PanelImperativeHandle } from "react-resizable-panels";
import DashboardSidebar from "@/components/dashboard/DashboardSidebar";
import LessonCard from "@/components/dashboard/LessonCard";
import SearchFilter from "@/components/dashboard/SearchFilter";
import FormatOutput from "@/components/ui/FormatOutput";
import { AuthButton } from "@/components/auth/AuthButton";
import { RequireAuth } from "@/components/auth/RequireAuth";
import { deleteLesson, listLessons } from "@/lib/api/lessons";
import { useApi } from "@/lib/hooks/useApi";
import type { LessonFormat, LessonListItem } from "@/lib/types/api";

export default function SearchPage() {
  const api = useApi();
  const panelRef = useRef<PanelImperativeHandle | null>(null);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [query, setQuery] = useState("");
  const [format, setFormat] = useState("");
  const [lessons, setLessons] = useState<LessonListItem[]>([]);
  const [isLoadingLessons, setIsLoadingLessons] = useState(false);
  const [lessonError, setLessonError] = useState<string | null>(null);

  useEffect(() => {
    const timeoutId = window.setTimeout(async () => {
      try {
        setIsLoadingLessons(true);
        setLessonError(null);
        const trimmedQuery = query.trim();
        const data = await listLessons(api, {
          q: trimmedQuery || undefined,
          format: (format || undefined) as LessonFormat | undefined,
        });
        setLessons(data);
      } catch (error) {
        console.error('Error searching lessons:', error);
        setLessonError(error instanceof Error ? error.message : 'Failed to search lessons');
      } finally {
        setIsLoadingLessons(false);
      }
    }, 300);

    return () => window.clearTimeout(timeoutId);
  }, [api, query, format]);

  const handleDeleteLesson = async (lessonId: string) => {
    try {
      await deleteLesson(api, lessonId);
      setLessons((currentLessons) => currentLessons.filter((lesson) => lesson.id !== lessonId));
    } catch (error) {
      console.error('Error deleting lesson:', error);
      setLessonError(error instanceof Error ? error.message : 'Failed to delete lesson');
    }
  };

  const togglePanel = () => {
    const panel = panelRef.current;
    if (!panel) {
      return;
    }

    if (panel.isCollapsed()) {
      panel.expand();
    } else {
      panel.collapse();
    }
  };

  return (
    <RequireAuth>
    <main className="app-route-without-site-header flex h-screen w-full flex-row overflow-hidden bg-primary-bg font-sans text-primary-text">
      <Group orientation="horizontal" id="search-layout">
        <Panel
          panelRef={panelRef}
          collapsible={true}
          collapsedSize="80px"
          onResize={(size) => {
            setIsCollapsed(size.asPercentage < 15);
          }}
          minSize="20%"
          maxSize="20%"
          defaultSize="20%"
          id="left-panel"
          className="flex h-full flex-col border-r border-border bg-secondary-bg"
        >
          <DashboardSidebar isCollapsed={isCollapsed} onToggle={togglePanel} />

          <section className="mt-auto p-4"><AuthButton /></section>
        </Panel>

        <Separator className="w-1 cursor-col-resize bg-border/20 shadow-[inset_0_0_1px_rgba(255,255,255,0.05)] transition-colors hover:bg-accent/40" />

        <Panel minSize="50%" defaultSize="80%" id="content-panel">
          <div className="flex h-full flex-col overflow-y-auto bg-primary-bg p-8">
            <header className="mb-6">
              <h2 className="mb-5 text-3xl font-bold tracking-tight text-primary-text">Search</h2>
              <div className="flex flex-col gap-3 lg:flex-row">
                <label className="relative flex min-h-12 flex-1 items-center rounded-lg border border-border bg-secondary-bg text-primary-text focus-within:border-accent">
                  <Search className="ml-4 shrink-0 text-secondary-text" size={20} />
                  <input
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="Search lessons"
                    className="h-12 min-w-0 flex-1 bg-transparent px-3 text-sm text-primary-text outline-none placeholder:text-secondary-text"
                  />
                  {query && (
                    <button
                      type="button"
                      onClick={() => setQuery("")}
                      className="mr-3 rounded-md p-1 text-secondary-text transition-colors hover:bg-primary-text/10 hover:text-primary-text focus:outline-none focus:ring-2"
                      title="Clear search"
                    >
                      <X size={18} />
                    </button>
                  )}
                </label>

                <div className="w-full lg:w-64">
                  <SearchFilter
                    format={format}
                    onFormatChange={setFormat}
                  />
                </div>
              </div>
            </header>

            {lessonError && (
              <p className="mb-4 rounded-lg border border-red-900/60 bg-red-950/30 p-3 text-sm text-red-200">
                {lessonError}
              </p>
            )}

            {isLoadingLessons && (
              <p className="rounded-lg border border-border bg-surface/30 p-4 text-sm text-secondary-text">
                Loading lessons...
              </p>
            )}

            {!isLoadingLessons && lessons.length === 0 && (
              <section className="rounded-lg border border-border bg-surface/30 p-8 text-center">
                <h3 className="text-lg font-semibold text-primary-text">No lessons found</h3>
                <p className="mt-2 text-sm text-secondary-text">
                  Try a different search term or format.
                </p>
              </section>
            )}

            {!isLoadingLessons && lessons.length > 0 && (
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
                {lessons.map((lesson) => (
                  <LessonCard
                    key={lesson.id}
                    id={lesson.id}
                    title={lesson.topic}
                    description={lesson.summary ? <FormatOutput rawContent={lesson.summary} /> : null}
                    format={lesson.format}
                    status={lesson.status}
                    createdAt={lesson.created_at}
                    onDelete={() => handleDeleteLesson(lesson.id)}
                  />
                ))}
              </div>
            )}
          </div>
        </Panel>
      </Group>
    </main>
    </RequireAuth>
  );
}
