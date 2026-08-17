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
import LessonViewport from '@/components/generation/LessonViewport';
import LoadingOverlay from '@/components/generation/LoadingOverlay';
import Button from '@/components/ui/Button';
import { useApi } from '@/lib/hooks/useApi';
import { useGeneration } from '@/lib/hooks/useGeneration';

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
    selectLessonVersion,
    stopGeneration,
    startNewLesson,
    generateLesson,
    updateTitle,
    downloadLesson,
  } = useGeneration(api);
  const [collapsed, setCollapsed] = useState(false);
  const [loadedPreviewUrl, setLoadedPreviewUrl] = useState('');
  const panelRef = useRef<PanelImperativeHandle | null>(null);
  const previewIsLoading = Boolean(lesson && !showCode && previewUrl && loadedPreviewUrl !== previewUrl);

  useEffect(() => {
    const lessonId = new URLSearchParams(window.location.search).get('lessonId');
    if (lessonId) void loadLesson(lessonId);
  }, [loadLesson]);

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
                <article className="relative flex h-full w-full flex-col overflow-hidden rounded-3xl border border-border bg-primary-bg shadow-2xl">
                  {lesson && <span className="pointer-events-none absolute left-4 top-4 z-20 rounded-full border border-accent/40 bg-primary-bg/80 px-3 py-1 text-xs font-semibold text-accent shadow-lg backdrop-blur-md">Version {lesson.version_number}</span>}
                  {lesson && <Button onClick={() => setShowCode((current) => !current)} className="absolute right-4 top-4 z-10 flex items-center gap-2 text-xs">{showCode ? <Eye size={14} /> : <Code size={14} />}{showCode ? 'View Material' : 'View Code'}</Button>}
                  {lesson ? (
                    showCode
                      ? <SyntaxHighlighter language={format === 'video' ? 'python' : 'html'} style={vscDarkPlus} customStyle={{ background: 'transparent', margin: 0, padding: '4rem 2rem 2rem', minHeight: '100%' }} codeTagProps={{ className: 'whitespace-pre-wrap break-words' }} wrapLongLines>{lesson.source_code || ''}</SyntaxHighlighter>
                      : previewUrl
                        ? <LessonViewport>
                            {format === 'video'
                              ? <video className="size-full bg-black object-contain" src={previewUrl} controls autoPlay onLoadedData={() => setLoadedPreviewUrl(previewUrl)} onError={() => setLoadedPreviewUrl(previewUrl)} />
                              : <iframe key={previewUrl} src={previewUrl} className="size-full border-none bg-primary-bg" title="Lesson preview" sandbox="allow-scripts" onLoad={() => setLoadedPreviewUrl(previewUrl)} />}
                          </LessonViewport>
                        : error
                          ? <section className="m-auto max-w-lg p-8 text-center"><h2 className="text-xl font-semibold">Lesson preview unavailable</h2><p className="mt-3 text-sm text-secondary-text">{error}</p><Button variant="outline" size="sm" className="mt-5" onClick={() => void loadLesson(lesson.id)}>Retry preview</Button></section>
                          : <section className="m-auto p-8 text-center text-secondary-text">Loading lesson preview…</section>
                  ) : <section className="m-auto max-w-md p-8 text-center"><h2 className="text-2xl font-bold">Lesson Preview</h2><p className="mt-4 text-lg text-secondary-text">Describe a topic and choose a format to create a lesson.</p></section>}

                  {(loading || previewIsLoading) && (
                    <LoadingOverlay
                      progress={loading ? progress : 0}
                      status={loading ? status : 'Loading lesson preview…'}
                    />
                  )}
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
              selectedLessonId={lesson?.id ?? null}
              onSelectVersion={(lessonId) => void selectLessonVersion(lessonId)}
              loading={loading}
              format={format}
              topic={topic}
              onFormatChange={setFormat}
              onTopicChange={setTopic}
              onGenerate={() => void generateLesson()}
              onStopGenerate={stopGeneration}
              sourceFiles={sourceFiles}
              onSourceFilesChange={setSourceFiles}
              error={error}
              generationStatus={status}
            />
          </Panel>
        </Group>
      </main>
    </RequireAuth>
  );
}
