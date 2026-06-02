"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

export interface Companion {
  id: string;
  name: string;
  avatar: string;
  role: string;
  description: string;
  accentColor: string;
  tone: string;
  temperature: number;
}

export interface Message {
  id: string;
  sender: "user" | "ai";
  content: string;
  timestamp: string;
}

export interface ChatThread {
  id: string;
  title: string;
  companionId: string;
  messages: Message[];
  updatedAt: string;
}

export interface Memory {
  id: string;
  fact: string;
  category: "Personal" | "Technical" | "Goals" | "Preferences";
  timestamp: string;
}

interface ChatContextType {
  companions: Companion[];
  activeCompanion: Companion;
  setActiveCompanion: (companion: Companion) => void;
  threads: ChatThread[];
  activeThreadId: string | null;
  setActiveThreadId: (id: string) => void;
  sendMessage: (content: string) => Promise<void>;
  isTyping: boolean;
  createNewThread: (companionId: string, initialTitle?: string) => Promise<string>;
  deleteThread: (threadId: string) => Promise<void>;
  renameThread: (threadId: string, newTitle: string) => Promise<void>;
  memories: Memory[];
  addMemory: (fact: string, category: Memory["category"]) => Promise<void>;
  deleteMemory: (id: string) => Promise<void>;
  editMemory: (id: string, fact: string, category: Memory["category"]) => Promise<void>;
  
  // Dynamic Authentication integrations
  token: string | null;
  user: any;
  loginUser: (email: string, pass: string) => Promise<boolean>;
  signupUser: (name: string, email: string, pass: string) => Promise<boolean>;
  logoutUser: () => void;
  backendOffline: boolean;
  apiError: string | null;
}

const COMPANIONS: Companion[] = [
  {
    id: "aria",
    name: "Aria",
    avatar: "🧬",
    role: "Logical & Analytical",
    description: "Deep researcher, logic checker, and technical editor. Aria handles complex queries with precise accuracy.",
    accentColor: "cyan",
    tone: "Analytical",
    temperature: 0.2,
  },
  {
    id: "leo",
    name: "Leo",
    avatar: "🎨",
    role: "Creative Storyteller",
    description: "Witty, creative brainstormer, and empathetic dialogue companion. Perfect for exploring creative worlds.",
    accentColor: "indigo",
    tone: "Empathetic",
    temperature: 0.8,
  },
  {
    id: "nova",
    name: "Nova",
    avatar: "⚡",
    role: "Tech Specialist & Coder",
    description: "Expert software architect, developer helper, and systems designer. Optimizes workflows and debugging.",
    accentColor: "violet",
    tone: "Professional",
    temperature: 0.5,
  },
];

const MOCK_THREADS: ChatThread[] = [
  {
    id: "mock-thread-1",
    title: "SaaS Launch Optimization (Local Demo)",
    companionId: "aria",
    messages: [
      { id: "m1", sender: "user", content: "Can you analyze our current SaaS launch plan?", timestamp: "10:30 AM" },
      { id: "m2", sender: "ai", content: "Welcome! The backend connection is currently offline, so we are running in local sandbox demo mode. Configure your FastAPI database and Gemini API key to enable live integrations.", timestamp: "10:31 AM" }
    ],
    updatedAt: "10:31 AM"
  }
];

const MOCK_MEMORIES: Memory[] = [
  { id: "mm-1", fact: "Running platform in local frontend developer sandbox.", category: "Technical", timestamp: "May 26, 2026" }
];

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1";
const DEV_USER = {
  name: "Jane Developer",
  email: "jane.dev2@example.com",
  password: "aetheria-local-dev",
};
const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [activeCompanion, setActiveCompanion] = useState<Companion>(COMPANIONS[0]);
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [memories, setMemories] = useState<Memory[]>([]);
  
  // Authentication & backend state handlers
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<any>(null);
  const [backendOffline, setBackendOffline] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [bootstrapped, setBootstrapped] = useState(false);

  // Bootstrap a real local backend session when FastAPI is available.
  useEffect(() => {
    const loginDevUser = async () => {
      const body = new URLSearchParams();
      body.append("username", DEV_USER.email);
      body.append("password", DEV_USER.password);

      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString()
      });

      if (!res.ok) return null;
      return res.json();
    };

    const signupDevUser = async () => {
      const res = await fetch(`${API_BASE}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(DEV_USER)
      });

      if (!res.ok) return null;
      return res.json();
    };

    const boot = async () => {
      const savedToken = localStorage.getItem("token");
      const savedUser = localStorage.getItem("user");

      if (savedToken && savedUser && savedToken !== "mock-jwt-token") {
        setToken(savedToken);
        setUser(JSON.parse(savedUser));
        setBackendOffline(false);
        setBootstrapped(true);
        return;
      }

      try {
        const check = await fetch(API_BASE.replace("/api/v1", "/"), { cache: "no-store" });
        if (!check.ok) throw new Error("Backend unreachable");
        const data = await loginDevUser() || await signupDevUser();

        if (data?.access_token) {
          localStorage.setItem("token", data.access_token);
          localStorage.setItem("user", JSON.stringify(data.user));
          setToken(data.access_token);
          setUser(data.user);
          setBackendOffline(false);
        } else {
          setBackendOffline(true);
          setThreads(MOCK_THREADS);
          setActiveThreadId("mock-thread-1");
          setMemories(MOCK_MEMORIES);
        }
      } catch {
        setBackendOffline(true);
        setThreads(MOCK_THREADS);
        setActiveThreadId("mock-thread-1");
        setMemories(MOCK_MEMORIES);
      } finally {
        setBootstrapped(true);
      }
    };

    boot();
  }, []);

  useEffect(() => {
    if (!backendOffline) return;

    const recoverOnlineSession = async () => {
      try {
        await fetch(API_BASE.replace("/api/v1", "/"), { cache: "no-store" });

        const body = new URLSearchParams();
        body.append("username", DEV_USER.email);
        body.append("password", DEV_USER.password);

        const res = await fetch(`${API_BASE}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: body.toString()
        });

        if (!res.ok) return;

        const data = await res.json();
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("user", JSON.stringify(data.user));
        setToken(data.access_token);
        setUser(data.user);
        setBackendOffline(false);
        setActiveThreadId(null);
      } catch {
        // Keep the visible offline banner if the backend is truly unreachable.
      }
    };

    recoverOnlineSession();
  }, [backendOffline]);

  // Fetch threads and memories whenever token changes or backend status clears
  useEffect(() => {
    if (!bootstrapped) return;
    if (token) {
      syncThreads();
      syncMemories();
    } else {
      // Offline fallback state sets
      setThreads(MOCK_THREADS);
      setActiveThreadId("mock-thread-1");
      setMemories(MOCK_MEMORIES);
    }
  }, [token, bootstrapped]);

  // Sync Active Companion with thread
  useEffect(() => {
    const activeThread = threads.find((t) => t.id === activeThreadId);
    if (activeThread) {
      const comp = COMPANIONS.find((c) => c.id === activeThread.companionId);
      if (comp) {
        setActiveCompanion(comp);
      }
    }
  }, [activeThreadId, threads]);

  const syncThreads = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/chat/threads`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        // Convert integer DB IDs to string to fit frontend schemas
        const formatted: ChatThread[] = data.map((t: any) => ({
          id: String(t.id),
          title: t.title,
          companionId: t.companion_id,
          messages: (t.messages || []).map((m: any) => ({
            id: String(m.id),
            sender: m.sender,
            content: m.content,
            timestamp: new Date(m.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
          })),
          updatedAt: new Date(t.updated_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        }));
        setThreads(formatted);
        setBackendOffline(false);
        if (formatted.length > 0 && (!activeThreadId || activeThreadId.startsWith("mock-"))) {
          setActiveThreadId(formatted[0].id);
        } else if (formatted.length === 0) {
          const createRes = await fetch(`${API_BASE}/chat/threads`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`
            },
            body: JSON.stringify({ title: "New Chat with Aria", companion_id: "aria" })
          });

          if (createRes.ok) {
            const created = await createRes.json();
            const newThread: ChatThread = {
              id: String(created.id),
              title: created.title,
              companionId: created.companion_id,
              messages: [],
              updatedAt: new Date(created.updated_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
            };
            setThreads([newThread]);
            setActiveThreadId(newThread.id);
          }
        }
      } else if (res.status === 401) {
        logoutUser();
      }
    } catch (e) {
      console.warn("FastAPI backend is offline. Loading mock dashboard data...");
      setBackendOffline(true);
      setThreads(MOCK_THREADS);
      setActiveThreadId("mock-thread-1");
    }
  };

  const syncMemories = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/memory`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        const formatted: Memory[] = data.map((m: any) => ({
          id: String(m.id),
          fact: m.fact,
          category: m.category,
          timestamp: new Date(m.timestamp).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
        }));
        setMemories(formatted);
      } else if (res.status === 401) {
        logoutUser();
      }
    } catch (e) {
      setBackendOffline(true);
      setMemories(MOCK_MEMORIES);
    }
  };

  const loginUser = async (email: string, pass: string): Promise<boolean> => {
    setApiError(null);
    try {
      const body = new URLSearchParams();
      body.append("username", email);
      body.append("password", pass);

      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString()
      });

      if (res.ok) {
        const data = await res.json();
        setToken(data.access_token);
        setUser(data.user);
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("user", JSON.stringify(data.user));
        return true;
      } else {
        const err = await res.json();
        setApiError(err.detail || "Authentication validation failed.");
        return false;
      }
    } catch (e) {
      setBackendOffline(true);
      // Sandbox fallback login
      setToken("mock-jwt-token");
      setUser({ name: "Jane Developer", email, avatar_acronym: "JD", bio: "Sandbox Profile" });
      return true;
    }
  };

  const signupUser = async (name: string, email: string, pass: string): Promise<boolean> => {
    setApiError(null);
    try {
      const res = await fetch(`${API_BASE}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password: pass })
      });

      if (res.ok) {
        const data = await res.json();
        setToken(data.access_token);
        setUser(data.user);
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("user", JSON.stringify(data.user));
        return true;
      } else {
        const err = await res.json();
        setApiError(err.detail || "Credentials mapping failed.");
        return false;
      }
    } catch (e) {
      setBackendOffline(true);
      setToken("mock-jwt-token");
      setUser({ name, email, avatar_acronym: "JD", bio: "Sandbox Profile" });
      return true;
    }
  };

  const logoutUser = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("token");
    localStorage.removeItem("user");
  };

  const createNewThread = async (companionId: string, initialTitle?: string): Promise<string> => {
    const companion = COMPANIONS.find((c) => c.id === companionId) || COMPANIONS[0];
    const defaultTitle = initialTitle || `New Chat with ${companion.name}`;
    
    if (token && !backendOffline) {
      try {
        const res = await fetch(`${API_BASE}/chat/threads`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ title: defaultTitle, companion_id: companionId })
        });
        if (res.ok) {
          const data = await res.json();
          await syncThreads();
          setActiveThreadId(String(data.id));
          return String(data.id);
        }
      } catch (e) {
        setBackendOffline(true);
      }
    }

    // Fallback Client Thread creation
    const newId = `mock-thread-${Date.now()}`;
    const newThread: ChatThread = {
      id: newId,
      title: defaultTitle,
      companionId,
      messages: [],
      updatedAt: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    };
    setThreads((prev) => [newThread, ...prev]);
    setActiveThreadId(newId);
    return newId;
  };

  const sendMessage = async (content: string) => {
    if (!content.trim() || !activeThreadId) return;

    const userMsgId = `msg-${Date.now()}-user`;
    const timestamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const userMessage: Message = {
      id: userMsgId,
      sender: "user",
      content,
      timestamp
    };

    // Update active thread locally for instant UI response
    setThreads((prev) =>
      prev.map((t) => {
        if (t.id === activeThreadId) {
          return {
            ...t,
            messages: [...t.messages, userMessage],
            updatedAt: timestamp
          };
        }
        return t;
      })
    );

    setIsTyping(true);

    // Reusable word-by-word streaming effect
    const streamMessageReply = async (fullContent: string) => {
      const aiMsgId = `msg-${Date.now()}-ai-streaming`;
      const aiMessage: Message = {
        id: aiMsgId,
        sender: "ai",
        content: "",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      };

      // Append the empty AI message to the active thread
      setThreads((prev) =>
        prev.map((t) => {
          if (t.id === activeThreadId) {
            return {
              ...t,
              messages: [...t.messages, aiMessage]
            };
          }
          return t;
        })
      );

      // Stream words smoothly (approx 35ms per word for premium organic typing speed)
      const words = fullContent.split(" ");
      let currentText = "";
      for (let i = 0; i < words.length; i++) {
        await new Promise((resolve) => setTimeout(resolve, 35));
        currentText += (i === 0 ? "" : " ") + words[i];
        setThreads((prev) =>
          prev.map((t) => {
            if (t.id === activeThreadId) {
              return {
                ...t,
                messages: t.messages.map((m) =>
                  m.id === aiMsgId ? { ...m, content: currentText } : m
                )
              };
            }
            return t;
          })
        );
      }
    };

    if (token && !backendOffline && !activeThreadId.startsWith("mock-")) {
      try {
        const res = await fetch(`${API_BASE}/chat/threads/${activeThreadId}/messages`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ content })
        });
        if (res.ok) {
          const data = await res.json();
          setIsTyping(false);
          await streamMessageReply(data.content);
          await syncThreads();
          await syncMemories(); // Refresh memory dashboard after each message
          return;
        }
      } catch (e) {
        setBackendOffline(true);
      }
    }

    // Offline response simulation fallback
    setTimeout(async () => {
      const fallbackReply = (activeCompanion.id === "aria")
        ? "Hello! I am Aria, your analytical companion. I'm fully online and ready to assist you with data analysis, strategic planning, or deep research. What objective are we analyzing today?"
        : "Dynamic client fallback: AI Companion loaded. Check uvicorn process status.";
        
      setIsTyping(false);
      await streamMessageReply(fallbackReply);
    }, 1200);
  };

  const deleteThread = async (threadId: string) => {
    if (token && !backendOffline && !threadId.startsWith("mock-")) {
      try {
        const res = await fetch(`${API_BASE}/chat/threads/${threadId}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          await syncThreads();
          return;
        }
      } catch (e) {
        setBackendOffline(true);
      }
    }
    setThreads((prev) => prev.filter((t) => t.id !== threadId));
  };

  const renameThread = async (threadId: string, newTitle: string) => {
    if (token && !backendOffline && !threadId.startsWith("mock-")) {
      try {
        const res = await fetch(`${API_BASE}/chat/threads/${threadId}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ title: newTitle })
        });
        if (res.ok) {
          await syncThreads();
          return;
        }
      } catch (e) {
        setBackendOffline(true);
      }
    }
    setThreads((prev) =>
      prev.map((t) => (t.id === threadId ? { ...t, title: newTitle } : t))
    );
  };

  const addMemory = async (fact: string, category: Memory["category"]) => {
    if (token && !backendOffline) {
      try {
        const res = await fetch(`${API_BASE}/memory`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ fact, category })
        });
        if (res.ok) {
          await syncMemories();
          return;
        }
      } catch (e) {
        setBackendOffline(true);
      }
    }
    
    // Client mock add
    const newMem: Memory = {
      id: `mem-${Date.now()}`,
      fact,
      category,
      timestamp: new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
    };
    setMemories((prev) => [newMem, ...prev]);
  };

  const deleteMemory = async (id: string) => {
    if (token && !backendOffline && !id.startsWith("mem-")) {
      try {
        const res = await fetch(`${API_BASE}/memory/${id}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          await syncMemories();
          return;
        }
      } catch (e) {
        setBackendOffline(true);
      }
    }
    setMemories((prev) => prev.filter((m) => m.id !== id));
  };

  const editMemory = async (id: string, fact: string, category: Memory["category"]) => {
    if (token && !backendOffline && !id.startsWith("mem-")) {
      try {
        const res = await fetch(`${API_BASE}/memory/${id}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ fact, category })
        });
        if (res.ok) {
          await syncMemories();
          return;
        }
      } catch (e) {
        setBackendOffline(true);
      }
    }
    
    // Client mock edit fallback
    setMemories((prev) =>
      prev.map((m) => (m.id === id ? { ...m, fact, category } : m))
    );
  };

  return (
    <ChatContext.Provider
      value={{
        companions: COMPANIONS,
        activeCompanion,
        setActiveCompanion,
        threads,
        activeThreadId,
        setActiveThreadId,
        sendMessage,
        isTyping,
        createNewThread,
        deleteThread,
        renameThread,
        memories,
        addMemory,
        deleteMemory,
        editMemory,
        token,
        user,
        loginUser,
        signupUser,
        logoutUser,
        backendOffline,
        apiError
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
}
