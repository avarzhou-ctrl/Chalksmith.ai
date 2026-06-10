'use client';

import { useState } from 'react';

export default function SimplePromptInput() {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!prompt.trim() || loading) return;
    setLoading(true);

    try {
      // Hit your local proxy endpoint. Middleware handles authorization checks transparently.
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt.trim() }),
      });

      const data = await response.json();
      console.log("Success:", data);
    } catch (err) {
      console.error("Submission failed:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <input
      type="text"
      value={prompt}
      onChange={(e) => setPrompt(e.target.value)}
      onKeyDown={(e) => e.key === 'Enter' && handleSubmit()} // Triggers on Enter key press
      placeholder="Generate a simulation..."
      className="bg-black text-white p-3 rounded border border-neutral-700"
      disabled={loading}
    />
  );
}