# Project Rules for Antigravity & Gemini

> **Source of Truth:**
> - Development Lifecycle & Workflow Rules: [`DEVELOPMENT_WORKFLOW.md`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/DEVELOPMENT_WORKFLOW.md)
> - UX/UI Design Standards: [`UX_UI.md`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/UX_UI.md)
> - Agent Guidelines: [`AGENTS.md`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/AGENTS.md)

All agents working on this project MUST strictly follow the rules below:

1. **Development Mode as Default:** DO NOT package `.exe` or run release pipelines after routine coding. Run directly from source.
2. **Build vs Package:** `build` is for compiler/typecheck verification; `package` is for `.exe`. Never package `.exe` unless explicitly commanded by the user with keywords: `build exe`, `package`, `release`.
3. **Iterative Loop:** `Understand → Code → Targeted Validation → Build when needed → Restart/Reload → Health Check → Ready for User Test`.
4. **Idempotent Process Lifecycle:** Prevent duplicate instances. Use `RESTART.bat` (or `RESTART.bat frontend` / `backend`), `start.bat`, `stop.bat`, and `healthcheck.bat`. Ensure ports 8000 and 3000 are freed before re-binding. Logs are stored in `logs/services.log`.
5. **Mandatory Health Check:**
   - Backend: `http://127.0.0.1:8000/api/health` (`status: ok`, `database: connected`)
   - Frontend: `http://127.0.0.1:3000` (HTTP 200)
6. **Task Completion Report:** Always report using the 7-item checklist from Section 15 of `DEVELOPMENT_WORKFLOW.md`.
