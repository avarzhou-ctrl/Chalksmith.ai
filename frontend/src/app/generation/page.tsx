'use client'

import { useState, useRef, useEffect } from "react";
import EditableTitle from "@/components/generation/EditableTitle";
import FormatOutput from "@/components/ui/FormatOutput";
import Button from "@/components/ui/Button";
import { LessonResponse, generateLessonStreaming, GenerationStatus, deleteLesson, fetchLessonById, renameLesson } from "@/lib/api";
import { Panel, Group, Separator } from "react-resizable-panels";
import { Eye, Code, Flame, Download, TriangleAlert, Loader2 } from "lucide-react";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import Modal from "@/components/ui/Modal";
import { Player } from '@remotion/player';
import { RemotionVideo } from '@/components/generation/RemotionVideo';
import GenerationSidebar from "@/components/generation/GenerationSidebar";

function isAuthGenerationError(error: string | null, status: GenerationStatus | null) {
  const message = error?.toLowerCase().trim();
  return Boolean(
    status?.upstreamStatus === 401 ||
    status?.upstreamStatus === 403 ||
    message === 'unauthorized' ||
    message?.includes('session is not authorized')
  );
}

function getGenerationErrorMessage(error: string, status?: GenerationStatus) {
  if (isAuthGenerationError(error, status ?? null)) {
    return 'Your session is not authorized. Refresh the page or sign in again, then retry generation.';
  }

  return error;
}

export default function Page() {
  // State for lesson configuration and rendering results
  const [topic, setTopic] = useState('');
  const [model, setModel] = useState('gemini-3.5-flash');
  const [format, setFormat] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LessonResponse | null>(null);
  const [showCode, setShowCode] = useState(false);
  const [title, setTitle] = useState("Untitled");
  const [sourceFiles, setSourceFiles] = useState<File[]>([]);

  // Status and progress for streaming generation
  const [generationStatus, setGenerationStatus] = useState<GenerationStatus | null>(null);

  // State for chat-like interaction history and iterative editing
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant'; content: React.ReactNode }[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [currentlessonID, setCurrentLessonID] = useState<string | null>(null);
  const [initialTopic, setInitialTopic] = useState<string>('');
  const [isResetModalOpen, setIsResetModalOpen] = useState(false);
  const [isErrorModalOpen, setIsErrorModalOpen] = useState(false);
  
  // State for renaming
  const [renameError, setRenameError] = useState<string | null>(null);
  const [isRenaming, setIsRenaming] = useState(false);
  const [displayTitle, setDisplayTitle] = useState(title);

  // Ref to track the active EventSource cleanup function for mid-generation cancellation
  const generationCleanupRef = useRef<(() => void) | null>(null);

  const stopGeneration = () => {
    // Aborts the SSE connection and stops UI loading states immediately
    if (generationCleanupRef.current) {
      generationCleanupRef.current();
      generationCleanupRef.current = null;
    }
    setLoading(false);
    setGenerationStatus(null);
  };

  const handleFormatChange = (newFormat: string) => {
    // Reset lesson context when changing formats as cross-format editing is unsupported
    setFormat(newFormat);
    setCurrentLessonID(null); 
  }

  const handleModelChange = (newModel: string) => {
    // Reset lesson context when changing models to prevent unexpected context mixing
    setModel(newModel);
    setCurrentLessonID(null); 
  }

  const startNewLesson = async () => {
    // Ensure any ongoing generation is halted before clearing state
    stopGeneration();

    // If we have an active lesson, delete it from the backend to clean up database and storage
    if (currentlessonID) {
      try {
        await deleteLesson(currentlessonID);
      } catch (err) {
        console.error("Failed to delete lesson during reset:", err);
      }
    }

    // Clears all states to allow starting a fresh generation from scratch
    setCurrentLessonID(null);
    setResult(null);
    setTopic('');
    setInitialTopic('');
    setMessages([]);
    setTitle("Untitled");
    setSourceFiles([]);
    setError(null);
  }

  const panelRef = useRef<any>(null);
  const [isCollapsed, setIsCollapsed] = useState(false);

  const scrollToBottom = () => {
    // Standard chat UX to keep newest messages in view
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const togglePanel = () => {
    // Imperative API for react-resizable-panels to handle manual collapse/expand
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

  useEffect(() => {
    // Safety cleanup: ensure connections are closed if the user navigates away mid-generation
    return () => {
      if (generationCleanupRef.current) {
        generationCleanupRef.current();
      }
    };
  }, []);

  useEffect(() => {
    const lessonId = new URLSearchParams(window.location.search).get('lessonId');

    if (!lessonId) return;

    const loadSavedLesson = async () => {
      try {
        setLoading(true);
        setError(null);

        const lesson = await fetchLessonById(lessonId);

        setTitle(lesson.topic);
        setTopic('');
        setInitialTopic(lesson.topic);
        setModel(lesson.model);
        setFormat(lesson.format);
        setCurrentLessonID(lesson.id);
        setResult({
          id: lesson.id,
          url: lesson.url,
          code: lesson.code,
          summary: lesson.summary,
        });
        setMessages([
          {
            role: 'assistant',
            content: lesson.summary || `Loaded "${lesson.topic}".`,
          },
        ]);
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Failed to load lesson.';
        setError(errorMsg);
        setIsErrorModalOpen(true);
      } finally {
        setLoading(false);
      }
    };

    loadSavedLesson();
  }, []);

  useEffect(() => {
    setDisplayTitle(title);
  }, [title]);

  const generateLesson = async (overridePrompt?: string) => {
    // If overridePrompt is provided and is a string (Auto-Fix), use it; otherwise fallback to 'topic'
    const activePrompt = typeof overridePrompt === 'string' ? overridePrompt : topic;
    
    if (!activePrompt || typeof activePrompt !== 'string' || !model || !format || loading) return;

    setLoading(true);
    setError(null);
    setShowCode(false);
    setGenerationStatus({ status: 'initializing', message: 'Starting generation...', progress: 0 });
    
    // Add the prompt to the chat history so the user sees the 'Auto-Fix' request
    setMessages((prev) => [...prev, { role: 'user', content: activePrompt }]);

    try {
      // Initiate SSE connection to receive real-time progress updates during long-running generation tasks
      const cleanup = generateLessonStreaming(
        { 
          topic: currentlessonID ? initialTopic : activePrompt, 
          model, 
          format, 
          lesson_id: currentlessonID || undefined,
          prompt: currentlessonID ? activePrompt : undefined,
          sourceFiles
        },
        (status) => {
          // Update status state to drive the progress bar and stage indicators in the UI
          setGenerationStatus(status);
          
          if (status.status === 'complete' && status.result) {
            const completedLesson = status.result;
            setResult(completedLesson);
            if (completedLesson.id) {
              setCurrentLessonID(completedLesson.id);
            }
            
            if (currentlessonID) {
              setMessages((prev) => [...prev, { 
                role: 'assistant', 
                content: `Updated your lesson based on: "${activePrompt.substring(0, 50)}...".` 
              }]);
            } else {
              setInitialTopic(activePrompt);
              setMessages((prev) => [...prev, { 
                role: 'assistant', 
                content: (
                  <>
                  Success! Created your ${format === 'manim' ? 'video' : format === 'p5.js' ? 'interactive display' : 'presentation slides'} about "${activePrompt}".{' '}
                  <FormatOutput rawContent={completedLesson.summary} />
                  </>
                )
              }]);
            }
            
            setLoading(false);
            generationCleanupRef.current = null;
            setSourceFiles([]);
            if (!overridePrompt) {
              setTopic('');
            }
          }
        },
        (errMsg, status) => {
          // Handle connection-level errors (e.g. timeout or network drop)
          const errorMsg = getGenerationErrorMessage(errMsg, status);
          if (status) {
            setGenerationStatus(status);
          }
          setError(errorMsg);
          setIsErrorModalOpen(true); 
          setMessages((prev) => [...prev, { role: 'assistant', content: `Error: ${errorMsg}` }]);
          setLoading(false);
          generationCleanupRef.current = null;
        }
      );

      // Store the cleanup function so we can manually abort if the user clicks Stop or Reset
      generationCleanupRef.current = cleanup;

    } catch (err: any) {
      const errorMsg = err.message || 'Oops! Failed to generate lesson.';
      setError(errorMsg);
      setIsErrorModalOpen(true); 
      setMessages((prev) => [...prev, { role: 'assistant', content: `Error: ${errorMsg}` }]);
      setLoading(false);
      generationCleanupRef.current = null;
    }
  }

  const isAuthError = isAuthGenerationError(error, generationStatus);

  const prepareFixPrompt = () => {
    // Direct trigger for Auto-Fix without filling the textarea
    const msg = error || "The code failed to render.";
    const fixPrompt = `The previous generation failed with this error: "${msg}". Please fix the code and return the complete, corrected version.`;
    generateLesson(fixPrompt);
  }

  const handleRenameLesson = async (newTitle: string, id: string) => {
    const trimmedTitle = newTitle.trim();

    if (!trimmedTitle || trimmedTitle === title || !id) {
      return;
    }

    try {
        setRenameError(null);
        setIsRenaming(true);
        await renameLesson(id, trimmedTitle);
        setTitle(trimmedTitle);
        setDisplayTitle(trimmedTitle);
      } catch (error) {
        setRenameError(error instanceof Error ? error.message : 'Failed to rename lesson');
      } finally {
        setIsRenaming(false);
      }
    };

  return (
    <main className="app-route-without-site-header flex flex-row h-screen w-full bg-primary-bg overflow-hidden font-sans text-primary-text">
      <Group orientation="horizontal" id="main-layout">
        {/* Left: Preview */}
        <Panel defaultSize="75%" minSize="50%">
          <div className="flex flex-col h-full bg-primary-bg">
            {/* Header Bar */}
            <div className="flex flex-row p-4 m-1 gap-4 shrink-0 items-end">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center overflow-hidden mb-1">
                <a href="https://app.chalksmith.ai/home">
                  <img src="/logo.png" alt="Logo" className="w-8 h-8 object-contain" />
                </a>
              </div>
              <EditableTitle
                initialTitle={displayTitle}
                onChange={(newTitle) => {
                  if (result?.id) {
                    handleRenameLesson(newTitle, result.id);
                  } else {
                    setTitle(newTitle);
                  }
                }}
              />
              <div className="flex gap-2 pb-1">
                <Button 
                  variant="outline" 
                  size="sm" 
                  title="Create new canvas"
                  onClick={() => setIsResetModalOpen(true)}
                  className="gap-1.5 h-8.5 px-3 py-1.5"
                >
                  <Flame size={14} />
                  <span>Create New</span>
                </Button>
                {result && (
                  <a
                    href={`/api/lesson-export?id=${result.id}`}
                    download
                    className="flex items-center text-xs font-medium gap-1.5 h-8.5 px-3 py-1.5 rounded-xl border border-border bg-transparent text-secondary-text hover:border-accent hover:text-accent transition-all duration-300"
                    title={`Download ${format === 'remotion' || format === 'manim' ? 'Video'
                                     : 'HTML'}`}
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
                          language={format === 'remotion' ? 'json' : format === 'manim' ? 'python' : format === 'p5.js' ? 'javascript' : 'html'}
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
                        ) : format === 'remotion' ? (
                          <div className="w-full h-full bg-stone-950 overflow-hidden flex flex-col items-center relative group">
                            {(() => {
                              try {
                                const lessonData = JSON.parse(result.code);
                                // Total frames calculated from dynamic scenes to tell Remotion when to stop/loop
                                const totalFrames = lessonData.scenes.reduce(
                                  (acc: number, s: any) => acc + (s.durationInSeconds || 5) * 30, 
                                  0
                                );

                                return (
                                  <Player
                                    component={RemotionVideo}
                                    inputProps={{ scenes: lessonData.scenes }}
                                    durationInFrames={Math.max(1, totalFrames)}
                                    fps={30}
                                    compositionWidth={1920}
                                    compositionHeight={1080}
                                    style={{ 
                                      width: '100%', 
                                      height: '100%',
                                      backgroundColor: '#0c0a09'
                                    }}
                                    controls
                                    autoPlay
                                    loop
                                  />
                                );
                              } catch (e: any) {
                                // Capture the parsing error so it can be sent back to the LLM
                                const parseError = e.message || "Invalid JSON structure";
                                if (error !== parseError) {
                                  setError(parseError);
                                }
                                return (
                                  <div className="flex flex-col items-center justify-center h-full p-10 text-center text-secondary-text">
                                    <TriangleAlert size={48} className="mb-4 text-accent/50" />
                                    <p className="mb-4">Failed to load video blueprint.</p>
                                    <Button 
                                      variant="outline"
                                      size="sm"
                                      onClick={() => setIsErrorModalOpen(true)}
                                      className="gap-2"
                                    >
                                      <TriangleAlert size={14} />
                                      <span>View Error Details</span>
                                    </Button>
                                  </div>
                                );
                              }
                            })()}
                          </div>
                        ) : (
                          // Iframes used to isolate p5.js and Reveal.js scripts from the main app's runtime
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
                  <div className ="absolute inset-0 bg-primary-bg/90 backdrop-blur-xl flex flex-col items-center justify-center z-50 p-8">
                    <div className="w-full max-w-md flex flex-col items-center">
                      <div className="relative mb-12">
                         <div className="w-24 h-24 border-b-2 border-accent rounded-full animate-spin"></div>
                         <div className="absolute inset-0 flex items-center justify-center">
                            <Flame className="text-accent animate-pulse" size={32} />
                         </div>
                      </div>
                      
                      <h2 className="text-accent text-3xl font-bold mb-2 text-center tracking-tight">
                        Chalksmith.ai
                      </h2>
                      
                      <p className="text-secondary-text text-sm mb-8 text-center font-medium uppercase tracking-widest opacity-80">
                        Crafting your {format === 'manim' ? 'video' : format === 'p5.js' ? 'interactive display' : 'presentation'}...
                      </p>

                      <div className="w-full bg-surface/50 rounded-full h-1.5 mb-4 overflow-hidden border border-border/30">
                        <div 
                          className="bg-accent h-full transition-all duration-500 ease-out shadow-[0_0_10px_rgba(217,119,6,0.5)]" 
                          style={{ width: `${generationStatus?.progress || 0}%` }}
                        ></div>
                      </div>

                      <div className="flex justify-between w-full text-[10px] font-bold uppercase tracking-tighter text-secondary-text mb-12 px-1">
                        <span className={generationStatus?.progress && generationStatus.progress >= 25 ? 'text-accent' : 'opacity-40'}>Planning</span>
                        <span className={generationStatus?.progress && generationStatus.progress >= 50 ? 'text-accent' : 'opacity-40'}>Generating</span>
                        <span className={generationStatus?.progress && generationStatus.progress >= 75 ? 'text-accent' : 'opacity-40'}>Rendering</span>
                        <span className={generationStatus?.progress && generationStatus.progress >= 100 ? 'text-accent' : 'opacity-40'}>Finishing</span>
                      </div>

                      <div className="flex flex-col items-center gap-6">
                        <div className="flex items-center gap-3 bg-accent/10 border border-accent/20 px-5 py-3 rounded-2xl animate-in fade-in slide-in-from-bottom-2 duration-500">
                          <Loader2 className="text-accent animate-spin" size={16} />
                          <p className="text-accent text-sm font-medium italic">
                            {generationStatus?.message || "Preparing..."}
                          </p>
                        </div>
                      </div>
                    </div>
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
          collapsible={true} 
          collapsedSize="80px"
          onResize={(size) => {
            if (size.asPercentage < 15) {
              setIsCollapsed(true);
            } else {
              setIsCollapsed(false);
            }
          }}
          minSize="20%" 
          maxSize="30%" 
          defaultSize="25%"
          id="right-panel"
        >
          <GenerationSidebar
            isCollapsed={isCollapsed}
            onToggle={togglePanel}
            title={title}
            messages={messages}
            loading={loading}
            messagesEndRef={messagesEndRef}
            model={model}
            format={format}
            topic={topic}
            onModelChange={handleModelChange}
            onFormatChange={handleFormatChange}
            onTopicChange={setTopic}
            onGenerate={generateLesson}
            onStopGenerate={stopGeneration}
            sourceFiles={sourceFiles}
            onSourceFilesChange={setSourceFiles}
            currentLessonId={currentlessonID}
            error={error}
            generationStatus={generationStatus}
          />
        </Panel>
      </Group>

      {/* Create New Confirmation Modal */}
      <Modal 
        isOpen={isResetModalOpen} 
        onClose={() => setIsResetModalOpen(false)} 
        title="Create new canvas?"
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
              Close
            </Button>
            <Button 
              variant="primary" 
              className="w-full bg-accent hover:bg-amber-700 border-none" 
              onClick={() => {
                startNewLesson();
                setIsResetModalOpen(false);
              }}
            >
              Create New
            </Button>
          </div>
        </div>
      </Modal>

      {/* Blueprint Error Modal */}
      <Modal 
        isOpen={isErrorModalOpen} 
        onClose={() => setIsErrorModalOpen(false)} 
        title={isAuthError ? "Session Required" : "Blueprint Error"}
      >
        <div className="flex min-h-0 flex-col items-center">
          <div className="w-12 h-12 bg-red-500/10 rounded-full flex items-center justify-center mb-4">
            <TriangleAlert className="text-accent" size={24} />
          </div>
          <p className="mb-4 text-center text-sm wrap-break-words">
            {isAuthError
              ? error
              : <>Unfortunately Chalksmith generated an invalid lesson because of {error}. Click Auto-Fix to have Chalksmith attempt to correct the issue, or view the source code to debug further.</>}
          </p>
          
          {!isAuthError && result && (
            <div className="mb-6 min-h-0 w-full">
              <p className="text-xs font-semibold text-secondary-text mb-2 uppercase tracking-wider">Source Code:</p>
              <pre className="max-h-64 overflow-auto whitespace-pre-wrap wrap-break-words rounded-xl border border-white/5 bg-black/40 p-4 text-left font-mono text-[10px] text-amber-400">
                {result.code}
              </pre>
            </div>
          )}

          <div className="flex w-full shrink-0 flex-row gap-3">
            <Button 
              variant="secondary" 
              className="w-full" 
              onClick={() => setIsErrorModalOpen(false)}
            >
              Close
            </Button>
            {isAuthError ? (
              <Button
                variant="primary"
                className="w-full bg-accent hover:bg-amber-700 border-none gap-2"
                onClick={() => window.location.reload()}
              >
                Refresh
              </Button>
            ) : (
              <Button 
                variant="primary" 
                className="w-full bg-accent hover:bg-amber-700 border-none gap-2" 
                onClick={() => {
                  prepareFixPrompt(); 
                  setIsErrorModalOpen(false);
                }}
              >
                Auto-fix
              </Button>
            )}
          </div>
        </div>
      </Modal>
    </main>
  );
}
