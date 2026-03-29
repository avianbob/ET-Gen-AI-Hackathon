import React from 'react';
import Modal from './Modal';

const shortcuts = [
  { keys: ['Ctrl', 'K'], action: 'Command Palette' },
  { keys: ['Ctrl', '/'], action: 'Focus AI Assistant' },
  { keys: ['Ctrl', 'Shift', 'N'], action: 'New Search' },
  { keys: ['Ctrl', 'Shift', 'D'], action: 'Dashboard' },
  { keys: ['Ctrl', 'Shift', 'H'], action: 'History' },
  { keys: ['?'], action: 'Keyboard Shortcuts' },
  { keys: ['Esc'], action: 'Close Modal' },
];

interface ShortcutsModalProps { isOpen: boolean; onClose: () => void; }

const ShortcutsModal: React.FC<ShortcutsModalProps> = ({ isOpen, onClose }) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Keyboard Shortcuts">
      <div className="space-y-3">
        {shortcuts.map((s, i) => (
          <div key={i} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
            <span className="text-sm text-slate-700">{s.action}</span>
            <div className="flex gap-1">
              {s.keys.map((k, j) => (
                <kbd key={j} className="px-2 py-1 text-xs bg-slate-100 text-slate-700 rounded-lg border border-slate-200">{k}</kbd>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Modal>
  );
};

export default ShortcutsModal;
