"use client";

import React, { useState } from "react";
import { useChat, Memory } from "@/context/ChatContext";
import Sidebar from "@/components/Sidebar";
import MemoryCard from "@/components/MemoryCard";
import ThemeToggle from "@/components/ThemeToggle";
import GlassCard from "@/components/GlassCard";
import { AnimatePresence } from "framer-motion";
import { FiPlus, FiSearch, FiCpu, FiPlusCircle, FiX } from "react-icons/fi";

export default function MemoryDashboard() {
  const { memories, addMemory, deleteMemory, editMemory } = useChat();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<string>("All");
  
  // Custom Memory Creator states
  const [showAddForm, setShowAddForm] = useState(false);
  const [newFact, setNewFact] = useState("");
  const [newCategory, setNewCategory] = useState<Memory["category"]>("Personal");

  const categories = ["All", "Personal", "Technical", "Goals", "Preferences"];

  const handleAddMemory = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFact.trim()) return;
    addMemory(newFact.trim(), newCategory);
    setNewFact("");
    setShowAddForm(false);
  };

  const filteredMemories = memories.filter((mem) => {
    const matchesSearch = mem.fact.toLowerCase().includes(search.toLowerCase());
    const matchesFilter = filter === "All" || mem.category === filter;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="flex h-screen overflow-hidden bg-zinc-50 dark:bg-zinc-950 font-sans">
      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Core Space */}
      <div className="flex-1 flex flex-col min-w-0 h-full relative">
        {/* Top Navbar */}
        <header className="h-16 flex items-center justify-between px-6 border-b border-zinc-200/50 dark:border-zinc-800/85 bg-white/70 dark:bg-zinc-950/70 backdrop-blur-md z-10">
          <div className="flex items-center gap-2.5">
            <FiCpu className="w-5 h-5 text-indigo-500" />
            <h2 className="text-[15px] font-bold text-zinc-900 dark:text-zinc-100 uppercase tracking-wider">
              Cognitive Memory Bank
            </h2>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowAddForm(!showAddForm)}
              className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-500 hover:opacity-95 text-white text-[12.5px] font-semibold flex items-center gap-1.5 transition cursor-pointer shadow-md shadow-indigo-500/10"
            >
              <FiPlus /> Sync Fact
            </button>
            <ThemeToggle />
          </div>
        </header>

        {/* Scrollable grid area */}
        <main className="flex-1 overflow-y-auto px-4 md:px-8 py-8 bg-zinc-50/50 dark:bg-[#080809]/40 relative">
          <div className="max-w-5xl mx-auto space-y-8">
            {/* Interactive Add Form overlay box */}
            {showAddForm && (
              <GlassCard className="p-6 border border-zinc-250 dark:border-zinc-800 shadow-lg relative max-w-lg mx-auto">
                <button
                  onClick={() => setShowAddForm(false)}
                  className="absolute right-4 top-4 p-1 rounded-lg text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-900"
                >
                  <FiX className="w-4 h-4" />
                </button>
                <h3 className="text-[15px] font-bold text-zinc-900 dark:text-zinc-100 mb-4 flex items-center gap-1.5">
                  <FiPlusCircle className="text-cyan-500" /> Commit Memory Fact
                </h3>
                <form onSubmit={handleAddMemory} className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-[11px] font-bold font-mono tracking-widest text-zinc-400 dark:text-zinc-500 uppercase">
                      Memory Description
                    </label>
                    <textarea
                      value={newFact}
                      onChange={(e) => setNewFact(e.target.value)}
                      required
                      placeholder="e.g. Prefers dark high-fidelity layouts and black tea in the afternoon."
                      className="w-full h-24 p-3 rounded-xl text-[13.5px] bg-zinc-100/50 dark:bg-zinc-900/50 border border-zinc-200/60 dark:border-zinc-800 focus:outline-none focus:border-cyan-500 dark:focus:border-cyan-500 text-zinc-800 dark:text-zinc-200 transition resize-none"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[11px] font-bold font-mono tracking-widest text-zinc-400 dark:text-zinc-500 uppercase">
                      Classification Tag
                    </label>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      {(["Personal", "Technical", "Goals", "Preferences"] as const).map((cat) => (
                        <button
                          key={cat}
                          type="button"
                          onClick={() => setNewCategory(cat)}
                          className={`
                            py-1.5 rounded-lg text-[12px] font-semibold border transition cursor-pointer
                            ${
                              newCategory === cat
                                ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-600 dark:text-cyan-400"
                                : "bg-transparent border-zinc-250 dark:border-zinc-850 text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-900"
                            }
                          `}
                        >
                          {cat}
                        </button>
                      ))}
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="w-full h-10.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-500 hover:opacity-95 text-white text-[13.5px] font-semibold flex items-center justify-center gap-1.5 transition cursor-pointer"
                  >
                    Commit to Core Core
                  </button>
                </form>
              </GlassCard>
            )}

            {/* Filter Panel & Search Panel */}
            <div className="flex flex-col md:flex-row gap-4 items-center justify-between pb-2">
              {/* Category Selector Chips */}
              <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto p-1 rounded-xl bg-zinc-100 dark:bg-zinc-900 border border-zinc-200/60 dark:border-zinc-800/80">
                {categories.map((cat) => {
                  const isSelected = filter === cat;
                  return (
                    <button
                      key={cat}
                      onClick={() => setFilter(cat)}
                      className={`
                        px-4 py-1.5 rounded-lg text-[12.5px] font-semibold transition shrink-0 cursor-pointer
                        ${
                          isSelected
                            ? "bg-white dark:bg-zinc-800 text-zinc-900 dark:text-white shadow-sm border border-zinc-200/30 dark:border-zinc-700/30"
                            : "text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-400"
                        }
                      `}
                    >
                      {cat}
                    </button>
                  );
                })}
              </div>

              {/* Search panel */}
              <div className="relative w-full md:w-72">
                <FiSearch className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-400 dark:text-zinc-500 w-4 h-4" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search remembered facts..."
                  className="w-full h-10 pl-10 pr-4 rounded-xl text-[13.5px] bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800/80 focus:outline-none focus:border-cyan-500 dark:focus:border-cyan-500 text-zinc-800 dark:text-zinc-200 transition shadow-sm"
                />
              </div>
            </div>

            {/* Interactive Grid of Memory Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              <AnimatePresence mode="popLayout">
                {filteredMemories.map((mem) => (
                  <MemoryCard key={mem.id} memory={mem} onDelete={deleteMemory} onEdit={editMemory} />
                ))}
              </AnimatePresence>
            </div>

            {/* Empty State visual */}
            {filteredMemories.length === 0 && (
              <div className="py-24 text-center space-y-4 border border-dashed border-zinc-200/80 dark:border-zinc-800 rounded-3xl">
                <div className="w-14 h-14 rounded-2xl bg-zinc-200 dark:bg-zinc-900 flex items-center justify-center text-xl text-zinc-400 mx-auto border border-zinc-350 dark:border-zinc-800">
                  🧬
                </div>
                <div className="space-y-1.5">
                  <h4 className="text-[15.5px] font-bold text-zinc-850 dark:text-zinc-200">No memory memories synced</h4>
                  <p className="text-[12.5px] text-zinc-400 dark:text-zinc-500 max-w-xs mx-auto leading-normal">
                    Try prompting the AI in the chat with "Remember that..." or commit a custom fact manually above.
                  </p>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
