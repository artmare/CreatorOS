# CreatorOS

CreatorOS is a B2B SaaS operating system for content creators and creator teams. It combines project memory, agent orchestration, content-pack generation, growth scoring, usage controls, notifications, admin visibility, and integration adapters for OpenAI, Supabase, Telegram, YouTube, and Lemon Squeezy.

## Local Development

```powershell
npm --prefix frontend install
python -m pip install -r backend/requirements.txt

npm run dev:frontend
npm run dev:backend
```

Frontend: http://localhost:3000

Backend: http://localhost:8000/docs

## Environment

Copy the examples before running provider-backed flows:

```powershell
Copy-Item frontend/.env.example frontend/.env.local
Copy-Item backend/.env.example backend/.env
```

OpenAI, Supabase, Telegram, YouTube, and Lemon Squeezy calls stay disabled until their corresponding environment variables are supplied.

## Status

This repo implements the requested MVP plus the Phase 2 platform layer as a working foundation. Local API routes use deterministic service logic and seed data so the product runs without secrets; provider adapters are included for production wiring.
