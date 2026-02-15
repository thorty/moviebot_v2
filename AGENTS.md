---
name: Moviebot Agent
description: Moviebot Fullstack: LangGraph/FastAPI Backend + React/Supabase Frontend
---

## Overview
LLM-Filmchatbot. Docker-local Supabase. Auth/DB/Logging integriert.

## Stack
Backend: FastAPI, Poetry, LangGraph, supabase-py
Frontend: Vite/React/TS, shadcn, supabase-js

## Code Style
- Python: Black + type hints, async FastAPI
- React: Hooks, Tailwind/shadcn
- Immer RLS in Supabase nutzen

## Commands
Backend: poetry run uvicorn main:app --reload
Frontend: npm run dev
Docker: docker compose up
