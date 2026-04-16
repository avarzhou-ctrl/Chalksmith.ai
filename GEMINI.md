# AGENTS.md

## Project Structure
### Function
- code-driven teaching material generation website called "Chalksmith.ai".
    - calls LLM APIs to generate code which is rendered into videos and interactives demonstrations, based on a given prompt.
    - LLM options: Gemini 3 Flash Preview, Gemini 3 Pro Preview, GPT-4o Mini, GPT-4o, Deepseek Chat, Deepseek Reasoner, Ark Deepseek Chat, Ark Deepseek Reasoner.
- **Audience:** elementary and middle school teachers and students, with a specific focus on STEM subjects.

### Backend
- Located at `backend/`
- Language: Python
- Framework: FastAPI (https://fastapi.tiangolo.com/) (API handling)
- Database/ORM: SQLModel (https://sqlmodel.tiangolo.com/) (SQL databases in Python)
- AI/LLM Integration: OpenAI API, Google Generative AI (https://ai.google.dev/) (Gemini), and Volcengine (https://www.volcengine.com/) (Ark SDK)
- Content Generation & Rendering:
    - Animations: Remotion (https://www.remotion.dev/) (React-based Video Engine)
    - Interactive Graphics: p5.js (https://p5js.org/)
    - Presentations: Reveal.js (https://revealjs.com/)
- Utilities: Uvicorn (ASGI server), python-dotenv, httpx, rich

### Frontend
- Located at `frontend/`
    - `fe/` - a semi-functional draft that you can READ from but do not EDIT.
- Framework: Next.js (https://nextjs.org/) (React 19)
- Language: TypeScript (https://www.typescriptlang.org/)
- Styling: Tailwind CSS (https://tailwindcss.com/) (v4) and Framer Motion (animations)
- Routing: Next.js App Router (located in `src/app/`)

### Structure
- Monorepo: Managed via NPM Workspaces (root `package.json`).
- Environment: Python virtual environment (.venv) for backend, Node.js for frontend.

### Design Style
- **Theme:** "Chalkboard Dark" - utilizing a stone-950/stone-800 background palette.
- **Accents:** Amber-600 (`#d97706`) used for highlights, primary buttons, and active states.
- **Typography:** Inter (sans-serif) as the primary font with stone-50/stone-400 text colors.
- **Layout:** 75/25 split for generation (Preview/Chat).

###

## Commands
### Backend
uvicorn backend.main:app --reload

### Frontend
npm run dev

## Boundaries
### Do
- use modular components that are written in `components/`
- use the Next.js App Router structure (e.g. `page.tsx`, `layout.tsx`)
- use only Tailwind CSS for styling

### Don't
- do not add new heavy dependencies without approval
- do not commit API keys
- do not use divs when a component exists already 
- do not use px for spacing; use Tailwind's spacing scale (e.g., p-4, m-2)

### Safety & Permissions
Allowed without prompt:
- read files, list files

Ask first:
- package installs
- deleting files

## Documentation
- **Helpful Commenting:** Keep comments concise and focused on "Why" something is being done.
    - Use single-line explanations that provide context or reasoning.
    - Document non-obvious dependencies or system-level requirements.
    - Ensure comments are helpful for anyone who didn't write the code.
- After completing any coding or design task, you must update the "# Project Log" section of this file. Include date, action, and files affected. Summarize why changes were made.
- Format: "**YYYY-MM-DD**: [Brief description of changes with which files were edited]"
- Ask if you should update the project log after major changes are made.

### Example Project Log
- **2026-02-23**: Initialized Next.js skeleton. Created `app/generation/page.tsx` with a 70/30 split.
- **2026-02-23**: Defined Tailwind color palette in `src/app/globals.css`.

# Project Log
- **2026-02-23**: Updated AGENTS.md with design system constants and logging requirements.
- **2026-03-01**: Implemented `Dropdown.tsx` in `frontend/src/components/ui/` featuring state management, a click-outside listener, and a conditional "amber theme" triggered upon value selection. The component includes a disabled state and smooth animations.
- **2026-03-01**: Summarized existing UI components in `frontend/src/components/ui/`: `Button.tsx` (variant-based styles), `Dropdown.tsx` (stateful selection), and `Textarea.tsx` (chalkboard-themed input).
- **2026-03-02**: Debugged and updated `frontend/src/components/generation/ModelSelector.tsx`: integrated TypeScript types, aligned model selection with backend `llm.py` support (including Gemini, GPT-4o, DeepSeek, and Ark), and applied modular component architecture. Clarified roles of `Layout` vs `Page` components for orchestration.
- **2026-03-04**: Fixed syntax and type errors in `InputForm.tsx`, updated `Button.tsx` with loading states and standard event props, and implemented the backend communication layer in `api.ts`. Reverted `page.tsx` to its original state per user request.
- **2026-03-06**: Reorganized API architecture: migrated client-side utilities to `frontend/src/lib/api.ts`, implemented a server-side proxy in `frontend/src/app/api/lesson/route.ts`, and updated the frontend to use relative internal API paths. Removed redundant `frontend/src/app/api/route.ts`.
- **2026-03-08**: Completed `EditableTitle.tsx` and implemented `Card.tsx` component. Refactored `frontend/src/app/generation/page.tsx` into a Client Component with a 70/30 split layout, integrating dynamic content rendering for Manim (video) and p5.js/reveal.js (iframe). Updated `globals.css` with corrected Tailwind v4 theme variables.
- **2026-03-12**: Fixed Tailwind v4 rendering by renaming `postcss.config.ts` to `postcss.config.mjs` and correcting the theme block in `globals.css`. Relocated `public/` folder to the frontend root for Next.js compatibility. Implemented a 70/30 split UI with integrated chat history and preview state in `frontend/src/app/generation/page.tsx`, and reverted the root `page.tsx` to a placeholder. Refined `EditableTitle.tsx` for seamless header integration.
- **2026-03-13**: Debugged and stabilized the resizable panel layout in `frontend/src/app/generation/page.tsx`. Corrected `react-resizable-panels` exports and fixed component nesting. Implemented a "narrow rail" collapse feature for the right interaction panel using the `collapsedSize` prop and imperative `panelRef` API.
- **2026-03-14**: Configured NPM workspaces in the root `package.json` to resolve cross-package dependency issues and VS Code resolution errors. Stabilized the interaction panel collapse logic using percentage-based thresholds in `onResize` to prevent layout leaking during window resizing. Fixed critical syntax and indentation errors in `page.tsx` and integrated `framer-motion` (installed) for future UI enhancements.
- **2026-03-17**: Enhanced `InputForm.tsx` by embedding the generate button (CircleArrowUp icon) in the bottom-right of the textarea and implemented a robust disabled state. Added a "View Code/Material" toggle with relative positioning and a custom regex-based syntax highlighter in `frontend/src/app/generation/page.tsx`. Fixed background color issues in the content area for consistent scrolling.
- **2026-03-23**: Integrated `react-syntax-highlighter` into the "View Code" function in `frontend/src/app/generation/page.tsx`. Added dynamic language support for Manim (Python), p5.js (JavaScript), and Reveal.js (HTML) using the `vscDarkPlus` Prism theme. Replaced sparkle emojis (✨) in the chat history welcome message with `Flame` icons from `lucide-react` styled with the `text-accent` color.
- **2026-03-23**: Audited backend export strategies; confirmed `render_manim_lesson`, `render_p5js_lesson`, and `render_revealjs_lesson` correctly save assets to the `static/` directory and return valid absolute URLs. Removed the redundant and unused `backend/services/exporters/` directory to streamline the codebase.
- **2026-03-23**: Implemented a scalable `ExportService` in `backend/services/export.py` using a strategy pattern. Added a new `/content/export` GET endpoint in the backend and updated the `LessonResponse` model to include a unique lesson ID. Enhanced the frontend UI by adding an "Export" button in `frontend/src/app/generation/page.tsx`, allowing users to download generated lesson assets.
- **2026-03-23**: Fixed `PDFExportStrategy` in `backend/services/export.py` by making the export process asynchronous and correctly implementing the Playwright PDF conversion logic. Installed Chromium for Playwright on the server. Updated `backend/routers/content.py` to await the export preparation.
- **2026-03-23**: Refined export strategies: `reveal.js` presentations are now converted to PDF format using `playwright` for high-quality downloads, while `p5.js` remains as an interactive HTML export. Added `playwright` to `backend/requirements.txt`.
- **2026-04-10**: Implemented an iterative editing feature across the backend and frontend. Updated `backend/models.py`, `backend/services/llm.py`, and `backend/routers/content.py` to support lesson context and specific edit prompts. Outlined the frontend state management strategy in `page.tsx` to handle "New" vs. "Edit" modes using a `currentLessonId` state.
- **2026-04-12**: Fixed Python 3.9 compatibility issues in `backend/models.py` by replacing `|` with `Optional`. Resolved Gemini API SSL connection errors by removing redundant and problematic proxy manual environment setting in `backend/services/llm.py`. Fully implemented frontend "Edit Mode" in `frontend/src/app/generation/page.tsx` with `initialTopic` persistence and a "New Lesson" reset feature. Updated `InputForm.tsx` with dynamic mode-aware placeholders and disabled the `FormatSelector` during edits. Added `outline` variant and `size` support to `Button.tsx` to resolve TypeScript assignment errors. Updated `Dropdown.tsx` with refined `disabled` state styling (`text-stone-600`, `opacity-50`). Installed all backend dependencies (FastAPI, SQLModel, LLM SDKs, Manim, Playwright, etc.) and froze them into `backend/requirements.txt`.
- **2026-04-12**: Recovered project state following a git reset. Re-established NPM workspace structure by creating a root `package.json`. Reinstalled missing frontend dependencies (`react@19`, `react-dom@19`, `react-resizable-panels`, `lucide-react`) to fix broken builds. Restored Tailwind v4 styling by recreating `frontend/postcss.config.mjs`. Recreated the `Modal.tsx` component in `frontend/src/components/ui/` to restore the reset confirmation functionality.
- **2026-04-15**: Migrated the video generation engine from Manim to Remotion + KaTeX. Updated `llm.py` with a structured JSON prompt and `render.py` to handle `npx remotion render` calls. Implemented a frame-deterministic rendering engine in `RemotionVideo.tsx` using Remotion's native spring physics and `react-katex`. Integrated `@remotion/player` into the frontend for instant live previews. Updated `export.py` and the API router to support MP4 downloads and JSON blueprint fallbacks. Removed obsolete Manim compatibility layers and styling.
- **2026-04-16**: Resolved TypeScript module declaration error by installing `@types/react-katex`. Fixed a type mismatch in `frontend/src/remotion/Root.tsx` by making `scenes` optional in `RemotionVideoProps`.
- **2026-04-16**: Fixed critical "Internal Server Error" in Manim generation by recreating the broken Python virtual environment (`.venv`) and repairing local executable paths. 
- **2026-04-16**: Implemented a "Self-Correction Loop" in `backend/services/render.py` that captures Manim Tracebacks and feeds them back to the LLM for automatic debugging and retries.
- **2026-04-16**: Automated Manim Community documentation synchronization. Created `backend/services/fetch_docs.py` to scrape `docs.manim.community` and integrated it into the FastAPI `lifespan` event to ensure the LLM always has access to the latest v0.18+ API reference, reducing code hallucinations.
- **2026-04-16**: Automated the "Auto-Fix" functionality to trigger AI generation directly from the error modal without modifying the user's input field. Expanded the error modal's code preview to display the full source code without truncation, improving the debugging experience for malformed blueprints.
- **2026-04-16**: Fixed TypeScript error "Property 'summary' does not exist on type 'LessonResponse'" by updating the interface in `frontend/src/lib/api.ts` to include `summary` and making `id` required to match the backend model.
- **2026-04-16**: Re-initialized the SQLite database by deleting `backend/lessons.db` to resolve a schema mismatch where the `summary` column was missing in the existing table.
- **2026-04-16**: Fixed a critical bug in `backend/database.py` where models were not being registered with `SQLModel.metadata` because they weren't imported before `create_all()`. Added an explicit import of `Lesson` and debug prints for database URL and registered tables.
- **2026-04-16**: Verified the `lesson` table schema using `sqlite3` and confirmed the `summary` column exists. Successfully restarted the backend (uvicorn) ensuring the `lifespan` event correctly initializes the database on startup.