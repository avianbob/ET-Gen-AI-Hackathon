import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Dna } from 'lucide-react';

const AuthLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-100/90 via-slate-50 to-slate-100/80 flex items-center justify-center p-4 relative overflow-hidden text-slate-800">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 -left-32 w-96 h-96 bg-cyan-400/15 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-teal-400/12 rounded-full blur-3xl" />
        <div
          className="absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage: `
              linear-gradient(rgba(6, 182, 212, 0.5) 1px, transparent 1px),
              linear-gradient(90deg, rgba(6, 182, 212, 0.5) 1px, transparent 1px)
            `,
            backgroundSize: '40px 40px',
          }}
        />
      </div>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }} className="relative w-full max-w-md">
        <Link to="/" className="flex items-center justify-center gap-3 mb-8">
          <div className="w-12 h-12 bg-gradient-to-br from-cyan-500 to-teal-600 rounded-2xl flex items-center justify-center shadow-lg shadow-cyan-500/30">
            <Dna className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Pharm<span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-600 to-teal-600">AI</span></h1>
            <p className="text-xs text-slate-500">Drug Intelligence Platform</p>
          </div>
        </Link>
        <div className="bg-white/90 backdrop-blur-md border border-slate-200/90 rounded-2xl p-8 shadow-xl shadow-slate-200/50">
          <Outlet />
        </div>
        <p className="text-center text-sm text-slate-500 mt-6">&copy; {new Date().getFullYear()} PharmAI. All rights reserved.</p>
      </motion.div>
    </div>
  );
};

export default AuthLayout;
