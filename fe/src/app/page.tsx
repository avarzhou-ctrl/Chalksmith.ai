// fe/src/app/page.tsx
'use client';

import { useState, useRef, useEffect } from 'react';
import { createLesson, LessonResponse } from '@/lib/api';

export default function Home() {
  const [topic, setTopic] = useState('');
  const [model, setModel] = useState('gpt-4o-mini');
  const [format, setFormat] = useState<'manim' | 'p5.js' | 'reveal.js'>('manim');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LessonResponse | null>(null);
  const [showCode, setShowCode] = useState(false);
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant'; content: string }[]>([]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleGenerate = async () => {
    if (!topic) return;

    setLoading(true);
    setError(null);
    setShowCode(false);
    setMessages((prev) => [...prev, { role: 'user', content: topic }]);

    try {
      const response = await createLesson({ topic, model, format });
      setResult(response);
      setMessages((prev) => [...prev, { role: 'assistant', content: `Generated content for "${topic}" using ${model} in ${format} format.` }]);
      setTopic('');
    } catch (err: any) {
      setError(err.message || 'An error occurred during generation.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex h-screen bg-stone-950 text-stone-50 overflow-hidden">
      {/* Left: Preview Area */}
      <section className="flex-1 flex flex-col border-r border-stone-800">
        <header className="p-4 border-b border-stone-800 flex justify-between items-center">
          <h2 className="font-semibold text-lg">Preview</h2>
          {result && (
             <div className="flex items-center gap-3">
               <button 
                 onClick={() => setShowCode(!showCode)}
                 className={`text-xs px-2 py-1 rounded transition-colors ${showCode ? 'bg-amber-600 text-white' : 'bg-stone-800 text-stone-400 hover:bg-stone-700'}`}
               >
                 {showCode ? 'View Material' : 'View Code'}
               </button>
               <div className="flex gap-2">
                 <span className="text-xs text-stone-400 bg-stone-900 px-2 py-1 rounded">Format: {format}</span>
                 <span className="text-xs text-stone-400 bg-stone-900 px-2 py-1 rounded">Model: {model}</span>
               </div>
             </div>
          )}
        </header>
        
        <div className="flex-1 bg-stone-900 flex items-center justify-center p-4 relative overflow-auto">
          {loading ? (
            <div className="flex flex-col items-center gap-4">
              <div className="w-12 h-12 border-4 border-amber-600 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-stone-400">Generating material...</p>
            </div>
          ) : result ? (
            <div className="w-full h-full flex flex-col">
              {showCode ? (
                <pre className="flex-1 p-6 text-xs font-mono text-stone-300 bg-black/50 rounded-lg overflow-auto border border-stone-800 whitespace-pre-wrap select-all">
                  <code>{result.code}</code>
                </pre>
              ) : (
                <>
                  {format === 'manim' ? (
                    <div className="flex-1 flex items-center justify-center">
                      <video key={result.url} controls className="max-w-full max-h-full rounded-lg shadow-2xl">
                        <source src={result.url} type="video/mp4" />
                        Your browser does not support the video tag.
                      </video>
                    </div>
                  ) : (
                    <div className="flex-1 w-full h-full bg-white rounded-lg overflow-hidden border border-stone-700">
                      <iframe src={result.url} className="w-full h-full border-none" title="Preview" />
                    </div>
                  )}
                </>
              )}
            </div>
          ) : (
            <div className="text-stone-500 text-center">
              <p className="text-xl font-light mb-2">No content generated yet.</p>
              <p className="text-sm">Enter a topic on the right to start generating.</p>
            </div>
          )}
        </div>

        {error && (
          <div className="p-4 bg-red-950/30 border-t border-red-900 text-red-400 text-sm">
            {error}
          </div>
        )}
      </section>

      {/* Right: Chat Interface */}
      <section className="w-96 flex flex-col bg-stone-950">
        <header className="p-4 border-b border-stone-800">
          <h1 className="text-xl font-bold text-amber-600">ClassKit Generator</h1>
        </header>

        <div className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth">
          {messages.length === 0 && (
            <div className="bg-stone-900/50 p-4 rounded-lg border border-stone-800 text-stone-400 text-sm">
              <p className="font-medium mb-1 text-stone-300">Tips:</p>
              <ul className="list-disc list-inside space-y-1">
                <li>Be specific about the topic</li>
                <li>Try different formats for different needs</li>
                <li>Manim is best for math animations</li>
                <li>reveal.js is best for slides</li>
                <li>p5.js is best for interactive visuals</li>
              </ul>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] p-3 rounded-2xl text-sm ${
                msg.role === 'user' 
                  ? 'bg-amber-600 text-white rounded-br-none' 
                  : 'bg-stone-800 text-stone-100 rounded-bl-none'
              }`}>
                {msg.content}
              </div>
            </div>
          ))}
          {loading && (
             <div className="flex justify-start">
               <div className="bg-stone-800 p-3 rounded-2xl rounded-bl-none text-stone-100 text-sm animate-pulse">
                 Thinking...
               </div>
             </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="p-4 border-t border-stone-800 space-y-4">
          <div className="grid grid-cols-2 gap-2">
             <select 
               value={format} 
               onChange={(e) => setFormat(e.target.value as any)}
               className="bg-stone-900 border border-stone-800 rounded px-2 py-1 text-xs outline-none focus:border-amber-600"
             >
               <option value="manim">Manim (Video)</option>
               <option value="reveal.js">reveal.js (Slides)</option>
               <option value="p5.js">p5.js (Interactive)</option>
             </select>
             <select 
               value={model} 
               onChange={(e) => setModel(e.target.value)}
               className="bg-stone-900 border border-stone-800 rounded px-2 py-1 text-xs outline-none focus:border-amber-600"
             >
               <option value="gpt-4o-mini">GPT-4o Mini</option>
               <option value="gpt-4o">GPT-4o</option>
               <option value="deepseek-chat">DeepSeek Chat</option>
               <option value="deepseek-reasoner">DeepSeek Reasoner</option>
               <option value="gemini-3-flash-preview">Gemini 3 Flash</option>
               <option value="ark-deepseek-chat">ARK DeepSeek Chat</option>
               <option value="ark-deepseek-reasoner">ARK DeepSeek Reasoner</option>
             </select>
          </div>
          
          <div className="flex gap-2">
            <textarea
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleGenerate();
                }
              }}
              placeholder="What do you want to learn?"
              className="flex-1 bg-stone-900 border border-stone-800 rounded-lg p-3 text-sm resize-none h-20 outline-none focus:border-amber-600 transition-colors"
              disabled={loading}
            />
          </div>
          <button
            onClick={handleGenerate}
            disabled={loading || !topic}
            className="w-full bg-amber-600 hover:bg-amber-700 disabled:bg-stone-800 disabled:text-stone-500 text-white font-medium py-2 rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            {loading ? 'Generating...' : 'Generate'}
          </button>
        </div>
      </section>
    </main>
  );
}
