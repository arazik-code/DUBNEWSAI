"use client"

import { useQueryClient } from "@tanstack/react-query"
import { createContext, ReactNode, useContext, useEffect, useMemo, useRef, useState } from "react"
import toast from "react-hot-toast"

import { getDefaultWsUrl } from "@/lib/config/api"
import { useAuthStore } from "@/lib/store/authStore"
import { useNotificationStore } from "@/lib/store/notificationStore"
import type { NotificationItem } from "@/types"

interface WebSocketContextType {
  socket: WebSocket | null
  isConnected: boolean
  sendMessage: (message: Record<string, unknown>) => void
  joinRoom: (room: string) => void
  subscribeSymbol: (symbol: string) => void
}

const WebSocketContext = createContext<WebSocketContextType>({
  socket: null,
  isConnected: false,
  sendMessage: () => undefined,
  joinRoom: () => undefined,
  subscribeSymbol: () => undefined
})

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const { accessToken, hydrated, user } = useAuthStore()
  const upsertNotification = useNotificationStore((state) => state.upsert)
  const [isConnected, setIsConnected] = useState(false)
  const socketRef = useRef<WebSocket | null>(null)
  const heartbeatRef = useRef<number | null>(null)

  useEffect(() => {
    if (
      typeof window === "undefined" ||
      !hydrated ||
      !accessToken ||
      !user ||
      !["premium", "admin"].includes(user.role) ||
      isTokenExpired(accessToken)
    ) {
      return
    }

    const wsBase = getDefaultWsUrl()
    const url = `${wsBase.replace(/\/$/, "")}/api/v1/ws?token=${encodeURIComponent(accessToken)}`
    const socket = new WebSocket(url)

    socket.onopen = () => {
      setIsConnected(true)
      socket.send(JSON.stringify({ type: "join_room", room: "trending" }))
      heartbeatRef.current = window.setInterval(() => {
        socket.send(JSON.stringify({ type: "ping" }))
      }, 30000)
    }

    socket.onclose = () => {
      setIsConnected(false)
      if (heartbeatRef.current) {
        window.clearInterval(heartbeatRef.current)
      }
    }

    socket.onerror = () => {
      setIsConnected(false)
    }

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)

        if (payload.type === "new_article") {
          toast.success("New article published")
          queryClient.invalidateQueries({ queryKey: ["news"] })
        }

        if (payload.type === "market_update") {
          queryClient.invalidateQueries({ queryKey: ["market"] })
        }

        if (payload.type === "notification") {
          const data = payload.data as NotificationItem | undefined
          if (data) {
            upsertNotification(data)
          }
          toast(data?.title || data?.message || "New notification")
        }
      } catch {
        toast.error("Received malformed realtime message")
      }
    }

    socketRef.current = socket
    return () => {
      if (heartbeatRef.current) {
        window.clearInterval(heartbeatRef.current)
      }
      socket.close()
      socketRef.current = null
    }
  }, [accessToken, hydrated, queryClient, upsertNotification, user])

  const value = useMemo<WebSocketContextType>(
    () => ({
      socket: socketRef.current,
      isConnected,
      sendMessage: (message) => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
          socketRef.current.send(JSON.stringify(message))
        }
      },
      joinRoom: (room) => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
          socketRef.current.send(JSON.stringify({ type: "join_room", room }))
        }
      },
      subscribeSymbol: (symbol) => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
          socketRef.current.send(JSON.stringify({ type: "subscribe_symbol", symbol }))
        }
      }
    }),
    [isConnected]
  )

  return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>
}

export const useWebSocket = () => useContext(WebSocketContext)

function isTokenExpired(token: string) {
  try {
    const [, payload] = token.split(".")
    if (!payload) {
      return true
    }
    const decoded = JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/"))) as { exp?: number }
    if (!decoded.exp) {
      return true
    }
    return decoded.exp * 1000 <= Date.now() + 30_000
  } catch {
    return true
  }
}
