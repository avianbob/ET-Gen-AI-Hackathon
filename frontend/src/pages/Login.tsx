import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, Lock, User, Eye, EyeOff, ArrowRight } from 'lucide-react';
import { useAppStore } from '../store';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { setUser } = useAppStore();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email.trim() || !password.trim()) {
      setError('Please fill in all required fields.');
      return;
    }

    if (isRegister && !fullName.trim()) {
      setError('Please enter your full name.');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }

    setLoading(true);
    try {
      await new Promise((r) => setTimeout(r, 800));
      setUser({
        id: crypto.randomUUID?.() || Date.now().toString(),
        email,
        username: isRegister ? fullName : email.split('@')[0],
        full_name: isRegister ? fullName : email.split('@')[0],
        name: isRegister ? fullName : email.split('@')[0],
        role: 'user',
      });
      navigate('/dashboard');
    } catch {
      setError('Authentication failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGuest = () => {
    setUser({
      id: 'guest',
      email: 'guest@pharmai.local',
      username: 'Guest',
      full_name: 'Guest User',
      name: 'Guest User',
      role: 'guest',
    });
    navigate('/dashboard');
  };

  const inputClass =
    'w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-cyan-500/60 focus:ring-2 focus:ring-cyan-500/15 transition-colors';

  return (
    <motion.div
      key={isRegister ? 'register' : 'login'}
      initial={{ opacity: 0, x: isRegister ? 20 : -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.25 }}
    >
      <h2 className="text-xl font-bold text-slate-900 mb-1">
        {isRegister ? 'Create Account' : 'Welcome Back'}
      </h2>
      <p className="text-sm text-slate-600 mb-6">
        {isRegister ? 'Sign up to get started with PharmAI' : 'Sign in to continue to PharmAI'}
      </p>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 p-3 rounded-xl bg-red-50 border border-red-200 text-sm text-red-700"
        >
          {error}
        </motion.div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {isRegister && (
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1.5">Full Name</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="John Doe"
                className={inputClass}
              />
            </div>
          </div>
        )}

        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1.5">Email Address</label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              className={inputClass}
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1.5">Password</label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full pl-10 pr-10 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-cyan-500/60 focus:ring-2 focus:ring-cyan-500/15 transition-colors"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 py-3 bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-500 hover:to-teal-500 text-white font-semibold rounded-xl shadow-md shadow-cyan-500/25 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : (
            <>
              {isRegister ? 'Create Account' : 'Sign In'}
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </form>

      <div className="flex items-center gap-3 my-6">
        <div className="flex-1 h-px bg-slate-200" />
        <span className="text-xs text-slate-400">or</span>
        <div className="flex-1 h-px bg-slate-200" />
      </div>

      <button
        type="button"
        onClick={handleGuest}
        className="w-full py-2.5 border border-slate-200 hover:border-cyan-300 text-slate-700 hover:text-slate-900 font-medium text-sm rounded-xl transition-all duration-200 hover:bg-slate-50"
      >
        Continue as Guest
      </button>

      <p className="text-center text-sm text-slate-500 mt-6">
        {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
        <button
          type="button"
          onClick={() => { setIsRegister(!isRegister); setError(null); }}
          className="text-cyan-600 hover:text-teal-600 font-medium transition-colors"
        >
          {isRegister ? 'Sign In' : 'Register'}
        </button>
      </p>
    </motion.div>
  );
};

export default Login;
