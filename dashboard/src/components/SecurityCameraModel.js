"use client"

import { Canvas, useFrame } from "@react-three/fiber"
import { OrbitControls, useGLTF } from "@react-three/drei"
import { useRef, useEffect } from "react"
import * as THREE from "three"

function CameraModel() {
  const { scene } = useGLTF("/models/surveillance_cam/scene.gltf")
  const groupRef = useRef()

  useEffect(() => {
    const textureLoader = new THREE.TextureLoader()

    const diffuse = textureLoader.load(
      "/models/surveillance_cam/textures/standard_varnish_diffuse.png"
    )

    diffuse.colorSpace = THREE.SRGBColorSpace
    diffuse.flipY = false

    scene.traverse((child) => {
      if (child.isMesh) {
        const normal = child.material.normalMap
        const ao = child.material.aoMap

        child.material = new THREE.MeshStandardMaterial({
          map: diffuse,
          normalMap: normal || null,
          aoMap: ao || null,
          metalness: 0.6,
          roughness: 0.4,
          envMapIntensity: 0,   // no env map needed
        })

        child.castShadow = true
        child.receiveShadow = true
      }
    })
  }, [scene])

  useFrame(() => {
    if (groupRef.current) {
      groupRef.current.rotation.y = Math.sin(Date.now() * 0.001) * 0.4
    }
  })

  return (
    <group ref={groupRef}>
      <primitive
        object={scene}
        scale={2.5}
        position={[0, 1, 0]}
        rotation={[-0.35, Math.PI, 0]}
      />
    </group>
  )
}

export default function SecurityCameraModel() {
  return (
    <div className="w-full h-screen">
      <Canvas camera={{ position: [3, 3, 7], fov: 45 }}>

        {/* ambient */}
        <ambientLight intensity={0.8} />

        {/* main spotlight */}
        <spotLight
          position={[5, 8, 5]}
          intensity={2.5}
          angle={0.35}
          penumbra={1}
          castShadow
        />

        {/* fill light */}
        <directionalLight
          position={[-5, 5, -5]}
          intensity={0.8}
        />

        {/* rim light for depth */}
        <pointLight position={[0, -3, 3]} intensity={0.4} color="#4ade80" />

        <CameraModel />

        <OrbitControls enableZoom={false} />

      </Canvas>
    </div>
  )
}

useGLTF.preload("/models/surveillance_cam/scene.gltf")