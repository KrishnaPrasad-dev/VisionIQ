import Link from "next/link"


export default function Navbar() {
  return (
    <nav className="fixed top-0 left-0 w-full z-50 backdrop-blur-md bg-black/30 border-b border-white/10">

      <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">

        <Link href="/" className="text-2xl font-bold tracking-tight text-white">
  Vision<span className="text-green-400">IQ</span>
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

          <a
            href="/login"
            className="hover:text-green-400 transition duration-200"
          >
            Login
          </a>

        </div>

      </div>

    </nav>
  )
}