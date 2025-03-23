# JaPi_Technical_Assessment 🎯💯

Repo for JaPi Technical Assessment using Flask Framework; a lightweight, flexible, and micro web framework written in Python, designed for building web applications and APIs. Furthermore, I utilized Supabase, which is an open-source platform that provides a hosted PostgreSQL database and a suite of tools, acting as a backend-as-a-service (BaaS) alternative to Firebase.

## Ollama Architecture 📖

This project adheres strictly to the Ollama LLM API to carry out the chat functionality with the user. Ollama is a simple tool designed for running LLM (Large Language Models) quickly. Users can easily interact with large language model without the
need for complex environment setup.

### Ollama Architecture & Conversation Flow Overview 🔎

*(Summarized from [Analysis of Ollama Architecture](https://medium.com/@rifewang/analysis-of-ollama-architecture-and-conversation-processing-flow-for-ai-llm-tool-ead4b9f40975))*

**Architecture Components** ⚙️
1. **Modular Design**  
   - *Model Runner*: Handles LLM loading/execution  
   - *API Layer*: REST/WebSocket interfaces for client interactions  
   - *Conversation Manager*: Maintains chat context/history  

2. **Inference Optimization**  
   - GPU acceleration (with CPU fallback)  
   - Context window optimization for memory management  
   - Dynamic batching for concurrent requests  

**Conversation Workflow** 📢‼️
1. **Input Phase**: Client sends prompt via REST/WebSocket  
2. **Context Injection**: System prepends conversation history to prompt  
3. **Tokenization**: Text → LLM-compatible tokens  
4. **Inference**: Parallel processing using model weights  
5. **Detokenization**: Tokens → Human-readable response  
6. **Context Update**: Stores conversation history for continuity  

**Key Advantages** ✅
- Enables local LLM execution with minimal setup  
- Optimized for low-latency conversational AI  
- Supports multiple simultaneous users through efficient resource allocation  

## Setup Instructions  ‼️️
1. first and foremost it is imperative to clone this project repository onto your local machine.
2. follow the instructions detailed on this video: https://youtu.be/d0o89z134CQ to install the latest necessary dependencies and files for the Ollama LLM API. Make sure that Ollama LLM API is **RUNNING** when you invoke `python3 app.py`.
3. install the latest version of python - i used *Python 3.12.9*
4. create a .env file with setup instruction as shown on the screenshot titled `dotenv_setup` and your project is good to go.

*if you have any trouble running any of the above setup please reach out to me via my personal email at Obie.kal22@gmail.com*.