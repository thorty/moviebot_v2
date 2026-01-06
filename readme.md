# Moviebot

## Introduction

Prototype for a LLM based recommendation system for movies and series. 

## Technologie
langgraph
chainlit as frontend (prototype)

## APIs
LLM: OpenAI GPT4
Search Engine: Serpa
TMDB as Main Datasource



## Funktionsweise
- InterviewAgent
- RetrievalAgent (ToolsUsage)
(- RecrommendAgent)
(- ReflectionAgent)

- State
- Memmory and Checkpoint
- Sessionhandling
- Shorttermmemory

## bugs
- fallback does not work ✅ 
- fallowup frage: und umsonst? - schlechte antwort

## testing
- provider ändern?

## todos

- suchoptimierung:
    - nur ein streaming provider - anders suchen: mehr prio auf provider
    - bei filmen wie xyz: besser heraus bekommen was die filme ausmacht. und nachfragen
- Eine Datenbank oder persistenter Checkpointer (z.B. SqliteSaver, PostgresSaver) würde den State komplett im Backend speichern und automatisch wiederherstellen.
- run in docker
- fullstack app:
  - frontend in react
  - frontend for streaming provider selection
  - backend with fastapi
- botlogik:
    - streamingprovidersuche (werstreamtes)
- direktlinks zu streamingprovider

### ideen
- playlisten erstellen 
- multiuser / login mit playlisten

### backend

- finished is included in the result (because of streaming)
- keine loop und sagt trotzdem manchmal was es macht anstelle es zu tun
- optimize research and retrieval (perplexity)
- include documentation

#### interview agent
- frag ob du mehrere filme empfehlen sollst *optional
- fragenkatalog instruieren
- promptengineering interviewagent, komplexer gestalten

### frontend
- filter streaming providers
- free / rent / buy option for those providers
- with login
- example questions as buttons


## sources, tutorials

https://levelup.gitconnected.com/building-an-ai-chatbot-with-langgraph-fastapi-streamlit-an-end-to-end-guide-f658969b4436

https://langchain-ai.github.io/langgraph/tutorials/get-started/1-build-basic-chatbot/#8-run-the-chatbot

