# Moviebot

## Introduction

Prototype for a LLM based recommendation system for movies and series. 

## Technologie POC
- backend: langgraph 
- frontend: gradio

## Used APIs
- LLM: OpenAI 
- Search Engine: tavily
- TMDB as API for streamingproviders
- Langsmith for tracing llm calls

## Funktionsweise
- InterviewAgent
- ContentResearcher (ToolsUsage)
- State
- Memmory and Checkpoint
- Sessionhandling
- Shorttermmemory

### Graph 

![alt text](graph.png)

## Featurelist

- allgemeine features:
  - clarfication questions ✅ 
  - filter for streamingprovider ✅ 
  - filter für paymenttype  ✅ 
  - tool erweitern für serien oder filme als filterkriterium ✅
  - wenn nur ein provider: gleich in suche einbeziehen ✅ 
  - fallbackmessage optimieren. simpel und klar mit empathie. ✅   
  - outofscope questions handeling ✅
  - mediatheken search (ard, zdf) ✅
  - direktlinks zu streamingprovider 
  - cover artwork 

- allgemeine features nice to have: 
  - suche optimieren / Retrieval 
    - mediatheken durchsuchen https://mediathekviewweb.de/#future=false
  - filtern durch mehr nachfragen ( doku / film oder serie, erwachsenencontent ja oder nein, ... )
  - buy providers ebenso suchen und vorschlagen. ⛔️  

#### interview agent
- promptengineering interviewagent, komplexer gestalten
  - frag ob du mehrere filme empfehlen sollst *optional
  - fragenkatalog instruieren

## Run
gradio frontend/gradio/app.py