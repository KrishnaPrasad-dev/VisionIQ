export default function StatusPanel() {
  return (
    <div className="bg-black border border-gray-800 rounded-xl p-4">
      <h2 className="text-gray-400 text-sm mb-3">SYSTEM STATUS</h2>

      <div className="space-y-2 text-sm text-gray-300">
        <div>Camera: Online</div>
        <div>People Detected: 0</div>
        <div>Zone Activity: None</div>
      </div>
    </div>
  )
}