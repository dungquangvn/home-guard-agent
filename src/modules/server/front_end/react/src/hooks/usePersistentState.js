import { useEffect, useState } from "react";

function resolveInitialValue(initialValue) {
  return typeof initialValue === "function" ? initialValue() : initialValue;
}

export default function usePersistentState(storageKey, initialValue) {
  const [state, setState] = useState(() => {
    if (typeof window === "undefined") {
      return resolveInitialValue(initialValue);
    }

    try {
      const stored = window.localStorage.getItem(storageKey);
      if (stored === null) {
        return resolveInitialValue(initialValue);
      }
      return JSON.parse(stored);
    } catch {
      return resolveInitialValue(initialValue);
    }
  });

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    try {
      window.localStorage.setItem(storageKey, JSON.stringify(state));
    } catch {
      // Ignore storage errors (quota, privacy mode, etc.)
    }
  }, [storageKey, state]);

  return [state, setState];
}
