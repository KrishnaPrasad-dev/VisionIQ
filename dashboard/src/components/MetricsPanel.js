export default function MetricsPanel() {

  return (

    <div className="grid grid-cols-2 gap-4">

      <Metric title="People" value="0" />
      <Metric title="Loitering" value="0" />
      <Metric title="Zone Breach" value="NO" />
      <Metric title="After Hours" value="NO" />

    </div>

  )
}

function Metric({ title, value }) {

  return (

    <div className="bg-white/5 border border-white/10 p-4 rounded-xl">

      <p className="text-xs text-gray-400">{title}</p>

      <h2 className="text-xl font-bold">{value}</h2>

    </div>

  )
}