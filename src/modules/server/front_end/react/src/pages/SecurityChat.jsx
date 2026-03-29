import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import usePersistentState from "../hooks/usePersistentState";
import { querySecurityLogs } from "../services/securityChatService";

const RANGE_STEP_MINUTES = 60;
const RANGE_MIN_GAP = RANGE_STEP_MINUTES;
const DEFAULT_TOP_K = 6;
const STORAGE_KEY = "home_guard_security_chat_state_v1";
const LEGACY_BOOT_MESSAGE_MARKER = "hay dat cau hoi ve lich su log";

const DEFAULT_CHAT_STATE = {
  question: "What essential events happened last 3 days?",
  topK: DEFAULT_TOP_K,
  messages: [],
  retrievedLogs: [],
  startOffsetMinutes: 0,
  endOffsetMinutes: null,
};

function toApiDateTime(date) {
  const pad = (value) => String(value).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(
    date.getHours()
  )}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

function toDisplayDateTime(date) {
  return date.toLocaleString("vi-VN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function LoadingDots() {
  return (
    <div className="flex items-center gap-1.5">
      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-300" style={{ animationDelay: "-0.3s" }} />
      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-300" style={{ animationDelay: "-0.15s" }} />
      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-300" />
    </div>
  );
}

export default function SecurityChat() {
  const navigate = useNavigate();
  const [chatState, setChatState] = usePersistentState(STORAGE_KEY, DEFAULT_CHAT_STATE);
  const [errorMessage, setErrorMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const {
    rangeStartDate,
    rangeEndDate,
    maxOffsetMinutes,
  } = useMemo(() => {
    const now = new Date();
    const marchStart = new Date(now.getFullYear(), 2, 1, 0, 0, 0, 0);
    if (marchStart > now) {
      marchStart.setFullYear(marchStart.getFullYear() - 1);
    }

    const diffMinutes = Math.max(
      RANGE_STEP_MINUTES,
      Math.floor((now.getTime() - marchStart.getTime()) / 60000)
    );

    return {
      rangeStartDate: marchStart,
      rangeEndDate: now,
      maxOffsetMinutes: diffMinutes,
    };
  }, []);

  const question = typeof chatState?.question === "string" ? chatState.question : "";
  const topK = Number(chatState?.topK) || DEFAULT_TOP_K;
  const messages = Array.isArray(chatState?.messages) ? chatState.messages : [];
  const retrievedLogs = Array.isArray(chatState?.retrievedLogs) ? chatState.retrievedLogs : [];

  const startOffsetMinutes = Number.isFinite(chatState?.startOffsetMinutes)
    ? chatState.startOffsetMinutes
    : 0;

  const endOffsetMinutes = Number.isFinite(chatState?.endOffsetMinutes)
    ? chatState.endOffsetMinutes
    : maxOffsetMinutes;

  useEffect(() => {
    setChatState((prev) => {
      const previous = prev || {};
      const prevStart = Number.isFinite(previous.startOffsetMinutes) ? previous.startOffsetMinutes : 0;
      const prevEnd = Number.isFinite(previous.endOffsetMinutes) ? previous.endOffsetMinutes : maxOffsetMinutes;

      const safeStart = Math.max(0, Math.min(prevStart, maxOffsetMinutes - RANGE_MIN_GAP));
      const safeEnd = Math.min(
        maxOffsetMinutes,
        Math.max(prevEnd, safeStart + RANGE_MIN_GAP)
      );

      const safeMessages = Array.isArray(previous.messages)
        ? previous.messages.filter((message) => {
            const content = String(message?.content || "").trim().toLowerCase();
            return !(
              message?.role === "assistant" &&
              content.includes(LEGACY_BOOT_MESSAGE_MARKER)
            );
          })
        : [];

      return {
        question:
          typeof previous.question === "string" ? previous.question : DEFAULT_CHAT_STATE.question,
        topK: Number(previous.topK) || DEFAULT_TOP_K,
        messages: safeMessages,
        retrievedLogs: Array.isArray(previous.retrievedLogs) ? previous.retrievedLogs : [],
        startOffsetMinutes: safeStart,
        endOffsetMinutes: safeEnd,
      };
    });
  }, [maxOffsetMinutes, setChatState]);

  const selectedStartDate = useMemo(
    () => new Date(rangeStartDate.getTime() + startOffsetMinutes * 60000),
    [rangeStartDate, startOffsetMinutes]
  );

  const selectedEndDate = useMemo(
    () => new Date(rangeStartDate.getTime() + endOffsetMinutes * 60000),
    [rangeStartDate, endOffsetMinutes]
  );

  const startPercent = (startOffsetMinutes / maxOffsetMinutes) * 100;
  const endPercent = (endOffsetMinutes / maxOffsetMinutes) * 100;

  const appendMessage = (message) => {
    setChatState((prev) => {
      const safePrevMessages = Array.isArray(prev?.messages) ? prev.messages : [];
      return {
        ...prev,
        messages: [...safePrevMessages, message],
      };
    });
  };

  const handleNewChat = () => {
    setErrorMessage("");
    setChatState((prev) => ({
      ...prev,
      question: DEFAULT_CHAT_STATE.question,
      messages: [],
      retrievedLogs: [],
    }));
  };

  const handleChangeStart = (event) => {
    const nextValue = Number(event.target.value);
    setChatState((prev) => ({
      ...prev,
      startOffsetMinutes: Math.min(nextValue, endOffsetMinutes - RANGE_MIN_GAP),
    }));
  };

  const handleChangeEnd = (event) => {
    const nextValue = Number(event.target.value);
    setChatState((prev) => ({
      ...prev,
      endOffsetMinutes: Math.max(nextValue, startOffsetMinutes + RANGE_MIN_GAP),
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const cleanQuestion = question.trim();

    if (!cleanQuestion || loading) {
      return;
    }

    setErrorMessage("");
    setLoading(true);
    appendMessage({ role: "user", content: cleanQuestion });

    try {
      const result = await querySecurityLogs({
        question: cleanQuestion,
        top_k: Number(topK),
        start_time: toApiDateTime(selectedStartDate),
        end_time: toApiDateTime(selectedEndDate),
      });

      appendMessage({
        role: "assistant",
        content: result.answer || "Khong co phan hoi.",
      });

      setChatState((prev) => ({
        ...prev,
        question: "",
        retrievedLogs: Array.isArray(result.retrieved_logs) ? result.retrieved_logs : [],
      }));
    } catch (error) {
      const msg = error?.message || "Co loi xay ra khi truy van.";
      setErrorMessage(msg);
      appendMessage({ role: "assistant", content: msg });
      setChatState((prev) => ({
        ...prev,
        retrievedLogs: [],
      }));
    } finally {
      setLoading(false);
    }
  };

  const handleOpenLogInLogsTab = (log) => {
    navigate("/logs", {
      state: {
        focusLog: {
          id: log?.id ?? "",
          time: log?.time ?? log?.occurrence_time ?? "",
          title: log?.title ?? "",
        },
      },
    });
  };

  return (
    <div className="min-h-screen bg-gray-900 p-6 text-white">
      <div className="mx-auto w-full max-w-7xl">
        <h1 className="text-2xl font-bold text-teal-300">Security Chat</h1>
        <div className="mt-3 flex justify-end">
          <button
            type="button"
            onClick={handleNewChat}
            className="rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-sm font-semibold text-gray-100 hover:border-teal-500 hover:text-teal-300"
          >
            New Chat
          </button>
        </div>

        <section className="mt-4 rounded-2xl border border-gray-700 bg-gray-800 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="text-sm text-gray-300">
              <span className="font-semibold text-gray-100">Time Window:</span>{" "}
              {toDisplayDateTime(selectedStartDate)} - {toDisplayDateTime(selectedEndDate)}
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-300">
              <span className="font-semibold text-gray-100">top_k:</span>
              <select
                value={topK}
                onChange={(event) => setChatState((prev) => ({ ...prev, topK: Number(event.target.value) }))}
                className="rounded-md border border-gray-600 bg-gray-900 px-2 py-1 text-sm text-white"
              >
                {[3, 5, 6, 8, 10, 12].map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="relative mt-4 h-10">
            <div className="absolute left-0 right-0 top-1/2 h-1 -translate-y-1/2 rounded bg-gray-700" />
            <div
              className="absolute top-1/2 h-1 -translate-y-1/2 rounded bg-teal-500"
              style={{ left: `${startPercent}%`, right: `${100 - endPercent}%` }}
            />
            <input
              type="range"
              min={0}
              max={maxOffsetMinutes}
              step={RANGE_STEP_MINUTES}
              value={startOffsetMinutes}
              onChange={handleChangeStart}
              className="dual-range absolute left-0 top-1/2 h-1 w-full -translate-y-1/2"
            />
            <input
              type="range"
              min={0}
              max={maxOffsetMinutes}
              step={RANGE_STEP_MINUTES}
              value={endOffsetMinutes}
              onChange={handleChangeEnd}
              className="dual-range absolute left-0 top-1/2 h-1 w-full -translate-y-1/2"
            />
          </div>
          <div className="mt-1 flex justify-between text-xs text-gray-500">
            <span>{toDisplayDateTime(rangeStartDate)}</span>
            <span>{toDisplayDateTime(rangeEndDate)}</span>
          </div>
        </section>

        <div className="relative mt-6 min-h-[70vh]">
          <div className="lg:pr-[22rem]">
            <section className="flex h-[70vh] flex-col overflow-hidden rounded-2xl border border-gray-700 bg-gray-800 shadow-xl">
              <div className="flex-1 space-y-4 overflow-y-auto p-5">
                {messages.map((message, index) => (
                  <div
                    key={`${message.role}-${index}`}
                    className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6 ${
                        message.role === "user"
                          ? "bg-teal-600 text-white"
                          : "border border-gray-700 bg-gray-900/70 text-gray-100"
                      }`}
                    >
                      {message.content}
                    </div>
                  </div>
                ))}

                {loading ? (
                  <div className="flex justify-start">
                    <div className="rounded-2xl border border-gray-700 bg-gray-900/70 px-4 py-3">
                      <LoadingDots />
                    </div>
                  </div>
                ) : null}
              </div>

              <form onSubmit={handleSubmit} className="border-t border-gray-700 p-4">
                <div className="flex items-end gap-3">
                  <textarea
                    rows={2}
                    value={question}
                    onChange={(event) => setChatState((prev) => ({ ...prev, question: event.target.value }))}
                    placeholder="Hoi ve lich su log trong khoang thoi gian da chon..."
                    className="w-full resize-none rounded-xl border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-white outline-none placeholder:text-gray-500 focus:border-teal-500"
                  />
                  <button
                    type="submit"
                    disabled={loading || !question.trim()}
                    className="rounded-xl bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-500 disabled:cursor-not-allowed disabled:bg-gray-600"
                  >
                    Send
                  </button>
                </div>
                {errorMessage ? <p className="mt-2 text-xs text-red-300">{errorMessage}</p> : null}
              </form>
            </section>
          </div>

          <aside
            className="absolute right-0 top-0 h-full w-80 rounded-l-2xl border-l border-gray-700 bg-gray-800 p-4 shadow-2xl"
          >
            <h2 className="text-sm font-bold uppercase tracking-wide text-yellow-300">Retrieved Logs</h2>
            <p className="mt-1 text-xs text-gray-400">
              {retrievedLogs.length > 0
                ? `${retrievedLogs.length} log duoc tra ve trong query gan nhat.`
                : "Chua co log duoc truy xuat."}
            </p>

            <div className="mt-4 max-h-[calc(100%-3.5rem)] space-y-3 overflow-y-auto pr-1">
              {retrievedLogs.map((log, index) => (
                <button
                  type="button"
                  key={log?.id || `${log?.time || log?.occurrence_time}-${index}`}
                  onClick={() => handleOpenLogInLogsTab(log)}
                  className="w-full rounded-lg border border-gray-700 bg-gray-900/70 p-3 text-left transition hover:border-teal-500 hover:bg-gray-900"
                >
                  <p className="text-sm font-semibold text-gray-100">{log?.title || "LOG"}</p>
                  <p className="mt-1 text-xs text-gray-500">{log?.time || log?.occurrence_time || "--:--:--"}</p>
                  <p className="mt-2 text-xs leading-5 text-gray-300">
                    {log?.description || log?.system_label || "Khong co mo ta"}
                  </p>
                  <p className="mt-2 text-[11px] font-semibold uppercase tracking-wide text-teal-300">
                    Open in Logs tab
                  </p>
                </button>
              ))}
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
