'use client'

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

import 'katex/dist/katex.min.css';

interface RenderedOutputProps {
    rawContent: string;
}

export default function RenderedOutput({ rawContent }: RenderedOutputProps) {
  return (
    <div className="prose max-w-none">
      <ReactMarkdown 
        remarkPlugins={[remarkMath]} 
        rehypePlugins={[rehypeKatex]}
      >
        {rawContent}
      </ReactMarkdown>
    </div>
  );
}