
"use client";

import Link from "next/link"
import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Bell } from "lucide-react"


export default function Navbar() {
  const router = useRouter()
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [isMounted, setIsMounted] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem("authToken")
    setIsLoggedIn(!!token)
    setIsMounted(true)
  }, [])

  const handleLogout = useCallback(() => {
    localStorage.removeItem("authToken")
    setIsLoggedIn(false)
    router.push("/login")
  }, [router])

  if (!isMounted) return null

  return (
    <nav className="fixed top-0 left-0 w-full z-50 backdrop-blur-md bg-black/30 border-b border-white/10">

      <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">

        <Link href="/" className="text-2xl font-bold tracking-tight text-white">
          Quantum<span className="text-green-400">Eye</span>
        </Link>

        {/* Links */}
        <div className="flex gap-10 text-sm uppercase tracking-wider font-medium text-gray-200">

          <a
            href="#"
            className="hover:text-green-400 transition duration-200"
          >
            Home
          </a>

          <a
            href="/dashboard"
            className="hover:text-green-400 transition duration-200"
          >
            Dashboard
          </a>

          <a
            href="/cameras"
            className="hover:text-green-400 transition duration-200"
          >
           Cameras
          </a>

          <a
            href="/alerts"
            className="hover:text-green-400 transition duration-200"
          >
            Alerts
          </a>

          <button
            className="relative hover:text-green-400 transition duration-200 flex items-center justify-center"
            title="Notifications"
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
            <a
              href="/login"
              className="hover:text-green-400 transition duration-200"
            >
              Login
            </a>
          )}

        </div>

      </div>

    </nav>
  )
}