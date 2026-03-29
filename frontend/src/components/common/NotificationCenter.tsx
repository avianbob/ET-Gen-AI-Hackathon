import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, X, CheckCircle, AlertTriangle, Info } from 'lucide-react';
import useAppStore from '../../store';

const NotificationCenter: React.FC = () => {
  const [open, setOpen] = useState(false);
  const { notifications, removeNotification, clearNotifications } = useAppStore();

  const iconMap: Record<string, React.ReactNode> = {
    success: <CheckCircle className="w-4 h-4 text-teal-600" />,
    warning: <AlertTriangle className="w-4 h-4 text-amber-600" />,
    error: <AlertTriangle className="w-4 h-4 text-red-600" />,
    info: <Info className="w-4 h-4 text-sky-600" />,
  };

  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)} className="relative p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors">
        <Bell className="w-4 h-4" />
        {notifications.length > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 bg-gradient-to-br from-cyan-500 to-teal-600 rounded-full text-[8px] text-white flex items-center justify-center font-bold shadow-sm">
            {notifications.length > 9 ? '9+' : notifications.length}
          </span>
        )}
      </button>

      <AnimatePresence>
        {open && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              className="absolute right-0 mt-2 w-80 bg-white border border-slate-200 rounded-xl shadow-lg shadow-slate-200/60 z-50 overflow-hidden"
            >
              <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
                <h3 className="text-sm font-semibold text-slate-900">Notifications</h3>
                {notifications.length > 0 && (
                  <button onClick={clearNotifications} className="text-xs text-cyan-600 hover:text-teal-600 font-medium">Clear all</button>
                )}
              </div>
              <div className="max-h-80 overflow-y-auto">
                {notifications.length === 0 ? (
                  <p className="text-center text-sm text-slate-500 py-8">No notifications</p>
                ) : (
                  notifications.map((n: any) => (
                    <div key={n.id} className="flex items-start gap-3 px-4 py-3 border-b border-slate-100 last:border-0 hover:bg-slate-50">
                      {iconMap[n.type] || iconMap.info}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-slate-900">{n.title}</p>
                        {n.message && <p className="text-xs text-slate-500 mt-0.5">{n.message}</p>}
                      </div>
                      <button onClick={() => removeNotification(n.id)} className="text-slate-400 hover:text-slate-600">
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

export const ToastContainer: React.FC = () => null;

export default NotificationCenter;
