# Moviebot

## Introduction

Prototype for a LLM based recommendation system for movies and series. 

## Technologie
langgraph
streamlit as frontend (prototype)

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


## todos

- run in docker

### backend

- finished is included in the result (because of streaming)
- datum in der titelsuche
- haluziniert wenn kein ergebnis
- optimize research and retrieval (perplexity)
- include documentation

#### interview agent
- frag ob du mehrere filme empfehlen sollst *optional

### frontend
- filter streaming providers
- free / rent / buy option for those providers
- with login
- example questions as buttons


## sources, tutorials

https://levelup.gitconnected.com/building-an-ai-chatbot-with-langgraph-fastapi-streamlit-an-end-to-end-guide-f658969b4436

https://langchain-ai.github.io/langgraph/tutorials/get-started/1-build-basic-chatbot/#8-run-the-chatbot

