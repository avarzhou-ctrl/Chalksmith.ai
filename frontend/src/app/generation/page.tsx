'use client'

import { useState, useRef, useEffect, useMemo } from "react";
import InputForm from "@/components/generation/InputForm";
import EditableTitle from "@/components/generation/EditableTitle";
import Button from "@/components/ui/Button";
import { createLesson, LessonResponse } from "@/lib/api";
import { Panel, Group, Separator } from "react-resizable-panels";
import { PanelRight, ChevronDown, Code, Eye, Share, Flame, Download, Link, TriangleAlert } from "lucide-react";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import Modal from "@/components/ui/Modal";

export default function Page() {
  const [topic, setTopic] = useState('');
  const [model, setModel] = useState('gemini-3-flash-preview');
  const [format, setFormat] = useState('manim');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LessonResponse | null>(null);
  const [showCode, setShowCode] = useState(false);
  const [title, setTitle] = useState("Untitled");
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant'; content: string }[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [currentlessonID, setCurrentLessonID] = useState<string | null>(null);
  const [initialTopic, setInitialTopic] = useState<string>('');
  const [isResetModalOpen, setIsResetModalOpen] = useState(false);
  
  const handleFormatChange = (newFormat: string) => {
    setFormat(newFormat);
    setCurrentLessonID(null); // reset lesson ID when format changes
  }

  const handleModelChange = (newModel: string) => {
    setModel(newModel);
    setCurrentLessonID(null); // reset lesson ID when model changes
  }

  const startNewLesson = () => {
    setCurrentLessonID(null);
    setResult(null);
    setTopic('');
    setInitialTopic('');
    setMessages([]);
    setTitle("Untitled");
    setError(null);
  }

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
    if (!topic || !model || !format || loading) return;

    setLoading(true);
    setError(null);
    setShowCode(false);
    setMessages((prev) => [...prev, { role: 'user', content: topic }]);

    try {
      let response;

      if (currentlessonID) {
        // edit mode
        response = await createLesson({ 
          topic: initialTopic, 
          model, 
          format, 
          lesson_id: currentlessonID,
          prompt: topic
        });

        setMessages((prev) => [...prev, { 
          role: 'assistant', 
          content: `Updated your lesson based on: "${topic}".` 
        }]);
      } else {
        // new lesson mode
        setInitialTopic(topic);
        response = await createLesson({ topic, model, format });
        
        setMessages((prev) => [...prev, { 
          role: 'assistant', 
          content: `Success! Created your ${format === 'manim' ? 'video animation' : format === 'p5.js' ? 'interactive display' : 'presentation slides'} about "${topic}".` 
        }]);
      }

      // update visuals
      setResult(response);

      // save id
      if (response.id) {
        setCurrentLessonID(response.id);
      }

      // clear input box
      setTopic('');
    } catch (err: any) {
      setError(err.message || 'Oops! Failed to generate lesson.');
      setMessages((prev) => [...prev, { role: 'assistant', content: `Error: ${err.message || 'Failed to generate lesson.'}` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex flex-row h-screen w-full bg-primary-bg overflow-hidden font-sans text-primary-text">
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
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => setIsResetModalOpen(true)}
                  className="gap-1.5 h-8.5 px-3 py-1.5"
                >
                  <Flame size={14} />
                  <span>Reset</span>
                </Button>
                {result && (
                  <a
                    href={`http://localhost:8000/content/export?id=${result.id}`}
                    download
                    className="flex items-center text-xs font-medium gap-1.5 h-8.5 px-3 py-1.5 rounded border border-border bg-transparent text-secondary-text hover:border-accent hover:text-accent transition-all duration-300"
                    title={`Download ${format === 'manim' ? 'Video'
                                     : format === 'p5.js' ? 'HTML' 
                                     : 'PDF'}`}
                  >
                    <Download size={14} />
                    <span>Export</span>
                  </a>
                )}
              </div>
            </div>

            {/* Content Area */}
            <div className="flex flex-col flex-1 justify-center items-center px-4 pb-8 relative overflow-hidden">
              <div className="w-full h-full bg-primary-bg rounded-3xl overflow-auto border border-border shadow-2xl relative flex flex-col">
                {/* View Code Toggle */}
                {result && (
                  <div className="absolute top-4 right-4 z-10">
                    <Button 
                      onClick={() => setShowCode(!showCode)}
                      className={`flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg border transition-all duration-200 backdrop-blur-md ${
                        showCode
                          ? 'bg-accent/90 text-primary-text border-accent shadow-lg shadow-accent/20'
                          : 'bg-surface/80 text-secondary-text border-border hover:bg-surface hover:text-primary-text'
                        }`}            
                    >
                      {showCode ? (
                        <><Eye size={14} /> <span>View Material</span></>
                      ) : (
                        <><Code size={14} /> <span>View Code</span></>
                      )}
                    </Button>
                  </div>
                )}

                {result ? (
                  <div className="flex-1 w-full h-full bg-primary-bg overflow-auto">
                    {showCode ? (
                      <div className="min-w-full min-h-full bg-primary-bg p-8 font-mono text-sm">
                        <SyntaxHighlighter
                          language={format === 'manim' ? 'python' : format === 'p5.js' ? 'javascript' : 'html'}
                          style={vscDarkPlus}
                          customStyle={{
                            background: 'transparent',
                            padding: '0',
                            margin: '0',
                            fontSize: '0.875rem',
                          }}
                        >
                          {result.code}
                        </SyntaxHighlighter>
                      </div>
                    ) : (
                      <div className="w-full h-full flex flex-col items-center justify-center">
                        {format === 'manim' ? (
                          <video
                            key={result.url}
                            className="w-full h-full object-contain bg-black"
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
            if (size.asPercentage <= 15) {
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
                            <li className="flex gap-2"><Flame size={16} className="text-accent mt-0.5 shrink-0" /> Choose a topic and AI model</li>
                            <li className="flex gap-2"><Flame size={16} className="text-accent mt-0.5 shrink-0" /> Select your favorite format</li>
                            <li className="flex gap-2"><Flame size={16} className="text-accent mt-0.5 shrink-0" /> Watch your lesson come to life!</li>
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
                        onModelChange={handleModelChange}
                        onFormatChange={handleFormatChange}
                        onTopicChange={setTopic}
                        onGenerate={generateLesson}
                        disabled={loading}
                        isEditMode={!!currentlessonID}
                      />
                      
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

      {/* Reset Confirmation Modal */}
      <Modal 
        isOpen={isResetModalOpen} 
        onClose={() => setIsResetModalOpen(false)} 
        title="Clear Canvas?"
      >
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 bg-amber-500/10 rounded-full flex items-center justify-center mb-4">
            <TriangleAlert className="text-accent" size={24} />
          </div>
          <p className="mb-6 text-center">
            This will delete your current lesson and chat history. You cannot undo this action.
          </p>
          <div className="flex flex-row gap-3 w-full">
            <Button 
              variant="secondary" 
              className="w-full" 
              onClick={() => setIsResetModalOpen(false)}
            >
              Cancel
            </Button>
            <Button 
              variant="primary" 
              className="w-full bg-accent hover:bg-amber-700 border-none" 
              onClick={() => {
                startNewLesson();
                setIsResetModalOpen(false);
              }}
            >
              Clear All
            </Button>
          </div>
        </div>
      </Modal>
    </main>
  );
}
