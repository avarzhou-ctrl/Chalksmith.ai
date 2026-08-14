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
- Repository with independent runtimes: npm is scoped to `frontend/`; uv is scoped to `backend/`.
- Environment: Python virtual environment (.venv) for backend, Node.js for frontend.

### Design Style
- **Theme:** "Chalkboard Dark" - utilizing a stone-950/stone-800 background palette.
- **Accents:** Amber-600 (`#d97706`) used for highlights, primary buttons, and active states.
- **Typography:** Inter (sans-serif) as the primary font with stone-50/stone-400 text colors.
- **Layout:** 75/25 split for generation (Preview/Chat).

## Commands
### Backend
uv run --project backend uvicorn backend.app.main:app --reload

### Frontend
cd frontend && npm run dev

### GitHub Commits
When told to reformat commits, follow the Conventional Commits (https://www.conventionalcommits.org/en/v1.0.0/) format.

**Structure:** <type>[optional scope]: <description>
- **Type:** Define the nature of the change.
    * feat: Adding a new feature.
    * fix: Resolving a bug.
    * docs: Changes to documentation or README.
    * refactor: Code restructuring without changing behavior.
    * perf: Performance-related improvements.
    * test: Adding or updating tests.
- **Scope (optional):** The specific area of the project affected (api, auth, dashboard, db, frontend, generation, home, render, ui)
- **Summary:** A concise, imperative sentence (e.g., Add support for...). Use the imperative mood (e.g., "Add," not "Added").
- **Example:** "feat: allow provided config object to extend other configs"

## Boundaries
### Do
- use modular components that are written in `components/`
- use the Next.js App Router structure (e.g. `page.tsx`, `layout.tsx`)
- use only Tailwind CSS for styling

### Don't
- do not add new heavy dependencies without approval
- do not commit without permission
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
- After completing any coding or design task, you must add an entry to [CHANGELOG.md](CHANGELOG.md), not to this file. Include date, action, and files affected. Summarize why changes were made.
- Format: "**YYYY-MM-DD**: [Brief description of changes with which files were edited]"
- Newest entry first, directly under the format line at the top of the list.
- Ask if you should update the changelog after major changes are made.

### Example changelog entry
- **2026-02-23**: Initialized Next.js skeleton. Created `app/generation/page.tsx` with a 70/30 split.
- **2026-02-23**: Defined Tailwind color palette in `src/app/globals.css`.

