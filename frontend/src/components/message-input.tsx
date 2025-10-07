'use client';

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useChat } from '@/lib/context/chat-context';
import { useMultimodal } from '@/lib/hooks/use-settings';
import { uploadDocument } from '@/lib/api/documents';

const MessageInput: React.FC = () => {
  const { sendStreamingMessage, isStreaming, setError, error, currentSession } = useChat();
  const { multimodalEnabled } = useMultimodal();
  const [message, setMessage] = useState('');
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [showRecordingTimer, setShowRecordingTimer] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const audioInputRef = useRef<HTMLInputElement>(null);

  const handleMessageChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setAttachedFiles(Array.from(e.target.files));
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files) {
      setAttachedFiles(Array.from(e.dataTransfer.files));
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      const chunks: Blob[] = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(chunks, { type: 'audio/wav' });
        const audioFile = new File([audioBlob], `recording_${Date.now()}.wav`, { type: 'audio/wav' });
        setAttachedFiles(prev => [...prev, audioFile]);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);
      setShowRecordingTimer(true);

      // Start timer
      recordingTimerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      setError('Could not access microphone for recording');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setShowRecordingTimer(false);
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }
    }
  };

  const handleImageSelect = () => {
    imageInputRef.current?.click();
  };

  const handleAudioSelect = () => {
    audioInputRef.current?.click();
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const imageFiles = Array.from(e.target.files).filter(file =>
        file.type.startsWith('image/')
      );
      setAttachedFiles(prev => [...prev, ...imageFiles]);
    }
  };

  const handleAudioChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const audioFiles = Array.from(e.target.files).filter(file =>
        file.type.startsWith('audio/')
      );
      setAttachedFiles(prev => [...prev, ...audioFiles]);
    }
  };

  const removeFile = (index: number) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if ((message.trim() || attachedFiles.length > 0) && !isStreaming) {
      setError(null);

      try {
        // Upload files if any first
        if (attachedFiles.length > 0) {
          for (const file of attachedFiles) {
            try {
              await uploadDocument(file);
            } catch (error) {
              console.error('File upload failed:', error);
              setError('File upload failed');
            }
          }
        }

        // Send message using streaming (this handles user message and AI response)
        await sendStreamingMessage(message.trim(), currentSession?.id);

        setMessage('');
        setAttachedFiles([]);
      } catch (error) {
        console.error('Message sending failed:', error);
        setError('Message sending failed');
      }
    }
  };

  return (
    <>
      {showRecordingTimer && (
        <div className="flex items-center justify-center p-2 bg-destructive/10 border border-destructive/20 rounded-lg mx-4 mb-2">
          <span className="text-destructive font-medium animate-pulse">
            🎤 Recording... {String(Math.floor(recordingTime / 60)).padStart(2, '0')}:{String(recordingTime % 60).padStart(2, '0')}
          </span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex items-center p-4 bg-card border-t border-border">
        <div
          className="flex-grow border border-input rounded-lg p-2 flex items-center bg-background"
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
        <textarea
          aria-label="Message input"
          value={message}
          onChange={handleMessageChange}
          placeholder="Type your message..."
          className="flex-grow resize-none outline-none bg-transparent text-foreground"
          rows={1}
          disabled={isStreaming} // Disable input if streaming
        />
        {attachedFiles.length > 0 && (
          <div className="w-full mt-2 space-y-1">
            {attachedFiles.map((file, index) => (
              <div key={index} className="flex items-center gap-2 bg-muted/50 rounded px-2 py-1 text-sm">
                <span className="truncate max-w-xs">{file.name}</span>
                <span className="text-muted-foreground">({(file.size / 1024).toFixed(1)} KB)</span>
                <button
                  type="button"
                  onClick={() => removeFile(index)}
                  className="text-muted-foreground hover:text-destructive ml-auto"
                  aria-label={`Remove ${file.name}`}
                  title="Remove file"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Multimodal input buttons */}
        {multimodalEnabled && (
          <div className="flex items-center gap-1 ml-2">
            {/* Voice recording button */}
            <button
              type="button"
              onClick={isRecording ? stopRecording : startRecording}
              className={`p-2 rounded-full transition-colors ${
                isRecording
                  ? 'bg-destructive text-destructive-foreground animate-pulse'
                  : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
              }`}
              aria-label={isRecording ? 'Stop recording' : 'Start voice recording'}
              title={isRecording ? `Recording (${recordingTime}s)` : 'Record voice message'}
              disabled={isStreaming} // Disable button if streaming
            >
              {isRecording ? '⏹️' : '🎤'}
            </button>

            {/* Image input button */}
            <button
              type="button"
              onClick={handleImageSelect}
              className="p-2 bg-secondary text-secondary-foreground rounded-full hover:bg-secondary/80 transition-colors"
              aria-label="Attach image"
              title="Attach image"
              disabled={isStreaming} // Disable button if streaming
            >
              📷
            </button>

            {/* Audio input button */}
            <button
              type="button"
              onClick={handleAudioSelect}
              className="p-2 bg-secondary text-secondary-foreground rounded-full hover:bg-secondary/80 transition-colors"
              aria-label="Attach audio file"
              title="Attach audio file"
              disabled={isStreaming} // Disable button if streaming
            >
              🎵
            </button>
          </div>
        )}

        {/* File attachment */}
        <input type="file" multiple onChange={handleFileChange} className="hidden" id="file-upload" disabled={isStreaming} />
        <label htmlFor="file-upload" className="cursor-pointer ml-2 p-2 bg-secondary text-secondary-foreground rounded hover:bg-secondary/80 transition-colors" aria-disabled={isStreaming}>
          📎
        </label>

        {/* Hidden inputs for image and audio selection */}
        <input
          ref={imageInputRef}
          type="file"
          accept="image/*"
          onChange={handleImageChange}
          className="hidden"
          id="image-upload"
          disabled={isStreaming}
        />
        <input
          ref={audioInputRef}
          type="file"
          accept="audio/*"
          onChange={handleAudioChange}
          className="hidden"
          id="audio-upload"
          disabled={isStreaming}
        />
      </div>

      <button
        type="submit"
        disabled={(!message.trim() && attachedFiles.length === 0) || isStreaming}
        className="ml-4 px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:bg-muted disabled:text-muted-foreground flex items-center transition-colors"
      >
        {isStreaming ? (
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
        ) : null}
        Send
      </button>

      {error && <div className="text-destructive text-sm mt-2 ml-4">{error}</div>}
    </form>
    </>
  );
};

export default MessageInput;
