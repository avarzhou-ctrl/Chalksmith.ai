'use client'

import dynamic from 'next/dynamic';
import { useEffect, useState } from 'react';
import Button from '../ui/Button';
import { Code, Eye, MousePointerClick } from 'lucide-react';
import Skeleton, { SkeletonStatus } from '@/components/ui/Skeleton';

const CodeHighlighter = dynamic<{ sourceCode: string }>(async () => {
  const [{ Prism: SyntaxHighlighter }, { default: vscDarkPlus }] = await Promise.all([
    import('react-syntax-highlighter'),
    import('react-syntax-highlighter/dist/esm/styles/prism/vsc-dark-plus'),
  ]);

  return function HighlightedCode({ sourceCode }: { sourceCode: string }) {
    return (
      <SyntaxHighlighter
        language="javascript"
        style={vscDarkPlus}
        customStyle={{
          background: 'transparent',
          padding: '0',
          margin: '0',
          fontSize: '0.875rem',
          maxWidth: '100%',
          overflowX: 'auto',
        }}
      >
        {sourceCode}
      </SyntaxHighlighter>
    );
  };
}, {
  loading: () => (
    <section className="space-y-3" aria-busy="true">
      <Skeleton className="h-4 w-3/5" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-11/12" />
      <Skeleton className="h-4 w-4/5" />
      <SkeletonStatus>Loading code viewer</SkeletonStatus>
    </section>
  ),
});

interface CodeDrivenDemoProps {
  filePath: string;
}

function extractGeneratedCode(html: string) {
  const document = new DOMParser().parseFromString(html, 'text/html');
  const generatedScript = Array.from(document.querySelectorAll('script'))
    .reverse()
    .find((script) => !script.src && script.textContent?.trim());

  return generatedScript?.textContent?.trim() || html;
}

export default function CodeDrivenDemo({ filePath }: CodeDrivenDemoProps) {
  const [showCode, setShowCode] = useState(false);
  const [sourceCode, setSourceCode] = useState('');
  const [sourceError, setSourceError] = useState<string | null>(null);
  const [isMaterialLoaded, setIsMaterialLoaded] = useState(false);

  useEffect(() => {
    if (!showCode || sourceCode || sourceError) return;

    let isMounted = true;

    async function loadSourceCode() {
      try {
        setSourceError(null);
        const response = await fetch(filePath);

        if (!response.ok) {
          throw new Error('Unable to load source code.');
        }

        const code = extractGeneratedCode(await response.text());
        if (isMounted) {
          setSourceCode(code);
        }
      } catch (error) {
        if (isMounted) {
          setSourceError(error instanceof Error ? error.message : 'Unable to load source code.');
        }
      }
    }

    loadSourceCode();

    return () => {
      isMounted = false;
    };
  }, [filePath, showCode, sourceCode, sourceError]);

  return (
    <div className="min-w-0">
      <div className="w-full h-[28rem] max-w-full bg-primary-bg rounded-3xl overflow-hidden border border-border shadow-2xl relative flex flex-col sm:h-[32rem] lg:h-[36rem]">
        <div className="absolute top-4 right-4 z-10">
          <Button
            onClick={() => setShowCode(!showCode)}
            className={`flex items-center gap-2 text-sm px-3 py-1.5 rounded-lg border transition-all duration-200 backdrop-blur-md ${
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

        {!showCode && (
          <div className="group absolute bottom-4 left-4 z-10 flex cursor-default items-center gap-2 rounded-lg border border-accent bg-accent/90 shadow-lg shadow-accent/20 px-3 py-1.5 text-sm font-medium text-primary-text backdrop-blur-md">
            <MousePointerClick size={14} className="text-primary-text"/>
            <span>Try the slider in this preview!</span>
          </div>
        )}

        {showCode ? (
          <div className="min-w-0 min-h-full w-full overflow-auto bg-primary-bg p-8 font-mono text-sm">
            {sourceError ? (
              <p className="text-sm text-red-300">{sourceError}</p>
            ) : !sourceCode ? (
              <section className="space-y-3" aria-busy="true">
                <Skeleton className="h-4 w-3/5" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-11/12" />
                <Skeleton className="h-4 w-4/5" />
                <SkeletonStatus>Loading source code</SkeletonStatus>
              </section>
            ) : (
              <CodeHighlighter sourceCode={sourceCode} />
            )}
          </div>
        ) : (
          <>
            {!isMaterialLoaded && <Skeleton className="absolute inset-0 size-full rounded-none" />}
            <iframe
              title="Unit Circle and Sine Wave"
              src={filePath}
              loading="lazy"
              onLoad={() => setIsMaterialLoaded(true)}
              className={`h-full w-full border-none bg-primary-bg transition-opacity duration-300 ${isMaterialLoaded ? 'opacity-100' : 'opacity-0'}`}
              sandbox="allow-scripts"
            />
            {!isMaterialLoaded && <SkeletonStatus>Loading interactive preview</SkeletonStatus>}
          </>
        )}
      </div>
    </div>
  );
}
