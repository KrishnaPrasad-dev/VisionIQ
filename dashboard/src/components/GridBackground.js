"use client"

import { GridScan } from "../components/GridScan"

export default function GridBackground() {
  return (
    <div className="absolute inset-0 -z-10">
      <GridScan
  sensitivity={0.5}
  lineThickness={1}
  linesColor="#000000"
  gridScale={0.10}
  scanColor="#00ff41"
  scanOpacity={0.25}
  enablePost
  bloomIntensity={0.3}
  chromaticAberration={0}
  noiseIntensity={0}
  lineJitter={0}
/>
    </div>
  )
}