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
    - Animations: Manim Community Edition (https://www.manim.community/) (Mathematical Animation Engine)
    - Interactive Graphics: p5.js (https://p5js.org/)
    - Presentations: Reveal.js (https://revealjs.com/)
- Utilities: Uvicorn (ASGI server), python-dotenv, httpx, rich

### Frontend
- Located at `frontend/`
    - `fe/` - a semi-functional draft that you can READ from but do not EDIT.
- Framework: Next.js (https://nextjs.org/) (React 19)
- Language: TypeScript (https://www.typescriptlang.org/)
- Styling: Tailwind CSS (https://tailwindcss.com/) (v4)
- Routing: Next.js App Router (located in `src/app/`)

### Project Structure
- Monorepo: Separate `backend/` and `frontend/` directories.
- Environment: Python virtual environment (.venv).

### Design Style
- **Theme:** "Chalkboard Dark" - utilizing a stone-950/stone-800 background palette.
- **Accents:** Amber-600 (`#d97706`) used for highlights, primary buttons, and active states.
- **Typography:** Inter (sans-serif) as the primary font with stone-50/stone-400 text colors.
- **Layout:** 75/25 split for generation (Preview/Chat).

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