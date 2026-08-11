'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { Code, Download, Eye, Flame } from 'lucide-react';
import { Group, Panel, Separator, type PanelImperativeHandle } from 'react-resizable-panels';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

import { RequireAuth } from '@/components/auth/RequireAuth';
import EditableTitle from '@/components/generation/EditableTitle';
import GenerationSidebar from '@/components/generation/GenerationSidebar';
import Button from '@/components/ui/Button';
import { useApi } from '@/lib/hooks/useApi';
import { useGeneration } from '@/lib/hooks/useGeneration';
import type { LessonFormat } from '@/lib/types/api';

export default function GenerationPage() {
  const api = useApi();
  const {
    topic,
    setTopic,
    format,
    setFormat,
    lesson,
    previewUrl,
    title,
    loading,
    status,
    progress,
    error,
    showCode,
    setShowCode,
    sourceFiles,
    setSourceFiles,
    messages,
    loadLesson,
    stopGeneration,
    startNewLesson,
    generateLesson,
    updateTitle,
    downloadLesson,
  } = useGeneration(api);
  const [collapsed, setCollapsed] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<PanelImperativeHandle | null>(null);

  useEffect(() => {
    const lessonId = new URLSearchParams(window.location.search).get('lessonId');
    if (lessonId) void loadLesson(lessonId);
  }, [loadLesson]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [loading, messages]);

  function togglePanel() {
    const panel = panelRef.current;
    if (panel) panel.isCollapsed() ? panel.expand() : panel.collapse();
  }

  return (
    <RequireAuth>
      <main className="app-route-without-site-header flex h-screen w-full overflow-hidden bg-primary-bg font-sans text-primary-text">
        <Group orientation="horizontal" id="main-layout">
          <Panel defaultSize="75%" minSize="50%">
            <section className="flex h-full flex-col bg-primary-bg">
              <header className="m-1 flex shrink-0 items-end gap-4 p-4">
                <Link href="/dashboard" className="mb-1 grid size-10 place-items-center rounded-xl"><img src="/logo.png" alt="Chalksmith" className="size-8 object-contain" /></Link>
                <EditableTitle initialTitle={title} onChange={(value) => void updateTitle(value)} />
                <section className="flex gap-2 pb-1">
                  <Button variant="outline" size="sm" onClick={startNewLesson} className="gap-1.5"><Flame size={14} />Create New</Button>
                  {lesson && <Button variant="outline" size="sm" onClick={() => void downloadLesson()} className="gap-1.5"><Download size={14} />Export</Button>}
                </section>
              </header>

              <section className="relative flex flex-1 items-center justify-center overflow-hidden px-4 pb-8">
                <article className="relative flex h-full w-full flex-col overflow-auto rounded-3xl border border-border bg-primary-bg shadow-2xl">
                  {lesson && <Button onClick={() => setShowCode((current) => !current)} className="absolute right-4 top-4 z-10 flex items-center gap-2 text-xs">{showCode ? <Eye size={14} /> : <Code size={14} />}{showCode ? 'View Material' : 'View Code'}</Button>}
                  {lesson ? (
                    showCode
                      ? <SyntaxHighlighter language={format === 'video' ? 'python' : 'html'} style={vscDarkPlus} customStyle={{ background: 'transparent', margin: 0, padding: '2rem', minHeight: '100%' }}>{lesson.source_code || ''}</SyntaxHighlighter>
                      : format === 'video'
                        ? <video className="h-full w-full bg-black object-contain" src={previewUrl} controls autoPlay />
                        : <iframe key={previewUrl} src={previewUrl} className="h-full w-full border-none bg-white" title="Lesson preview" sandbox="allow-scripts" />
                  ) : <section className="m-auto max-w-md p-8 text-center"><h2 className="text-2xl font-bold">Lesson Preview</h2><p className="mt-4 text-lg text-secondary-text">Describe a topic and choose a format to create a lesson.</p></section>}

                  {loading && <section className="absolute inset-0 z-50 grid place-items-center bg-primary-bg/90 p-8 backdrop-blur-xl"><div className="w-full max-w-md text-center"><Flame className="mx-auto size-16 animate-pulse text-accent" /><h2 className="mt-6 text-3xl font-bold text-accent">Chalksmith.ai</h2><p className="mt-2 text-sm text-secondary-text">{status}</p><div className="mt-8 h-1.5 overflow-hidden rounded-full bg-surface"><div className="h-full bg-accent transition-all" style={{ width: `${progress}%` }} /></div></div></section>}
                </article>
              </section>
            </section>
          </Panel>
          <Separator className="w-1 cursor-col-resize bg-border/20 hover:bg-accent/40" />
          <Panel panelRef={panelRef} collapsible collapsedSize="64px" defaultSize="25%" minSize="20%" maxSize="40%" onResize={(size) => setCollapsed(size.asPercentage < 15)}>
            <GenerationSidebar
              isCollapsed={collapsed}
              onToggle={togglePanel}
              title={title}
              messages={messages}
              loading={loading}
              messagesEndRef={messagesEndRef}
              format={format}
              topic={topic}
              onFormatChange={(value) => setFormat(value as LessonFormat)}
              onTopicChange={setTopic}
              onGenerate={() => void generateLesson()}
              onStopGenerate={stopGeneration}
              sourceFiles={sourceFiles}
              onSourceFilesChange={setSourceFiles}
              currentLessonId={lesson?.id ?? null}
              error={error}
              generationStatus={status}
            />
          </Panel>
        </Group>
      </main>
    </RequireAuth>
  );
}
