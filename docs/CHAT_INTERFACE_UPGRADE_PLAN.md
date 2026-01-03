# Comprehensive Chat Interface Upgrade Plan

## Overview
The current chat interface in `frontend/src/app/page.tsx` uses a manual implementation for message scrolling, input handling, and mode switching. This proposal suggests refactoring the interface to use the specialized components in `src/components/ai-elements`, which are designed for high-performance AI interactions.

## 1. Scrolling & Layout Architecture
*   **Problem**: Manual `scrollIntoView` in `useEffect` can be jittery and often fails if the user manually scrolls up during streaming.
*   **Solution**: Integrate the `Conversation` component (`ai-elements/conversation.tsx`) powered by `use-stick-to-bottom`.
*   **Benefits**: 
    *   Rock-solid auto-scroll that respects user intent.
    *   Built-in "Scroll to bottom" button when new content arrives.
    *   Cleaner, more declarative code in the main page.

## 2. Next-Generation Input Experience
*   **Problem**: Mode switching (Web Search, Deep Research) is hidden in a modal, and file attachments lack visual previews.
*   **Solution**: Adopt the full `PromptInput` suite (`ai-elements/prompt-input.tsx`).
*   **Key Features**:
    *   **In-line Toolbars**: Move mode toggles and model selection directly into the input area.
    *   **Rich Attachments**: Visual previews for images and clear removal buttons for documents.
    *   **Voice-to-Text**: Enable the integrated Mic button for speech recognition.
    *   **Smart Sizing**: Automatic height adjustment as the user types.

## 3. Standardized Message Rendering
*   **Problem**: The current `ChatMessage` is a large, monolithic component.
*   **Solution**: Transition to the variant-based `Message` component (`ai-elements/message.tsx`).
*   **Benefits**:
    *   Easily switch between "Contained" (bubbles) and "Flat" (modern) styles via props.
    *   Consistent avatar and timestamp placement.
    *   Better support for specialized content like code blocks and reasoning chains.

## 4. Interactive Empty State
*   **Problem**: The current welcome screen is static and informative but not actionable.
*   **Solution**: Use `ConversationEmptyState` combined with `Suggestions` (`ai-elements/suggestion.tsx`).
*   **Benefit**: Allow users to click "Starter Suggestions" (e.g., "Analyze this PDF", "Latest AI News") to immediately engage with the bot.

## 5. Visual Polish
*   **Animations**: Integrate `framer-motion` (already in `package.json`) for smooth message transitions.
*   **Typing State**: Replace the "Assistant is typing..." text with a modern CSS pulsing indicator or the specialized `Loader` component.

## Implementation Roadmap
1.  **Phase 1**: Replace the scrolling container with `StickToBottom`.
2.  **Phase 2**: Overhaul the input area with `PromptInput`.
3.  **Phase 3**: Refactor message mapping to use the new `Message` variants.
4.  **Phase 4**: Update the Welcome screen with clickable suggestions.
