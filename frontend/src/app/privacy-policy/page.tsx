import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import { marked } from 'marked';
import '../markdown.css'; 

export default async function PrivacyPolicyPage() {
  // Locate and read your file layout
  const filePath = path.join(process.cwd(), 'src/content/Privacy-Policy.md');
  const fileContent = fs.readFileSync(filePath, 'utf8');

  // Convert Markdown  into HTML
  const htmlContent = marked(fileContent);

  return (
    <main style={{ maxWidth: '42rem', margin: '0 auto', padding: '3rem 1.5rem' }}>
      <header style={{ borderBottom: '1px solid #e4e4e7', paddingBottom: '1.5rem', marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.25rem', fontWeight: 700, color: '#fafaf9' }}>Privacy Policy</h1>
        <p style={{ fontSize: '0.875rem', color: '#a8a29e', marginTop: '0.5rem' }}>Last Updated: June 11, 2026</p>
      </header>
      
      <article 
        className="markdown-body"
        style={{ color: '#fafaf9' }}
        dangerouslySetInnerHTML={{ __html: htmlContent }}
      />
    </main>
  );
}