'use client'

import { useEffect, useRef } from 'react';
import { PanelRight, Flame, Loader2, Star } from "lucide-react";
import { Group, Panel, Separator } from "react-resizable-panels";
import InputForm from "./InputForm";
import FormatOutput from "@/components/ui/FormatOutput";
import type { GenerationMessage } from '@/lib/hooks/useGeneration';
import type { LessonFormat } from '@/lib/types/api';

interface GenerationSidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
  title: string;
  messages: GenerationMessage[];
  selectedLessonId: string | null;
  onSelectVersion: (lessonId: string) => void;
  onSelectFinalVersion: (lessonId: string) => void;
  loading: boolean;
  format: LessonFormat | '';
  topic: string;
  onFormatChange: (format: LessonFormat) => void;
  onTopicChange: (topic: string) => void;
  onGenerate: () => void;
  onStopGenerate: () => void;
  sourceFiles: File[];
  onSourceFilesChange: (files: File[]) => void;
  error: string | null;
  generationStatus: string | null;
}

export default function GenerationSidebar({
  isCollapsed,
  onToggle,
  title,
  messages,
  selectedLessonId,
  onSelectVersion,
  onSelectFinalVersion,
  loading,
  format,
  topic,
  onFormatChange,
  onTopicChange,
  onGenerate,
  onStopGenerate,
  sourceFiles,
  onSourceFilesChange,
  error,
  generationStatus
}: GenerationSidebarProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const versionStartRefs = useRef(new Map<string, HTMLDivElement>());
  const isGenerating = loading && generationStatus !== 'Loading lesson…';

  useEffect(() => {
    if (!selectedLessonId) return;
    const frame = window.requestAnimationFrame(() => {
      versionStartRefs.current.get(selectedLessonId)?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [selectedLessonId]);

  useEffect(() => {
    if (isGenerating) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [generationStatus, isGenerating, messages.length]);

  function selectVersion(lessonId: string) {
    versionStartRefs.current.get(lessonId)?.scrollIntoView({
      behavior: 'smooth',
      block: 'start',
    });
    onSelectVersion(lessonId);
  }

  return (
    <div className="flex flex-col h-full bg-secondary-bg border-l border-border overflow-hidden">
      {/* Standardized Header Area: Matches Dashboard height and padding */}
      <div className="pt-4 px-4 pb-2 flex flex-col shrink-0">
        <div className="h-10 mb-2 flex items-center justify-between">
          {!isCollapsed ? (
            <>
              <h2 className="text-lg font-semibold text-primary-text truncate whitespace-nowrap min-w-0 mr-4" title={title}>
                {title}
              </h2>
              <div className="flex items-center gap-2 shrink-0">
                <button 
                  className="p-2 hover:bg-surface/50 rounded-lg text-secondary-text transition-all duration-300" 
                  title="Collapse Sidebar"
                  onClick={onToggle}
                >
                  <PanelRight size={20} />
                </button>
              </div>
            </>
          ) : (
            <button 
              className="p-2 hover:bg-surface/50 rounded-lg text-secondary-text transition-all duration-300 mx-auto shrink-0" 
              onClick={onToggle}
            >
              <PanelRight size={20} />
            </button>
          )}
        </div>
      </div>

      {!isCollapsed && (
        <Group orientation="vertical" id="interaction-layout" className="flex-1 min-h-0">
          {/* Chat History */}
          <Panel minSize={30}>
            <div className="h-full overflow-y-auto px-5 space-y-4 scroll-smooth pb-4">
              {messages.length === 0 && (
                <div className="bg-surface/30 p-4 rounded-2xl border border-border/50 text-secondary-text text-sm animate-in fade-in duration-500">
                  <p className="font-semibold mb-2 text-primary-text">Welcome to Chalksmith.ai!</p>
                  <ul className="space-y-2">
                    <li className="flex gap-2"><Flame size={16} className="text-accent mt-0.5 shrink-0" /> Choose a short topic</li>
                    <li className="flex gap-2"><Flame size={16} className="text-accent mt-0.5 shrink-0" /> Select your favorite format</li>
                    <li className="flex gap-2"><Flame size={16} className="text-accent mt-0.5 shrink-0" /> Watch your lesson come to life!</li>
                  </ul>
                </div>
              )}
              {messages.map((msg, i) => {
                const isVersionStart = Boolean(msg.lessonId && messages[i - 1]?.lessonId !== msg.lessonId);
                return (
                <div
                  key={`${msg.lessonId ?? 'draft'}-${msg.role}-${i}`}
                  ref={isVersionStart && msg.lessonId ? (node) => {
                    if (node) versionStartRefs.current.set(msg.lessonId!, node);
                    else versionStartRefs.current.delete(msg.lessonId!);
                  } : undefined}
                  className={`flex scroll-mt-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in slide-in-from-bottom-2 duration-300`}
                >
                  <div
                    className={`max-w-[90%] p-4 rounded-2xl text-left text-sm transition-colors ${
                    msg.role === 'user' 
                      ? 'bg-accent text-primary-text rounded-tr-none shadow-lg shadow-accent/10' 
                      : 'bg-surface/50 text-primary-text rounded-tl-none border border-border/50'
                  } ${msg.lessonId ? 'cursor-pointer hover:ring-1 hover:ring-accent/70 focus:outline-none focus:ring-2 focus:ring-accent' : 'cursor-default'} ${msg.lessonId === selectedLessonId ? 'ring-2 ring-accent' : ''}`}>
                    {msg.versionNumber && (
                      <span className="mb-1 flex items-center gap-1.5">
                        <span className={`block text-xs font-medium ${msg.role === 'user' ? 'text-primary-text' : 'text-secondary-text'}`}>
                          Version {msg.versionNumber}
                        </span>
                        {msg.role === 'user' && msg.lessonId && (
                          <button
                            type="button"
                            disabled={loading || !msg.canFinalize || msg.isFinal}
                            onClick={() => onSelectFinalVersion(msg.lessonId!)}
                            className="grid size-6 place-items-center rounded-md text-primary-text transition-colors hover:bg-black/15 disabled:cursor-default disabled:opacity-70"
                            title={msg.isFinal ? 'Final version' : 'Set as final version'}
                            aria-label={msg.isFinal ? `Version ${msg.versionNumber} is final` : `Set version ${msg.versionNumber} as final`}
                            aria-pressed={Boolean(msg.isFinal)}
                          >
                            <Star className={msg.isFinal ? 'size-4 fill-amber-300 text-amber-300' : 'size-4'} />
                          </button>
                        )}
                      </span>
                    )}
                    <button
                      type="button"
                      disabled={!msg.lessonId || loading}
                      onClick={() => msg.lessonId && selectVersion(msg.lessonId)}
                      className="block w-full text-left disabled:cursor-default"
                    >
                      {msg.role === 'assistant' && typeof msg.content === 'string' ? (
                        <FormatOutput rawContent={msg.content} />
                      ) : (
                        msg.content
                      )}
                    </button>
                  </div>
                </div>
                );
              })}
              {isGenerating && (
                <div className="flex justify-start">
                  <div className="bg-surface/50 p-4 rounded-2xl rounded-tl-none text-secondary-text text-sm animate-pulse border border-border/50 flex items-center gap-2">
                    <Loader2 size={14} className="animate-spin" />
                    <span>Thinking...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </Panel>

          <Separator className="h-1 bg-border/20 hover:bg-accent/40 transition-colors cursor-row-resize" />

          {/* Control Panel */}
          <Panel minSize="20%" maxSize="50" defaultSize="35%">
            {/* pb-8 matches the preview card's bottom offset so both boxes end on the same line */}
            <div className="h-full px-6 pt-6 pb-8 bg-primary-bg/50 border-t border-border flex flex-col gap-4 backdrop-blur-lg overflow-y-auto">
              {error && (
                <p className="shrink-0 text-xs text-red-500 bg-red-500/10 p-2 rounded border border-red-500/20 text-center animate-in fade-in">
                  {error}
                </p>
              )}
              <InputForm
                format={format}
                topic={topic}
                onFormatChange={onFormatChange}
                onTopicChange={onTopicChange}
                onGenerate={onGenerate}
                onStopGenerate={onStopGenerate}
                sourceFiles={sourceFiles}
                onSourceFilesChange={onSourceFilesChange}
                disabled={loading}
                isEditMode={Boolean(selectedLessonId)}
              />
            </div>
          </Panel>
        </Group>
      )}
    </div>
  );
}
