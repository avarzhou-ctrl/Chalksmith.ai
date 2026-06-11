// src/app/privacy/page.tsx
import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import { MDXRemote } from 'next-mdx-remote/rsc';
import '../markdown.css';

export default async function PrivacyPolicyPage() {
  // Locate the path to your Markdown file
  const filePath = path.join(process.cwd(), 'src/content/privacy-policy.md');
  
  // Read the raw text content of the file
  const fileContent = fs.readFileSync(filePath, 'utf8');
  
  // Parse the metadata (front matter) and the body text
  const { data, content } = matter(fileContent);

  return (
    <main className="max-w-4xl mx-auto px-6 py-12">
      {/* Page Header Headers */}
      <header className="border-b border-zinc-200 pb-6 mb-8">
        <h1 className="text-4xl font-bold tracking-tight text-zinc-900">{data.title}</h1>
        {data.lastUpdated && (
          <p className="text-sm text-zinc-500 mt-2">Last Updated: {data.lastUpdated}</p>
        )}
      </header>

      {/* Rendered Markdown Text with custom CSS class */}
      <article className="markdown-body">
        <MDXRemote source={content} />
      </article>
    </main>
  );
}