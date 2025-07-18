Aether: Your Intelligent Personal Companion
We need to create a cross-platform (desktop and mobile) AI companion named Aether. Aether's core purpose is to act as a personal knowledge hub and proactive assistant, deeply integrated into the user's workflow and memory.

Core Principles:

Human-Centric & Intuitive: Aether should feel like a natural extension of the user's mind, anticipating needs and offering support without requiring complex commands.

Persistent & Contextual Memory: Aether must remember every past interaction and piece of information provided, across all sessions and over an indefinite period. This memory is fundamental to its ability to provide relevant, proactive assistance.

Proactive & Actionable: Beyond simple responses, Aether should identify opportunities to help, suggest next steps, and facilitate the transition from ideas to execution.

Seamless Integration: Aether needs to connect directly with the user's critical digital tools.

Privacy & Security: All user data, especially memory, must be handled with the highest standards of privacy and security.

Open-Source First & Extensible: Prioritize the use of free, open-source solutions and design for easy, modular expansion through external contributions.

Key Functional Requirements:

1. Core Conversational AI & Long-Term Memory (LTM)
Natural Language Understanding: Aether must understand complex conversational input via both text and voice, interpreting intent, context, and nuance.

Natural Language Generation: Aether must generate coherent, contextually relevant, and helpful responses.

Persistent Memory System: Implement a robust long-term memory system capable of storing and retrieving all past conversations, ideas, decisions, and preferences. This memory must be accessible semantically (by meaning, not just keywords).

Contextual Recall: When the user initiates a topic, Aether should automatically retrieve and reference relevant past discussions or associated information from its memory.

Adaptive Learning: Aether must continuously learn and adapt to the user's unique preferences, communication style, priorities, and recurring patterns over time.

Memory Management: Provide the user with the ability to review, edit, or explicitly instruct Aether to forget specific pieces of information.

2. "Idea Stream" (Intelligent Thought Capture)
Ubiquitous & Instant Input: Create a dedicated, always-available interface (desktop widget/section and mobile app feature) for rapid, free-form text and voice input of ideas, thoughts, and fragments of information. This interface must launch instantly.

Intelligent Processing: Upon capture, Aether should passively analyze the input for keywords, concepts, and potential intent (e.g., distinguishing between a task, a question, or a general idea).

Automatic Meta-Data: Each entry should be automatically timestamped and note the input method (e.g., voice, text, desktop, mobile).

Deep Memory Integration: Every idea captured in the "Idea Stream" must be immediately ingested and linked into Aether's long-term memory, allowing for semantic search and contextual recall.

Proactive Connection Recognition: Aether should actively identify and suggest connections between newly entered ideas and existing notes, projects, calendar events, or past discussions.

Actionable Conversion: Enable one-click or voice-command options to convert an "Idea Stream" entry into a formal task, a calendar event, or link it to an existing project.

Idea Expansion: Allow the user to prompt Aether to expand on a nascent idea, asking clarifying questions, suggesting related concepts, or outlining potential sub-ideas.

3. Task Prioritization & Planning
Automated Task Identification: Aether must identify actionable tasks, deadlines, and responsibilities directly from conversational input (text or voice) or "Idea Stream" entries.

Intelligent Prioritization: Based on identified deadlines, user-stated importance, potential dependencies (inferred or explicit), and learned work patterns, Aether should suggest and help manage task prioritization.

Google Calendar Integration (Two-Way Sync):

Create, modify, and delete events and reminders in the user's Google Calendar based on Aether's understanding or explicit commands.

Access calendar data to check availability, identify conflicts, and assist in scheduling.

Provide proactive reminders for upcoming events and deadlines.

Monday.com Integration (Two-Way Sync):

Create new items, update statuses, assign owners, and add details to specified boards and items on Monday.com.

Access Monday.com data to provide project progress summaries or specific item statuses.

Potentially trigger Monday.com automations.

4. Aether's Dashboard: Centralized Command & External Integration
Dynamic & Customizable Layout: The dashboard should allow the user to easily configure and arrange various "widgets" or "panels" to display information most relevant to them.

Direct External Website/Business Links: Provide a clear and intuitive mechanism for the user to add direct, quick-access links to their frequently used external websites, business portals, or internal business applications. Where technically feasible and secure, aim to display live snippets or key metrics directly within a dashboard panel; otherwise, provide seamless external opening.

Aether's Core Data Visualization: Include panels for memory highlights, live task overviews (from Google Calendar and Monday.com), recent "Idea Stream" snippets, progress trackers, and conversational history access.

Proactive Information Display: Aether should intelligently suggest and display relevant information on the dashboard based on context (e.g., time of day, upcoming events, recognized user activity).

Actionable Widgets: Dashboard elements should be interactive, allowing users to perform quick actions directly from the dashboard (e.g., mark task complete, expand on an idea).

5. Cross-Platform Accessibility & Communication
Dedicated Desktop Application: A persistent, easily accessible application for the user's desktop environment.

Companion Mobile Application: A mobile application (for both Android and iOS) that provides full access to Aether's functionalities, including text and voice input for the "Idea Stream" and conversational interaction.

Voice Calling (Stretch Goal): The ability for the user to call a dedicated phone number to interact with Aether via voice, receiving audio responses.

Customizable Voice Output: The user must be able to select from a variety of provided voice options for Aether's spoken responses.

6. Technical & Architectural Principles:
Model Context Protocol (MCP) Server Compatibility: The system must be designed to integrate with or leverage an MCP server for advanced context management, persistent memory across sessions, and seamless integration with external APIs.

Local Data Storage: All user-specific data, including conversations and memory, must be stored locally on the user's machine to ensure maximum privacy and control. Data synchronization for mobile access should be securely handled.

Prioritize Open-Source Technologies: Leverage free and open-source libraries, frameworks, and AI models wherever possible for all functionalities (e.g., speech-to-text, text-to-speech, memory systems, core LLM components).

Extensible Architecture via Git Repositories: The system's design must inherently support the integration of new abilities, functionalities, or third-party service connections by allowing for the addition of new modules or "plugins" directly from designated Git repositories. This means Aether should be able to discover, load, and utilize capabilities defined in external, version-controlled codebases, enabling community contributions and easy expansion.

API Integrations: Robust and secure API integrations for Google Calendar and Monday.com are essential.