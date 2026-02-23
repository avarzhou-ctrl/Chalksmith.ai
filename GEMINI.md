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
- 

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
- Format: "**YYYY-MM-DD**: [Brief description of changes]"
- Ask if you should update the project log after major changes are made.

Example Project Log:
- **2026-02-23**: Initialized Next.js skeleton. Created `app/generation/page.tsx` with a 60/40 split.
- **2026-02-23**: Defined Tailwind color palette in `tailwind.config.ts` using Forest Sage (#2D6A4F) and Harvest Gold (#F59E0B).
- **2026-02-23**: Drafted Origami Fox mascot component in `components/ui/MascotIcon.tsx`.

# Project Log
- **2026-02-23**: Updated AGENTS.md with design system constants and logging requirements.