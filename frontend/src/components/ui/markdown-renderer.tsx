import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { cn } from '@/lib/utils';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className }) => {
  // Try to detect theme - fallback to light if not available
  const [theme, setTheme] = React.useState<'light' | 'dark'>('light');

  React.useEffect(() => {
    // Check for theme preference
    const darkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    setTheme(darkMode ? 'dark' : 'light');

    // Listen for theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      setTheme(e.matches ? 'dark' : 'light');
    };
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  const codeStyle = theme === 'dark' ? vscDarkPlus : oneLight;

  return (
    <div className={cn('markdown-container', className)}>
      <ReactMarkdown
        components={{
          // Enhanced code block rendering with syntax highlighting
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            const language = match ? match[1] : '';
            const codeString = String(children).replace(/\n$/, '');

            return !inline && language ? (
              <div className="relative my-4 rounded-lg overflow-hidden border border-border">
                <div className="flex items-center justify-between bg-muted/50 px-4 py-2 text-xs text-muted-foreground">
                  <span className="font-medium">{language}</span>
                </div>
                <SyntaxHighlighter
                  style={codeStyle}
                  language={language}
                  PreTag="div"
                  customStyle={{
                    margin: 0,
                    padding: '1rem',
                    background: 'transparent',
                    fontSize: '0.875rem',
                    lineHeight: '1.5',
                  }}
                  {...props}
                >
                  {codeString}
                </SyntaxHighlighter>
              </div>
            ) : (
              <code
                className={cn(
                  'relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm',
                  className,
                )}
                {...props}
              >
                {children}
              </code>
            );
          },
          // Enhanced blockquote styling
          blockquote({ children }) {
            return (
              <blockquote className="border-l-4 border-primary/30 pl-4 py-2 my-4 italic text-muted-foreground bg-muted/30 rounded-r">
                {children}
              </blockquote>
            );
          },
          // Enhanced link styling
          a({ href, children }) {
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline underline-offset-2"
              >
                {children}
              </a>
            );
          },
          // Enhanced list styling
          ul({ children }) {
            return <ul className="list-disc list-inside my-2 space-y-1">{children}</ul>;
          },
          ol({ children }) {
            return <ol className="list-decimal list-inside my-2 space-y-1">{children}</ol>;
          },
          // Enhanced heading styling
          h1({ children }) {
            return <h1 className="text-2xl font-bold mt-6 mb-3">{children}</h1>;
          },
          h2({ children }) {
            return <h2 className="text-xl font-semibold mt-5 mb-2">{children}</h2>;
          },
          h3({ children }) {
            return <h3 className="text-lg font-semibold mt-4 mb-2">{children}</h3>;
          },
          // Enhanced paragraph spacing
          p({ children }) {
            return <p className="mb-3 leading-relaxed">{children}</p>;
          },
          // Enhanced table styling
          table({ children }) {
            return (
              <div className="overflow-x-auto my-4">
                <table className="min-w-full border-collapse border border-border rounded-lg">
                  {children}
                </table>
              </div>
            );
          },
          th({ children }) {
            return (
              <th className="border border-border px-4 py-2 bg-muted font-semibold text-left">
                {children}
              </th>
            );
          },
          td({ children }) {
            return <td className="border border-border px-4 py-2">{children}</td>;
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
