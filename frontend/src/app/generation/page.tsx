'use client'

import { useState } from "react";
import InputForm from "@/components/generation/InputForm";
import EditableTitle from "@/components/generation/EditableTitle";
import Button from "@/components/ui/Button";
import { createLesson, LessonResponse } from "@/lib/api";

export default function Page() {
  const [topic, setTopic] = useState('');
  const [model, setModel] = useState('Gemini 3 Flash');
  const [format, setFormat] = useState<'manim' | 'p5.js' | 'reveal.js'>('manim');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LessonResponse | null>(null);
  const [title, setTitle] = useState("Untitled Lesson Plan");

  const generateLesson = async () => {
    if (!topic || !model || !format) return;

    setLoading(true);
    setError(null);

    try {
      const response = await createLesson({ topic, model, format });
      setResult(response);
    } catch (err) {
      setError('Oops! Failed to generate lesson.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex flex-row h-screen w-full bg-primary-bg overflow-hidden">
      {/* Left: Preview */}
      <div className="flex flex-col h-full w-[70%] bg-primary-bg">
        {/* Title */}
        <div className="flex flex-row p-4 m-4 gap-4 shrink-0 items-center">
          <img src="/next.svg" alt="Logo" className="w-8 h-8 rounded-lg bg-white p-1"/>
          <EditableTitle initialTitle="Untitled" onChange={setTitle}/>
        </div>

        {/* Content */}
        <div className="flex flex-col flex-1 justify-center items-center px-8 relative">
          {result ? (
            <div className="w-full h-full bg-primary-bg rounded-xl border border-border shadow-2xl overflow-hidden group">
              {format == 'manim' ? (
                <video
                  key={result.url}
                  className="w-full h-full object-contain"
                  controls
                  autoPlay
                >
                  <source src={result.url} type="video/mp4" />
                  Your browser does not support the video tag.
                </video>
              ) : format == 'p5.js' ? (
                <iframe
                  key={result.url}
                  src={result.url}
                  className="w-full h-full bg-primary-text border-none"
                  title="Interactive Display Preview"
                />
              ) : (
                <iframe
                  key={result.url}
                  src={result.url}
                  className="w-full h-full bg-primary-text border-none"
                  title="Presentation Preview"
                />
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center gap-6 max-w-md animate-in fade-in zoom-in duration-700">
              <h2 className="text-center text-xl font-bold text-accent">
                Ready to bring your lesson to life?
              </h2>
              <p className="text-center text-secondary-text">
                Enter a topic in the chat panel on the right to generate a custom {format === 'manim' ? 'video' : format === 'p5.js' ? 'interactive display' : 'presentation'}!
              </p>
            </div>
          )}

          {loading && (
            <div className ="absolute inset-0 bg-primary-bg/80 backdrop-blur-md flex flex-col items-center justify-center z-20">
              <div className="w-16 h-16 border-4 border-accent border-t-transparent rounded-full animate-spin mb-6"></div>
              <p className="text-accent text-xl font-bold animate-pulse tracking-wide italic text-center">
                Crafting your {format === 'manim' ? 'video' : format === 'p5.js' ? 'interactive display' : 'presentation'} lesson...
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Right: Chat */}
      <div className="flex flex-col h-full w-[30%] bg-secondary-bg border-l border-border">
      </div>
    </main>
  )
}
