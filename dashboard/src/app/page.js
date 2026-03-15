import GridBackground from "../components/GridBackground"
import Navbar from "../components/Navbar"
import SecurityCameraModel from "../components/SecurityCameraModel"

export default function Home() {
  return (
    <main className="relative min-h-screen text-white overflow-hidden">

      <GridBackground />
      <Navbar />

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-8 pt-32 pb-20 grid md:grid-cols-2 items-center gap-12">

        {/* Left Side Text */}
        <div className="space-y-6">

          <h1 className="text-6xl md:text-7xl font-extrabold tracking-tight">
            Vision<span className="text-green-400 drop-shadow-[0_0_6px_black]">IQ</span>
          </h1>

          <p className="text-xl text-gray-300 font-medium">
            An AI-Based Smart Surveillance System
          </p>

          <p className="text-lg text-gray-400 max-w-xl leading-relaxed">
            VisionIQ is an AI-powered smart surveillance system that goes beyond traditional monitoring by analyzing visual data in real time.
          </p>

          <p className="text-green-400 rounded-lg bg-black/50 pl-3 border border-black/50 font-semibold text-lg py-2 tracking-wide">
           &quot;See Smarter. Stay Safer.&quot;
          </p>

        </div>

        {/* Right Side 3D Model */}
        <div className="h-[500px] w-full">
          <SecurityCameraModel />
        </div>

      </section>

    </main>
  )
}