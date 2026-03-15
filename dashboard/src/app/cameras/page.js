"use client"

import { useState } from "react"
import Navbar from "../../components/Navbar"
import GridBackground from "../../components/GridBackground"

export default function CamerasPage(){

  const [name,setName] = useState("")
  const [url,setUrl] = useState("")

  const [activeCamera,setActiveCamera] = useState("Shop Entrance")

  const [cameras,setCameras] = useState([
    {
      name:"Shop Entrance",
      url:"rtsp://192.168.1.10/stream"
    },
    {
      name:"Cash Counter",
      url:"rtsp://192.168.1.11/stream"
    },
    {
      name:"Storage Room",
      url:"rtsp://192.168.1.12/stream"
    }
  ])

  const addCamera = () => {

    if(!name || !url) return

    setCameras([
      ...cameras,
      {name,url}
    ])

    setName("")
    setUrl("")
  }

  return(

    <main className="min-h-screen bg-[#080c0e] text-white">

      <GridBackground/>
      <Navbar/>

      <div className="max-w-6xl mx-auto pt-32 px-6">

        <h1 className="text-xl font-bold mb-10">
          CAMERA MANAGEMENT
        </h1>

        <div className="grid md:grid-cols-[1fr_420px] gap-8">

          {/* CAMERA LIST */}

          <div className="bg-white/5 border border-white/10 rounded-xl p-6">

            <h2 className="text-sm text-gray-400 mb-5 tracking-widest">
              CONNECTED CAMERAS
            </h2>

            <div className="space-y-3">

              {cameras.map((cam,i)=>{

                const active = activeCamera === cam.name

                return(

                  <div
                    key={i}
                    onClick={()=>setActiveCamera(cam.name)}
                    className={`cursor-pointer flex justify-between items-center p-3 rounded-lg border transition
                      ${
                        active
                        ? "border-green-400 bg-green-400/10"
                        : "border-white/10 hover:border-white/30"
                      }
                    `}
                  >

                    <div>

                      <p className="font-semibold">
                        {cam.name}
                      </p>

                      <p className="text-xs text-gray-500">
                        {cam.url}
                      </p>

                    </div>

                    {active && (
                      <span className="text-green-400 text-xs font-semibold">
                        ACTIVE
                      </span>
                    )}

                  </div>

                )

              })}

            </div>

          </div>

          {/* ADD CAMERA FORM */}

          <div className="bg-white/5 border border-white/10 rounded-xl p-6 space-y-4">

            <h2 className="text-sm text-gray-400 tracking-widest">
              ADD NEW CAMERA
            </h2>

            <input
              placeholder="Camera Name"
              value={name}
              onChange={(e)=>setName(e.target.value)}
              className="w-full p-2 bg-black border border-white/10 rounded"
            />

            <input
              placeholder="RTSP / Camera URL"
              value={url}
              onChange={(e)=>setUrl(e.target.value)}
              className="w-full p-2 bg-black border border-white/10 rounded"
            />

            <button
              onClick={addCamera}
              className="w-full bg-green-500/20 border border-green-500 text-green-400 py-2 rounded-lg hover:bg-green-500/30 transition"
            >
              Add Camera
            </button>

          </div>

        </div>

      </div>

    </main>

  )
}