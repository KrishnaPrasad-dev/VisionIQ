
"use client";

import Link from "next/link"
import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Bell } from "lucide-react"

const TOKEN_KEYS = ["visioniq_token", "authToken", "quantumeye_token"]


export default function Navbar() {
  const router = useRouter()
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [isMounted, setIsMounted] = useState(false)

  useEffect(() => {
    const token = TOKEN_KEYS.find(key => localStorage.getItem(key))
    setIsLoggedIn(!!token)
    setIsMounted(true)
  }, [])

  const handleLogout = useCallback(() => {
    TOKEN_KEYS.forEach(key => localStorage.removeItem(key))
    setIsLoggedIn(false)
    router.push("/login")
  }, [router])

  if (!isMounted) return null

  return (
    <nav className="fixed top-0 left-0 w-full z-50 backdrop-blur-md bg-black/30 border-b border-white/10">

      <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">

        <Link href="/" className="text-2xl font-bold tracking-tight text-white">
          Vision<span className="text-green-400">IQ</span>
        </Link>

        {/* Links */}
        <div className="flex gap-10 text-sm uppercase tracking-wider font-medium text-gray-200">

          <Link href="/" className="hover:text-green-400 transition duration-200">
            Home
          </Link>

          <Link href="/dashboard" className="hover:text-green-400 transition duration-200">
            Dashboard
          </Link>

          <Link href="/cameras" className="hover:text-green-400 transition duration-200">
           Cameras
          </Link>

          <Link href="/alerts" className="hover:text-green-400 transition duration-200">
            Alerts
          </Link>

          <button
            className="relative hover:text-green-400 transition duration-200 flex items-center justify-center"
            title="Notifications"
            aria-label="Notifications"
          >
            <Bell size={20} />
            <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>

          {isLoggedIn ? (
            <button
              onClick={handleLogout}
              className="hover:text-red-400 transition duration-200 cursor-pointer"
            >
              Logout
            </button>
          ) : (
            <Link href="/login" className="hover:text-green-400 transition duration-200">
              Login
            </Link>
          )}

        </div>

      </div>

    </nav>
  )
}