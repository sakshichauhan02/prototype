"use client";

import React, { useState, useRef, useEffect } from "react";
import { useChat } from "@/context/ChatContext";
import Sidebar from "@/components/Sidebar";
import ChatBubble from "@/components/ChatBubble";
import TypingLoader from "@/components/TypingLoader";
import ThemeToggle from "@/components/ThemeToggle";
import GlassCard from "@/components/GlassCard";
import { FiSend, FiPlus, FiAlertCircle, FiCpu, FiMessageSquare } from "react-icons/fi";

export default function ChatDashboard() {
  const {
    companions,
    activeCompanion,
    setActiveCompanion,
    threads,
    activeThreadId,
    sendMessage,
    isTyping,
    createNewThread,
    backendOffline,
    changeThreadMode,
  } = useChat();

  const [inputMsg, setInputMsg] = useState("");
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const activeThread = threads.find((t) => t.id === activeThreadId) || null;

  // Scroll to bottom on messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [activeThread?.messages, isTyping]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMsg.trim() || !activeThreadId) return;
    sendMessage(inputMsg);
    setInputMsg("");
  };

  const handlePromptSuggestion = (promptText: string) => {
    if (!activeThreadId) return;
    sendMessage(promptText);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-zinc-50 dark:bg-zinc-950 font-sans">
      {/* Responsive Sidebar component */}
      <Sidebar />

      {/* Main Board Pane */}
      <div className="flex-1 flex flex-col min-w-0 h-full relative">
        {/* Top Navbar */}
        <header className="h-16 flex items-center justify-between px-6 border-b border-zinc-200/50 dark:border-zinc-800/85 bg-white/70 dark:bg-zinc-950/70 backdrop-blur-md z-10">
          <div className="flex items-center gap-3">
            {activeThread && (
              <>
                <span className="text-2xl">{activeCompanion.avatar}</span>
                <div>
                  <h2 className="text-[14.5px] font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                    {activeCompanion.name}
                    <span className="text-[10px] uppercase font-bold tracking-wider text-cyan-500 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                      {activeCompanion.tone}
                    </span>
                  </h2>
                  <p className="text-[11px] text-zinc-400 dark:text-zinc-500 truncate max-w-[200px] sm:max-w-md font-medium">
                    {activeCompanion.description}
                  </p>
                </div>
              </>
            )}
          </div>

          <div className="flex items-center gap-4">
            {/* Quick Session Mode Selector in Navbar */}
            {activeThread && (
              <div className="flex items-center gap-1.5 p-1 rounded-xl bg-zinc-100 dark:bg-zinc-900 border border-zinc-200/60 dark:border-zinc-800/80">
                <span className="text-[11px] font-mono font-bold text-zinc-400 dark:text-zinc-500 uppercase ml-2 select-none">Mode:</span>
                <select
                  value={activeThread.sessionMode || "personal"}
                  onChange={(e) => {
                    changeThreadMode(activeThread.id, e.target.value as any);
                  }}
                  className="h-8 px-2 rounded-lg text-[12px] font-bold bg-white dark:bg-zinc-800 border border-zinc-200/35 dark:border-zinc-700/30 text-zinc-800 dark:text-zinc-200 focus:outline-none focus:ring-1 focus:ring-cyan-500 cursor-pointer"
                >
                  <option value="personal">Personal</option>
                  <option value="professional">Professional</option>
                  <option value="academic">Academic</option>
                  <option value="researcher">Researcher</option>
                  <option value="playground">Playground</option>
                </select>
              </div>
            )}

            {/* Quick Companion Selector in Navbar */}
            <div className="hidden lg:flex items-center gap-1.5 p-1 rounded-xl bg-zinc-100 dark:bg-zinc-900 border border-zinc-200/60 dark:border-zinc-800/80">
              {companions.map((comp) => {
                const isSelected = activeCompanion.id === comp.id;
                return (
                  <button
                    key={comp.id}
                    onClick={() => {
                      // Switch companion for current thread
                      setActiveCompanion(comp);
                      if (activeThread) {
                        activeThread.companionId = comp.id;
                      }
                    }}
                    className={`
                      px-3 py-1.5 rounded-lg text-[12px] font-bold transition flex items-center gap-1 cursor-pointer
                      ${
                        isSelected
                          ? "bg-white dark:bg-zinc-800 text-zinc-900 dark:text-white shadow-sm border border-zinc-200/30 dark:border-zinc-700/30"
                          : "text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-400"
                      }
                    `}
                  >
                    <span>{comp.avatar}</span>
                    <span>{comp.name}</span>
                  </button>
                );
              })}
            </div>
            <ThemeToggle />
          </div>
        </header>

        {/* Offline Alert Banner */}
        {backendOffline && (
          <div className="bg-amber-500/10 border-b border-amber-500/20 text-amber-600 dark:text-amber-400 px-6 py-2.5 text-[12px] font-semibold flex items-center gap-2 select-none">
            <FiAlertCircle className="w-4 h-4 text-amber-500 shrink-0" />
            <span>Backend is offline. Running in local frontend sandbox (RAG features and Gemini keys bypassed).</span>
          </div>
        )}

        {/* Dynamic Conversational Space */}
        <main className="flex-1 overflow-y-auto px-4 md:px-6 py-6 scroll-smooth bg-zinc-50/50 dark:bg-[#080809]/40 relative">
          <div className="max-w-3xl mx-auto min-h-full flex flex-col">
            {activeThread ? (
              activeThread.messages.length === 0 ? (
                /* Welcoming intro screen for empty chats */
                <div className="my-auto py-12 flex flex-col items-center text-center space-y-8">
                  <div className="w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-500 flex items-center justify-center text-2xl shadow-[0_0_20px_rgba(6,182,212,0.1)]">
                    {activeCompanion.avatar}
                  </div>
                  <div className="space-y-3">
                    <h1 className="text-3xl font-extrabold tracking-tight text-zinc-900 dark:text-white">
                      Meet {activeCompanion.name}
                    </h1>
                    <p className="text-[14.5px] text-zinc-500 dark:text-zinc-400 max-w-md mx-auto">
                      "{activeCompanion.description}" Adjust cognitive switches in the Settings panel or start querying below.
                    </p>
                  </div>

                  {/* Suggestion Prompt Chips */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-lg mt-6">
                    <button
                      onClick={() => handlePromptSuggestion("Can you analyze our current SaaS launch plan? We want to prioritize organic developer marketing.")}
                      className="p-4.5 rounded-xl border border-zinc-200/60 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/60 text-left hover:border-cyan-500 dark:hover:border-cyan-500 text-[13.5px] hover:scale-[1.01] transition duration-200 cursor-pointer shadow-black/5"
                    >
                      <span className="font-bold text-zinc-800 dark:text-zinc-200 block mb-1">💡 SaaS Organic Plan</span>
                      <p className="text-[12px] text-zinc-500 dark:text-zinc-400 font-normal leading-normal">
                        Analyze SaaS developer launch strategies using interactive playgrounds.
                      </p>
                    </button>

                    <button
                      onClick={() => handlePromptSuggestion("Give me an opening paragraph for a sci-fi story about a world where human memories can be visualised as floating lights.")}
                      className="p-4.5 rounded-xl border border-zinc-200/60 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/60 text-left hover:border-indigo-500 dark:hover:border-indigo-500 text-[13.5px] hover:scale-[1.01] transition duration-200 cursor-pointer shadow-black/5"
                    >
                      <span className="font-bold text-zinc-800 dark:text-zinc-200 block mb-1">✍️ Sci-Fi Creative Spark</span>
                      <p className="text-[12px] text-zinc-500 dark:text-zinc-400 font-normal leading-normal">
                        Explore creative prompts describing cities of Lumina and memory particles.
                      </p>
                    </button>

                    <button
                      onClick={() => handlePromptSuggestion("Explain the main advantages of client-side contexts in NextJS 15 App router.")}
                      className="p-4.5 rounded-xl border border-zinc-200/60 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/60 text-left hover:border-cyan-500 dark:hover:border-cyan-500 text-[13.5px] hover:scale-[1.01] transition duration-200 cursor-pointer shadow-black/5"
                    >
                      <span className="font-bold text-zinc-800 dark:text-zinc-200 block mb-1">💻 Next.js 15 App Router</span>
                      <p className="text-[12px] text-zinc-500 dark:text-zinc-400 font-normal leading-normal">
                        Optimal coding conventions for client provider context hooks.
                      </p>
                    </button>

                    <button
                      onClick={() => handlePromptSuggestion("Remember that user drinks coffee black and works in the morning.")}
                      className="p-4.5 rounded-xl border border-zinc-200/60 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/60 text-left hover:border-amber-500 dark:hover:border-amber-500 text-[13.5px] hover:scale-[1.01] transition duration-200 cursor-pointer shadow-black/5"
                    >
                      <span className="font-bold text-zinc-800 dark:text-zinc-200 block mb-1">🧠 Add to Cognitive Vault</span>
                      <p className="text-[12px] text-zinc-500 dark:text-zinc-400 font-normal leading-normal">
                        Simulate logging facts into the companion's core memory storage.
                      </p>
                    </button>
                  </div>
                </div>
              ) : (
                /* Message lists */
                <div className="flex-1">
                  {activeThread.messages.map((message) => (
                    <ChatBubble key={message.id} message={message} companion={activeCompanion} />
                  ))}
                  {isTyping && (
                    <div className="flex items-start gap-4 mb-6">
                      <div className="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-xl">
                        {activeCompanion.avatar}
                      </div>
                      <div className="flex flex-col">
                        <span className="text-xs text-zinc-400 dark:text-zinc-500 mb-1.5 font-mono tracking-wider">
                          {activeCompanion.name} is computing...
                        </span>
                        <TypingLoader />
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              )
            ) : (
              /* No Threads Left State */
              <div className="my-auto py-12 flex flex-col items-center text-center space-y-6">
                <div className="w-16 h-16 rounded-2xl bg-zinc-200 dark:bg-zinc-900 flex items-center justify-center text-2xl text-zinc-400 border border-zinc-300/40 dark:border-zinc-800">
                  <FiAlertCircle />
                </div>
                <div className="space-y-2">
                  <h2 className="text-xl font-bold text-zinc-800 dark:text-zinc-200">No active threads found</h2>
                  <p className="text-[13.5px] text-zinc-500 dark:text-zinc-400 max-w-xs mx-auto">
                    Create a new thread using the button below or within the sidebar navigation.
                  </p>
                </div>
                <button
                  onClick={() => createNewThread("aria")}
                  className="px-5 h-10 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-500 hover:opacity-95 text-white text-[13.5px] font-semibold flex items-center gap-2 transition"
                >
                  <FiPlus /> New Thread
                </button>
              </div>
            )}
          </div>
        </main>

        {/* Bottom Fixed input bar */}
        {activeThread && (
          <footer className="px-4 md:px-6 py-5 bg-white/70 dark:bg-zinc-950/70 border-t border-zinc-200/50 dark:border-zinc-850 backdrop-blur-md">
            <div className="max-w-3xl mx-auto">
              <form onSubmit={handleSend} className="relative flex items-center">
                <input
                  type="text"
                  value={inputMsg}
                  onChange={(e) => setInputMsg(e.target.value)}
                  disabled={isTyping}
                  placeholder={`Send prompt to ${activeCompanion.name}... (Try: "Remember that...")`}
                  className="w-full h-13 pl-4 pr-14 rounded-xl text-[14px] bg-zinc-100/60 dark:bg-zinc-900/65 border border-zinc-200/80 dark:border-zinc-800/80 focus:outline-none focus:border-cyan-500 dark:focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 dark:focus:ring-cyan-500 text-zinc-800 dark:text-zinc-200 transition shadow-inner disabled:opacity-60"
                />
                <button
                  type="submit"
                  disabled={!inputMsg.trim() || isTyping}
                  className="absolute right-3.5 w-8.5 h-8.5 rounded-lg bg-gradient-to-r from-cyan-500 to-indigo-500 hover:opacity-95 text-white flex items-center justify-center transition cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed disabled:scale-100 active:scale-95 shadow-md shadow-indigo-500/10"
                >
                  <FiSend className="w-3.5 h-3.5" />
                </button>
              </form>

              {/* Sub-bar tags */}
              <div className="flex items-center justify-between text-[11px] font-mono text-zinc-400 dark:text-zinc-500 mt-3.5 px-1 select-none">
                <span className="flex items-center gap-1">
                  <FiCpu className="w-3 h-3 text-cyan-500" /> Cognitive Engine active
                </span>
                <span className="hidden sm:inline">
                  Enter to prompt, Shift+Enter for multiline
                </span>
              </div>
            </div>
          </footer>
        )}
      </div>
    </div>
  );
}
