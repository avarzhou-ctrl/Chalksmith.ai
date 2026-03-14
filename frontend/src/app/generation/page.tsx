'use client'

import { useState, useRef, useEffect } from "react";
import InputForm from "@/components/generation/InputForm";
import EditableTitle from "@/components/generation/EditableTitle";
import Button from "@/components/ui/Button";
import { createLesson, LessonResponse } from "@/lib/api";
import { Panel, Group, Separator } from "react-resizable-panels";
import { PanelRight, ChevronDown } from "lucide-react";

export default function Page() {
  const [topic, setTopic] = useState('');
  const [model, setModel] = useState('gemini-3-flash-preview');
  const [format, setFormat] = useState('manim');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LessonResponse | null>(null);
  const [title, setTitle] = useState("Untitled Lesson Plan");
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant'; content: string }[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const panelRef = useRef<any>(null);
  const [isCollapsed, setIsCollapsed] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const togglePanel = () => {
    const panel = panelRef.current;
    if (panel) {
      if (panel.isCollapsed()) {
        panel.expand();
      } else {
        panel.collapse();
      }
    }
  }

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const generateLesson = async () => {
    if (!topic || !model || !format) return;

    setLoading(true);
    setError(null);
    setMessages((prev) => [...prev, { role: 'user', content: topic }]);

    try {
      const response = await createLesson({ topic, model, format });
      setResult(response);
      setMessages((prev) => [...prev, { role: 'assistant', content: `Success! Created your ${format === 'manim' ? 'video animation' : format === 'p5.js' ? 'interactive display' : 'presentation slides'} about "${topic}".` }]);
      setTopic('');
    } catch (err: any) {
      setError(err.message || 'Oops! Failed to generate lesson.');
      setMessages((prev) => [...prev, { role: 'assistant', content: `Error: ${err.message || 'Failed to generate lesson.'}` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex flex-row h-screen w-full bg-primary-bg overflow-hidden font-sans">
      <Group orientation="horizontal" id="main-layout">
        {/* Left: Preview */}
        <Panel defaultSize="75%" minSize="30%">
          <div className="flex flex-col h-full bg-primary-bg">
            {/* Header Bar */}
            <div className="flex flex-row p-4 m-1 gap-4 shrink-0 items-center">
              <div className="w-10 h-10 bg-accent rounded-xl flex items-center justify-center shadow-lg shadow-accent/20 overflow-hidden">
                <img src="/logo.png" alt="Logo" className="w-8 h-8 object-contain" />
              </div>
              <EditableTitle initialTitle={title} onChange={setTitle}/>
              {result && (
                <div className="flex gap-2 shrink-0">
                  <span className="text-xs px-2 py-1 bg-surface/50 border border-border rounded-lg text-secondary-text uppercase tracking-tighter shrink-0">{format}</span>
                  <span className="text-xs px-2 py-1 bg-surface/50 border border-border rounded-lg text-secondary-text uppercase tracking-tighter shrink-0">{model}</span>
                </div>
              )}
            </div>

            {/* Content Area */}
            <div className="flex flex-col flex-1 justify-center items-center px-4 pb-8 relative">
              <div className="w-full h-full bg-secondary-bg rounded-3xl overflow-hidden border border-border shadow-2xl relative flex flex-col">
                {result ? (
                  <div className="flex-1 w-full h-full bg-primary-bg overflow-hidden">
                    {format === 'manim' ? (
                      <video
                        key={result.url}
                        className="w-full h-full object-contain"
                        title="Video Preview"
                        controls
                        autoPlay
                      >
                        <source src={result.url} type="video/mp4" />
                        Your browser does not support the video tag.
                      </video>
                    ) : (
                      <iframe
                        key={result.url}
                        src={result.url}
                        className="w-full h-full border-none bg-white"
                        title="Interactive Display Preview"
                      />
                    )}
                  </div>
                ) : (
                  <div className="flex-1 flex flex-col items-center justify-center gap-6 max-w-md mx-auto animate-in fade-in zoom-in duration-700">
                    <h2 className="text-center text-2xl font-bold text-primary-text">
                      Lesson Preview
                    </h2>
                    <p className="text-center text-secondary-text text-lg">
                      Describe a topic on the right and choose a format to start generating lesson materials!
                    </p>
                  </div>
                )}

                {loading && (
                  <div className ="absolute inset-0 bg-primary-bg/80 backdrop-blur-md flex flex-col items-center justify-center z-20">
                    <div className="w-16 h-16 border-4 border-accent border-t-transparent rounded-full animate-spin mb-6"></div>
                    <p className="text-accent text-2xl font-bold animate-pulse tracking-wide italic text-center px-8">
                      Chalksmith.ai is crafting your {format === 'manim' ? 'video' : format === 'p5.js' ? 'interactive display' : 'presentation'}...
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </Panel>

        <Separator className="w-1 bg-border/20 hover:bg-accent/40 transition-colors cursor-col-resize shadow-[inset_0_0_1px_rgba(255,255,255,0.05)]" />

        {/* Right: Interaction Panel */}
        <Panel 
          panelRef={panelRef}
          collapsible 
          collapsedSize="75px"
          onResize={(size) => {
            if (size.asPercentage <= 4) {
              setIsCollapsed(true);
            } else {
              setIsCollapsed(false);
            }
          }}
          minSize="15%" 
          maxSize="50%" 
          defaultSize="25%"
          id="right-panel"
        >
          <div className="flex flex-col h-full bg-secondary-bg border-l border-border overflow-hidden">
            {isCollapsed ? (
              <div className="flex flex-col items-center justify-end p-4 m-1 shrink-0">
                <button
                  className="p-2 hover:bg-surface/50 rounded-lg text-secondary-text transition-colors" 
                  onClick={togglePanel}
                >
                  <PanelRight size={20} />
                </button>
              </div>
            ) : (
              <div className="flex flex-col h-full min-w-0">
                <div className="flex flex-row items-center justify-between p-4 m-1 gap-4 shrink-0">
                  <h2 className="text-lg font-semibold text-primary-text truncate whitespace-nowrap" title={title}>{title}</h2>
                  <button className="text-secondary-text hover:text-primary-text transition-colors">
                    <ChevronDown size={20} />
                  </button>
                  <button 
                    className="ml-auto p-2 hover:bg-surface/50 rounded-lg text-secondary-text transition-colors" 
                    onClick={togglePanel}
                  >
                    <PanelRight size={20} />
                  </button>
                </div>

                <Group orientation="vertical" id="interaction-layout">
                  {/* Chat History */}
                  <Panel minSize="30%">
                    <div className="h-full overflow-y-auto px-5 space-y-4 scroll-smooth">
                      {messages.length === 0 && (
                        <div className="bg-surface/30 p-4 rounded-2xl border border-border/50 text-secondary-text text-sm">
                          <p className="font-semibold mb-2 text-primary-text">Welcome to Chalksmith.ai!</p>
                          <ul className="space-y-2">
                            <li className="flex gap-2"><span>✨</span> Choose a topic and AI model</li>
                            <li className="flex gap-2"><span>✨</span> Select your favorite format</li>
                            <li className="flex gap-2"><span>✨</span> Watch your lesson come to life!</li>
                          </ul>
                        </div>
                      )}
                      {messages.map((msg, i) => (
                        <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
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
                          <div className="bg-surface/50 p-4 rounded-2xl rounded-tl-none text-secondary-text text-sm animate-pulse border border-border/50">
                            Thinking...
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
                        onModelChange={setModel}
                        onFormatChange={setFormat}
                        onTopicChange={setTopic}
                        disabled={loading}
                      />
                      
                      <Button 
                        variant="primary" 
                        onClick={generateLesson} 
                        isLoading={loading}
                        disabled={!topic || loading}
                        className="w-full h-12 text-lg shadow-lg shadow-accent/20 shrink-0"
                      >
                        Generate Material
                      </Button>

                      {error && (
                        <p className="text-xs text-red-500 bg-red-500/10 p-2 rounded border border-red-500/20 text-center">
                          {error}
                        </p>
                      )}
                    </div>
                  </Panel>
                </Group>
              </div>
            )}
          </div>
        </Panel>
      </Group>
    </main>
  );
}
