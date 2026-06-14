IMAGE

# Chalksmith

[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-v0.110-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[*Chalksmith*](https://chalksmith.ai) is an AI-driven tool for generating code-driven educational STEM animations from natural language. Generate and **edit** lessons through simple prompts, balancing speed and **AI-transparency**.

Supported, exportable formats include:
* Interactive display (p5.js library)
* Presentation (reveal.js library)
* Video (Manim library)

*Disclaimer:* This website is currently in beta-testing stage, feel free the reach out with any errors.

## Examples

### Video Walkthrough
<div align="center">
  <video src="https://github.com/user-attachments/assets/be35e3f2-7c95-4cef-80a8-daf3e694acc8" width="100%" controls>
    Your browser does not support the video tag.
  </video>
</div>

### Lesson Examples
[**Examples**](https://chalksmith.ai/#examples)

### Sample Topics
* Fractions, Percentages, and Decimals
* Linear Equations
* The Pythagorean Theorem
* Experimental vs. Theoretical Probability
* Phases of the Moon
* Light Reflection and Refraction
* Heat Transfer via Convection
* States of Matter
* Bohr Model of the Atom (Protons, Neutrons, Electrons)
* Law of Conservation of Mass
* Photosynthesis Inputs and Outputs
* Food Web Energy Pyramid
* Natural Selection

## Motivation
Did you know **teachers** spend up to **12 hours** per week on lessons?—5 hours collecting resources, 7 hours building them from scratch. As a high schooler attending an international school with a highly diverse student body, I acutely perceived this issue, especially in STEM subjects where prior experience differed drastically.

From this issue emerged the incentive to create a solution. Over these past few months, I learned how to code, design, and deploy websites, and tested my website with over 50+ students and teachers across K12 grades.

## Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Next.js | User interface, state management, layouts |
| **Backend** | FastAPI | Compute engine, heavy rendering workflows |
| **Database** | Neon Postgres | Scalable relational data storage |
| **Authentication**| Clerk, Svix Webhooks | Secure authentication and account sync |

---

## Local Development Setup

Follow these steps to configure your local development environment. You will need both **Node.js (v18+)** and **Python (3.10+)** installed on your system.

### 1. Clone the Repository

Clone the project from GitHub and navigate into the root workspace directory:
```bash
git clone [https://github.com/avarzhou-ctrl/Chalksmith.ai.git](https://github.com/avarzhou-ctrl/Chalksmith.ai.git)
cd Chalksmith.ai
```

## 2. Environment Configuration
You need to establish local environment files for both layers to bridge network tokens and database connections.

### Frontend (.env.local)
Create a ```.env.local``` file inside the ```frontend/``` directory.

```bash
# Clerk Authentication Keys
NEXT_PUBLIC_ClERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
CLERK_WEBHOOK_SECRET=whsec_...

# Core Engine Connection
API_BASE_URL=http://localhost:8000
INTERNAL_BACKEND_SECRET=your_local_secure_bridge_token
```

### Backend (.env.local)
Create a ```.env.local``` file inside the ```backend/``` directory.
```bash
# LLM API keys
GEMINI_API_KEY=...

# Database
NEON_DATABASE_URL=postgresql://...

# Core Engine Connection
INTERNAL_BACKEND_SECRET=your_local_secure_bridge_token
FRONTEND_ORIGINS=http://localhost:3000
```

## 3. Spin Up the Frontend (Next.js)
Open a new terminal window, install the Node package modules, and spin up the local development serverless loop:
(Note: run commands from root)

```bash
cd frontend
npm install
npm run dev
```

The user interface will compile and initialize locally at ```http://localhost:3000``.

## 4. Spin Up the Backend (FastAPI)
Open a secondary terminal window to run your media compilation compute worker. Initialize a virtual environment, activate it, and launch the server instance:
(Note: run commands from root)

### macOS / Linux
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

### Windows (Command Prompt)
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

The FastAPI worker engine will start listening for proxied payload calls locally at ```http://localhost:8000```.

## 5. Local Webhook Testing Verification
Because Clerk webhooks require a public domain address to push account lifecycle mutations (```user.created```) down to your local loop, you must expose your local port securely.

For this step, please refer to Clerk's [syncing data with webhooks](https://clerk.com/docs/guides/development/webhooks/syncing) documentation!

## Contact
💬 **Contact us:** Feel free to reach out with any errors you encounter to our support email, [help@chalksmith.ai](mailto:help@chalksmith.ai)!

🖥️ **Author:** I'm [Ava Zhou](https://github.com/avarzhou-ctrl). I started building Chalksmith during my high school freshman year as part of a school project—marking my very first full-stack web application. The project grew from a curiosity about systems architecture and a desire to build real-world tools. Want to connect? Feel free to reach out at [avarzhou@gmail.com](mailto:avarzhou@gmail.com).
