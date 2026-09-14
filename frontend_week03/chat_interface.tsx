"use client";

import { FormEvent, useState, useEffect, useRef } from "react";
import ReactECharts from "echarts-for-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function EChartRenderer({ option }: { option: object }) {
  return (
    <ReactECharts option={option} style={{ height: "300px", width: "100%" }} />
  );
}

/* ------------------------------------------------------------------ */
/* Lightweight inline icon set (no external icon dependency required)  */
/* ------------------------------------------------------------------ */
function IconSparkle({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className}>
      <path
        d="M12 3l1.8 4.9L18.7 9.7l-4.9 1.8L12 16.4l-1.8-4.9L5.3 9.7l4.9-1.8L12 3z"
        fill="currentColor"
      />
    </svg>
  );
}

function IconPlus({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      className={className}
    >
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

function IconChat({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
    </svg>
  );
}

function IconEdit({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M17 3a2.83 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" />
    </svg>
  );
}

function IconTrash({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0-1 14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2L4 6h16z" />
    </svg>
  );
}

function IconLogout({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" />
    </svg>
  );
}

function IconSummarize({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" />
      <path d="M14 2v6h6M9 13h6M9 17h6M9 9h1" />
    </svg>
  );
}

function IconBot({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <rect x="4" y="8" width="16" height="12" rx="3" />
      <path d="M12 8V4M9 2h6" />
      <circle cx="9" cy="14" r="1.2" fill="currentColor" stroke="none" />
      <circle cx="15" cy="14" r="1.2" fill="currentColor" stroke="none" />
      <path d="M9 17.5h6" />
    </svg>
  );
}

function IconPaperclip({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M21.44 11.05 12.25 20.24a5 5 0 0 1-7.07-7.07l9.19-9.19a3.5 3.5 0 0 1 4.95 4.95L9.64 18.36a2 2 0 0 1-2.83-2.83l8.49-8.48" />
    </svg>
  );
}

function IconSend({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M2.94 21.06 22 12 2.94 2.94 2.9 9.7a1 1 0 0 0 .8.98L15 12 3.7 13.32a1 1 0 0 0-.8.98l.04 6.76z" />
    </svg>
  );
}

function IconClose({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      className={className}
    >
      <path d="M18 6 6 18M6 6l12 12" />
    </svg>
  );
}

type Conversation = {
  id: string;
  title: string;
};

type Message = {
  role: "user" | "assistant";
  content: string;
};

type SummaryResponse = {
  conversation_id: string;
  summary: string;
  open_questions: string[];
  recommended_next_actions: string[];
  recent_messages: { role: "user" | "assistant"; content: string }[];
};

type UserSession = {
  user_id: string | number; // Fixed TypeScript type (was 'int')
  username: string;
};

export default function ChatInterface() {
  // --- Auth State ---
  const [currentUser, setCurrentUser] = useState<UserSession | null>(null);
  const [authMode, setAuthMode] = useState<"signin" | "signup">("signin");
  const [usernameInput, setUsernameInput] = useState("");
  const [emailInput, setEmailInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [authError, setAuthError] = useState("");

  // --- Chat State ---
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  // Summary state
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [authToken, setAuthToken] = useState<string | null>(null);

  // Upload state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<
    "idle" | "uploading" | "success" | "error"
  >("idle");
  const [uploadMessage, setUploadMessage] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  // Add this array near the top of your component, after state declarations:

  const SUGGESTIONS = [
    {
      icon: "📊",
      title: "Visualise my spending",
      subtitle: "Generate a chart of spending by category",
      prompt: "Show me a pie chart of my spending by category",
    },
    {
      icon: "💰",
      title: "Analyse my budget",
      subtitle: "See where I'm overspending this month",
      prompt: "Analyse my budget and show me where I am overspending",
    },
    {
      icon: "📋",
      title: "Summarise my transactions",
      subtitle: "Highlight key trends in my financial data",
      prompt: "Summarise my transaction history and highlight key trends",
    },
    {
      icon: "🔍",
      title: "Search my documents",
      subtitle: "Find insights from my uploaded files",
      prompt:
        "Search my documents and tell me what financial policies apply to me",
    },
  ];
  // 1. Rehydrate User Session on Mount
  useEffect(() => {
    const saved = localStorage.getItem("user_session");
    const savedToken = localStorage.getItem("token");
    if (saved) {
      try {
        setCurrentUser(JSON.parse(saved));
        setAuthToken(savedToken);
      } catch (e) {
        localStorage.removeItem("user_session");
      }
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);
  // 2. Fetch conversations belonging to the logged-in user
  useEffect(() => {
    if (!currentUser) return;

    async function fetchSessions() {
      try {
        const res = await fetch(`http://localhost:8000/api/conversations`, {
          headers: {
            Authorization: `Bearer ${authToken}`,
          },
        });
        if (res.ok) {
          const data = await res.json();
          setConversations(data);
          if (data.length > 0) {
            setActiveId(data[0].id);
          } else {
            createNewChat();
          }
        }
      } catch (err) {
        console.error("Failed to load conversation list:", err);
      }
    }
    fetchSessions();
  }, [currentUser]);

  // 3. Load transcript when active chat changes
  useEffect(() => {
    if (!activeId || !currentUser) return;
    async function loadTranscript() {
      setLoading(true);
      try {
        const res = await fetch(
          `http://localhost:8000/api/conversations/${activeId}`,
          {
            headers: {
              Authorization: `Bearer ${authToken}`,
            },
          },
        );
        if (res.ok) {
          const history = await res.json();
          setMessages(history);
        }
      } catch (err) {
        console.error("Error loading transcript:", err);
      } finally {
        setLoading(false);
      }
    }

    loadTranscript();
  }, [activeId, currentUser]);

  useEffect(() => {
    setSummary(null);
    setShowSummary(false);
  }, [activeId]);

  // --- Auth Handlers ---
  const handleAuthSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setAuthError("");

    const endpoint =
      authMode === "signup"
        ? "http://localhost:8000/api/signup"
        : "http://localhost:8000/api/signin";

    const payload =
      authMode === "signup"
        ? {
            username: usernameInput,
            email: emailInput,
            password: passwordInput,
          }
        : { username: usernameInput, password: passwordInput };

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        setAuthError(data.detail || "Authentication failed.");
        return;
      }

      const session: UserSession = {
        user_id: data.user_id,
        username: data.username,
      };
      if (data.access_token) {
        localStorage.setItem("token", data.access_token);
        setAuthToken(data.access_token);
      }
      setCurrentUser(session);
      localStorage.setItem("user_session", JSON.stringify(session));
      setPasswordInput("");
      setAuthError("");
    } catch (err) {
      setAuthError("Failed to connect to authentication server.");
    }
  };

  const handleSignOut = () => {
    setCurrentUser(null);
    setAuthToken(null);
    localStorage.removeItem("user_session");
    localStorage.removeItem("token");
    setConversations([]);
    setMessages([]);
    setActiveId(null);
  };

  const handleUpload = async () => {
    if (!uploadFile || !currentUser) return;
    setUploadStatus("uploading");
    setUploadMessage("");

    const formData = new FormData();
    formData.append("file", uploadFile);
    formData.append("user_id", String(currentUser.user_id));

    try {
      const res = await fetch("http://localhost:8000/api/upload", {
        method: "POST",
        headers: {
          "X-API-Key": "my-super-secret-ingestion-key-123",
        },
        body: formData, // NOTE: do NOT set Content-Type here, browser sets it automatically for FormData
      });

      const data = await res.json();

      if (res.ok) {
        setUploadStatus("success");
        setUploadMessage(`✓ ${data.message}`);
        setUploadFile(null);
      } else {
        setUploadStatus("error");
        setUploadMessage(data.detail || "Upload failed.");
      }
    } catch (err) {
      setUploadStatus("error");
      setUploadMessage("Could not reach server.");
    }
  };

  const createNewChat = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/conversations", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({ title: "New Chat" }),
      });
      if (res.ok) {
        const newSession = await res.json();
        setConversations((prev) => [newSession, ...prev]);
        setActiveId(newSession.id);
        setMessages([]);
      }
    } catch (err) {
      console.error("Failed to create new conversation:", err);
    }
  };

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!draft.trim() || !activeId || !currentUser) return;

    const nextMessage: Message = { role: "user", content: draft };
    setMessages((current) => [...current, nextMessage]);
    setDraft("");

    try {
      const response = await fetch(
        `http://localhost:8000/api/conversations/${activeId}/messages`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${authToken}`,
          },
          body: JSON.stringify({
            user_message: nextMessage.content,
          }),
        },
      );
      if (response.ok) {
        const payload = (await response.json()) as { reply: string };
        setMessages((current) => [
          ...current,
          { role: "assistant", content: payload.reply },
        ]);
      }
    } catch (err) {
      console.error("Failed to send message:", err);
    }
  }

  async function handleGetSummary() {
    if (!activeId) return;
    setSummaryLoading(true);
    setShowSummary(true);
    try {
      const res = await fetch(
        `http://localhost:8000/api/conversations/${activeId}/summary`,
        {
          headers: {
            Authorization: `Bearer ${authToken}`,
          },
        },
      );
      if (res.ok) {
        const data = (await res.json()) as SummaryResponse;
        setSummary(data);
      } else {
        setSummary(null);
      }
    } catch (err) {
      setSummary(null);
    } finally {
      setSummaryLoading(false);
    }
  }

  async function deleteConversation(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    if (!window.confirm("Delete this conversation?")) return;

    try {
      const res = await fetch(`http://localhost:8000/api/conversations/${id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      });
      if (res.ok || res.status === 204) {
        setConversations((prev) => prev.filter((c) => c.id !== id));
        if (activeId === id) {
          const remaining = conversations.filter((c) => c.id !== id);
          if (remaining.length > 0) {
            setActiveId(remaining[0].id);
          } else {
            setActiveId(null);
            setMessages([]);
            createNewChat();
          }
        }
      }
    } catch (err) {
      console.error("Failed to delete conversation:", err);
    }
  }

  function startRename(conv: Conversation, e: React.MouseEvent) {
    e.stopPropagation();
    setEditingId(conv.id);
    setEditValue(conv.title);
  }

  function cancelRename() {
    setEditingId(null);
    setEditValue("");
  }

  async function submitRename(id: string) {
    const trimmed = editValue.trim();
    if (!trimmed) {
      cancelRename();
      return;
    }
    try {
      const res = await fetch(`http://localhost:8000/api/conversations/${id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({ title: trimmed }),
      });
      if (res.ok) {
        const updated = await res.json();
        setConversations((prev) =>
          prev.map((c) => (c.id === id ? { ...c, title: updated.title } : c)),
        );
      }
    } catch (err) {
      console.error("Failed to rename conversation:", err);
    } finally {
      cancelRename();
    }
  }

  // --- RENDER LOGIN VIEW IF NOT LOGGED IN ---
  if (!currentUser) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#131313] p-4 text-zinc-100 antialiased">
        <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#1c1b1b] p-8 shadow-2xl">
          <div className="text-center mb-6">
            <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-orange-500/10 border border-orange-500/40 flex items-center justify-center">
              <IconSparkle className="w-6 h-6 text-orange-400" />
            </div>
            <h1 className="text-2xl font-bold text-white">FinanceAI</h1>
            <p className="text-xs text-orange-500 font-semibold uppercase tracking-widest mt-1">
              {authMode === "signin"
                ? "Sign in to account"
                : "Create new account"}
            </p>
          </div>

          <div className="flex rounded-xl bg-[#131313] p-1 border border-white/10 mb-6">
            <button
              type="button"
              onClick={() => {
                setAuthMode("signin");
                setAuthError("");
              }}
              className={`flex-1 rounded-lg py-2 text-xs font-semibold transition-all ${
                authMode === "signin"
                  ? "bg-orange-500 text-black"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {
                setAuthMode("signup");
                setAuthError("");
              }}
              className={`flex-1 rounded-lg py-2 text-xs font-semibold transition-all ${
                authMode === "signup"
                  ? "bg-orange-500 text-black"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              Sign Up
            </button>
          </div>

          {authError && (
            <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/30 p-3 text-xs text-red-400 text-center">
              {authError}
            </div>
          )}

          <form onSubmit={handleAuthSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1">
                Username
              </label>
              <input
                required
                type="text"
                value={usernameInput}
                onChange={(e) => setUsernameInput(e.target.value)}
                placeholder="e.g. johndoe"
                className="w-full rounded-xl border border-white/10 bg-[#131313] px-4 py-2.5 text-sm text-white focus:border-orange-500 focus:outline-none"
              />
            </div>

            {authMode === "signup" && (
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1">
                  Email
                </label>
                <input
                  required
                  type="email"
                  value={emailInput}
                  onChange={(e) => setEmailInput(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full rounded-xl border border-white/10 bg-[#131313] px-4 py-2.5 text-sm text-white focus:border-orange-500 focus:outline-none"
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1">
                Password
              </label>
              <input
                required
                type="password"
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-xl border border-white/10 bg-[#131313] px-4 py-2.5 text-sm text-white focus:border-orange-500 focus:outline-none"
              />
            </div>

            <button
              type="submit"
              className="w-full rounded-xl bg-orange-500 py-3 text-sm font-semibold text-black hover:bg-orange-400 active:scale-95 transition-all mt-2"
            >
              {authMode === "signin" ? "Sign In" : "Create Account"}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // Derived helpers for the sidebar (visual only — no new data/logic)
  const activeConversation =
    conversations.find((c) => c.id === activeId) ?? null;
  const historyConversations = conversations.filter((c) => c.id !== activeId);

  // Shared renderer for a single conversation row (nav / history) so the
  // rename + delete + select behaviour stays 100% identical everywhere.
  function ConversationRow({ conv }: { conv: Conversation }) {
    const isActive = activeId === conv.id;
    return (
      <div
        onClick={() => editingId !== conv.id && setActiveId(conv.id)}
        className={`group flex items-center justify-between gap-2 px-4 py-2.5 rounded-lg cursor-pointer transition-all duration-200 border ${
          isActive
            ? "bg-[#2a2a2a] border-orange-500/50 text-orange-400 font-bold"
            : "bg-transparent border-transparent hover:bg-[#232323] text-zinc-300"
        }`}
      >
        {editingId === conv.id ? (
          <input
            autoFocus
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onClick={(e) => e.stopPropagation()}
            onBlur={() => submitRename(conv.id)}
            onKeyDown={(e) => {
              if (e.key === "Enter") submitRename(conv.id);
              if (e.key === "Escape") cancelRename();
            }}
            className="w-full bg-[#131313] border border-orange-500 rounded px-2 py-1 text-xs text-white focus:outline-none"
          />
        ) : (
          <>
            <div className="flex items-center gap-3 overflow-hidden">
              <IconChat
                className={`w-4 h-4 shrink-0 ${
                  isActive ? "text-orange-400" : "text-zinc-500"
                }`}
              />
              <div className="flex flex-col overflow-hidden">
                <span className="text-sm truncate">{conv.title}</span>
                <span className="font-mono text-[10px] opacity-70 truncate">
                  ID: {conv.id}
                </span>
              </div>
            </div>
            <div className="opacity-0 group-hover:opacity-100 flex gap-1 transition-opacity shrink-0">
              <button
                onClick={(e) => startRename(conv, e)}
                className="text-zinc-500 hover:text-orange-400 p-1"
              >
                <IconEdit className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={(e) => deleteConversation(conv.id, e)}
                className="text-zinc-500 hover:text-red-400 p-1"
              >
                <IconTrash className="w-3.5 h-3.5" />
              </button>
            </div>
          </>
        )}
      </div>
    );
  }

  // --- RENDER MAIN CHAT INTERFACE IF LOGGED IN ---

  return (
    <div className="flex h-screen w-screen bg-[#131313] text-zinc-100 antialiased overflow-hidden">
      <style jsx global>{`
        @keyframes brandBreathe {
          0%, 100% {
            transform: scale(1);
            box-shadow: 0 0 0 0 rgba(249, 115, 22, 0.35);
          }
          50% {
            transform: scale(1.2);
            box-shadow: 0 0 0 6px rgba(249, 115, 22, 0);
          }
        }
        .animate-brand-breathe {
          animation: brandBreathe 3s ease-in-out infinite;
        }
        @keyframes floatBot {
          0%,
          100% {
            transform: translateY(0px) rotate(0deg);
          }
          50% {
            transform: translateY(-9px) rotate(-2deg);
          }
        }
        .animate-float-bot {
          animation: floatBot 1s ease-in-out infinite;
        }

        @keyframes glowRing {
          0% {
            box-shadow: 0 0 0 0 rgba(249, 115, 22, 0.5);
          }
          70% {
            box-shadow: 0 0 0 16px rgba(249, 115, 22, 0);
          }
          100% {
            box-shadow: 0 0 0 0 rgba(249, 115, 22, 0);
          }
        }
        .animate-glow-ring {
          animation: glowRing 2s ease-out infinite;
        }
      `}</style>
      {/* Sidebar */}
      <aside className="h-screen w-64 shrink-0 border-r border-white/10 bg-[#181818] flex flex-col py-6 px-3">
        {/* Brand */}
        <div className="flex items-center gap-3 mb-8 px-2">
          <div className="animate-brand-breathe w-10 h-10 rounded-full bg-orange-500/15 flex items-center justify-center border border-orange-500/40 shrink-0">
            <IconSparkle className="w-5 h-5 text-orange-400" />
          </div>
          <div className="overflow-hidden">
            <h1 className="text-base font-bold text-orange-400 truncate">
              FinanceAI
            </h1>
            <p className="text-[11px] font-mono text-zinc-500 truncate">
              Analytical Intelligence
            </p>
          </div>
        </div>

        {/* CTA */}
        <button
          onClick={() => createNewChat()}
          className="w-full mb-6 bg-orange-500 text-black text-sm font-semibold py-3 px-4 rounded-xl flex items-center justify-center gap-2 shadow-[inset_0_1px_1px_rgba(255,255,255,0.25)] hover:bg-orange-400 hover:scale-[1.01] active:scale-95 transition-all duration-200"
        >
          <IconPlus className="w-4 h-4" />
          New Chat
        </button>

        {/* Navigation + History */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-1">
          {activeConversation && (
            <>
              <p className="font-mono text-[11px] tracking-wider text-orange-500/80 mb-2 px-3">
                NAVIGATION
              </p>
              <ConversationRow conv={activeConversation} />
            </>
          )}

          <div className="mt-8">
            <p className="font-mono text-[11px] tracking-wider text-zinc-500 mb-2 px-3">
              RECENT HISTORY
            </p>
            <div className="space-y-1">
              {historyConversations.length === 0 && !activeConversation ? (
                <p className="px-3 text-xs text-zinc-600">
                  No conversations yet.
                </p>
              ) : (
                historyConversations.map((conv) => (
                  <ConversationRow key={conv.id} conv={conv} />
                ))
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-white/10 mt-auto">
          <div className="flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-[#232323] transition-colors">
            <div className="w-8 h-8 rounded-full bg-orange-500/20 border border-orange-500/40 flex items-center justify-center text-xs font-bold text-orange-400 shrink-0">
              {currentUser.username?.[0]?.toUpperCase() ?? "U"}
            </div>
            <div className="flex-1 overflow-hidden">
              <p className="text-sm text-white font-medium truncate">
                {currentUser.username}
              </p>
              <p className="text-[10px] text-zinc-500 font-mono truncate">
                ID: {currentUser.user_id}
              </p>
            </div>
            <button
              onClick={handleSignOut}
              title="Log out"
              className="text-zinc-500 hover:text-red-400 transition-colors p-1"
            >
              <IconLogout className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>
      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-screen relative min-w-0">
        {/* Top App Bar */}
        <header className="bg-[#131313]/80 backdrop-blur-md border-b border-white/10 h-16 px-6 flex items-center justify-between z-40 sticky top-0 shrink-0">
          <div className="flex items-center gap-4 overflow-hidden">
            <h2 className="text-lg font-bold text-white tracking-tight truncate">
              Multi-Agent Dashboard
            </h2>
            {activeId && (
              <span className="bg-[#232323] text-zinc-400 font-mono px-2 py-0.5 rounded text-[11px] border border-white/10 flex items-center gap-1.5 shrink-0">
                <span className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse" />
                SESSION: {activeId}
              </span>
            )}
          </div>

          {activeId && (
            <div className="flex items-center gap-3 shrink-0 pl-6 border-l border-white/10">
              <button
                onClick={handleGetSummary}
                disabled={summaryLoading}
                className="bg-[#232323] hover:bg-[#2c2c2c] text-zinc-200 px-4 py-2 rounded-lg border border-white/10 font-medium transition-colors text-sm flex items-center gap-2 disabled:opacity-50"
              >
                <IconSummarize className="w-4 h-4" />
                {summaryLoading ? "Summarizing..." : "Summarize Session"}
              </button>
            </div>
          )}
        </header>

        {/* Summary Panel */}
        {showSummary && (
          <div className="w-full max-w-[800px] mx-auto px-4 md:px-6 pt-4 shrink-0">
            <div className="rounded-xl border border-white/10 bg-[#1c1b1b] text-sm text-zinc-200 relative flex flex-col max-h-[50vh] overflow-y-auto p-4">
              <button
                onClick={() => setShowSummary(false)}
                className="absolute top-2 right-2 text-zinc-500 hover:text-zinc-300 bg-[#1c1b1b] rounded-full w-9 h-9 flex items-center justify-center transition-colors"
              >
                <IconClose className="w-5 h-5" />
              </button>
              {summaryLoading ? (
                <p className="text-zinc-500">Generating summary...</p>
              ) : summary ? (
                <div className="space-y-4 pr-6">
                  <div>
                    <p className="font-semibold text-orange-400 mb-2">
                      Summary
                    </p>
                    <p className="leading-relaxed">{summary.summary}</p>
                  </div>
                  {summary.open_questions?.length > 0 && (
                    <div>
                      <p className="font-semibold text-orange-400 mb-2">
                        Open Questions
                      </p>
                      <ul className="list-disc pl-4 space-y-1 text-zinc-300">
                        {summary.open_questions.map((q, i) => (
                          <li key={i}>{q}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {summary.recommended_next_actions?.length > 0 && (
                    <div>
                      <p className="font-semibold text-orange-400 mb-2">
                        Recommended Next Actions
                      </p>
                      <ul className="list-disc pl-4 space-y-1 text-zinc-300">
                        {summary.recommended_next_actions.map((a, i) => (
                          <li key={i}>{a}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-zinc-500">Could not generate summary.</p>
              )}
            </div>
          </div>
        )}

        {/* Chat Canvas */}
        <div className="flex-1 overflow-y-auto relative p-4 md:p-6 flex flex-col items-center">
          {loading ? (
            <div className="flex-1 flex items-center justify-center text-zinc-500 text-sm">
              Loading chat transcript...
            </div>
          ) : messages.length === 0 ? (
            <div className="w-full max-w-[800px] mt-6 md:mt-12 mb-8 flex flex-col items-center text-center">
              <div className="animate-float-bot animate-glow-ring w-16 h-16 rounded-2xl bg-[#232323] border border-white/10 flex items-center justify-center mb-6 shadow-lg shadow-black/20">
                <IconBot className="w-8 h-8 text-orange-400" />
              </div>
              <h3 className="text-3xl md:text-4xl font-bold text-white mb-2">
                Welcome back, {currentUser.username}.
              </h3>
              <p className="text-zinc-400 mb-10 max-w-lg">
                I'm your personal finance assistant. I can analyse your
                transactions, visualise your spending, and search your uploaded
                documents. What would you like to explore today?
              </p>

              {/* Suggestion buttons */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s.title}
                    onClick={() => {
                      setDraft("");
                      const nextMessage: Message = {
                        role: "user",
                        content: s.prompt,
                      };
                      setMessages((current) => [...current, nextMessage]);
                      fetch(
                        `http://localhost:8000/api/conversations/${activeId}/messages`,
                        {
                          method: "POST",
                          headers: {
                            "Content-Type": "application/json",
                            Authorization: `Bearer ${authToken}`,
                          },
                          body: JSON.stringify({ user_message: s.prompt }),
                        },
                      )
                        .then((res) => res.json())
                        .then((data) => {
                          setMessages((current) => [
                            ...current,
                            { role: "assistant", content: data.reply },
                          ]);
                        })
                        .catch(console.error);
                    }}
                    className="bg-[#1c1b1b]/60 backdrop-blur-md border border-white/10 p-4 rounded-xl text-left hover:scale-[1.01] hover:border-orange-500/50 transition-all duration-300 group"
                  >
                    <span className="text-2xl block mb-2">{s.icon}</span>
                    <h4 className="font-medium text-white mb-1 group-hover:text-orange-400 transition-colors">
                      {s.title}
                    </h4>
                    <p className="text-sm text-zinc-400">{s.subtitle}</p>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="w-full max-w-[800px] space-y-6 pb-4">
              {messages.map((message, index) => {
                // Detect chart messages
                if (
                  message.role === "assistant" &&
                  message.content.startsWith("__CHART__")
                ) {
                  try {
                    const rest = message.content.replace("__CHART__", "");
                    const parts = rest.split("__TITLE__");
                    const chartConfig = parts[0];
                    const titleAndRows = parts[1] || "";
                    const [title = "Chart", rowCountStr = "0"] =
                      titleAndRows.split("__ROWS__");

                    const parsedOption = JSON.parse(chartConfig);

                    return (
                      <div
                        key={`${message.role}-${index}`}
                        className="flex justify-start w-full gap-4"
                      >
                        <div className="w-8 h-8 rounded-full bg-[#232323] border border-white/10 shrink-0 flex items-center justify-center mt-1">
                          <IconBot className="w-4 h-4 text-orange-400" />
                        </div>
                        <article className="bg-[#1c1b1b]/60 backdrop-blur-md border-l-2 border-l-orange-500 border-y border-r border-white/10 px-5 py-4 rounded-2xl rounded-tl-sm max-w-[85%] w-full">
                          <p className="text-xs text-orange-400 font-semibold mb-2">
                            {title}
                          </p>
                          <EChartRenderer option={parsedOption} />
                          <p className="text-[10px] text-zinc-500 mt-2">
                            {rowCountStr} rows used
                          </p>
                        </article>
                      </div>
                    );
                  } catch (err) {
                    console.error("Failed to render chart:", err);
                    return (
                      <article
                        key={`${message.role}-${index}`}
                        className="mr-auto bg-red-900/20 text-red-400 p-3 rounded-xl border border-red-800/30 text-xs max-w-[85%]"
                      >
                        Failed to load chart visualization.
                      </article>
                    );
                  }
                }

                // Normal message
                if (message.role === "user") {
                  return (
                    <div
                      key={`${message.role}-${index}`}
                      className="flex justify-end w-full"
                    >
                      <div className="bg-orange-500 text-black px-5 py-3 rounded-2xl rounded-tr-sm max-w-[80%] shadow-md text-sm md:text-base leading-relaxed">
                        {message.content}
                      </div>
                    </div>
                  );
                }

                return (
                  <div
                    key={`${message.role}-${index}`}
                    className="flex justify-start w-full gap-4"
                  >
                    <div className="w-8 h-8 rounded-full bg-[#232323] border border-white/10 shrink-0 flex items-center justify-center mt-1">
                      <IconBot className="w-4 h-4 text-orange-400" />
                    </div>
                    <article className="bg-[#1c1b1b]/60 backdrop-blur-md border-l-2 border-l-orange-500 border-y border-r border-white/10 px-5 py-4 rounded-2xl rounded-tl-sm max-w-[85%] w-full">
                      <div
                        className="prose prose-invert max-w-none text-sm space-y-4
                        [&>ul]:list-disc [&>ul]:pl-4
                        [&>ol]:list-decimal [&>ol]:pl-4
                        [&_table]:w-full [&_table]:border-collapse [&_table]:my-4
                        [&_th]:border [&_th]:border-white/10 [&_th]:bg-[#232323] [&_th]:p-2 [&_th]:text-left [&_th]:text-orange-400
                        [&_td]:border [&_td]:border-white/10 [&_td]:p-2 [&_td]:text-zinc-300"
                      >
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {message.content}
                        </ReactMarkdown>
                      </div>
                    </article>
                  </div>
                );
              })}
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="w-full p-4 md:p-6 bg-gradient-to-t from-[#131313] via-[#131313]/90 to-transparent flex justify-center shrink-0">
          <div className="w-full max-w-[800px]">
            <form
              onSubmit={handleSubmit}
              className="bg-[#1c1b1b]/60 backdrop-blur-md rounded-2xl p-2 flex items-end gap-2 shadow-[0_4px_30px_rgba(0,0,0,0.5)] border border-white/10 focus-within:border-orange-500/50 transition-colors"
            >
              {/* Paperclip upload button */}
              <label
                className="p-2.5 shrink-0 flex items-center justify-center w-11 h-11 rounded-xl text-zinc-400 hover:text-orange-400 hover:bg-white/5 cursor-pointer transition-colors"
                title={uploadFile ? uploadFile.name : "Attach a document"}
              >
                {uploadStatus === "uploading" ? (
                  <span className="text-xs animate-pulse">⏳</span>
                ) : uploadStatus === "success" ? (
                  <span className="text-xs text-green-400">✓</span>
                ) : uploadFile ? (
                  <span className="text-xs text-orange-400">📄</span>
                ) : (
                  <IconPaperclip className="w-5 h-5" />
                )}
                <input
                  type="file"
                  accept=".pdf,.docx,.xlsx,.txt,.md"
                  className="hidden"
                  onChange={async (e) => {
                    const file = e.target.files?.[0] ?? null;
                    setUploadFile(file);
                    setUploadStatus("idle");
                    setUploadMessage("");
                    if (file) {
                      // Auto-upload on file select
                      setUploadStatus("uploading");
                      const formData = new FormData();
                      formData.append("file", file);
                      formData.append("user_id", String(currentUser?.user_id));
                      try {
                        const res = await fetch(
                          "http://localhost:8000/api/upload",
                          {
                            method: "POST",
                            headers: {
                              "X-API-Key": "my-super-secret-ingestion-key-123",
                            },
                            body: formData,
                          },
                        );
                        const data = await res.json();
                        if (res.ok) {
                          setUploadStatus("success");
                          setUploadMessage(`✓ ${data.message}`);
                        } else {
                          setUploadStatus("error");
                          setUploadMessage(data.detail || "Upload failed.");
                        }
                      } catch {
                        setUploadStatus("error");
                        setUploadMessage("Could not reach server.");
                      }
                    }
                  }}
                />
              </label>

              {/* Text input */}
              <textarea
                className="w-full bg-transparent border-none text-white text-sm focus:ring-0 focus:outline-none resize-none max-h-32 min-h-[44px] py-2.5 placeholder:text-zinc-500"
                onChange={(event) => setDraft(event.target.value)}
                placeholder={uploadMessage || "Ask FinanceAI anything..."}
                value={draft}
                disabled={!activeId}
                rows={1}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    (e.currentTarget.form as HTMLFormElement)?.requestSubmit();
                  }
                }}
              />

              {/* Send button */}
              <button
                className="bg-orange-500 text-black p-2.5 rounded-xl shrink-0 shadow-[inset_0_1px_1px_rgba(255,255,255,0.25)] hover:bg-orange-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                type="submit"
                disabled={!activeId || !draft.trim()}
              >
                <IconSend className="w-5 h-5" />
              </button>
            </form>
            <p className="text-center text-[11px] text-zinc-600 mt-2 font-mono">
              FinanceAI may produce inaccurate information about people, places,
              or facts.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
