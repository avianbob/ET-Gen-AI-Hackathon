import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, MessageSquare, Search, Bookmark, ArrowRight } from 'lucide-react';

const steps = [
  { title: 'Welcome to PharmAI', description: 'Your AI-powered drug intelligence platform. Let us show you around.', icon: <MessageSquare className="w-8 h-8 text-cyan-600" /> },
  { title: 'AI Assistant', description: 'Chat with our AI to get instant insights about drug repurposing opportunities.', icon: <MessageSquare className="w-8 h-8 text-teal-600" /> },
  { title: 'Drug Search', description: 'Search for any drug to discover repurposing opportunities scored across 4 dimensions.', icon: <Search className="w-8 h-8 text-cyan-600" /> },
  { title: 'Save & Compare', description: 'Bookmark opportunities and compare drugs side-by-side.', icon: <Bookmark className="w-8 h-8 text-teal-600" /> },
];

const OnboardingTour: React.FC = () => {
  const [show, setShow] = useState(false);
  const [step, setStep] = useState(0);

  useEffect(() => {
    const seen = localStorage.getItem('pharmai-onboarding-complete');
    if (!seen) setShow(true);
  }, []);

  const finish = () => {
    setShow(false);
    localStorage.setItem('pharmai-onboarding-complete', 'true');
  };

  return (
    <AnimatePresence>
      {show && (
        <>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-[60]" />
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-white border border-slate-200 rounded-2xl shadow-xl shadow-slate-300/50 z-[60] p-8"
          >
            <button onClick={finish} className="absolute top-4 right-4 text-slate-400 hover:text-slate-700"><X className="w-5 h-5" /></button>
            <div className="text-center">
              <div className="mb-4 flex justify-center">{steps[step].icon}</div>
              <h2 className="text-xl font-bold text-slate-900 mb-2">{steps[step].title}</h2>
              <p className="text-slate-600 mb-8">{steps[step].description}</p>
              <div className="flex items-center justify-center gap-2 mb-6">
                {steps.map((_, i) => (
                  <div key={i} className={`w-2 h-2 rounded-full transition-colors ${i === step ? 'bg-gradient-to-r from-cyan-500 to-teal-600' : 'bg-slate-200'}`} />
                ))}
              </div>
              <div className="flex gap-3 justify-center">
                {step > 0 && (
                  <button onClick={() => setStep(step - 1)} className="px-4 py-2 text-sm text-slate-600 hover:text-slate-900 transition-colors">Back</button>
                )}
                {step < steps.length - 1 ? (
                  <button onClick={() => setStep(step + 1)} className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-cyan-600 to-teal-600 text-white rounded-xl font-medium shadow-md shadow-cyan-500/25 hover:from-cyan-500 hover:to-teal-500 transition-colors">
                    Next <ArrowRight className="w-4 h-4" />
                  </button>
                ) : (
                  <button onClick={finish} className="px-6 py-2.5 bg-gradient-to-r from-cyan-600 to-teal-600 text-white rounded-xl font-medium shadow-md shadow-cyan-500/25 hover:from-cyan-500 hover:to-teal-500 transition-colors">Get Started</button>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default OnboardingTour;
