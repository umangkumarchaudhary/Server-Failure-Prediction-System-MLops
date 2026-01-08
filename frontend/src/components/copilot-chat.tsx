"use client";

import { useState, useRef, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Send, Bot, User, Sparkles, Loader2 } from "lucide-react";
import api from "@/lib/api";

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp: Date;
}

export default function CopilotChat({ assetId }: { assetId?: string }) {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: "welcome",
            role: "assistant",
            content: "Hello! I'm your AI maintenance copilot. I can help you understand anomalies, suggest maintenance actions, and answer questions about your assets. How can I help you today?",
            timestamp: new Date(),
        },
    ]);
    const [input, setInput] = useState("");
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const chatMutation = useMutation({
        mutationFn: async (message: string) => {
            const response = await api.post("/copilot/chat", {
                message,
                asset_id: assetId,
            });
            return response.data;
        },
        onSuccess: (data) => {
            setMessages((prev) => [
                ...prev,
                {
                    id: `assistant-${Date.now()}`,
                    role: "assistant",
                    content: data.response,
                    timestamp: new Date(),
                },
            ]);
        },
    });

    const handleSend = () => {
        if (!input.trim() || chatMutation.isPending) return;

        const userMessage: Message = {
            id: `user-${Date.now()}`,
            role: "user",
            content: input,
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        chatMutation.mutate(input);
        setInput("");
    };

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    return (
        <div className="flex flex-col h-[500px] rounded-xl border border-border bg-card overflow-hidden">
            {/* Header */}
            <div className="flex items-center gap-3 p-4 border-b border-border bg-primary/5">
                <div className="w-10 h-10 rounded-full gradient-primary flex items-center justify-center">
                    <Bot className="w-5 h-5 text-white" />
                </div>
                <div>
                    <h3 className="font-semibold">AI Maintenance Copilot</h3>
                    <p className="text-xs text-muted-foreground">Powered by PredictrAI</p>
                </div>
                <div className="ml-auto flex items-center gap-1 px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-500 text-xs">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    Online
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={`flex gap-3 ${message.role === "user" ? "flex-row-reverse" : ""}`}
                    >
                        <div
                            className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${message.role === "user"
                                    ? "bg-primary text-primary-foreground"
                                    : "bg-muted"
                                }`}
                        >
                            {message.role === "user" ? (
                                <User className="w-4 h-4" />
                            ) : (
                                <Sparkles className="w-4 h-4 text-primary" />
                            )}
                        </div>
                        <div
                            className={`max-w-[80%] p-3 rounded-xl ${message.role === "user"
                                    ? "bg-primary text-primary-foreground"
                                    : "bg-muted"
                                }`}
                        >
                            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                            <p
                                className={`text-xs mt-1 ${message.role === "user"
                                        ? "text-primary-foreground/70"
                                        : "text-muted-foreground"
                                    }`}
                            >
                                {message.timestamp.toLocaleTimeString()}
                            </p>
                        </div>
                    </div>
                ))}
                {chatMutation.isPending && (
                    <div className="flex gap-3">
                        <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                            <Loader2 className="w-4 h-4 text-primary animate-spin" />
                        </div>
                        <div className="bg-muted p-3 rounded-xl">
                            <div className="flex gap-1">
                                <span className="w-2 h-2 rounded-full bg-muted-foreground/50 animate-bounce" style={{ animationDelay: "0ms" }} />
                                <span className="w-2 h-2 rounded-full bg-muted-foreground/50 animate-bounce" style={{ animationDelay: "150ms" }} />
                                <span className="w-2 h-2 rounded-full bg-muted-foreground/50 animate-bounce" style={{ animationDelay: "300ms" }} />
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-border">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleSend()}
                        placeholder="Ask about anomalies, maintenance, or asset health..."
                        className="flex-1 px-4 py-3 rounded-lg bg-background border border-input focus:border-primary outline-none"
                    />
                    <button
                        onClick={handleSend}
                        disabled={chatMutation.isPending || !input.trim()}
                        className="px-4 py-3 rounded-lg gradient-primary text-white hover:opacity-90 disabled:opacity-50 transition-opacity"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </div>
            </div>
        </div>
    );
}
