import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Clock, Download, Trash2, Search, FileText, Calendar } from 'lucide-react';
import { useAppStore } from '../store';
import { formatTimeAgo, formatDate } from '../utils/formatters';
import { getArchivedReports, downloadArchivedReport, deleteArchivedReport } from '../services/api';
import { downloadFile } from '../utils/helpers';
import Tabs from '../components/common/Tabs';
import Card from '../components/common/Card';
import EmptyState from '../components/common/EmptyState';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';

interface ArchivedReport {
  id: string;
  drugName: string;
  createdAt: string;
  format: string;
  size?: number;
}

function getDateGroup(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today.getTime() - 86400000);
  if (date >= today) return 'Today';
  if (date >= yesterday) return 'Yesterday';
  return formatDate(timestamp);
}

const History: React.FC = () => {
  const { searchHistory, deleteFromHistory } = useAppStore();
  const [activeTab, setActiveTab] = useState('search');
  const [searchQuery, setSearchQuery] = useState('');
  const [reports, setReports] = useState<ArchivedReport[]>([]);
  const [reportsLoading, setReportsLoading] = useState(false);
  const [reportsError, setReportsError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<{ drugName: string; timestamp: string } | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  useEffect(() => {
    if (activeTab === 'archived') {
      fetchReports();
    }
  }, [activeTab]);

  const fetchReports = async () => {
    setReportsLoading(true);
    setReportsError(null);
    try {
      const data = await getArchivedReports();
      setReports(Array.isArray(data) ? data : data.reports || []);
    } catch (err: any) {
      setReportsError(err.message || 'Failed to load archived reports');
    } finally {
      setReportsLoading(false);
    }
  };

  const handleDeleteHistoryItem = (drugName: string, timestamp: string) => {
    setConfirmDelete({ drugName, timestamp });
  };

  const confirmDeleteItem = () => {
    if (confirmDelete) {
      deleteFromHistory(confirmDelete.drugName, confirmDelete.timestamp);
      setConfirmDelete(null);
    }
  };

  const handleDownloadReport = async (reportId: string, drugName: string) => {
    setDownloadingId(reportId);
    try {
      const blob = await downloadArchivedReport(reportId);
      downloadFile(blob, `${drugName}_report.pdf`);
    } catch {
      // silent fail
    } finally {
      setDownloadingId(null);
    }
  };

  const handleDeleteReport = async (reportId: string) => {
    setDeletingId(reportId);
    try {
      await deleteArchivedReport(reportId);
      setReports((prev) => prev.filter((r) => r.id !== reportId));
    } catch {
      // silent fail
    } finally {
      setDeletingId(null);
    }
  };

  const filteredHistory = useMemo(() => {
    if (!searchQuery.trim()) return searchHistory;
    const q = searchQuery.toLowerCase();
    return searchHistory.filter(
      (item: any) => item.drugName?.toLowerCase().includes(q)
    );
  }, [searchHistory, searchQuery]);

  const groupedHistory = useMemo(() => {
    const groups: Record<string, any[]> = {};
    for (const item of filteredHistory) {
      const group = getDateGroup(item.timestamp);
      if (!groups[group]) groups[group] = [];
      groups[group].push(item);
    }
    return groups;
  }, [filteredHistory]);

  const filteredReports = useMemo(() => {
    if (!searchQuery.trim()) return reports;
    const q = searchQuery.toLowerCase();
    return reports.filter(
      (r) => r.drugName?.toLowerCase().includes(q)
    );
  }, [reports, searchQuery]);

  const tabs = [
    { id: 'search', label: 'Search History', icon: <Clock className="w-4 h-4" />, count: searchHistory.length },
    { id: 'archived', label: 'Archived Reports', icon: <FileText className="w-4 h-4" />, count: reports.length },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">History</h1>
          <p className="text-sm text-slate-600 mt-1">Review past searches and archived reports</p>
        </div>
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Filter..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-cyan-500/50"
          />
        </div>
      </div>

      <Tabs tabs={tabs} active={activeTab} onChange={setActiveTab} />

      <AnimatePresence mode="wait">
        {activeTab === 'search' && (
          <motion.div
            key="search"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {filteredHistory.length === 0 ? (
              <EmptyState
                icon={<Clock className="w-12 h-12" />}
                title="No search history"
                description="Your drug searches will appear here. Start by searching for a drug."
              />
            ) : (
              <div className="space-y-6">
                {Object.entries(groupedHistory).map(([dateLabel, items]) => (
                  <div key={dateLabel}>
                    <div className="flex items-center gap-2 mb-3">
                      <Calendar className="w-4 h-4 text-slate-500" />
                      <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider">{dateLabel}</span>
                      <Badge variant="gray" size="sm">{items.length}</Badge>
                    </div>
                    <div className="space-y-2">
                      {items.map((item: any, idx: number) => (
                        <motion.div
                          key={`${item.drugName}-${item.timestamp}-${idx}`}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.03 }}
                        >
                          <Card hover className="flex items-center justify-between gap-4">
                            <div className="flex items-center gap-3 min-w-0">
                              <div className="w-10 h-10 rounded-lg bg-cyan-500/10 flex items-center justify-center shrink-0">
                                <FileText className="w-5 h-5 text-cyan-700" />
                              </div>
                              <div className="min-w-0">
                                <p className="text-sm font-semibold text-slate-900 truncate">{item.drugName}</p>
                                <div className="flex items-center gap-2 mt-0.5">
                                  <span className="text-xs text-slate-500">{formatTimeAgo(item.timestamp)}</span>
                                  {item.opportunityCount != null && (
                                    <Badge variant="teal" size="sm">
                                      {item.opportunityCount} opportunities
                                    </Badge>
                                  )}
                                </div>
                              </div>
                            </div>
                            <Button
                              variant="ghost"
                              size="xs"
                              icon={<Trash2 className="w-3.5 h-3.5" />}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteHistoryItem(item.drugName, item.timestamp);
                              }}
                              className="text-slate-500 hover:text-red-400 shrink-0"
                            />
                          </Card>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        )}

        {activeTab === 'archived' && (
          <motion.div
            key="archived"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {reportsLoading ? (
              <div className="flex items-center justify-center py-16">
                <div className="w-8 h-8 border-2 border-cyan-500/25 border-t-cyan-600 rounded-full animate-spin" />
              </div>
            ) : reportsError ? (
              <Card className="text-center py-8">
                <p className="text-red-400 text-sm mb-3">{reportsError}</p>
                <Button variant="secondary" size="sm" onClick={fetchReports}>Retry</Button>
              </Card>
            ) : filteredReports.length === 0 ? (
              <EmptyState
                icon={<FileText className="w-12 h-12" />}
                title="No archived reports"
                description="Generated reports will be stored here for later access."
              />
            ) : (
              <div className="space-y-2">
                {filteredReports.map((report, idx) => (
                  <motion.div
                    key={report.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.03 }}
                  >
                    <Card hover className="flex items-center justify-between gap-4">
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center shrink-0">
                          <FileText className="w-5 h-5 text-blue-400" />
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-slate-900 truncate">{report.drugName}</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="text-xs text-slate-500">{formatDate(report.createdAt)}</span>
                            {report.format && <Badge variant="gray" size="sm">{report.format.toUpperCase()}</Badge>}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        <Button
                          variant="ghost"
                          size="xs"
                          icon={<Download className="w-3.5 h-3.5" />}
                          loading={downloadingId === report.id}
                          onClick={() => handleDownloadReport(report.id, report.drugName)}
                          className="text-slate-600 hover:text-cyan-700"
                        />
                        <Button
                          variant="ghost"
                          size="xs"
                          icon={<Trash2 className="w-3.5 h-3.5" />}
                          loading={deletingId === report.id}
                          onClick={() => handleDeleteReport(report.id)}
                          className="text-slate-500 hover:text-red-400"
                        />
                      </div>
                    </Card>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Delete confirmation modal */}
      <AnimatePresence>
        {confirmDelete && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
            onClick={() => setConfirmDelete(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-slate-50 border border-slate-200 rounded-xl p-6 max-w-sm w-full shadow-2xl"
            >
              <h3 className="text-lg font-bold text-slate-900 mb-2">Delete History Item</h3>
              <p className="text-sm text-slate-600 mb-6">
                Remove <span className="text-slate-900 font-medium">{confirmDelete.drugName}</span> from your search history? This cannot be undone.
              </p>
              <div className="flex gap-3 justify-end">
                <Button variant="secondary" size="sm" onClick={() => setConfirmDelete(null)}>Cancel</Button>
                <Button variant="danger" size="sm" icon={<Trash2 className="w-3.5 h-3.5" />} onClick={confirmDeleteItem}>Delete</Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default History;
