import { useState, useEffect } from "react";
import { Bot, Loader2, MessageSquare, Send, User2, Copy, CheckCircle, } from "lucide-react";
import Markdown from "react-markdown";
import { streamChat } from '~/utils/streamChat';
import React from 'react';
import { Input } from '~/components/input';
import { Button } from '~/components/button';
import { useSettings } from "~/contexts/SettingsContext";
import { ConversationCard, Message } from "~/types";
import { streamSuggestions } from "~/utils/streamSuggestions";
import { CustomLink } from "../customLink";

export function AIChat() {
    const { 
      integrator, 
      articleUrl, 
      articleTitle,
      setUserQuery, 
      userQuery, 
      model
    } = useSettings();

    const [conversations, setConversations] = useState<ConversationCard[]>([]);
    const [chatLoading, setChatLoading] = useState(false);
    const [suggestionsLoading, setSuggestionsLoading] = useState(false);

    const chatContainerRef = React.useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [conversations]);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        const userMessage = userQuery.trim();
        if (!userMessage) return;
    
        setUserQuery("");
        setChatLoading(true);
            // Create a new card with the user message and an empty assistant message
        const newCard: ConversationCard = {
            user: { role: "user", content: userMessage },
            assistant: { role: "assistant", content: "" },
        };

        // Add the new card to the history
        setConversations((prev) => [...prev, newCard]);

        try {
        await streamChat({
          url: articleUrl,
          query: userMessage,
          integrator,
          model,
          onChunk: (partialResponse: string) => {
            setConversations((prev) => {
              const updated = [...prev];
              const lastIndex = updated.length - 1;
              updated[lastIndex] = {
                ...updated[lastIndex],
                assistant: { role: "assistant", content: partialResponse },
              };
              return updated;
            });
          }
        });

        } catch (error) {
          console.error("Error streaming response:", error);
        } finally {
          setChatLoading(false);
        }
      }

      
    async function handleSuggestArticles() {
        if (!articleUrl) return;
      
        setSuggestionsLoading(true);
      
        // Create a new conversation card with a header indicating suggestions.
        const newCard: ConversationCard = {
          user: { role: "user", content: "Suggested Articles:" },
          assistant: { role: "assistant", content: "" },
        };
      
        // Append the new card to the conversation history.
        setConversations((prev) => [...prev, newCard]);
      
        try {
          await streamSuggestions({
            url: articleUrl,
            integrator,
            onChunk: (partialResponse: string) => {
              setConversations((prev) => {
                const updated = [...prev];
                const lastIndex = updated.length - 1;
                updated[lastIndex] = {
                  ...updated[lastIndex],
                  assistant: { role: "assistant", content: partialResponse },
                };
                return updated;
              });
            },
          });
        } catch (error) {
          console.error("Error streaming suggestions:", error);
        } finally {
          setSuggestionsLoading(false);
        }
      }
      

  return (
    <div className="flex flex-col h-screen">
      <div 
        ref={chatContainerRef} 
        className="flex-1 p-4 container mx-auto max-w-4xl space-y-4 overflow-y-auto scrollbar-hide"
        >
      {conversations.map((card, index) => (
          <div key={index} className="space-y-2">
            <AIMessage message={card.user} />
            <AIMessage message={card.assistant} loading={chatLoading || suggestionsLoading} />
          </div>
        ))}
      </div>

        <div className="w-full p-4 bg-zinc-800 border-t border-gray-700 flex-shrink-0">
            <form onSubmit={handleSubmit} className="mx-auto max-w-4xl">
                <div className="flex gap-2">
                <div className="flex-1 relative">
                    <MessageSquare className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                        className="flex-1 bg-zinc-900 border-gray-700 text-gray-100 pl-10"
                        value={userQuery}
                        disabled={chatLoading}
                        placeholder="Ask your local AI Assistant..."
                        onChange={(e) => setUserQuery(e.target.value)}
                    />
                </div>
                <Button
                    type="submit"
                    disabled={chatLoading}
                    className="bg-primary/80 hover:bg-primary/100"
                >
                    {chatLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                    <Send className="h-4 w-4" />
                    )}
                    <span className="sr-only">Send message</span>
                </Button>
                {integrator === "openai" && articleTitle && (
                  <Button
                    onClick={handleSuggestArticles}
                    disabled={chatLoading || suggestionsLoading || !articleUrl}
                    className="bg-primary/80 hover:bg-primary/100"
                  >
                     {suggestionsLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      'Suggestions'
                    )}
                  </Button>
                )}
                </div>
            </form>
        </div>
    </div>
  );
}

const AIMessage: React.FC<{ message: Message, loading?: boolean }> = React.memo(({ message, loading }) => {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(message.content)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      })
      .catch((err) => console.error("Failed to copy text: ", err));
  };

  return (
    <div
      className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`max-w-[80%] rounded-lg p-4 ${message.role === "user"
          ? "bg-primary text-black"
          : "bg-zinc-700 text-gray-100"
          }`}
      >
        <div className="flex items-center gap-2 mb-2" style={{ justifyContent: "space-between" }}>
          <span className="text-sm font-medium" style={{ display: "flex", gap: 10 }}>
            {message.role === "user" ? (
              <User2 className="h-4 w-4" />
            ) : (
              loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Bot className="h-4 w-4" />
            )}

            <span>{message.role === "user" ? "You" : "Assistant"}</span>
          </span>
          {message.role === "assistant" && (
            <div className="relative inline-block">
              <button 
                onClick={copyToClipboard} 
                className="text-gray-400 hover:text-white transition"
                aria-label="Copy to clipboard"
              >
                {copied ? <CheckCircle className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4" />}
              </button>
              {copied && (
                <span
                  className="absolute top-0 left-full ml-2 text-xs bg-black text-white px-2 py-1 rounded shadow animate-fadeOut"
                  onAnimationEnd={() => setCopied(false)}
                >
                  Copied!
                </span>
              )}
            </div>
          )}
        </div>

        {message.role === "assistant" && loading && (
          <div className="flex items-center gap-2 text-gray-400">
            <span className="text-sm">Thinking...</span>
          </div>
        )}

        <article className={`prose max-w-none ${message.role === "user" ? "prose-invert prose-p:text-black prose-headings:text-black prose-strong:text-black prose-li:text-black" : "prose-invert prose-p:text-gray-100 prose-headings:text-gray-100 prose-strong:text-gray-100 prose-li:text-gray-100"}`}>
        <Markdown components={{ a: CustomLink }}>{message.content}</Markdown>
        </article>
      </div>
    </div>
  )
})

