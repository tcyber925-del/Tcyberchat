# Deep Research UI Fix Plan

## Problem Analysis
The Deep Research report output is currently constrained by a fixed height of `75vh` in `DeepResearchArtifact`, causing content to be cropped or requiring uncomfortable scrolling within the chat bubble. Additionally, wide content like tables may be clipped due to the lack of horizontal scrolling support in the `ScrollArea` component.

## Proposed Solution

### 1. Enable Horizontal Scrolling
**File**: `frontend/src/components/ui/scroll-area.tsx`
- Update the `ScrollArea` component to render a `<ScrollBar orientation="horizontal" />` alongside the vertical one.
- This ensures that wide content (tables, code blocks) triggers a visible scrollbar instead of being clipped.

### 2. Implement Expandable Artifact View
**File**: `frontend/src/components/ai-elements/deep-research-artifact.tsx`
- **Remove Fixed Height**: Replace the hardcoded `h-[75vh]` with a flexible default height (e.g., `h-[500px]`).
- **Add Expansion State**: Introduce an `isExpanded` state.
  - **Default**: Inline view (`h-[500px]`) for seamless chat history browsing.
  - **Expanded**: Fullscreen view (`fixed inset-4 z-50`) for focused reading and analysis.
- **Toggle Control**: Add an "Expand/Collapse" button to the artifact header.

## User Experience Improvements
- Users can quickly scan the report in the chat flow.
- Users can expand the report to use the full screen for deep reading.
- Tables and wide code blocks will be fully accessible via horizontal scroll.
