"use client";

import React, { useState, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useChat } from "@/context/ChatContext";
import { useTheme } from "@/context/ThemeContext";
import {
  FiMessageSquare,
  FiCpu,
  FiSettings,
  FiLogOut,
  FiPlus,
  FiTrash2,
  FiEdit3,
  FiMenu,
  FiX,
  FiCheck,
  FiCheckSquare,
  FiBriefcase,
  FiBookOpen,
  FiSearch,
  FiCompass,
} from "react-icons/fi";
import Link from "next/link";

export default function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const { theme } = useTheme();
  const {
    threads,
    activeThreadId,
    setActiveThreadId,
    createNewThread,
    deleteThread,
    renameThread,
    companions,
    changeThreadMode,
  } = useChat();

  const [isOpen, setIsOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [localDefaultMode, setLocalDefaultMode] = useState<"personal" | "professional" | "academic" | "researcher" | "playground">("personal");

  // Load default mode from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("aetheria_default_session_mode");
    if (saved && ["personal", "professional", "academic", "researcher", "playground"].includes(saved)) {
      setLocalDefaultMode(saved as any);
    }
  }, []);

  const activeThread = threads.find((t) => t.id === activeThreadId);
  const currentMode = activeThread?.sessionMode || localDefaultMode;

  const handleModeChange = async (modeId: "personal" | "professional" | "academic" | "researcher" | "playground") => {
    localStorage.setItem("aetheria_default_session_mode", modeId);
    setLocalDefaultMode(modeId);
    if (activeThread) {
      await changeThreadMode(activeThread.id, modeId);
    }
  };

  const mainLinks = [
    { name: "AI Companion Chat", href: "/dashboard", icon: FiMessageSquare },
    { name: "Memory Dashboard", href: "/dashboard/memory", icon: FiCpu },
    { name: "Tasks Dashboard", href: "/dashboard/tasks", icon: FiCheckSquare },
    { name: "Settings Portal", href: "/dashboard/settings", icon: FiSettings },
  ];

  const workspaceModes = [
    { id: "personal", name: "Personal", icon: FiMessageSquare, desc: "Bhai mode & private chat" },
    { id: "professional", name: "Professional", icon: FiBriefcase, desc: "Automation & resume pipeline" },
    { id: "academic", name: "Academic", icon: FiBookOpen, desc: "Step-by-step tutoring" },
    { id: "researcher", name: "Researcher", icon: FiSearch, desc: "Web search & citations" },
    { id: "playground", name: "Playground", icon: FiCompass, desc: "Custom temp & engines" },
  ] as const;

  const handleStartRename = (id: string, currentTitle: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(id);
    setEditTitle(currentTitle);
  };

  const saveRename = (id: string) => {
    if (editTitle.trim()) {
      renameThread(id, editTitle.trim());
    }
    setEditingId(null);
  };

  const handleSaveRename = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    saveRename(id);
  };

  const handleCreateNewChat = () => {
    // Spawn chat with active mode pre-selected
    createNewThread("aria", undefined, currentMode);
    router.push("/dashboard");
  };

  const handleLogout = () => {
    router.push("/login");
  };

  return (
    <>
      {/* Mobile Drawer Trigger Bar */}
      <div className="flex md:hidden items-center justify-between px-4 py-3 bg-white dark:bg-zinc-950 border-b border-zinc-200/50 dark:border-zinc-800/80 z-40 w-full">
        <div className="flex items-center gap-2">
          <span className="text-xl">🌌</span>
          <span className="font-bold tracking-tight bg-gradient-to-r from-cyan-500 to-indigo-500 bg-clip-text text-transparent">
            AETHERIA
          </span>
        </div>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="p-2 rounded-xl border border-zinc-200/60 dark:border-zinc-800 text-zinc-600 dark:text-zinc-400"
        >
          {isOpen ? <FiX className="w-5 h-5" /> : <FiMenu className="w-5 h-5" />}
        </button>
      </div>

      {/* Main Sidebar Shell */}
      <div
        className={`
          fixed inset-y-0 left-0 z-30 w-72 transform flex flex-col justify-between
          border-r border-zinc-200/50 dark:border-zinc-800/80 transition-all duration-300 ease-in-out
          bg-zinc-50/90 dark:bg-[#0b0b0d]/95 backdrop-blur-md md:relative md:translate-x-0
          ${isOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        {/* Upper Header Container */}
        <div className="flex flex-col flex-1 min-h-0">
          <div className="flex items-center justify-between px-6 py-5.5 border-b border-zinc-200/50 dark:border-zinc-800/80">
            <Link href="/dashboard" className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-400 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-cyan-500/10">
                🌌
              </div>
              <span className="font-bold tracking-tight text-[17px] bg-gradient-to-r from-cyan-500 to-indigo-500 bg-clip-text text-transparent">
                AETHERIA
              </span>
            </Link>
            <span className="text-[10px] font-bold tracking-wider font-mono text-zinc-400 dark:text-zinc-500 uppercase px-2 py-0.5 rounded bg-zinc-200/50 dark:bg-zinc-800/50 border border-zinc-300/30 dark:border-zinc-700/30">
              v1.0
            </span>
          </div>

          {/* Navigation Links */}
          <div className="px-4 py-3 space-y-1">
            {mainLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.name}
                  href={link.href}
                  onClick={() => setIsOpen(false)}
                  className={`
                    flex items-center gap-3 px-3 py-2 rounded-xl text-[13.5px] font-medium transition-all
                    ${
                      isActive
                        ? "bg-indigo-500/10 dark:bg-cyan-500/10 text-indigo-600 dark:text-cyan-400 border border-indigo-500/20 dark:border-cyan-500/20"
                        : "text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200/50 dark:hover:bg-zinc-900/60 border border-transparent"
                    }
                  `}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-indigo-600 dark:text-cyan-400" : ""}`} />
                  <span>{link.name}</span>
                </Link>
              );
            })}
          </div>

          {/* Workspace Mode Selector */}
          <div className="px-4 py-2 border-t border-zinc-200/20 dark:border-zinc-800/40">
            <span className="text-[10px] font-bold tracking-widest font-mono text-zinc-400 dark:text-zinc-500 uppercase px-2">
              Workspace Mode
            </span>
            <div className="mt-2 space-y-1 bg-zinc-200/30 dark:bg-zinc-900/30 p-1 rounded-xl border border-zinc-200/40 dark:border-zinc-800/40">
              {workspaceModes.map((mode) => {
                const Icon = mode.icon;
                const isActive = currentMode === mode.id;
                return (
                  <button
                    key={mode.id}
                    onClick={() => handleModeChange(mode.id)}
                    className={`
                      flex items-center justify-between w-full px-2.5 py-1.5 rounded-lg text-left transition-all duration-300 border
                      ${
                        isActive
                          ? "bg-white dark:bg-zinc-900 text-indigo-600 dark:text-cyan-400 border-zinc-200/80 dark:border-zinc-800/80 shadow-[0_2px_8px_rgba(0,0,0,0.06)]"
                          : "text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200/40 dark:hover:bg-zinc-900/40 border-transparent"
                      }
                    `}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <div className={`p-1 rounded-md transition-colors ${isActive ? "bg-indigo-500/10 dark:bg-cyan-500/10" : "bg-transparent"}`}>
                        <Icon className={`w-3.5 h-3.5 ${isActive ? "text-indigo-500 dark:text-cyan-400" : "text-zinc-400 dark:text-zinc-500"}`} />
                      </div>
                      <div className="min-w-0">
                        <span className="text-[12.5px] font-medium block leading-none">{mode.name}</span>
                        <span className="text-[9px] text-zinc-400 dark:text-zinc-500 block truncate mt-0.5">{mode.desc}</span>
                      </div>
                    </div>
                    {isActive && (
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 dark:bg-cyan-400 mr-1" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Chat Threads Section */}
          <div className="flex-1 flex flex-col min-h-0 px-4 mt-2 border-t border-zinc-200/20 dark:border-zinc-800/40 pt-3">
            <div className="flex items-center justify-between px-3 mb-2">
              <span className="text-[10px] font-bold tracking-widest font-mono text-zinc-400 dark:text-zinc-500 uppercase">
                Active Threads
              </span>
              <button
                onClick={handleCreateNewChat}
                className="p-1 rounded bg-zinc-200/60 dark:bg-zinc-900 hover:bg-zinc-300 dark:hover:bg-zinc-800 text-zinc-600 dark:text-cyan-400 transition"
                title="Create New Thread"
              >
                <FiPlus className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Scrollable threads list */}
            <div className="flex-1 overflow-y-auto space-y-1 pr-1">
              {threads.map((thread) => {
                const companion = companions.find((c) => c.id === thread.companionId);
                const isSelected = activeThreadId === thread.id && pathname === "/dashboard";
                const isEditing = editingId === thread.id;

                return (
                  <div
                    key={thread.id}
                    onClick={() => {
                      if (!isEditing) {
                        setActiveThreadId(thread.id);
                        router.push("/dashboard");
                        setIsOpen(false);
                      }
                    }}
                    className={`
                      group relative flex items-center justify-between px-3 py-2.5 rounded-xl text-[13.5px] cursor-pointer transition border
                      ${
                        isSelected
                          ? theme === "dark"
                            ? "bg-zinc-900/70 text-zinc-100 border-zinc-800/80 shadow-sm"
                            : "bg-white text-zinc-800 border-zinc-200 shadow-sm"
                          : "text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300 border-transparent hover:bg-zinc-200/30 dark:hover:bg-zinc-900/20"
                      }
                    `}
                  >
                    <div className="flex items-center gap-2.5 w-full min-w-0 pr-12">
                      <span className="text-[15px]">{companion?.avatar || "🧬"}</span>
                      {isEditing ? (
                        <input
                          type="text"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          className="bg-transparent text-zinc-800 dark:text-zinc-200 focus:outline-none w-full border-b border-indigo-500 py-0.5"
                          autoFocus
                          onClick={(e) => e.stopPropagation()}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") {
                              e.stopPropagation();
                              saveRename(thread.id);
                            }
                          }}
                        />
                      ) : (
                        <div className="flex flex-col min-w-0">
                          <span className="truncate font-medium leading-tight">{thread.title}</span>
                          {thread.sessionMode && (
                            <span className="text-[9px] uppercase font-bold text-zinc-400 dark:text-zinc-500 mt-0.5 tracking-wider">
                              {thread.sessionMode} Mode
                            </span>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Inline actions list */}
                    <div className="absolute right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity bg-zinc-50/90 dark:bg-zinc-950/80 rounded pl-1.5 py-0.5">
                      {isEditing ? (
                        <button
                          onClick={(e) => handleSaveRename(thread.id, e)}
                          className="p-1 text-emerald-500 hover:bg-zinc-200 dark:hover:bg-zinc-800 rounded"
                        >
                          <FiCheck className="w-3.5 h-3.5" />
                        </button>
                      ) : (
                        <>
                          <button
                            onClick={(e) => handleStartRename(thread.id, thread.title, e)}
                            className="p-1 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 hover:bg-zinc-200 dark:hover:bg-zinc-800 rounded"
                          >
                            <FiEdit3 className="w-3 h-3" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteThread(thread.id);
                            }}
                            className="p-1 text-zinc-400 hover:text-red-400 hover:bg-zinc-200 dark:hover:bg-zinc-800 rounded"
                          >
                            <FiTrash2 className="w-3 h-3" />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Lower User Info Bar */}
        <div className="p-4 border-t border-zinc-200/50 dark:border-zinc-800/80 bg-zinc-100/50 dark:bg-zinc-950/30">
          <div className="flex items-center justify-between">
            <Link href="/dashboard/settings" className="flex items-center gap-3 min-w-0 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-400 to-indigo-500 flex items-center justify-center text-white font-bold shadow-md shadow-indigo-500/10">
                JD
              </div>
              <div className="min-w-0">
                <p className="text-[13.5px] font-semibold text-zinc-700 dark:text-zinc-300 truncate group-hover:text-cyan-500 transition">
                  Jane Developer
                </p>
                <span className="text-[10px] font-medium font-mono text-zinc-400 dark:text-zinc-500 uppercase tracking-wider">
                  Pro Account
                </span>
              </div>
            </Link>
            <button
              onClick={handleLogout}
              className="p-2 text-zinc-400 hover:text-red-400 rounded-xl hover:bg-zinc-200/50 dark:hover:bg-zinc-900/60 transition"
              title="Logout Account"
            >
              <FiLogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer Overlay Backdrop */}
      {isOpen && (
        <div
          onClick={() => setIsOpen(false)}
          className="fixed inset-0 bg-black/30 dark:bg-black/60 backdrop-blur-xs z-20 md:hidden"
        />
      )}
    </>
  );
}

