"use client";
import PixelBlast from "../../components/PixelBlast";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function SignupPage() {
  const router = useRouter();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSignup = async (e) => {
    e.preventDefault();

    const res = await fetch("/api/auth/signup", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ name, email, password })
    });

    const data = await res.json();

    if (res.ok) {
      alert("Signup successful ✅");
      router.push("/login");
    } else {
      alert(data.error || "Signup failed ❌");
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

        
        <div className="flex-1 flex items-center justify-center px-8 md:px-16">
          <div className="max-w-xl space-y-6">

            <h1 className="text-4xl md:text-6xl font-bold leading-tight">
              Enter the future of{" "}
              <span className="text-[#14eb55]">AI Surveillance</span>
            </h1>

            <p className="text-gray-400 text-lg">
              Monitor. Analyze. Detect threats in real time.
              VisionIQ gives you intelligent control over your digital security space.
            </p>

            <div className="text-sm text-gray-500">
              Watch real time alerts over your cameras.
            </div>

          </div>
        </div>

        
        <div className="flex-1 flex items-center justify-center px-6 py-10">

        <form
          onSubmit={handleSignup}
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
            <h2 className="text-3xl font-semibold tracking-tight">
              Create Account
            </h2>
            <p className="text-sm text-gray-400">
              Start monitoring your digital space
            </p>
          </div>

          {/* Inputs from the user */}
          <div className="space-y-4">
            <input
              type="text"
              placeholder="Full Name"
              className="
                w-full p-3 rounded-lg 
                bg-black/40 
                border border-white/10 
                focus:border-[#14eb55] 
                outline-none
              "
              value={name}
              onChange={(e) => setName(e.target.value)}
            />

            <input
              type="email"
              placeholder="Email"
              className="
                w-full p-3 rounded-lg 
                bg-black/40 
                border border-white/10 
                focus:border-[#14eb55] 
                outline-none
              "
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            

            <input
              type="password"
              placeholder="Password"
              className="
                w-full p-3 rounded-lg 
                bg-black/40 
                border border-white/10 
                focus:border-[#14eb55] 
                outline-none
              "
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          
          <button
            className="
              w-full py-3 rounded-lg 
              bg-[#14eb55] 
              text-black font-semibold 
              hover:opacity-90 
              transition
            "
          >
            Sign Up
          </button>

          
          <p className="text-sm text-center text-gray-400">
            Already have an account?{" "}
            <span
              onClick={() => router.push("/login")}
              className="text-white cursor-pointer hover:underline"
            >
              Login
            </span>
          </p>
        </form>

      </div>
      </div>
    </main>
  );
}