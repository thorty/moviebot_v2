# Moviebot

## Introduction

Prototype for a LLM based recommendation system for movies and series. 

## Technologie
langgraph
gradio as frontend

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
- fallowup frage: und umsonst? - schlechte antwort ✅ 

## testing
- provider ändern?

## todos

- allgemeine features:
  - filterkriterium für paymenttype hinzufügen ✅ 
  - tool erweitern für serien oder filme als filterkriterium ✅
  - wenn nur ein provider: gleich in suche einbeziehen ✅ 
  - outofscope questions handeling
  - fallbackmessage optimieren. simpel und klar mit empathie. 
  - buy providers ebenso suchen und vorschlagen.
  - suche optimieren / Retrieval 
    - mediatheken durchsuchen https://mediathekviewweb.de/#future=false
  - run in docker
  - using superbase framework for, database, login and usermngmnt, logging,...
- fullstack app:
  - frontend (nodejs)
    - logim 
    - frontend in react
    - frontend for streaming provider selection
    - loaading animation
    - cover artwork
    - use cookie for perovider selection
    - direktlinks zu streamingprovider 
    - example questions as buttons
  - backend (fastapi with db):
    - store conversations     
    - psa complience check    
    - setup rate limits
    - chat history:
      - Eine Datenbank oder persistenter Checkpointer (z.B. SqliteSaver, PostgresSaver) würde den State komplett im Backend speichern und automatisch wiederherstellen.
  
- hosting: 
  - single docker container 
  - superbase
  

#### interview agent
- promptengineering interviewagent, komplexer gestalten
  - frag ob du mehrere filme empfehlen sollst *optional
  - fragenkatalog instruieren


## sources, tutorials

https://levelup.gitconnected.com/building-an-ai-chatbot-with-langgraph-fastapi-streamlit-an-end-to-end-guide-f658969b4436

https://langchain-ai.github.io/langgraph/tutorials/get-started/1-build-basic-chatbot/#8-run-the-chatbot

