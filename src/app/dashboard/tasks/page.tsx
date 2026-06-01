"use client";

import React, { useState, useEffect } from "react";
import { useChat } from "@/context/ChatContext";
import Sidebar from "@/components/Sidebar";
import ThemeToggle from "@/components/ThemeToggle";
import GlassCard from "@/components/GlassCard";
import { 
  FiPlus, 
  FiCheckSquare, 
  FiClock, 
  FiPlusCircle, 
  FiX, 
  FiTrash2, 
  FiCalendar,
  FiActivity,
  FiCpu,
  FiSquare
} from "react-icons/fi";

interface TaskItem {
  id: number;
  user_id: number;
  title: string;
  description: string | null;
  status: string;
  priority: number;
  source: string;
  due_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export default function TasksDashboard() {
  const { token, backendOffline } = useChat();
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [showAddForm, setShowAddForm] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<number>(3);
  const [dueDate, setDueDate] = useState("");

  // Reusable Premium Toast Notification State
  const [toast, setToast] = useState<{ show: boolean; message: string; type: "success" | "error" }>({
    show: false,
    message: "",
    type: "success"
  });

  const triggerToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    // Reset toast state after 3.5s
    setTimeout(() => {
      setToast((prev) => ({ ...prev, show: false }));
    }, 3500);
  };

  const API_BASE = "http://localhost:8000/api/v1";

  // Fetch tasks
  const fetchTasks = async () => {
    setLoading(true);
    setError(null);
    if (!token) {
      // Mock Fallback
      setTasks(getMockTasks());
      setLoading(false);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/tasks`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTasks(data);
      } else {
        setError("Failed to fetch tasks from server.");
        setTasks(getMockTasks());
      }
    } catch (e) {
      setError("Server is unreachable. Displaying sandbox tasks.");
      setTasks(getMockTasks());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, [token]);

  // Create task
  const handleAddTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    const payload = {
      title: title.trim(),
      description: description.trim() || null,
      status: "pending",
      priority,
      source: "manual",
      due_at: dueDate ? new Date(dueDate).toISOString() : null
    };

    if (!token || backendOffline) {
      // Simulate client addition
      const mockNew: TaskItem = {
        id: Date.now(),
        user_id: 1,
        title: payload.title,
        description: payload.description,
        status: payload.status,
        priority: payload.priority,
        source: payload.source,
        due_at: payload.due_at,
        completed_at: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      setTasks((prev) => [mockNew, ...prev]);
      resetForm();
      triggerToast(`Task "${payload.title}" created successfully (Local Sandbox)!`);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/tasks`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const newTask = await res.json();
        setTasks((prev) => [newTask, ...prev]);
        resetForm();
        triggerToast(`Task "${payload.title}" saved to core engine!`);
      } else {
        triggerToast("Could not save task on server.", "error");
      }
    } catch (err) {
      triggerToast("Error contacting tasks backend.", "error");
    }
  };

  // Toggle completed status
  const handleToggleStatus = async (task: TaskItem) => {
    const newStatus = task.status === "completed" ? "pending" : "completed";
    
    if (!token || backendOffline) {
      setTasks((prev) =>
        prev.map((t) =>
          t.id === task.id
            ? { 
                ...t, 
                status: newStatus, 
                completed_at: newStatus === "completed" ? new Date().toISOString() : null 
              }
            : t
        )
      );
      triggerToast(newStatus === "completed" ? "Task marked as completed!" : "Task set back to pending.");
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/tasks/${task.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ status: newStatus })
      });

      if (res.ok) {
        const updated = await res.json();
        setTasks((prev) => prev.map((t) => (t.id === task.id ? updated : t)));
        triggerToast(newStatus === "completed" ? "Task marked as completed!" : "Task set back to pending.");
      }
    } catch (err) {
      console.error("Error toggling task status:", err);
      triggerToast("Failed to update status on server.", "error");
    }
  };

  // Delete task
  const handleDeleteTask = async (taskId: number) => {
    const taskToDelete = tasks.find((t) => t.id === taskId);
    const taskTitle = taskToDelete ? taskToDelete.title : "Task";

    if (!token || backendOffline) {
      setTasks((prev) => prev.filter((t) => t.id !== taskId));
      triggerToast(`Removed task: "${taskTitle}"`);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.ok) {
        setTasks((prev) => prev.filter((t) => t.id !== taskId));
        triggerToast(`Deleted task: "${taskTitle}"`);
      }
    } catch (err) {
      console.error("Error deleting task:", err);
      triggerToast("Failed to delete task from server.", "error");
    }
  };

  const resetForm = () => {
    setTitle("");
    setDescription("");
    setPriority(3);
    setDueDate("");
    setShowAddForm(false);
  };


  const getMockTasks = (): TaskItem[] => {
    return [
      {
        id: 1,
        user_id: 1,
        title: "Setup PostgreSQL local workspace schema",
        description: "Configure async user, memories, tasks, and history logging models.",
        status: "completed",
        priority: 1,
        source: "manual",
        due_at: new Date(Date.now() - 3600000 * 24).toISOString(),
        completed_at: new Date().toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        id: 2,
        user_id: 1,
        title: "Refactor TypeScript context providers",
        description: "Review compilation bottlenecks for Next.js Turbopack dev builds.",
        status: "pending",
        priority: 2,
        source: "AI Agent (Nova)",
        due_at: new Date(Date.now() + 3600000 * 48).toISOString(),
        completed_at: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        id: 3,
        user_id: 1,
        title: "Verify incognito private mode skips DB saves",
        description: "Set private toggle on settings portal and inspect FastAPI server console logs.",
        status: "pending",
        priority: 3,
        source: "AI Agent (Aria)",
        due_at: new Date(Date.now() + 3600000 * 72).toISOString(),
        completed_at: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    ];
  };

  // Stats calculation
  const total = tasks.length;
  const pending = tasks.filter((t) => t.status !== "completed").length;
  const completed = tasks.filter((t) => t.status === "completed").length;
  const aiGenerated = tasks.filter((t) => t.source !== "manual").length;

  return (
    <div className="flex h-screen overflow-hidden bg-zinc-50 dark:bg-zinc-950 font-sans">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 h-full relative">
        {/* Top Navbar */}
        <header className="h-16 flex items-center justify-between px-6 border-b border-zinc-200/50 dark:border-zinc-800/85 bg-white/70 dark:bg-zinc-950/70 backdrop-blur-md z-10">
          <div className="flex items-center gap-2.5">
            <FiCheckSquare className="w-5 h-5 text-cyan-500" />
            <h2 className="text-[15px] font-bold text-zinc-900 dark:text-zinc-100 uppercase tracking-wider">
              Automated Task Workspace
            </h2>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowAddForm(!showAddForm)}
              className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-500 hover:opacity-95 text-white text-[12.5px] font-semibold flex items-center gap-1.5 transition cursor-pointer shadow-md shadow-indigo-500/10"
            >
              <FiPlus /> New Task
            </button>
            <ThemeToggle />
          </div>
        </header>

        {/* Core Layout space */}
        <main className="flex-1 overflow-y-auto px-4 md:px-8 py-8 bg-zinc-50/50 dark:bg-[#080809]/40 relative">
          <div className="max-w-5xl mx-auto space-y-8">
            
            {/* Stats Dashboard Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <GlassCard className="p-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-zinc-100 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-850 flex items-center justify-center text-zinc-500">
                  <FiActivity className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-[11px] font-bold font-mono tracking-widest text-zinc-400 dark:text-zinc-500 uppercase">Total Tasks</p>
                  <h4 className="text-xl font-extrabold text-zinc-800 dark:text-zinc-150">{total}</h4>
                </div>
              </GlassCard>

              <GlassCard className="p-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-500">
                  <FiClock className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-[11px] font-bold font-mono tracking-widest text-zinc-400 dark:text-zinc-500 uppercase">Pending</p>
                  <h4 className="text-xl font-extrabold text-amber-600 dark:text-amber-400">{pending}</h4>
                </div>
              </GlassCard>

              <GlassCard className="p-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-500">
                  <FiCheckSquare className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-[11px] font-bold font-mono tracking-widest text-zinc-400 dark:text-zinc-500 uppercase">Completed</p>
                  <h4 className="text-xl font-extrabold text-emerald-600 dark:text-emerald-400">{completed}</h4>
                </div>
              </GlassCard>

              <GlassCard className="p-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-500">
                  <FiCpu className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-[11px] font-bold font-mono tracking-widest text-zinc-400 dark:text-zinc-500 uppercase">AI Automated</p>
                  <h4 className="text-xl font-extrabold text-indigo-600 dark:text-indigo-400">{aiGenerated}</h4>
                </div>
              </GlassCard>
            </div>

            {/* Inline creation modal */}
            {showAddForm && (
              <GlassCard className="p-6 border border-zinc-250 dark:border-zinc-800 shadow-lg relative max-w-lg mx-auto">
                <button
                  onClick={resetForm}
                  className="absolute right-4 top-4 p-1 rounded-lg text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-900"
                >
                  <FiX className="w-4 h-4" />
                </button>
                <h3 className="text-[15px] font-bold text-zinc-900 dark:text-zinc-100 mb-4 flex items-center gap-1.5">
                  <FiPlusCircle className="text-cyan-500" /> Create Manual Task
                </h3>
                <form onSubmit={handleAddTask} className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-[11px] font-bold font-mono tracking-widest text-zinc-400 dark:text-zinc-500 uppercase">Task Title</label>
                    <input
                      type="text"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      required
                      placeholder="e.g. Test memory database obfuscations"
                      className="w-full h-11 px-3 rounded-xl text-[13.5px] bg-zinc-100/50 dark:bg-zinc-900/50 border border-zinc-200/60 dark:border-zinc-800 focus:outline-none focus:border-cyan-500 dark:focus:border-cyan-500 text-zinc-800 dark:text-zinc-200 transition"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[11px] font-bold font-mono tracking-widest text-zinc-400 dark:text-zinc-500 uppercase">Description</label>
                    <textarea
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="e.g. Ensure base64 decoding does not crash on empty strings."
                      className="w-full h-20 p-3 rounded-xl text-[13.5px] bg-zinc-100/50 dark:bg-zinc-900/50 border border-zinc-200/60 dark:border-zinc-800 focus:outline-none focus:border-cyan-500 dark:focus:border-cyan-500 text-zinc-800 dark:text-zinc-200 transition resize-none"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-[11px] font-bold font-mono tracking-widest text-zinc-400 dark:text-zinc-500 uppercase">Priority</label>
                      <select
                        value={priority}
                        onChange={(e) => setPriority(Number(e.target.value))}
                        className="w-full h-11 px-3 rounded-xl text-[13.5px] bg-zinc-100/50 dark:bg-zinc-900/50 border border-zinc-200/60 dark:border-zinc-800 focus:outline-none focus:border-cyan-500 dark:focus:border-cyan-500 text-zinc-850 dark:text-zinc-200 transition"
                      >
                        <option value={1}>1 - High</option>
                        <option value={2}>2 - Medium</option>
                        <option value={3}>3 - Low</option>
                      </select>
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-[11px] font-bold font-mono tracking-widest text-zinc-400 dark:text-zinc-500 uppercase">Due Date</label>
                      <input
                        type="date"
                        value={dueDate}
                        onChange={(e) => setDueDate(e.target.value)}
                        className="w-full h-11 px-3 rounded-xl text-[13.5px] bg-zinc-100/50 dark:bg-zinc-900/50 border border-zinc-200/60 dark:border-zinc-800 focus:outline-none focus:border-cyan-500 dark:focus:border-cyan-500 text-zinc-850 dark:text-zinc-200 transition"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="w-full h-10.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-500 hover:opacity-95 text-white text-[13.5px] font-semibold flex items-center justify-center gap-1.5 transition cursor-pointer"
                  >
                    Add to Workspace Board
                  </button>
                </form>
              </GlassCard>
            )}

            {/* Task list list panel */}
            <div className="space-y-4">
              {loading ? (
                <div className="text-center py-12 text-zinc-400">Loading your task desk...</div>
              ) : tasks.length === 0 ? (
                <div className="py-24 text-center space-y-4 border border-dashed border-zinc-200/80 dark:border-zinc-800 rounded-3xl">
                  <div className="w-14 h-14 rounded-2xl bg-zinc-200 dark:bg-zinc-900 flex items-center justify-center text-xl text-zinc-400 mx-auto">
                    ⏰
                  </div>
                  <div className="space-y-1">
                    <h4 className="text-[15.5px] font-bold text-zinc-800 dark:text-zinc-200">No tasks listed</h4>
                    <p className="text-[12px] text-zinc-400 dark:text-zinc-500 max-w-xs mx-auto">
                      Ask your AI companions (e.g. Nova or Aria) to set a reminder for you, or create one manually.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  {tasks.map((task) => {
                    const isCompleted = task.status === "completed";
                    const priorityLabels: Record<number, { text: string; css: string }> = {
                      1: { text: "High", css: "bg-red-500/10 border-red-500/20 text-red-600 dark:text-red-400" },
                      2: { text: "Medium", css: "bg-amber-500/10 border-amber-500/20 text-amber-600 dark:text-amber-400" },
                      3: { text: "Low", css: "bg-emerald-500/10 border-emerald-500/20 text-emerald-600 dark:text-emerald-400" }
                    };

                    const priorityConfig = priorityLabels[task.priority] || priorityLabels[3];

                    return (
                      <GlassCard 
                        key={task.id} 
                        className={`p-4 flex items-start gap-4 border transition-all duration-200
                          ${isCompleted 
                            ? "border-zinc-200/40 dark:border-zinc-900/60 opacity-60" 
                            : "border-zinc-200/70 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700 shadow-sm"
                          }
                        `}
                      >
                        {/* Custom Checkbox toggle */}
                        <button
                          onClick={() => handleToggleStatus(task)}
                          className="mt-1 flex-shrink-0 text-zinc-400 dark:text-zinc-600 hover:text-cyan-500 transition cursor-pointer"
                        >
                          {isCompleted ? (
                            <FiCheckSquare className="w-5 h-5 text-cyan-500" />
                          ) : (
                            <FiSquare className="w-5 h-5" />
                          )}
                        </button>

                        {/* Task information details */}
                        <div className="flex-1 min-w-0 space-y-1">
                          <h4 
                            className={`text-[14px] font-bold text-zinc-900 dark:text-zinc-150 leading-snug
                              ${isCompleted ? "line-through text-zinc-400 dark:text-zinc-600" : ""}
                            `}
                          >
                            {task.title}
                          </h4>
                          {task.description && (
                            <p className="text-[12px] text-zinc-500 dark:text-zinc-450 leading-relaxed font-normal">
                              {task.description}
                            </p>
                          )}

                          <div className="flex flex-wrap gap-2.5 pt-2">
                            {/* Priority badge */}
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${priorityConfig.css}`}>
                              {priorityConfig.text} Priority
                            </span>

                            {/* Source badge */}
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded border border-zinc-200/60 dark:border-zinc-800 text-zinc-400 dark:text-zinc-500 bg-zinc-100/50 dark:bg-zinc-900/35">
                              {task.source}
                            </span>

                            {/* Due Date badge */}
                            {task.due_at && (
                              <span className="text-[10px] font-medium font-mono text-zinc-400 dark:text-zinc-500 flex items-center gap-1">
                                <FiCalendar className="w-3 h-3 text-cyan-500" />
                                Due: {new Date(task.due_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Delete action button */}
                        <button
                          onClick={() => handleDeleteTask(task.id)}
                          className="text-zinc-400 dark:text-zinc-655 hover:text-red-500 hover:bg-red-500/5 p-2 rounded-xl transition cursor-pointer"
                          title="Delete Task"
                        >
                          <FiTrash2 className="w-4 h-4" />
                        </button>
                      </GlassCard>
                    );
                  })}
                </div>
              )}
            </div>

          </div>
        </main>
      </div>

      {/* Floating Glassmorphic Toast Notification */}
      {toast.show && (
        <div className="fixed top-6 right-6 z-50 transform transition-all duration-300 animate-in fade-in slide-in-from-top-4">
          <div className="px-5 py-4 rounded-2xl bg-white/75 dark:bg-zinc-950/80 backdrop-blur-xl border border-zinc-200/50 dark:border-zinc-800/80 shadow-[0_10px_30px_rgba(0,0,0,0.08)] dark:shadow-[0_10px_30px_rgba(0,0,0,0.45)] flex items-center gap-3.5 max-w-sm">
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 text-white shadow-sm ${
              toast.type === "success" 
                ? "bg-gradient-to-r from-emerald-500 to-teal-500 shadow-emerald-500/20" 
                : "bg-gradient-to-r from-red-500 to-rose-500 shadow-red-500/20"
            }`}>
              {toast.type === "success" ? <FiCheckSquare className="w-4.5 h-4.5" /> : <FiAlertCircle className="w-4.5 h-4.5" />}
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="text-[13px] font-bold text-zinc-900 dark:text-zinc-150 leading-tight">
                {toast.type === "success" ? "Notification Alert" : "System Error"}
              </h4>
              <p className="text-[11.5px] text-zinc-500 dark:text-zinc-400 font-semibold mt-0.5 truncate leading-normal">
                {toast.message}
              </p>
            </div>
            <button 
              onClick={() => setToast(prev => ({ ...prev, show: false }))}
              className="p-1 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-900 text-zinc-400 dark:text-zinc-650 transition cursor-pointer"
            >
              <FiX className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
