import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Settings as SettingsIcon, User, Database, Trash2, Shield, Bell } from 'lucide-react';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';
import useAppStore from '../store';
import { clearAllData } from '../services/api';

const Settings: React.FC = () => {
  const user = useAppStore((s) => s.user);
  const sidebarCollapsed = useAppStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useAppStore((s) => s.toggleSidebar);
  const storeClearAllData = useAppStore((s) => s.clearAllData);

  const [showClearModal, setShowClearModal] = useState(false);
  const [clearing, setClearing] = useState(false);

  const handleClearAllData = async () => {
    setClearing(true);
    try {
      await clearAllData();
    } catch {
      // server clear is best-effort
    }
    storeClearAllData();
    setClearing(false);
    setShowClearModal(false);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* Page Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-cyan-500/15 flex items-center justify-center">
          <SettingsIcon className="w-5 h-5 text-cyan-700" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
          <p className="text-sm text-slate-600">Manage your preferences and data</p>
        </div>
      </div>

      {/* User Info */}
      <Card>
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-full bg-gradient-to-br from-cyan-500 to-teal-600 flex items-center justify-center shadow-md shadow-cyan-500/25">
            <User className="w-7 h-7 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-slate-900 truncate">
              {user?.name || 'PharmAI User'}
            </h3>
            <p className="text-sm text-slate-600 truncate">
              {user?.email || 'user@pharmai.et.com'}
            </p>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-teal-50 border border-teal-200">
            <Shield className="w-3.5 h-3.5 text-teal-700" />
            <span className="text-xs font-medium text-teal-800">Active</span>
          </div>
        </div>
      </Card>

      {/* Quick Settings */}
      <Card>
        <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wider mb-4">
          Quick Settings
        </h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2">
            <div className="flex items-center gap-3">
              <Bell className="w-4 h-4 text-slate-600" />
              <span className="text-sm text-slate-800">Compact Sidebar</span>
            </div>
            <button
              onClick={toggleSidebar}
              className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${
                sidebarCollapsed ? 'bg-gradient-to-r from-cyan-600 to-teal-600' : 'bg-slate-300'
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200 ${
                  sidebarCollapsed ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
        </div>
      </Card>

      {/* Data & Storage */}
      <Card>
        <div className="flex items-center gap-3 mb-4">
          <Database className="w-4 h-4 text-slate-600" />
          <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wider">
            Data & Storage
          </h3>
        </div>
        <p className="text-sm text-slate-600 mb-4">
          Clear all cached searches, saved opportunities, chat history, and notifications.
          This action cannot be undone.
        </p>
        <Button
          variant="danger"
          size="sm"
          icon={<Trash2 className="w-4 h-4" />}
          onClick={() => setShowClearModal(true)}
        >
          Clear All Data
        </Button>
      </Card>

      {/* Version Footer */}
      <div className="text-center pt-4 pb-8">
        <p className="text-xs text-slate-500">
          PharmAI Platform &middot; v3.1.0 &middot; ET Pharmaceutical Intelligence
        </p>
      </div>

      {/* Confirmation Modal */}
      <Modal
        isOpen={showClearModal}
        onClose={() => setShowClearModal(false)}
        title="Clear All Data"
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-700">
            This will permanently delete all your local data including:
          </p>
          <ul className="text-sm text-slate-600 space-y-1.5 list-disc list-inside">
            <li>Search history &amp; cached results</li>
            <li>Saved opportunities &amp; notes</li>
            <li>Chat messages</li>
            <li>Notifications</li>
          </ul>
          <p className="text-sm text-red-400 font-medium">
            This action cannot be undone.
          </p>
          <div className="flex items-center justify-end gap-3 pt-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowClearModal(false)}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              size="sm"
              icon={<Trash2 className="w-4 h-4" />}
              loading={clearing}
              onClick={handleClearAllData}
            >
              Clear Everything
            </Button>
          </div>
        </div>
      </Modal>
    </motion.div>
  );
};

export default Settings;
