"use client";

import { useState } from "react";
import { Message, Companion } from "@/context/ChatContext";
import { useTheme } from "@/context/ThemeContext";
import { motion } from "framer-motion";
import { FiCode, FiUser, FiDownload } from "react-icons/fi";

interface ChatBubbleProps {
  message: Message;
  companion: Companion;
}

export default function ChatBubble({ message, companion }: ChatBubbleProps) {
  const isUser = message.sender === "user";
  const { theme } = useTheme();
  const isDark = theme === "dark";

  let displayContent = message.content;
  let downloadUrl: string | null = null;
  let imageUrl: string | null = null;

  const urlMatch = displayContent.match(/(?:pdf_url|download_url|resume_url)\s*:\s*(https?:\/\/[^\s\r\n]+)/i);
  if (urlMatch) {
    downloadUrl = urlMatch[1];
    displayContent = displayContent.replace(urlMatch[0], "").trim();
  }

  const imageMatch = displayContent.match(/(https?:\/\/image\.pollinations\.ai\/prompt\/[^\s\r\n]+|https?:\/\/[^\s\r\n]+\/static_images\/[^\s\r\n]+)/i);
  if (imageMatch) {
    imageUrl = imageMatch[1];
    displayContent = displayContent.replace(imageMatch[0], "").trim();
  }

  let videoUrl: string | null = null;
  const videoMatch = displayContent.match(/(https?:\/\/[^\s\r\n]+(?:\.mp4)(?:\?[^\s\r\n]*)?)/i);
  if (videoMatch) {
    videoUrl = videoMatch[1];
    displayContent = displayContent.replace(videoMatch[0], "").trim();
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className={`flex w-full items-start gap-4 mb-6 ${isUser ? "justify-end" : "justify-start"}`}
    >
      {/* AI Avatar */}
      {!isUser && (
        <div className="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-xl shadow-[0_0_15px_rgba(6,182,212,0.1)]">
          {companion.avatar}
        </div>
      )}

      {/* Bubble Shell */}
      <div className={`max-w-[85%] md:max-w-[70%] flex flex-col ${isUser ? "items-end" : "items-start"}`}>
        {/* Author Metadata */}
        <span className="text-xs text-zinc-400 dark:text-zinc-500 mb-1.5 font-mono tracking-wider flex items-center gap-1">
          {isUser ? (
            <>
              You <FiUser className="w-2.5 h-2.5" />
            </>
          ) : (
            <>
              {companion.name} <span className="text-[10px] uppercase font-bold text-cyan-500 dark:text-cyan-400 px-1 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20">{companion.role}</span>
            </>
          )}
          <span className="opacity-60">•</span>
          <span>{message.timestamp}</span>
        </span>

        {/* Content Box */}
        <div
          className={`
            px-4.5 py-3 rounded-2xl text-[15px] leading-relaxed shadow-sm w-full
            ${
              isUser
                ? "bg-gradient-to-br from-indigo-500 to-indigo-600 dark:from-indigo-600 dark:to-indigo-700 text-white rounded-tr-sm border border-indigo-400/20 shadow-indigo-500/10"
                : isDark
                  ? "bg-zinc-900 text-zinc-100 rounded-tl-sm border border-zinc-800 shadow-black/20"
                  : "bg-white text-zinc-800 rounded-tl-sm border border-zinc-200/50 shadow-black/5"
            }
          `}
        >
          {/* Support inline mock code format if message contains code boxes */}
          {displayContent.trim() && (
            displayContent.includes("```") ? (
              <div className="space-y-3 font-sans">
                {displayContent.split("```").map((chunk, index) => {
                  if (index % 2 === 1) {
                    // Code block section
                    const codeLines = chunk.trim().split("\n");
                    const lang = codeLines[0].length < 12 ? codeLines[0] : "";
                    const codeText = lang ? codeLines.slice(1).join("\n") : codeLines.join("\n");

                    return (
                      <div key={index} className={`rounded-xl overflow-hidden my-3 border font-mono text-[13px] ${isDark ? "border-zinc-800 bg-black" : "border-zinc-200/80 bg-zinc-50"}`}>
                        <div className={`flex items-center justify-between px-4 py-2 border-b text-[11px] font-mono uppercase select-none ${isDark ? "border-zinc-800 text-zinc-400" : "border-zinc-200/80 text-zinc-500"}`}>
                          <span>{lang || "code"}</span>
                          <span className="flex items-center gap-1"><FiCode /> auto-formatted</span>
                        </div>
                        <pre className={`p-4 overflow-x-auto leading-normal ${isDark ? "text-cyan-400" : "text-cyan-600"}`}>
                          <code>{codeText}</code>
                        </pre>
                      </div>
                    );
                  }
                  // Text chunk, format paragraphs & bold bullet lines
                  return (
                    <p key={index} className="whitespace-pre-line">
                      {chunk}
                    </p>
                  );
                })}
              </div>
            ) : (
              <p className="whitespace-pre-line">{displayContent}</p>
            )
          )}

          {imageUrl && (
            <PollinationsImage imageUrl={imageUrl} isDark={isDark} />
          )}

          {videoUrl && (
            <DIDVideo videoUrl={videoUrl} isDark={isDark} />
          )}

          {downloadUrl && (
            <div className="mt-3.5 w-full flex justify-start">
              <motion.a
                href={downloadUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2.5 px-5 py-3 rounded-xl border border-cyan-500/30 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 font-medium text-sm transition-all duration-300 backdrop-blur-md shadow-[0_8px_32px_0_rgba(6,182,212,0.15)] hover:shadow-[0_8px_32px_0_rgba(6,182,212,0.3)] cursor-pointer w-full sm:w-auto justify-center"
                whileHover={{ scale: 1.03, y: -1 }}
                whileTap={{ scale: 0.97 }}
              >
                <motion.span
                  animate={{ y: [0, -3, 0] }}
                  transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
                >
                  <FiDownload className="w-4.5 h-4.5 text-cyan-400" />
                </motion.span>
                Download Your Resume
              </motion.a>
            </div>
          )}
        </div>
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-xl bg-zinc-200 dark:bg-zinc-800 border border-zinc-300/40 dark:border-zinc-700/40 text-sm font-bold text-zinc-700 dark:text-zinc-300">
          U
        </div>
      )}
    </motion.div>
  );
}

interface PollinationsImageProps {
  imageUrl: string;
  isDark: boolean;
}

function PollinationsImage({ imageUrl, isDark }: PollinationsImageProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  return (
    <div className="mt-3.5 w-full max-w-lg overflow-hidden rounded-xl border border-zinc-200/60 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 relative min-h-[220px] flex items-center justify-center shadow-md">
      {loading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-zinc-50 dark:bg-zinc-900 text-xs text-zinc-500 dark:text-zinc-400 gap-3">
          <div className="w-9 h-9 rounded-full border-4 border-cyan-500/20 border-t-cyan-500 animate-spin" />
          <span className="font-medium tracking-wide animate-pulse">Generating image...</span>
        </div>
      )}
      {error ? (
        <div className="p-5 flex flex-col items-center justify-center text-center text-sm text-red-500 dark:text-red-400 gap-3">
          <span className="font-semibold">Failed to load the generated image.</span>
          <span className="text-xs text-zinc-500 dark:text-zinc-400 max-w-xs">
            Pollinations.ai returned an error (likely rate limit or quota exceeded). Try adding a free <code className="px-1 py-0.5 rounded bg-zinc-200 dark:bg-zinc-800 font-mono">POLLINATIONS_API_KEY</code> to your backend <code className="px-1 py-0.5 rounded bg-zinc-200 dark:bg-zinc-800 font-mono">.env</code>.
          </span>
          <a
            href={imageUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-500 dark:text-red-400 font-semibold border border-red-500/20 transition-all duration-200 cursor-pointer"
          >
            Open Image in New Tab
          </a>
        </div>
      ) : (
        <img
          src={imageUrl}
          alt="Pollinations AI Generated"
          className={`w-full h-auto rounded-lg shadow-lg object-contain transition-all duration-500 ${loading ? "opacity-0 scale-95" : "opacity-100 scale-100"}`}
          onLoad={() => setLoading(false)}
          onError={() => {
            setError(true);
            setLoading(false);
          }}
        />
      )}
    </div>
  );
}

interface DIDVideoProps {
  videoUrl: string;
  isDark: boolean;
}

function DIDVideo({ videoUrl, isDark }: DIDVideoProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  return (
    <div className="mt-3.5 w-full max-w-lg overflow-hidden rounded-xl border border-zinc-200/60 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 relative min-h-[220px] flex items-center justify-center shadow-md">
      {loading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-zinc-50 dark:bg-zinc-900 text-xs text-zinc-500 dark:text-zinc-400 gap-3">
          <div className="w-9 h-9 rounded-full border-4 border-cyan-500/20 border-t-cyan-500 animate-spin" />
          <span className="font-medium tracking-wide animate-pulse">Generating avatar video...</span>
        </div>
      )}
      {error ? (
        <div className="p-5 flex flex-col items-center justify-center text-center text-sm text-red-500 dark:text-red-400 gap-3">
          <span className="font-semibold">Failed to load the talking avatar video.</span>
          <span className="text-xs text-zinc-500 dark:text-zinc-400 max-w-xs">
            There was an error loading the video file. Make sure your <code className="px-1 py-0.5 rounded bg-zinc-200 dark:bg-zinc-800 font-mono">DID_API_KEY</code> is active and valid in your backend <code className="px-1 py-0.5 rounded bg-zinc-200 dark:bg-zinc-800 font-mono">.env</code>.
          </span>
          <a
            href={videoUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-500 dark:text-red-400 font-semibold border border-red-500/20 transition-all duration-200 cursor-pointer"
          >
            Open Video in New Tab
          </a>
        </div>
      ) : (
        <video
          src={videoUrl}
          controls
          autoPlay
          className={`w-full h-auto rounded-lg shadow-lg object-contain transition-all duration-500 ${loading ? "opacity-0 scale-95" : "opacity-100 scale-100"}`}
          onLoadedData={() => setLoading(false)}
          onError={() => {
            setError(true);
            setLoading(false);
          }}
        />
      )}
    </div>
  );
}
