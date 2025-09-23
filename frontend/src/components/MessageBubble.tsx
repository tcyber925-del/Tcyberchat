import React from 'react';
import { Message } from '../services/api';

interface Citation {
  documentId: string;
  chunkIndex: number;
  score: number;
  contentPreview: string;
}

interface MessageBubbleProps {
  message: Message;
  onCitationClick?: (citation: Citation) => void;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, onCitationClick }) => {
  const isUser = message.type === 'user';

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleCitationClick = (citation: Citation) => {
    if (onCitationClick) {
      onCitationClick(citation);
    }
  };

  const renderCitations = () => {
    if (!message.citations || message.citations.length === 0) {
      return null;
    }

    return (
      <div className="mt-3 space-y-2">
        <div className="text-xs text-gray-500 font-medium">Sources:</div>
        <div className="space-y-1">
          {message.citations.map((citation, index) => (
            <button
              key={index}
              onClick={() => handleCitationClick(citation)}
              className="block w-full text-left p-2 bg-gray-700 hover:bg-gray-600 rounded-md border border-gray-600 transition-colors group"
            >
              <div className="flex items-start space-x-2">
                <div className="flex-shrink-0 w-4 h-4 bg-blue-600 text-white text-xs rounded-full flex items-center justify-center font-medium">
                  {index + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-blue-300 line-clamp-2">
                    {citation.contentPreview}
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    Document: {citation.documentId}
                    {citation.chunkIndex !== undefined && ` • Chunk ${citation.chunkIndex}`}
                    {citation.score !== undefined && ` • Score: ${(citation.score * 100).toFixed(1)}%`}
                  </div>
                </div>
                <div className="flex-shrink-0 text-gray-400 group-hover:text-gray-200">
                  →
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    );
  };

  const renderMessageContent = () => {
    // For now, treat content as plain text
    // In the future, this could support markdown rendering
    return (
      <div className="whitespace-pre-wrap break-words">
        {message.content}
      </div>
    );
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[80%] ${isUser ? 'order-2' : 'order-1'}`}>
        {/* Message Header */}
        <div className={`flex items-center space-x-2 mb-1 ${isUser ? 'justify-end' : 'justify-start'}`}>
          <span className={`text-xs text-gray-500 font-medium`}>
            {isUser ? 'You' : 'Assistant'}
          </span>
          <span className="text-xs text-gray-400">
            {formatTimestamp(message.timestamp)}
          </span>
        </div>

        {/* Message Bubble */}
        <div
          className={`px-4 py-3 rounded-2xl ${
            isUser
              ? 'bg-[#10a37f] text-white rounded-br-lg'
              : 'bg-[#ececec] text-gray-900 rounded-bl-lg'
          }`}
        >
          {/* Message Content */}
          <div className="text-sm leading-relaxed">
            {renderMessageContent()}
          </div>

          {/* Citations */}
          {!isUser && renderCitations()}

          {/* Status indicators for bot messages */}
          {!isUser && message.metadata && (
            <div className="mt-2 pt-2 border-t border-gray-100">
              <div className="flex items-center space-x-4 text-xs text-gray-500">
                {message.metadata.model && (
                  <span>Model: {message.metadata.model}</span>
                )}
                {message.metadata.tokens && (
                  <span>Tokens: {message.metadata.tokens}</span>
                )}
                {message.metadata.processingTime && (
                  <span>Time: {(message.metadata.processingTime / 1000).toFixed(1)}s</span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Message Status for user messages (if needed) */}
        {isUser && (
          <div className="flex justify-end mt-1">
            <span className="text-xs text-gray-400">
              ✓
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;