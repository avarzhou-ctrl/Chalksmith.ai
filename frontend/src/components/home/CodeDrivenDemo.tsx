'use client'

import { useEffect, useState } from 'react';
import Button from '../ui/Button';
import { Code, Eye } from 'lucide-react';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

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

  useEffect(() => {
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
  }, [filePath]);

  return (
    <div className="min-w-0">
      <div className="w-full h-[28rem] max-w-full bg-primary-bg rounded-3xl overflow-hidden border border-border shadow-2xl relative flex flex-col sm:h-[32rem] lg:h-[36rem]">
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

        {showCode ? (
          <div className="min-w-0 min-h-full w-full overflow-auto bg-primary-bg p-8 font-mono text-sm">
            {sourceError ? (
              <p className="text-sm text-red-300">{sourceError}</p>
            ) : (
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
                {sourceCode || 'Loading source code...'}
              </SyntaxHighlighter>
            )}
          </div>
        ) : (
          <iframe
            title="Unit Circle and Sine Wave"
            src={filePath}
            className="w-full h-full border-none bg-primary-bg"
          />
        )}
      </div>
    </div>
  );
}
