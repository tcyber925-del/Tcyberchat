import React, { useState, useEffect } from 'react'
import { apiService, Message } from '../services/api'
import MessageBubble from './MessageBubble'

interface ChatMessage extends Message {
  // Additional UI state
  isLoading?: boolean
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | undefined>()

  // Load existing conversation on mount
  useEffect(() => {
    loadExistingConversation()
  }, [])

  const loadExistingConversation = async () => {
    try {
      const conversations = await apiService.getConversations()
      if (conversations.length > 0) {
        // Load the most recent conversation
        const recentConversation = conversations[0]
        setConversationId(recentConversation.id)

        const conversationMessages = await apiService.getConversationMessages(recentConversation.id)
        setMessages(conversationMessages as ChatMessage[])
      }
    } catch (error) {
      console.error('Failed to load conversation:', error)
    }
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: inputValue.trim(),
      type: 'user',
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    // Add loading message
    const loadingMessage: ChatMessage = {
      id: `loading-${Date.now()}`,
      content: '',
      type: 'assistant',
      isLoading: true,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, loadingMessage])

    try {
      const response = await apiService.sendChatMessage({
        message: userMessage.content,
        conversationId,
        includeCitations: true
      })

      // Update conversation ID if this is the first message
      if (!conversationId && response.conversationId) {
        setConversationId(response.conversationId)
      }

      // Replace loading message with actual response
      setMessages(prev => prev.map(msg =>
        msg.id === loadingMessage.id
          ? {
              id: Date.now().toString(),
              content: response.response,
              type: 'assistant',
              citations: response.citations,
              timestamp: new Date().toISOString()
            } as ChatMessage
          : msg
      ))

    } catch (error) {
      console.error('Failed to send message:', error)

      // Replace loading message with error message
      setMessages(prev => prev.map(msg =>
        msg.id === loadingMessage.id
          ? {
              id: Date.now().toString(),
              content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}`,
              type: 'assistant',
              timestamp: new Date().toISOString()
            } as ChatMessage
          : msg
      ))
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="flex flex-col h-full bg-[#343541]">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-300">
            <h1 className="text-4xl font-semibold mb-4">What are you working on?</h1>
            <div className="relative w-full max-w-md">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder="Ask anything"
                className="w-full px-4 py-3 pr-12 bg-[#40414f] border border-gray-700 rounded-md focus:outline-none focus:ring-1 focus:ring-gray-600 focus:border-transparent resize-none min-h-[48px] max-h-40 text-white placeholder-gray-500"
                rows={1}
                disabled={isLoading}
                style={{ height: 'auto', minHeight: '48px' }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = 'auto';
                  target.style.height = Math.min(target.scrollHeight, 160) + 'px';
                }}
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isLoading}
                className="absolute right-3 bottom-3 p-1 text-gray-400 hover:text-gray-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <svg stroke="currentColor" fill="none" strokeWidth="2" viewBox="0 0 24 24" className="h-5 w-5" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
              </button>
            </div>
          </div>
        )}

        <div className="max-w-4xl mx-auto space-y-6">
          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              onCitationClick={(citation) => {
                console.log('Citation clicked:', citation);
              }}
            />
          ))}
        </div>
      </div>

      {/* Input Area - Fixed at bottom */}
      {messages.length > 0 && (
        <div className="border-t border-gray-700 bg-[#343541] px-4 py-4 sticky bottom-0">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-end space-x-3">
              <div className="flex-1 relative">
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  placeholder="Message Local Chatbot..."
                  className="w-full px-4 py-3 pr-12 bg-[#40414f] border border-gray-700 rounded-md focus:outline-none focus:ring-1 focus:ring-gray-600 focus:border-transparent resize-none min-h-[48px] max-h-40 text-white placeholder-gray-500"
                  rows={1}
                  disabled={isLoading}
                  style={{ height: 'auto', minHeight: '48px' }}
                  onInput={(e) => {
                    const target = e.target as HTMLTextAreaElement;
                    target.style.height = 'auto';
                    target.style.height = Math.min(target.scrollHeight, 160) + 'px';
                  }}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim() || isLoading}
                  className="absolute right-3 bottom-3 p-1 text-gray-400 hover:text-gray-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  <svg stroke="currentColor" fill="none" strokeWidth="2" viewBox="0 0 24 24" className="h-5 w-5" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                </button>
              </div>
            </div>
            <div className="text-xs text-gray-500 mt-2 text-center">
              Local Chatbot may produce inaccurate information.
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ChatInterface