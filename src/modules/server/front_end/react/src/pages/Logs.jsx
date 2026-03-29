import { useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";

import LogsList from "../components/LogPageComponents/LogsList";
import LoadingBar from "../components/LoadingBar";
import usePersistentState from "../hooks/usePersistentState";
import { getLogs } from "../services/logsService";
import { findLogIndex, getLogIdentity } from "../utils/logIdentity";

const STORAGE_KEY = "home_guard_logs_page_state_v1";
const ITEMS_PER_PAGE = 10;
const CACHE_TTL_MS = 30_000;

const DEFAULT_LOG_STATE = {
  logs: [],
  page: 1,
  selectedLogIdentity: "",
  lastFetchedAt: 0,
};

export default function Logs() {
  const location = useLocation();
  const [logsState, setLogsState] = usePersistentState(STORAGE_KEY, DEFAULT_LOG_STATE);
  const [loading, setLoading] = useState(false);

  const logs = Array.isArray(logsState?.logs) ? logsState.logs : [];
  const page = Number(logsState?.page) > 0 ? Number(logsState.page) : 1;
  const selectedLogIdentity = String(logsState?.selectedLogIdentity || "");
  const lastFetchedAt = Number(logsState?.lastFetchedAt || 0);

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(logs.length / ITEMS_PER_PAGE)),
    [logs.length]
  );

  const fetchLogsFromServer = async ({ force = false } = {}) => {
    if (loading) {
      return;
    }

    if (!force && logs.length > 0 && Date.now() - lastFetchedAt < CACHE_TTL_MS) {
      return;
    }

    setLoading(true);

    try {
      const data = await getLogs();
      setLogsState((prev) => {
        const safePage = Number(prev?.page) > 0 ? Number(prev.page) : 1;
        const nextTotalPages = Math.max(1, Math.ceil(data.length / ITEMS_PER_PAGE));

        return {
          ...prev,
          logs: data,
          page: Math.min(safePage, nextTotalPages),
          lastFetchedAt: Date.now(),
        };
      });
    } catch (error) {
      console.error("Error loading logs:", error);
    } finally {
      setTimeout(() => setLoading(false), 300);
    }
  };

  useEffect(() => {
    fetchLogsFromServer();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const focusLog = location.state?.focusLog;
    if (!focusLog || logs.length === 0) {
      return;
    }

    const focusIndex = findLogIndex(logs, focusLog);
    if (focusIndex < 0) {
      return;
    }

    const focusPage = Math.floor(focusIndex / ITEMS_PER_PAGE) + 1;
    const focusIdentity = getLogIdentity(logs[focusIndex], focusIndex);

    setLogsState((prev) => ({
      ...prev,
      page: focusPage,
      selectedLogIdentity: focusIdentity,
    }));
  }, [location.state, logs, setLogsState]);

  useEffect(() => {
    if (page <= totalPages) {
      return;
    }
    setLogsState((prev) => ({ ...prev, page: totalPages }));
  }, [page, totalPages, setLogsState]);

  const handlePageChange = (nextPage) => {
    const safePage = Math.max(1, Math.min(nextPage, totalPages));
    setLogsState((prev) => ({ ...prev, page: safePage }));
  };

  const handleSelectLog = (log, absoluteIndex) => {
    const identity = getLogIdentity(log, absoluteIndex);
    setLogsState((prev) => ({
      ...prev,
      selectedLogIdentity: identity,
    }));
  };

  return (
    <div className="min-h-screen bg-gray-900 p-6 text-white">
      <LoadingBar loading={loading} />

      <div className="rounded-t-2xl border-b border-gray-700 bg-gray-800 p-6 shadow-xl">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-red-400">System Logs & Events</h1>
            <p className="mt-2 text-sm text-gray-400">Nguon du lieu: PostgreSQL logs (fallback file neu DB unavailable).</p>
          </div>

          <button
            onClick={() => fetchLogsFromServer({ force: true })}
            className={`rounded-xl px-6 py-2 shadow transition ${
              loading
                ? "cursor-not-allowed bg-gray-600 text-gray-400"
                : "bg-teal-600 text-white hover:bg-teal-500"
            }`}
            disabled={loading}
          >
            {loading ? "Dang tai..." : "Tai lai Logs"}
          </button>
        </div>
      </div>

      <div className="min-h-[70vh] rounded-b-2xl border border-gray-700 bg-gray-800 p-4 shadow-2xl">
        {logs.length === 0 ? (
          <div className="mt-10 p-4 text-center text-gray-500">
            {loading ? "Dang cho du lieu..." : "Khong co log nao de hien thi."}
          </div>
        ) : (
          <LogsList
            logs={logs}
            page={page}
            onPageChange={handlePageChange}
            itemsPerPage={ITEMS_PER_PAGE}
            selectedLogIdentity={selectedLogIdentity}
            onSelectLog={handleSelectLog}
          />
        )}
      </div>
    </div>
  );
}
