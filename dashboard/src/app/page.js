"use client"

import GridBackground from "../components/GridBackground"
import Navbar from "../components/Navbar"
import SecurityCameraModel from "../components/SecurityCameraModel"
import CardTilt from "../components/CardTilt"
import Link from "next/link"

export default function Home() {
  return (
    <main className="relative text-white overflow-hidden">

      {/* Hero Section - Full screen with Grid Background */}
      <section className="relative min-h-screen flex items-center">
        <GridBackground />
        <Navbar />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8 pt-20 sm:pt-24 md:pt-32 pb-12 sm:pb-16 md:pb-20 grid grid-cols-1 md:grid-cols-2 items-center gap-6 sm:gap-8 md:gap-12 relative z-10">

          {/* Left Side Text */}
          <div className="space-y-6 sm:space-y-8 text-center md:text-left">

            <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight leading-tight">
              Vision<span className="text-green-400 drop-shadow-[0_0_6px_black]">IQ</span>
            </h1>

            

            <p className="text-xl sm:text-xl text-gray-200 leading-relaxed">
              VisionIQ is an AI-powered smart surveillance system that goes beyond traditional monitoring by analyzing visual data in real time.
            </p>


            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 pt-4 md:pt-0">
              <Link href="/login" className="w-full sm:w-auto">
                <button className="w-full px-6 sm:px-8 py-3 bg-green-500 hover:bg-green-600 text-black font-bold rounded-lg transition">
                  Get Started
                </button>
              </Link>
            </div>

          </div>

          {/* Right Side 3D Model */}
          <div className="block h-56 sm:h-72 md:h-[400px] lg:h-[600px] w-full">
            <SecurityCameraModel />
          </div>

        </div>
      </section>

      {/* How It Works Section - Premium Design */}
      <section className="relative bg-black pt-12 sm:pt-16 md:pt-24 pb-12 sm:pb-20 md:pb-40 overflow-hidden">
        {/* Gradient fade-in at top */}
        <div className="absolute top-0 left-0 right-0 h-20 sm:h-32 md:h-40 bg-gradient-to-b from-transparent via-black/50 to-black pointer-events-none"></div>

        {/* Animated background grid */}
        <div className="absolute inset-0 opacity-5">
          <div className="absolute inset-0" style={{
            backgroundImage: 'linear-gradient(rgba(34,197,94,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(34,197,94,0.1) 1px, transparent 1px)',
            backgroundSize: '50px 50px'
          }}></div>
        </div>

        <div className="max-w-6xl mx-auto px-4 sm:px-6 md:px-8 relative z-10">
          {/* Section Header */}
          <div className="text-center mb-12 sm:mb-16 md:mb-24">
            <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold mb-4 md:mb-6 leading-tight">
              How <span className="text-green-400">VisionIQ</span> Works
            </h2>
            <p className="text-gray-300 text-sm sm:text-base md:text-lg max-w-2xl mx-auto leading-relaxed px-2">
              Deploy in minutes. Detect threats in milliseconds. Manage incidents in real-time.
            </p>
          </div>

          {/* Steps Container */}
          <div className="relative">
            {/* Connecting line - Desktop only */}
            <div className="hidden md:block absolute top-24 left-[8%] right-[8%] h-1 bg-gradient-to-r from-transparent via-green-500/30 to-transparent"></div>

            {/* Steps Grid - Responsive columns */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6 md:gap-10 md:gap-12">

              <CardTilt 
                number="1"
                title="Connect"
                description="Add RTSP streams or IP cameras to your VisionIQ instance"
              />

              <CardTilt 
                number="2"
                title="Analyze"
                description="YOLOv8 AI detects objects, people, and behavioral anomalies"
              />

              <CardTilt 
                number="3"
                title="Score"
                description="Intelligent threat levels calculated in real-time"
              />

              <CardTilt 
                number="4"
                title="Alert"
                description="Instant notifications and incident management from dashboard"
              />

            </div>
          </div>
        </div>
      </section>

    </main>
  )
}
