"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import axios from "axios"
import { useRouter } from "next/navigation"
import { useEffect } from "react"
import toast from "react-hot-toast"

import { getCurrentUser, loginUser, registerUser } from "@/lib/api/auth"
import { useAuthStore } from "@/lib/store/authStore"
import type { LoginPayload, RegisterPayload } from "@/types"

export function useAuth() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const { accessToken, refreshToken, hydrated, user, setAuth, setTokens, setUser, clearAuth } = useAuthStore()
  const shouldFetchProfile = hydrated && Boolean(accessToken) && !user

  const profileQuery = useQuery({
    queryKey: ["auth", "me"],
    queryFn: getCurrentUser,
    enabled: shouldFetchProfile,
    retry: false,
    staleTime: Infinity,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false
  })

  useEffect(() => {
    if (profileQuery.data) {
      setUser(profileQuery.data)
    }
  }, [profileQuery.data, setUser])

  useEffect(() => {
    const isUnauthorized =
      axios.isAxiosError(profileQuery.error) &&
      (profileQuery.error.response?.status === 401 || profileQuery.error.response?.status === 403)

    if (isUnauthorized && hydrated && accessToken) {
      clearAuth()
      router.replace("/login")
    }
  }, [accessToken, clearAuth, hydrated, profileQuery.error, router])

  const loginMutation = useMutation({
    mutationFn: loginUser,
    onSuccess: async (tokens) => {
      setTokens(tokens.access_token, tokens.refresh_token)
      const currentUser = await getCurrentUser()
      setAuth(currentUser, tokens.access_token, tokens.refresh_token)
      queryClient.setQueryData(["auth", "me"], currentUser)
      toast.success("Welcome back to DUBNEWSAI")
      router.push("/dashboard")
    },
    onError: () => {
      toast.error("Unable to sign in with those credentials")
    }
  })

  const registerMutation = useMutation({
    mutationFn: async (payload: RegisterPayload) => {
      await registerUser(payload)
      return loginUser({
        email: payload.email,
        password: payload.password
      })
    },
    onSuccess: async (tokens) => {
      setTokens(tokens.access_token, tokens.refresh_token)
      const currentUser = await getCurrentUser()
      setAuth(currentUser, tokens.access_token, tokens.refresh_token)
      queryClient.setQueryData(["auth", "me"], currentUser)
      toast.success("Your account is ready")
      router.push("/dashboard")
    },
    onError: () => {
      toast.error("Unable to create your account")
    }
  })

  return {
    accessToken,
    refreshToken,
    hydrated,
    user,
    isAuthenticated: hydrated && !!accessToken,
    isLoadingProfile: profileQuery.isLoading,
    login: (payload: LoginPayload) => loginMutation.mutateAsync(payload),
    register: (payload: RegisterPayload) => registerMutation.mutateAsync(payload),
    logout: () => {
      clearAuth()
      queryClient.removeQueries({ queryKey: ["auth"] })
      router.push("/login")
    },
    loginPending: loginMutation.isPending,
    registerPending: registerMutation.isPending
  }
}
