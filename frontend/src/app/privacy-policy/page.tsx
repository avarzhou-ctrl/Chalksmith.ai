// src/app/privacy-policy/page.tsx
import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import { marked } from 'marked';
import '../markdown.css'; 

export default async function PrivacyPolicyPage() {
  // 1. Locate and read your file layout
  const filePath = path.join(process.cwd(), 'src/content/Privacy-Policy.md');
  const fileContent = fs.readFileSync(filePath, 'utf8');
  
  // 2. Parse the front matter metadata and text body
  const { data, content } = matter(fileContent);

  // 3. Convert the Markdown body text directly into standard HTML
  const htmlContent = marked(content);

  return (
    <main style={{ maxWidth: '42rem', margin: '0 auto', padding: '3rem 1.5rem' }}>
      <header style={{ borderBottom: '1px solid #e4e4e7', paddingBottom: '1.5rem', marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.25rem', fontWeight: 700, color: '#18181b' }}>{data.title}</h1>
        {data.lastUpdated && (
          <p style={{ fontSize: '0.875rem', color: '#71717a', marginTop: '0.5rem' }}>Last Updated: {data.lastUpdated}</p>
        )}
      </header>

      {/* 4. Inject the raw static HTML safely into your styled article container */}
      <article 
        className="markdown-body"
        dangerouslySetInnerHTML={{ __html: htmlContent }}
      />
    </main>
  );
}