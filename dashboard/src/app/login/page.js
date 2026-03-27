"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import PixelBlast from "../../components/PixelBlast";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();

    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ email, password })
    });

    const data = await res.json();

    if (res.ok) {
      if (data.token) {
        localStorage.setItem("quantumeye_token", data.token)
      }
      router.push("/dashboard");
    } else {
      alert(data.error || "Login failed ❌");
    }
  };

  return (
    <main className="relative min-h-screen overflow-hidden text-white">

      <div className="absolute inset-0">
        <PixelBlast
          variant="diamond"
          pixelSize={3}
          color="#14eb55"
          patternScale={2}
          patternDensity={0.7}
          enableRipples
          rippleSpeed={0.4}
          transparent
        />
      </div>

      <div className="relative z-10 flex flex-col md:flex-row min-h-screen">

        {/* Text section on the left */}
        <div className="flex-1 flex items-center justify-center px-8 md:px-16">
          <div className="max-w-xl space-y-6">

            <h1 className="text-4xl md:text-6xl font-bold leading-tight">
              Welcome back to{" "}
              <span className="text-[#14eb55]">QuantumEye</span>
            </h1>

            <p className="text-gray-400 text-lg">
              Access your AI-powered surveillance system.
              Monitor activity, detect threats, and stay in control.
            </p>

            <div className="text-md text-gray-200">
              Secure. Intelligent. Real-time.
            </div>

          </div>
        </div>

        {/* Login form */}
        <div className="flex-1 flex items-center justify-center px-6 py-10">

          <form
            onSubmit={handleLogin}
            className="
              w-full max-w-md 
              p-8 
              rounded-2xl 
              backdrop-blur-xl 
              bg-white/5 
              border border-white/10 
              shadow-[0_0_60px_rgba(20,235,85,0.15)]
              space-y-5
            "
          >
          
            <div className="space-y-1 text-center">
              <h2 className="text-4xl font-semibold">Login</h2>
              <p className="text-sm text-gray-400">
                Enter your credentials
              </p>
            </div>

            {/* The User Input Fields */}
            <input
              type="email"
              placeholder="Email"
              className="w-full p-3 rounded-lg bg-black/40 border border-white/10 focus:border-[#14eb55] outline-none"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <input
              type="password"
              placeholder="Password"
              className="w-full p-3 rounded-lg bg-black/40 border border-white/10 focus:border-[#14eb55] outline-none"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            <button className="w-full py-3 rounded-lg bg-[#14eb55] text-black font-semibold hover:opacity-90 transition">
              Login
            </button>

            <p className="text-sm text-center text-gray-400">
              Don’t have an account?{" "}
              <span
                onClick={() => router.push("/signup")}
                className="text-white cursor-pointer hover:underline"
              >
                Signup
              </span>
            </p>
          </form>

        </div>

      </div>
    </main>
  );
}