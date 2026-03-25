'use client'

import { useState, useCallback } from 'react'

function throttle(func, delay) {
  let lastCall = 0
  return (...args) => {
    const now = new Date().getTime()
    if (now - lastCall < delay) {
      return
    }
    lastCall = now
    return func(...args)
  }
}

export default function CardTilt({ icon, number, title, description }) {
  const [rotate, setRotate] = useState({ x: 0, y: 0 })

  const onMouseMove = useCallback(
    throttle((e) => {
      const card = e.currentTarget
      const box = card.getBoundingClientRect()
      const x = e.clientX - box.left
      const y = e.clientY - box.top
      const centerX = box.width / 2
      const centerY = box.height / 2
      const rotateX = (y - centerY) / 5
      const rotateY = (centerX - x) / 5

      setRotate({ x: rotateX, y: rotateY })
    }, 50),
    []
  )

  const onMouseLeave = () => {
    setRotate({ x: 0, y: 0 })
  }

  return (
    <div
      className='relative h-full transition-all duration-300 will-change-transform'
      onMouseMove={onMouseMove}
      onMouseLeave={onMouseLeave}
      style={{
        transform: `perspective(1200px) rotateX(${rotate.x}deg) rotateY(${rotate.y}deg) scale3d(1, 1, 1)`,
        transition: 'all 300ms cubic-bezier(0.23, 1, 0.32, 1)',
      }}
    >
      {/* Card Body */}
      <div className='relative h-full min-h-56 sm:min-h-64 md:min-h-72 rounded-lg sm:rounded-xl border border-green-500/20 bg-gradient-to-b from-gray-900/40 to-black/80 p-6 sm:p-8 md:p-10 md:p-12 backdrop-blur-sm overflow-hidden flex flex-col justify-between'>
        
        {/* Background gradient on hover */}
        <div className='absolute inset-0 bg-gradient-to-br from-green-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none rounded-xl'></div>

        {/* Top accent line */}
        <div className='absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-green-500/40 to-transparent'></div>

        <div className='relative z-10'>
          
          {/* Number Badge */}
          <div className='inline-flex items-center justify-center w-12 h-12 sm:w-13 sm:h-13 md:w-14 md:h-14 rounded-lg border border-green-500/40 bg-green-500/10 text-xs sm:text-sm md:text-base font-bold text-green-400 mb-4 sm:mb-6 md:mb-8'>
            {number}
          </div>

          {/* Title */}
          <h3 className='text-xl sm:text-2xl md:text-3xl font-bold text-white mb-2 sm:mb-3 md:mb-4'>
            {title}
          </h3>

          {/* Description */}
          <p className='text-gray-400 leading-relaxed text-xs sm:text-sm md:text-base'>
            {description}
          </p>

          {/* Bottom accent */}
          <div className='absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-green-500/20 to-transparent'></div>
        </div>
      </div>
    </div>
  )
}
