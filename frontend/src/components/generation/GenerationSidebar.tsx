'use client'

import { PanelRight, ChevronDown, Flame, Loader2 } from "lucide-react";
import { Group, Panel, Separator } from "react-resizable-panels";
import InputForm from "./InputForm";
import { GenerationStatus } from "@/lib/api";

interface GenerationSidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
  title: string;
  messages: { role: 'user' | 'assistant'; content: string }[];
  loading: boolean;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  model: string;
  format: string;
  topic: string;
  onModelChange: (model: string) => void;
  onFormatChange: (format: string) => void;
  onTopicChange: (topic: string) => void;
  onGenerate: (override?: string) => void;
  onStopGenerate: () => void;
  currentLessonId: string | null;
  error: string | null;
  generationStatus: GenerationStatus | null;
}

export default function GenerationSidebar({
  isCollapsed,
  onToggle,
  title,
  messages,
  loading,
  messagesEndRef,
  model,
  format,
  topic,
  onModelChange,
  onFormatChange,
  onTopicChange,
  onGenerate,
  onStopGenerate,
  currentLessonId,
  error,
  generationStatus
}: GenerationSidebarProps) {
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
                <button className="text-secondary-text hover:text-primary-text transition-colors">
                  <ChevronDown size={20} />
                </button>
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
        <Group orientation="vertical" id="interaction-layout">
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
              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in slide-in-from-bottom-2 duration-300`}>
                  <div className={`max-w-[90%] p-4 rounded-2xl text-sm ${
                    msg.role === 'user' 
                      ? 'bg-accent text-primary-text rounded-tr-none shadow-lg shadow-accent/10' 
                      : 'bg-surface/50 text-primary-text rounded-tl-none border border-border/50'
                  }`}>
                    {msg.content}
                  </div>
                </div>
              ))}
              {loading && (
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
          <Panel minSize="20%" defaultSize="40%">
            <div className="h-full p-6 bg-primary-bg/50 border-t border-border flex flex-col gap-6 backdrop-blur-lg overflow-y-auto">
              <InputForm
                model={model}
                format={format}
                topic={topic}
                onModelChange={onModelChange}
                onFormatChange={onFormatChange}
                onTopicChange={onTopicChange}
                onGenerate={onGenerate}
                onStopGenerate={onStopGenerate}
                disabled={loading}
                isEditMode={!!currentLessonId}
                generationStatus={generationStatus}
              />
              
              {error && (
                <p className="text-xs text-red-500 bg-red-500/10 p-2 rounded border border-red-500/20 text-center animate-in fade-in">
                  {error}
                </p>
              )}
            </div>
          </Panel>
        </Group>
      )}
    </div>
  );
}
