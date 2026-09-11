import { useCallback, useEffect, useRef, useState } from "react";
import type { TableState } from "./types";

const apiBase = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const wsBase = apiBase.replace(/^http/, "ws");

export function useTable(tableId: string, playerId: string) {
  const [table, setTable] = useState<TableState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const socket = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!tableId || !playerId) return;
    let retry: number | undefined;
    let closed = false;
    const connect = () => {
      const ws = new WebSocket(`${wsBase}/ws/${tableId}/${playerId}`);
      socket.current = ws;
      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.type === "state") setTable(message.state);
        if (message.type === "error") setError(message.message);
      };
      ws.onopen = () => setError(null);
      ws.onclose = () => {
        if (!closed) retry = window.setTimeout(connect, 1000);
      };
    };
    connect();
    return () => {
      closed = true;
      if (retry) clearTimeout(retry);
      socket.current?.close();
    };
  }, [tableId, playerId]);

  const send = useCallback((message: object) => {
    if (socket.current?.readyState !== WebSocket.OPEN) {
      setError("Waiting for the table connection");
      return;
    }
    socket.current.send(JSON.stringify(message));
  }, []);

  return { table, error, send };
}

