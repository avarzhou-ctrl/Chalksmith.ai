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

## Commands
### Backend
uvicorn backend.main:app --reload

### Frontend
npm run dev

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
- After completing any coding or design task, you must update the "# Project Log" section of this file. Include date, action, and files affected. Summarize why changes were made.
- Format: "**YYYY-MM-DD**: [Brief description of changes with which files were edited]"
- Ask if you should update the project log after major changes are made.

### Example Project Log
- **2026-02-23**: Initialized Next.js skeleton. Created `app/generation/page.tsx` with a 70/30 split.
- **2026-02-23**: Defined Tailwind color palette in `src/app/globals.css`.

# Project Log
- **2026-06-25**: Connected temporary PDF source uploads to lesson generation by replacing `backend/services/sources.py` with a LangChain/PyMuPDF extractor, adding multipart POST streaming generation in `backend/routers/lesson.py`, passing source context through `backend/services/llm.py`, fixing the source preview route in `backend/routers/sources.py`, and adding source-upload dependencies to `backend/requirements.txt`.
- **2026-06-25**: Tightened the physics p5.js sidebar in `frontend/public/ex_interactive.html` by reducing control spacing, widening the sidebar, shortening the instruction text, and compacting the formula copy so bottom-left text stays inside the scaled 16:9 shell.
- **2026-06-25**: Applied the same internal responsive scaling approach to the physics p5.js lab in `frontend/public/ex_interactive.html`, fitting the sidebar and canvas to a 16:9 shell and remapping pointer coordinates so dragging still works after scaling.
- **2026-06-25**: Moved p5.js example scaling from the iframe shell into `frontend/public/ex_interactive.html` by fitting the 900x600 sketch to the carousel iframe at runtime and scaling the p5-created controls with the same layout; restored the carousel iframe in `frontend/src/components/home/ExamplesCarousel.tsx` to normal sizing.
- **2026-06-25**: Scaled only the p5.js example preview in `frontend/src/components/home/ExamplesCarousel.tsx` by rendering the interactive iframe larger and applying a 0.8 transform inside the shared 16:9 frame.
- **2026-06-25**: Updated `frontend/src/components/home/ExamplesCarousel.tsx` so video, p5.js interactive, and Reveal.js slide examples all use the same 16:9 media frame ratio.
- **2026-06-25**: Scaled down the drawn clock and timeline icons in the new elapsed-time p5.js example at `frontend/public/ex_interactive.html`, including the clock face, tick marks, hands, center pin, timeline nodes, active tracker, and arrowheads.
- **2026-06-25**: Scaled down the p5.js example sidebar and controls in `frontend/public/ex_interactive.html`, including narrower sidebar sizing, smaller slider thumbs, tighter buttons/stats, and a smaller draggable laser source.
- **2026-06-25**: Reapplied proportional scaling to the restored original p5.js interactive in `frontend/public/ex_interactive.html`, reducing the ray length, arcs, labels, ray widths, pulse dots, and draggable laser source while preserving the restored control styling.
- **2026-06-25**: Scaled down the p5.js optical scene in `frontend/public/ex_interactive.html` by reducing ray length, arc size, label size, ray stroke widths, pulse markers, and the draggable laser source so the interactive has more breathing room in the examples carousel.
- **2026-06-25**: Tightened the carousel example assets in `frontend/public/ex_interactive.html` and `frontend/public/ex_slides.html`, and adjusted `frontend/src/components/home/ExamplesCarousel.tsx` so p5.js controls, canvas content, and Reveal.js slides fit inside the homepage examples frame.
- **2026-06-25**: Added an examples carousel to the homepage with `frontend/src/components/home/ExamplesCarousel.tsx`, wired it into `frontend/src/app/page.tsx`, and added `frontend/public/example_reveal.html` so examples can show Manim video, p5.js, and Reveal.js formats.
- **2026-06-25**: Adjusted the connect section alignment in `frontend/src/app/about/page.tsx` so the contact text sits higher while staying visually centered with the books image.
- **2026-06-25**: Fixed the about page Substack contact icon in `frontend/src/app/about/page.tsx` by switching from an unloaded Bootstrap Icons class to a Font Awesome icon, and removed the invalid jsDelivr stylesheet link from `frontend/src/app/layout.tsx`.
- **2026-06-25**: Reworked the about page contact section in `frontend/src/app/about/page.tsx` into a left-side social contact list with the book image on the right, and restored the landing page footer on the about page.
- **2026-06-25**: Enlarged the about page portrait in `frontend/src/app/about/page.tsx` and made its desktop frame stretch to match the height of the adjacent founder text.
- **2026-06-25**: Rebuilt the about page in `frontend/src/app/about/page.tsx` with valid JSX styling, a polished chalkboard-themed founder layout, and Font Awesome icon usage loaded from `frontend/src/app/layout.tsx`.
- **2026-06-20**: Constrained `frontend/src/components/ui/Modal.tsx` to a viewport-safe maximum height with an internal scroll area, and tightened the generation error modal in `frontend/src/app/generation/page.tsx` so long error/source text scrolls without overflowing off-screen.
- **2026-06-20**: Moved `/api/lesson-generate` authentication into `frontend/src/app/api/lesson-generate/route.ts` and removed it from the protected lesson API proxy matcher in `frontend/src/proxy.ts` so EventSource generation failures return SSE error payloads instead of Clerk middleware 404 HTML responses.
- **2026-06-20**: Updated `deploy/daemontools/chalksmith-backend/run` so the VPS backend service binds to `0.0.0.0` for direct network exposure instead of loopback-only access.
- **2026-06-20**: Added daemontools deployment support for the FastAPI backend with `deploy/daemontools/chalksmith-backend/run`, `deploy/daemontools/chalksmith-backend/log/run`, and `scripts/server/chalksmith-backend`, guarded macOS-only `pyobjc` requirements, and updated the NumPy pin in `backend/requirements.txt` so Ubuntu Python 3.12 installs can complete.
- **2026-06-19**: Added a diagram-backed bullet-point architecture section in `README.md` that embeds `Architecture.png` and explains how the Next.js frontend, FastAPI backend, Neon database, Clerk/Svix auth flow, LLM providers, and rendering pipelines work together.
- **2026-06-14**: Updated `frontend/src/app/api/lesson-generate/route.ts` so generation proxy failures are returned as SSE error messages instead of JSON responses that EventSource reports only as a generic connection error, and recorded the change in `AGENTS.md`.
- **2026-06-13**: Added a shared auth redirect target in `frontend/src/lib/auth-redirects.ts`, wired marketing sign-up buttons in `frontend/src/app/page.tsx`, `frontend/src/app/layout.tsx`, and `frontend/src/components/home/ProfileLink.tsx` to send completed sign-up/sign-in flows directly to the app generation page, updated the dashboard create-new link in `frontend/src/app/dashboard/page.tsx`, restored `frontend/.env.example` with Clerk multi-domain notes, and allowed env example files in `.gitignore`.
- **2026-06-13**: Fixed saved lesson dashboard navigation crashing in `frontend/src/app/generation/page.tsx` by removing an invalid named `React` import, using named React hooks consistently, and guarding title rename handling until a loaded lesson result exists.
- **2026-06-13**: Added backend CRUD modules in `backend/crud/lessons.py` and `backend/crud/users.py`, moved lesson and user SQLModel database reads/writes out of `backend/routers/lesson.py` and `backend/routers/users.py`, and kept tenant-isolated lesson fetching in `get_user_lessons`.
- **2026-06-13**: Moved Clerk protection for lesson API routes into `frontend/src/proxy.ts`, added the trusted proxy auth header helper in `frontend/src/lib/auth-headers.ts`, and removed duplicated route-level `auth()` calls from `frontend/src/app/api/lesson-generate/route.ts`, `frontend/src/app/api/lesson-record/route.ts`, `frontend/src/app/api/lesson-list/route.ts`, `frontend/src/app/api/lessons/route.ts`, and `frontend/src/app/api/lesson-export/route.ts` so lesson handlers rely on proxy-verified identity without opening unauthenticated access.
- **2026-06-13**: Updated the homepage interaction cue hover styling in `frontend/src/components/home/CodeDrivenDemo.tsx` so it transitions into the same amber treatment as the material toggle.
- **2026-06-13**: Added a small interaction cue to `frontend/src/components/home/CodeDrivenDemo.tsx` so homepage visitors know they can try the embedded preview controls.
- **2026-06-13**: Added a strict Reveal.js screen containment rule in `backend/services/llm.py` so generated presentations keep all slide elements within the visible viewport instead of clipping or overflowing.
- **2026-06-13**: Fixed lesson generation finalization crashing with `name 'User' is not defined` by importing `User` in `backend/routers/lesson.py` before checking or lazily creating authenticated users.
- **2026-06-13**: Fixed missing icon assets by adding `frontend/public/favicon.ico` and pointing the Apple icon metadata in `frontend/src/app/layout.tsx` at `frontend/public/logo.png`.
- **2026-06-13**: Hardened Clerk webhook user syncing by updating `frontend/src/app/api/webhooks/clerk/route.ts` to verify the raw Svix request body, select Clerk's primary email address, and fail clearly when backend webhook env vars are missing; updated `backend/routers/users.py` to avoid logging internal secrets and report missing webhook auth configuration.
- **2026-06-12**: Fixed Clerk `UserButton` dark styling in `frontend/src/app/layout.tsx` by importing the `dark` theme object from `@clerk/themes` instead of passing the ignored string value, and removed the unused `ProfileLink` import.
- **2026-06-12**: Fixed signed-in users being redirected to sign-in from marketing app links by reordering `frontend/src/proxy.ts` so `chalksmith.ai/generation` and `chalksmith.ai/dashboard` redirect to `app.chalksmith.ai` before Clerk route protection runs.
- **2026-06-12**: Fixed the homepage code-driven demo by updating `frontend/src/components/home/CodeDrivenDemo.tsx` to reuse the generation page's code toggle appearance, show a title/description header, extract the embedded p5.js source for matching syntax colors, keep code overflow inside the demo frame, and updated `frontend/src/app/page.tsx` to render the demo.
- **2026-06-11**: Removed all subscription, billing, and Stripe-related code, database fields, and legal documentation. Retired usage tracking and quotas. Removed `ModelSelector` from the UI and set `gemini-3.5-flash` as the default model to simplify the generation flow.
- **2026-06-11**: Updated logo usage in `frontend/src/app/layout.tsx`, `frontend/src/app/page.tsx`, `frontend/src/app/generation/page.tsx`, and `frontend/src/components/dashboard/DashboardSidebar.tsx` to import the bundled asset from `frontend/src/content/logo.png` instead of referencing `/logo.png`.
- **2026-06-11**: Moved the generation input character counter inside the bottom-left of `frontend/src/components/generation/InputForm.tsx` and added bottom padding so the counter and submit/stop icon remain contained within the textarea without covering input text.
- **2026-06-11**: Added a 100-character topic/edit input limit in `frontend/src/components/generation/InputForm.tsx` with a visible character counter so generation prompts stay concise before submission.
- **2026-06-11**: Stopped hidden Remotion generation from fresh lessons by changing `frontend/src/app/generation/page.tsx` to default to the visible `manim` video format, aligning success/loading copy with the shown format options, and removing the stale Remotion option comment from `frontend/src/components/generation/FormatSelector.tsx`.
- **2026-06-11**: Reduced Remotion render memory pressure in `backend/services/render.py` by sanitizing generated scene props, lowering default render dimensions/FPS/concurrency, redirecting Remotion CLI logs to disk instead of memory, and tightened `backend/services/llm.py` Remotion prompts to keep generated videos within a smaller render budget.
- **2026-06-11**: Installed Vercel AI SDK streaming support by adding `ai` and `@ai-sdk/react` to `frontend/package.json` and creating `frontend/src/app/api/chat/route.ts`, an authenticated AI Gateway streaming route for Chalksmith STEM assistant responses.
- **2026-06-11**: Rebuilt the legal pages in `frontend/src/app/privacy-policy/page.tsx` and `frontend/src/app/terms-of-service/page.tsx` with matching dark layouts, all-white text styling, and table-of-contents links so the policy and terms pages share the same format without uninstalled markdown dependencies.
- **2026-06-10**: Finished lesson ownership enforcement by requiring authenticated user headers across `backend/routers/lesson.py`, scoping lesson fetch/edit/delete/list/export queries by `Lesson.user_id`, saving `user_id` on new generated lessons, forwarding Clerk user headers from `frontend/src/app/api/lesson-record/route.ts`, `frontend/src/app/api/lesson-list/route.ts`, and `frontend/src/app/api/lessons/route.ts`, and adding a `lesson.user_id` compatibility column check in `backend/database.py`.
- **2026-06-10**: Wired authenticated monthly lesson usage enforcement into the real generation flow by adding `backend/services/usage.py`, extending `backend/models.py` with `User.usage_month`, registering Neon-backed models in `backend/database.py`, applying quota checks in `backend/routers/lesson.py` and `backend/main.py`, forwarding Clerk user headers from `frontend/src/app/api/lesson-generate/route.ts` and `frontend/src/app/api/lesson-record/route.ts`, and adding the psycopg Postgres driver in `backend/requirements.txt`; new lessons count toward usage while edits with `lesson_id` do not.
- **2026-06-10**: Reworked `frontend/src/components/home/FireParticleBackground.tsx` into a Three.js interpretation of the golden-amber murmuration prompt: particles originate from the bottom-left, spiral across the hero, taper toward the top-right, and vary between sharp dense core lines and soft bokeh outer mist.
- **2026-06-10**: Deleted `frontend/src/components/home/ParticleWaveBackground.tsx` and ported the earlier canvas-based amber wave from commit `17c3510` into a Three.js `FireParticleBackground` using one `THREE.Points` buffer, GPU sine/cosine wave motion, visible amber sprite particles, and pointer repulsion; updated `frontend/src/app/page.tsx` to use it.
- **2026-06-10**: Removed a redundant incompatible Clerk `authObj.protect()` call from `frontend/src/proxy.ts` so the frontend build can type-check against the installed Clerk middleware API while preserving the existing `await auth.protect()` route protection.
- **2026-06-10**: Replaced the first homepage Three.js background with `frontend/src/components/home/ParticleWaveBackground.tsx`, a fresh visible amber particle wave that uses a single `THREE.Points` shader system and parts around the user pointer; updated `frontend/src/app/page.tsx` to render the new component.
- **2026-06-10**: Tuned the homepage Three.js particle shader in `frontend/src/components/home/MurmurationBackground.tsx` and adjusted the hero overlay in `frontend/src/app/page.tsx` so the landing page reads more like a dense amber school of fish moving in diagonal wave ribbons.
- **2026-06-10**: Added a shader-driven Three.js murmuration background in `frontend/src/components/home/MurmurationBackground.tsx`, installed `three` and `@types/three`, and updated `frontend/src/app/page.tsx` to render the optimized amber particle field behind the homepage hero.
- **2026-06-09**: Fixed the backend CORS defaults in `backend/main.py` so local development and Chalksmith production domains are allowed even when `FRONTEND_ORIGINS` is not set, while still allowing deployment-specific origins from the environment.
- **2026-06-09**: Added a frontend build-time Clerk environment check in `frontend/next.config.ts` and documented required deployment variables in `frontend/.env.example` so Vercel fails clearly when `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` is missing.
- **2026-06-09**: Fixed Render backend startup in `backend/main.py` by importing dotenv and defining the CORS origin regex, and added `beautifulsoup4` to `backend/requirements.txt` so the Manim docs startup helper has its explicit dependency in clean deploy builds.
- **2026-06-09**: Enhanced backend error logging in `backend/routers/content.py` and added a startup write-permission check for the `static/` directory in `backend/main.py` to diagnose post-deployment "Internal Server Error" issues.
- **2026-06-09**: Removed server-side Clerk `Show` usage from `frontend/src/app/layout.tsx` and `frontend/src/app/page.tsx`, moving signed-in UI checks to client-side Clerk hooks in `frontend/src/components/layout/ProfileLink.tsx` so the marketing homepage no longer triggers server auth middleware errors.
- **2026-06-09**: Removed the root layout server-side Clerk user lookup in `frontend/src/app/layout.tsx` and added `frontend/src/components/layout/ProfileLink.tsx` so the header avatar renders client-side without triggering `auth()` middleware detection errors.
- **2026-06-09**: Moved Clerk route protection and app subdomain routing into `frontend/src/proxy.ts` and removed `frontend/src/middleware.ts` so Next 16 uses a single proxy entrypoint for `app.chalksmith.ai` rewrites.
- **2026-06-09**: Updated `frontend/src/app/layout.tsx`, `frontend/src/app/globals.css`, `frontend/src/app/dashboard/page.tsx`, and `frontend/src/app/generation/page.tsx` so the root header sticks to the top, is hidden on app workspace pages, and links the signed-in profile image to `/dashboard`.
- **2026-06-09**: Linked the homepage "Build a lesson now" CTAs in `frontend/src/app/page.tsx` to Clerk sign-in for signed-out users while keeping signed-in users routed to `/generation`.
- **2026-06-09**: Hardened deployment API connectivity by normalizing backend CORS origins in `backend/main.py`, adding the same-origin streaming proxy `frontend/src/app/api/lesson-generate/route.ts`, and updating frontend API calls in `frontend/src/lib/api.ts`, `frontend/src/app/api/lesson-record/route.ts`, `frontend/src/app/api/lesson-list/route.ts`, and `frontend/src/app/api/lessons/route.ts` so lesson generation no longer depends on browser cross-origin SSE.
- **2026-06-09**: Reduced homepage particle background cost in `frontend/src/components/home/FireParticleBackground.tsx` by lowering particle count, capping animation to 24fps, using 1x canvas resolution, and removing blur/shadow filters.
- **2026-06-09**: Reworked the homepage particle background in `frontend/src/components/home/FireParticleBackground.tsx` into a coordinated golden-amber murmuration flow with sharp core particles and blurred outer mist.
- **2026-06-09**: Replaced the homepage fire particle emitter with a slow-moving amber particle wave in `frontend/src/components/home/FireParticleBackground.tsx` for a calmer chalkboard background effect.
- **2026-06-08**: Center-aligned the plus and equals operators with the Educator's Dilemma stat boxes in `frontend/src/app/page.tsx`.
- **2026-06-08**: Grouped the homepage footer Legal and Contact columns together on the right in `frontend/src/app/page.tsx` and restored the final CTA section closing wrappers.
- **2026-06-08**: Widened homepage footer column spacing in `frontend/src/app/page.tsx` so the Legal links sit farther from the Chalksmith copyright block.
- **2026-06-08**: Increased bottom spacing before the homepage footer in `frontend/src/app/page.tsx` so the final CTA has more visual breathing room.
- **2026-06-08**: Moved the homepage feature card JSX directly into the "Why choose Chalksmith?" section of `frontend/src/app/page.tsx` and removed the local `FeatureMockup` helper.
- **2026-06-08**: Inlined the homepage feature mockup component into `frontend/src/app/page.tsx` and deleted `frontend/src/components/home/HomepageMockups.tsx` to keep homepage-specific code in the route file.
- **2026-06-08**: Rebuilt the homepage from the Figma design in `frontend/src/app/page.tsx`, added `frontend/src/components/home/FireParticleBackground.tsx` for an interactive mouse-reactive fire particle canvas, and added `frontend/src/components/home/HomepageMockups.tsx` for product preview and feature panels with legal/footer links.
- **2026-06-08**: Added user-friendly LLM region/access error handling in `backend/services/llm.py` and updated frontend SSE handling in `frontend/src/lib/api.ts` and `frontend/src/app/generation/page.tsx` so blocked country/region provider errors show a clear message to users.
- **2026-06-08**: Added `.npmrc` and `frontend/.npmrc` to force npm to include optional native dependencies during deployment so packages like Lightning CSS install their Linux binaries on Vercel.
- **2026-06-08**: Fixed case-sensitive frontend import in `frontend/src/components/generation/InputForm.tsx` so the deployed build resolves the tracked `frontend/src/components/ui/Textarea.tsx` component on Linux/Vercel.
- **2026-05-12**: Connected dashboard lesson listing. Updated `backend/models.py` and `backend/routers/content.py` to return lesson metadata, added `frontend/src/app/api/lessons/route.ts` as the Next.js proxy, and updated `frontend/src/lib/api.ts`, `frontend/src/app/dashboard/page.tsx`, and `frontend/src/components/dashboard/LessonCard.tsx` so saved lessons render and can be deleted from the dashboard.
- **2026-05-12**: Added valid placeholder route components in `frontend/src/app/favorites/page.tsx` and `frontend/src/app/search/page.tsx` so the frontend build can type-check routes linked from the dashboard sidebar.
- **2026-05-12**: Tightened TypeScript narrowing in `frontend/src/app/generation/page.tsx` by storing completed lesson responses in a local constant before updating chat state.
- **2026-05-12**: Fixed `frontend/src/components/dashboard/LessonCard.tsx` header alignment so the ellipsis action stays on the right and normalized saved lesson format labels for dashboard cards.
- **2026-05-12**: Increased saved lesson title size in `frontend/src/components/dashboard/LessonCard.tsx` for stronger dashboard card hierarchy.
- **2026-05-12**: Scoped the lesson card navigation overlay in `frontend/src/components/dashboard/LessonCard.tsx` to each card by making the card positioned and layering controls above the link.
- **2026-05-12**: Anchored the saved lesson date/model row and trash action to the bottom of `frontend/src/components/dashboard/LessonCard.tsx` cards for more consistent card alignment.
- **2026-05-14**: Added a responsive ellipsis action dropdown in `frontend/src/components/dashboard/LessonCard.tsx` with open and delete buttons so card actions are grouped behind the menu.
- **2026-05-14**: Raised the lesson card action header layer in `frontend/src/components/dashboard/LessonCard.tsx` so the ellipsis dropdown renders above the description text.
- **2026-05-14**: Fixed the dashboard rename modal in `frontend/src/components/dashboard/LessonCard.tsx` by adding local title state for `EditableTitle` instead of referencing an undefined setter.
- **2026-05-14**: Tightened the rename modal footer spacing in `frontend/src/components/dashboard/LessonCard.tsx` so the close button sits closer to the modal bottom.
- **2026-05-18**: Completed the lesson rename pathway by adding `LessonRenameRequest` in `backend/models.py`, updating `backend/routers/content.py` to read rename JSON bodies, and wiring `frontend/src/components/dashboard/LessonCard.tsx` to call `renameLesson` with the lesson id and handle rename errors.
- **2026-05-18**: Renamed frontend proxy folders to `lesson-record` and `lesson-list`, removed the empty `lesson_by_id` proxy stub, fixed the single-lesson proxy GET to use id-based backend loading, and updated `frontend/src/app/generation/page.tsx` to hydrate lessons opened from dashboard card links.
