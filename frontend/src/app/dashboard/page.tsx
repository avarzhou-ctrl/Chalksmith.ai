'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { CirclePlus } from 'lucide-react';
import { Group, Panel, Separator, type PanelImperativeHandle } from 'react-resizable-panels';

import { AuthButton } from '@/components/auth/AuthButton';
import { RequireAuth } from '@/components/auth/RequireAuth';
import DashboardSidebar from '@/components/dashboard/DashboardSidebar';
import LessonCard from '@/components/dashboard/LessonCard';
import FormatOutput from '@/components/ui/FormatOutput';
import { deleteLesson, listLessons } from '@/lib/api/lessons';
import { useApi } from '@/lib/hooks/useApi';
import type { LessonListItem } from '@/lib/types/api';

export default function Dashboard() {
  const api = useApi();
  const panelRef = useRef<PanelImperativeHandle | null>(null);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [lessons, setLessons] = useState<LessonListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void listLessons(api)
      .then(setLessons)
      .catch((caught) => setError(caught instanceof Error ? caught.message : 'Failed to fetch lessons.'))
      .finally(() => setLoading(false));
  }, [api]);

  async function remove(lessonId: string) {
    try {
      await deleteLesson(api, lessonId);
      setLessons((current) => current.filter((lesson) => lesson.id !== lessonId));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to delete lesson.');
    }
  }

  function togglePanel() {
    const panel = panelRef.current;
    if (panel) panel.isCollapsed() ? panel.expand() : panel.collapse();
  }

  return (
    <RequireAuth>
      <main className="app-route-without-site-header flex h-screen w-full overflow-hidden bg-primary-bg font-sans text-primary-text">
        <Group orientation="horizontal" id="dashboard-layout">
          <Panel panelRef={panelRef} collapsible collapsedSize="80px" minSize="20%" maxSize="20%" defaultSize="20%" onResize={(size) => setIsCollapsed(size.asPercentage < 15)} className="flex h-full flex-col border-r border-border bg-secondary-bg">
            <DashboardSidebar isCollapsed={isCollapsed} onToggle={togglePanel} />
            <section className="mt-auto p-4"><AuthButton /></section>
          </Panel>
          <Separator className="w-1 cursor-col-resize bg-border/20 hover:bg-accent/40" />
          <Panel minSize="50%" defaultSize="80%">
            <section className="flex h-full flex-col overflow-y-auto bg-primary-bg p-8">
              <header className="mb-2"><h2 className="text-3xl font-bold tracking-tight">Lessons</h2></header>
              {error && <p className="mb-4 rounded-lg border border-red-900/60 bg-red-950/30 p-3 text-sm text-red-200">{error}</p>}
              <section className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
                <Link href="/generation" className="flex min-h-48 flex-col items-center justify-center rounded-lg border border-dashed border-border bg-surface/30 p-6 text-center transition-colors hover:border-accent hover:bg-surface/40">
                  <CirclePlus className="text-accent" size={55} /><p className="mt-4 text-lg">Create New Lesson</p>
                </Link>
                {loading && <p className="min-h-48 rounded-lg border border-border bg-surface/30 p-4 text-sm text-secondary-text">Loading lessons…</p>}
                {!loading && lessons.map((lesson) => (
                  <LessonCard
                    key={lesson.id}
                    id={lesson.id}
                    title={lesson.topic}
                    description={lesson.summary ? <FormatOutput rawContent={lesson.summary} /> : null}
                    format={lesson.format}
                    status={lesson.status}
                    createdAt={lesson.created_at}
                    versionCount={lesson.version_count}
                    onDelete={() => void remove(lesson.id)}
                  />
                ))}
              </section>
            </section>
          </Panel>
        </Group>
      </main>
    </RequireAuth>
  );
}
