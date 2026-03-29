import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

export const Home: React.FC = () => {
  const navigate = useNavigate();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 50);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="min-h-screen overflow-hidden bg-gradient-to-b from-slate-100/90 via-slate-50 to-slate-100/80 font-sans text-slate-800 relative">
      {/* Ambient background: gradients, molecules, line animations, particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Liquid gradient orbs */}
        <div className="absolute top-1/4 -left-32 w-96 h-96 bg-cyan-400/20 rounded-full blur-3xl animate-float-slow" />
        <div className="absolute bottom-1/4 -right-32 w-[500px] h-[500px] bg-teal-400/15 rounded-full blur-3xl animate-float-slow-delayed" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-cyan-300/10 rounded-full blur-3xl animate-pulse-slow" />

        {/* Thin line grid */}
        <div
          className="absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage: `
              linear-gradient(rgba(6, 182, 212, 0.6) 1px, transparent 1px),
              linear-gradient(90deg, rgba(6, 182, 212, 0.6) 1px, transparent 1px)
            `,
            backgroundSize: '40px 40px',
          }}
        />

        {/* Benzene ring molecule (hexagon) - line draw animation */}
        <div className="absolute left-[8%] top-[20%] w-24 h-24 opacity-[0.15] hidden md:block animate-molecule-float" style={{ animationDelay: '0s' }}>
          <svg viewBox="0 0 80 80" fill="none" stroke="#06b6d4" strokeWidth="0.8">
            <polygon points="40,8 68,28 68,62 40,82 12,62 12,28" strokeDasharray="240" strokeDashoffset="240" style={{ animation: 'drawLine 6s ease-in-out infinite' }} />
          </svg>
        </div>

        {/* Paracetamol molecule - benzene + OH + acetamide (hexagon-style) */}
        <div className="absolute left-[18%] top-[35%] w-28 h-28 opacity-[0.14] hidden md:block animate-molecule-float" style={{ animationDelay: '1s' }}>
          <svg viewBox="0 0 80 90" fill="none" stroke="#06b6d4" strokeWidth="0.7">
            <defs>
              <linearGradient id="paraGrad" x1="0" y1="0" x2="1" y2="1">
                <stop stopColor="#06b6d4" />
                <stop offset="1" stopColor="#14b8a6" />
              </linearGradient>
            </defs>
            <polygon points="40,15 65,32 65,58 40,75 15,58 15,32" stroke="url(#paraGrad)" strokeDasharray="220" strokeDashoffset="220" style={{ animation: 'drawLine 6s ease-in-out infinite' }} />
            <path d="M40 15 L40 5" stroke="url(#paraGrad)" strokeWidth="0.6" strokeDasharray="12" strokeDashoffset="12" style={{ animation: 'drawLine 4s ease-in-out 0.5s infinite' }} />
            <circle cx="40" cy="4" r="2.5" fill="#14b8a6" opacity="0.6" />
            <path d="M40 75 L40 82 L48 88 L48 90" stroke="url(#paraGrad)" strokeWidth="0.6" strokeDasharray="30" strokeDashoffset="30" style={{ animation: 'drawLine 5s ease-in-out 1s infinite' }} />
            <circle cx="40" cy="82" r="1.5" fill="#06b6d4" opacity="0.5" />
            <circle cx="48" cy="88" r="2" fill="#14b8a6" opacity="0.5" />
          </svg>
        </div>

        {/* Metformin molecule - biguanide (CH3)2N-C-N-C-N chain, hexagon-style */}
        <div className="absolute right-[15%] top-[38%] w-32 h-20 opacity-[0.13] hidden lg:block animate-molecule-float" style={{ animationDelay: '2s' }}>
          <svg viewBox="0 0 110 45" fill="none" stroke="#14b8a6" strokeWidth="0.6">
            <defs>
              <linearGradient id="metGrad" x1="0" y1="0" x2="1" y2="0">
                <stop stopColor="#06b6d4" />
                <stop offset="1" stopColor="#14b8a6" />
              </linearGradient>
            </defs>
            <path d="M10 22 L28 22 M28 22 L46 22 M46 22 L64 22 M64 22 L82 22 M82 22 L100 22" stroke="url(#metGrad)" strokeDasharray="110" strokeDashoffset="110" style={{ animation: 'drawLine 7s ease-in-out infinite' }} />
            <path d="M10 22 L10 8 M6 8 L14 8" stroke="url(#metGrad)" strokeWidth="0.5" strokeDasharray="18" strokeDashoffset="18" style={{ animation: 'drawLine 4s ease-in-out 0.5s infinite' }} />
            <path d="M46 22 L46 38 M42 38 L50 38" stroke="url(#metGrad)" strokeWidth="0.5" strokeDasharray="20" strokeDashoffset="20" style={{ animation: 'drawLine 4s ease-in-out 0.9s infinite' }} />
            <path d="M64 22 L64 38 M60 38 L68 38" stroke="url(#metGrad)" strokeWidth="0.5" strokeDasharray="20" strokeDashoffset="20" style={{ animation: 'drawLine 4s ease-in-out 1.1s infinite' }} />
            <circle cx="10" cy="22" r="3" fill="#06b6d4" opacity="0.5" />
            <circle cx="28" cy="22" r="2.5" fill="#06b6d4" opacity="0.5" />
            <circle cx="46" cy="22" r="2.5" fill="#06b6d4" opacity="0.5" />
            <circle cx="64" cy="22" r="2.5" fill="#14b8a6" opacity="0.5" />
            <circle cx="82" cy="22" r="2.5" fill="#14b8a6" opacity="0.5" />
            <circle cx="100" cy="22" r="3" fill="#14b8a6" opacity="0.5" />
          </svg>
        </div>

        {/* Carbon chain / molecular bonds - thin line aesthetic */}
        <div className="absolute right-[12%] top-[25%] w-32 h-16 opacity-[0.12] hidden lg:block animate-molecule-float" style={{ animationDelay: '2s' }}>
          <svg viewBox="0 0 120 60" fill="none" stroke="#14b8a6" strokeWidth="0.6">
            <path d="M10 30 L35 30 M35 30 L60 30 M60 30 L85 30 M85 30 L110 30" strokeDasharray="80" strokeDashoffset="80" style={{ animation: 'drawLine 8s ease-in-out infinite' }} />
            <circle cx="10" cy="30" r="3" fill="#06b6d4" opacity="0.5" />
            <circle cx="35" cy="30" r="3" fill="#06b6d4" opacity="0.5" />
            <circle cx="60" cy="30" r="3" fill="#06b6d4" opacity="0.5" />
            <circle cx="85" cy="30" r="3" fill="#06b6d4" opacity="0.5" />
            <circle cx="110" cy="30" r="3" fill="#06b6d4" opacity="0.5" />
          </svg>
        </div>

        {/* DNA double helix - subtle, large */}
        <div className="absolute right-4 top-1/2 -translate-y-1/2 w-48 h-48 opacity-[0.08] hidden lg:block animate-spin-slow">
          <svg viewBox="0 0 100 100" fill="none">
            <defs>
              <linearGradient id="dnaGrad" x1="0" y1="0" x2="1" y2="1">
                <stop stopColor="#06b6d4" />
                <stop offset="1" stopColor="#14b8a6" />
              </linearGradient>
            </defs>
            <path d="M50 10 Q70 25 50 40 Q30 25 50 10" stroke="url(#dnaGrad)" strokeWidth="0.8" fill="none" strokeDasharray="60" strokeDashoffset="60" style={{ animation: 'drawLine 5s ease-in-out infinite' }} />
            <path d="M50 60 Q70 75 50 90 Q30 75 50 60" stroke="url(#dnaGrad)" strokeWidth="0.8" fill="none" strokeDasharray="60" strokeDashoffset="60" style={{ animation: 'drawLine 5s ease-in-out 0.5s infinite' }} />
            <line x1="50" y1="25" x2="50" y2="75" stroke="url(#dnaGrad)" strokeWidth="0.5" opacity="0.5" />
          </svg>
        </div>

        {/* Pill/capsule shape - pharma themed */}
        <div className="absolute left-[15%] bottom-[30%] w-16 h-8 opacity-[0.1] hidden lg:block animate-molecule-float" style={{ animationDelay: '1.5s' }}>
          <svg viewBox="0 0 60 30">
            <rect x="5" y="5" width="50" height="20" rx="10" fill="none" stroke="#06b6d4" strokeWidth="0.8" strokeDasharray="100" strokeDashoffset="100" style={{ animation: 'drawLine 7s ease-in-out infinite' }} />
          </svg>
        </div>

        {/* Abstract molecular structure - hexagonal network */}
        <div className="absolute right-[20%] bottom-[25%] w-28 h-28 opacity-[0.1] hidden xl:block animate-molecule-float" style={{ animationDelay: '3s' }}>
          <svg viewBox="0 0 80 80" fill="none" stroke="#14b8a6" strokeWidth="0.5">
            <path d="M40 10 L60 25 L60 55 L40 70 L20 55 L20 25 Z M40 10 L40 70 M20 25 L60 55 M20 55 L60 25" strokeDasharray="300" strokeDashoffset="300" style={{ animation: 'drawLine 10s ease-in-out infinite' }} />
          </svg>
        </div>

        {/* Second benzene ring - smaller, different position */}
        <div className="absolute left-[25%] top-[12%] w-16 h-16 opacity-[0.12] hidden lg:block animate-float-diagonal">
          <svg viewBox="0 0 60 60" fill="none" stroke="#14b8a6" strokeWidth="0.6">
            <polygon points="30,5 52,17 52,43 30,55 8,43 8,17" strokeDasharray="180" strokeDashoffset="180" style={{ animation: 'drawLine 5s ease-in-out 1s infinite' }} />
          </svg>
        </div>

        {/* Pyridine-like ring (hexagon with different bond) */}
        <div className="absolute right-[30%] top-[15%] w-20 h-20 opacity-[0.1] hidden xl:block animate-drift-slow">
          <svg viewBox="0 0 60 60" fill="none" stroke="#06b6d4" strokeWidth="0.6">
            <path d="M30 8 L50 20 L50 40 L30 52 L10 40 L10 20 Z" strokeDasharray="200" strokeDashoffset="200" style={{ animation: 'drawLine 7s ease-in-out 0.5s infinite' }} />
            <circle cx="30" cy="30" r="2" fill="#14b8a6" opacity="0.6" />
          </svg>
        </div>

        {/* Amino acid backbone (simplified - zigzag) */}
        <div className="absolute left-[5%] bottom-[20%] w-20 h-14 opacity-[0.11] hidden md:block animate-float-up-down">
          <svg viewBox="0 0 80 50" fill="none" stroke="#06b6d4" strokeWidth="0.5">
            <path d="M5 25 L25 10 L45 25 L65 10 L75 25" strokeDasharray="120" strokeDashoffset="120" style={{ animation: 'drawLine 6s ease-in-out 2s infinite' }} />
            <circle cx="5" cy="25" r="2" fill="#14b8a6" opacity="0.4" />
            <circle cx="25" cy="10" r="2" fill="#14b8a6" opacity="0.4" />
            <circle cx="45" cy="25" r="2" fill="#14b8a6" opacity="0.4" />
            <circle cx="65" cy="10" r="2" fill="#14b8a6" opacity="0.4" />
            <circle cx="75" cy="25" r="2" fill="#14b8a6" opacity="0.4" />
          </svg>
        </div>

        {/* Glucose/pyranose ring (6-membered sugar) */}
        <div className="absolute right-[5%] bottom-[35%] w-20 h-20 opacity-[0.09] hidden xl:block animate-scale-pulse">
          <svg viewBox="0 0 70 70" fill="none" stroke="#14b8a6" strokeWidth="0.6">
            <path d="M35 5 L55 17 L55 42 L35 65 L15 42 L15 17 Z" strokeDasharray="220" strokeDashoffset="220" style={{ animation: 'drawLine 8s ease-in-out 3s infinite' }} />
          </svg>
        </div>

        {/* Double bond structure (ethene-like) */}
        <div className="absolute left-[35%] top-[8%] w-14 h-10 opacity-[0.13] hidden lg:block animate-molecule-float" style={{ animationDelay: '2.5s' }}>
          <svg viewBox="0 0 50 35" fill="none" stroke="#06b6d4" strokeWidth="0.7">
            <line x1="8" y1="17" x2="42" y2="17" strokeDasharray="40" strokeDashoffset="40" style={{ animation: 'drawLine 4s ease-in-out infinite' }} />
            <line x1="8" y1="22" x2="42" y2="22" strokeDasharray="40" strokeDashoffset="40" style={{ animation: 'drawLine 4s ease-in-out 0.2s infinite' }} />
            <circle cx="10" cy="20" r="3" fill="#06b6d4" opacity="0.4" />
            <circle cx="40" cy="20" r="3" fill="#06b6d4" opacity="0.4" />
          </svg>
        </div>

        {/* Triple bond (ethyne-like) */}
        <div className="absolute right-[35%] bottom-[15%] w-12 h-8 opacity-[0.1] hidden xl:block animate-float-up-down" style={{ animationDelay: '1s' }}>
          <svg viewBox="0 0 45 25" fill="none" stroke="#14b8a6" strokeWidth="0.5">
            <line x1="5" y1="12" x2="40" y2="12" strokeDasharray="35" strokeDashoffset="35" style={{ animation: 'drawLine 3.5s ease-in-out infinite' }} />
            <line x1="5" y1="8" x2="40" y2="8" strokeDasharray="35" strokeDashoffset="35" style={{ animation: 'drawLine 3.5s ease-in-out 0.15s infinite' }} />
            <line x1="5" y1="16" x2="40" y2="16" strokeDasharray="35" strokeDashoffset="35" style={{ animation: 'drawLine 3.5s ease-in-out 0.3s infinite' }} />
            <circle cx="7" cy="12" r="2" fill="#14b8a6" opacity="0.35" />
            <circle cx="38" cy="12" r="2" fill="#14b8a6" opacity="0.35" />
          </svg>
        </div>

        {/* Second pill - different size */}
        <div className="absolute right-[25%] top-[70%] w-12 h-6 opacity-[0.08] hidden xl:block animate-drift-slow" style={{ animationDelay: '2s' }}>
          <svg viewBox="0 0 48 24">
            <rect x="4" y="4" width="40" height="16" rx="8" fill="none" stroke="#14b8a6" strokeWidth="0.6" strokeDasharray="80" strokeDashoffset="80" style={{ animation: 'drawLine 6s ease-in-out 1s infinite' }} />
          </svg>
        </div>

        {/* Concentric molecular orbital circles */}
        <div className="absolute left-[12%] top-[55%] w-20 h-20 opacity-[0.07] hidden lg:block animate-spin-slow-reverse">
          <svg viewBox="0 0 60 60" fill="none" stroke="#06b6d4" strokeWidth="0.4">
            <circle cx="30" cy="30" r="25" strokeDasharray="8 4" strokeDashoffset="100" style={{ animation: 'drawLine 12s ease-in-out infinite' }} />
            <circle cx="30" cy="30" r="18" strokeDasharray="6 3" strokeDashoffset="80" style={{ animation: 'drawLine 10s ease-in-out 1s infinite' }} />
            <circle cx="30" cy="30" r="10" strokeDasharray="4 2" strokeDashoffset="50" style={{ animation: 'drawLine 6s ease-in-out 2s infinite' }} />
          </svg>
        </div>

        {/* Benzene + side chain (simplified aspirin-like) */}
        <div className="absolute right-[8%] top-[40%] w-24 h-20 opacity-[0.09] hidden xl:block animate-molecule-float" style={{ animationDelay: '4s' }}>
          <svg viewBox="0 0 70 55" fill="none" stroke="#06b6d4" strokeWidth="0.5">
            <polygon points="35,5 55,17 55,40 35,52 15,40 15,17" strokeDasharray="150" strokeDashoffset="150" style={{ animation: 'drawLine 7s ease-in-out infinite' }} />
            <path d="M55 28 L75 28" strokeDasharray="25" strokeDashoffset="25" style={{ animation: 'drawLine 4s ease-in-out 1.5s infinite' }} />
            <circle cx="75" cy="28" r="3" fill="#14b8a6" opacity="0.4" />
          </svg>
        </div>

        {/* Flask/beaker icon - pharma lab */}
        <div className="absolute left-[40%] bottom-[18%] w-14 h-18 opacity-[0.08] hidden xl:block animate-float-up-down" style={{ animationDelay: '2s' }}>
          <svg viewBox="0 0 40 55" fill="none" stroke="#14b8a6" strokeWidth="0.6">
            <path d="M8 5 L8 35 Q8 48 20 48 Q32 48 32 35 L32 5 M12 5 L28 5" strokeDasharray="120" strokeDashoffset="120" style={{ animation: 'drawLine 5s ease-in-out infinite' }} />
          </svg>
        </div>

        {/* Floating particles - particle network */}
        <div className="absolute inset-0">
          {[
            { x: 15, y: 35 }, { x: 28, y: 22 }, { x: 42, y: 38 }, { x: 55, y: 18 }, { x: 72, y: 32 },
            { x: 20, y: 65 }, { x: 38, y: 72 }, { x: 58, y: 68 }, { x: 75, y: 55 }, { x: 85, y: 70 },
            { x: 8, y: 45 }, { x: 92, y: 25 }, { x: 50, y: 85 }, { x: 35, y: 12 }, { x: 65, y: 78 },
          ].map((pos, i) => (
            <div
              key={i}
              className="absolute w-1.5 h-1.5 rounded-full bg-cyan-400/40 animate-particle-drift"
              style={{
                left: `${pos.x}%`,
                top: `${pos.y}%`,
                animationDelay: `${i * 0.5}s`,
                animationDuration: `${10 + (i % 5)}s`,
              }}
            />
          ))}
        </div>

        {/* Extra subtle particles - smaller, more numerous */}
        {[...Array(28)].map((_, i) => (
          <div
            key={`p${i}`}
            className="absolute rounded-full bg-teal-400/25 animate-particle-float"
            style={{
              width: i % 3 === 0 ? 2 : 1,
              height: i % 3 === 0 ? 2 : 1,
              left: `${3 + (i * 3.4) % 94}%`,
              top: `${5 + (i * 4.2) % 88}%`,
              animationDelay: `${i * 0.25}s`,
              animationDuration: `${4 + (i % 5)}s`,
            }}
          />
        ))}

        {/* Micro dots - tiny accent particles */}
        {[...Array(15)].map((_, i) => (
          <div
            key={`d${i}`}
            className="absolute w-0.5 h-0.5 rounded-full bg-cyan-500/30 animate-float-diagonal"
            style={{
              left: `${10 + (i * 6) % 85}%`,
              top: `${15 + (i * 5) % 75}%`,
              animationDelay: `${i * 0.4}s`,
              animationDuration: `${7 + (i % 3)}s`,
            }}
          />
        ))}

        {/* Thin flowing lines - wavy liquid aesthetic */}
        <svg className="absolute inset-0 w-full h-full opacity-[0.06]" preserveAspectRatio="none">
          <defs>
            <linearGradient id="flowGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#06b6d4" />
              <stop offset="100%" stopColor="#14b8a6" />
            </linearGradient>
          </defs>
          <path d="M0,30 Q200,20 400,30 T800,30 T1200,30 T1600,30" fill="none" stroke="url(#flowGrad)" strokeWidth="0.5" strokeDasharray="200" strokeDashoffset="200" style={{ animation: 'drawLine 15s ease-in-out infinite' }} />
          <path d="M0,70 Q200,80 400,70 T800,70 T1200,70 T1600,70" fill="none" stroke="url(#flowGrad)" strokeWidth="0.5" strokeDasharray="200" strokeDashoffset="200" style={{ animation: 'drawLine 15s ease-in-out 2s infinite' }} />
          <path d="M0,90 Q300,80 600,90 T1200,90 T1800,90" fill="none" stroke="url(#flowGrad)" strokeWidth="0.5" strokeDasharray="250" strokeDashoffset="250" style={{ animation: 'drawLine 18s ease-in-out 4s infinite' }} />
        </svg>

        {/* Additional wavy lines - diagonal and vertical flow */}
        <svg className="absolute inset-0 w-full h-full opacity-[0.04]" viewBox="0 0 800 100" preserveAspectRatio="none">
          <defs>
            <linearGradient id="flowGrad2" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#06b6d4" />
              <stop offset="100%" stopColor="#14b8a6" />
            </linearGradient>
          </defs>
          <path d="M0,15 Q100,5 200,15 T400,15 T600,15 T800,15" fill="none" stroke="url(#flowGrad2)" strokeWidth="0.4" strokeDasharray="180" strokeDashoffset="180" style={{ animation: 'drawLine 12s ease-in-out 1s infinite' }} />
          <path d="M0,85 Q150,95 300,85 T600,85 T800,85" fill="none" stroke="url(#flowGrad2)" strokeWidth="0.4" strokeDasharray="200" strokeDashoffset="200" style={{ animation: 'drawLine 14s ease-in-out 3s infinite' }} />
        </svg>
      </div>

      {/* Content */}
      <div className="relative z-10 flex flex-col min-h-screen items-center justify-center px-6 py-16">
        {/* Logo */}
        <div
          className={`flex items-center gap-3 mb-12 transition-all duration-1000 ${
            mounted ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-8'
          }`}
        >
          <div className="w-14 h-14 flex items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-500 to-teal-600 shadow-lg shadow-cyan-500/30">
            <i className="fas fa-dna text-white text-2xl" />
          </div>
          <span className="font-extrabold text-2xl md:text-3xl tracking-tight text-slate-800">PharmAI</span>
         
        </div>

        {/* Hero section */}
        <div
          className={`text-center max-w-4xl mx-auto transition-all duration-1000 delay-150 ${
            mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-black text-slate-900 tracking-tight leading-[1.1] mb-6">
            Explore the future of {' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-600 via-teal-500 to-cyan-600 bg-[length:200%_auto] animate-gradient-shift">
              Pharma
            </span>
            {' '}With PharmAI
          </h1>
          <p className="text-lg md:text-xl text-slate-600 max-w-2xl mx-auto mb-14 font-medium leading-relaxed">
            AI-powered pharmaceutical intelligence for market analysis, patent landscape, and manufacturing feasibility.
          </p>

          {/* CTA buttons */}
          <div className={`flex flex-wrap justify-center gap-4 transition-all duration-1000 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`} style={{ transitionDelay: '400ms' }}>
            <button
              type="button"
              onClick={() => navigate('/chat')}
              className="group relative inline-flex items-center gap-3 px-10 py-4 rounded-2xl font-bold text-white text-lg bg-gradient-to-r from-cyan-600 to-teal-600 shadow-lg shadow-cyan-500/35 hover:shadow-xl hover:shadow-cyan-500/45 hover:scale-105 active:scale-[0.98] transition-all duration-300 overflow-hidden"
            >
              <span className="relative z-10">AI Assistant</span>
              <i className="fas fa-comment-dots text-lg relative z-10 group-hover:translate-x-1 transition-transform" />
              <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
            </button>
            <button
              type="button"
              onClick={() => navigate('/search')}
              className="group relative inline-flex items-center gap-3 px-8 py-4 rounded-2xl font-bold text-slate-700 text-lg bg-white/80 border border-slate-200 shadow-md hover:shadow-lg hover:scale-105 active:scale-[0.98] transition-all duration-300"
            >
              <span>Drug Search</span>
              <i className="fas fa-search text-lg group-hover:translate-x-1 transition-transform" />
            </button>
            <button
              type="button"
              onClick={() => navigate('/dashboard')}
              className="group relative inline-flex items-center gap-3 px-8 py-4 rounded-2xl font-bold text-slate-700 text-lg bg-white/80 border border-slate-200 shadow-md hover:shadow-lg hover:scale-105 active:scale-[0.98] transition-all duration-300"
            >
              <span>Dashboard</span>
              <i className="fas fa-arrow-right text-lg group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>

        {/* Bottom decorative pill / features hint */}
        <div
          className={`mt-20 flex flex-wrap justify-center gap-4 text-sm text-slate-500 transition-all duration-1000 delay-500 ${
            mounted ? 'opacity-100' : 'opacity-0'
          }`}
        >
          <span className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 border border-slate-200/80 shadow-sm backdrop-blur-sm">
            <i className="fas fa-robot text-cyan-500" />
            AI Chat Assistant
          </span>
          <span className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 border border-slate-200/80 shadow-sm backdrop-blur-sm">
            <i className="fas fa-search text-teal-500" />
            Unified drug search report
          </span>
          <span className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 border border-slate-200/80 shadow-sm backdrop-blur-sm">
            <i className="fas fa-chart-line text-cyan-500" />
            4D Composite Scoring
          </span>
          <span className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 border border-slate-200/80 shadow-sm backdrop-blur-sm">
            <i className="fas fa-flask text-teal-500" />
            Process Design & TEA
          </span>
          <span className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 border border-slate-200/80 shadow-sm backdrop-blur-sm">
            <i className="fas fa-file-contract text-cyan-600" />
            Drug Comparison
          </span>
        </div>
      </div>
    </div>
  );
};
