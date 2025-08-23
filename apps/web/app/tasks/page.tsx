"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  backgroundTaskService, 
  TaskStatus, 
  ActiveTasks,
  RefreshRequest,
  ComputeRequest,
  ReportRequest,
  CleanupRequest 
} from '../services/api/background';

export default function TasksPage() {
  const router = useRouter();
  const [activeTasks, setActiveTasks] = useState<ActiveTasks | null>(null);
  const [taskStatuses, setTaskStatuses] = useState<Map<string, TaskStatus>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showNewTaskModal, setShowNewTaskModal] = useState(false);
  const [selectedTaskType, setSelectedTaskType] = useState<'refresh' | 'compute' | 'report' | 'cleanup'>('refresh');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;

  useEffect(() => {
    if (!token) {
      router.push("/login");
      return;
    }
    
    fetchActiveTasks();
    const interval = setInterval(fetchActiveTasks, 2000); // Poll every 2 seconds
    return () => clearInterval(interval);
  }, [token, router]);

  const fetchActiveTasks = async () => {
    try {
      const tasks = await backgroundTaskService.getActiveTasks();
      setActiveTasks(tasks);
      
      // Poll status for each active task
      if (tasks.active) {
        Object.values(tasks.active).flat().forEach(async (task: any) => {
          try {
            const status = await backgroundTaskService.getTaskStatus(task.id);
            setTaskStatuses(prev => {
              const newMap = new Map(prev);
              newMap.set(task.id, status);
              return newMap;
            });
          } catch (err) {
            console.error(`Failed to fetch status for task ${task.id}:`, err);
          }
        });
      }
      setError(null);
    } catch (err: any) {
      setError('Failed to fetch active tasks');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTask = async () => {
    setIsSubmitting(true);
    try {
      let response;
      
      switch (selectedTaskType) {
        case 'refresh':
          response = await backgroundTaskService.triggerRefresh({ mode: 'smart' });
          break;
        case 'compute':
          response = await backgroundTaskService.triggerCompute({});
          break;
        case 'report':
          response = await backgroundTaskService.generateReport({ 
            report_type: 'performance', 
            period_days: 30 
          });
          break;
        case 'cleanup':
          response = await backgroundTaskService.cleanupData({ days_to_keep: 365 });
          break;
      }
      
      if (response) {
        setShowNewTaskModal(false);
        fetchActiveTasks(); // Refresh the task list
      }
    } catch (err: any) {
      alert('Failed to create task: ' + (err.message || 'Unknown error'));
    } finally {
      setIsSubmitting(false);
    }
  };

  const getTaskProgress = (taskId: string): number => {
    const status = taskStatuses.get(taskId);
    if (!status) return 0;
    if (status.status === 'SUCCESS') return 100;
    if (status.current && status.total) {
      return (status.current / status.total) * 100;
    }
    return status.status === 'STARTED' ? 50 : 0;
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'SUCCESS': return 'bg-green-500';
      case 'FAILURE': return 'bg-red-500';
      case 'STARTED': return 'bg-blue-500';
      case 'PENDING': return 'bg-yellow-500';
      case 'RETRY': return 'bg-orange-500';
      default: return 'bg-gray-500';
    }
  };

  const totalTasks = activeTasks?.stats.total_active || 0;

  return (
    <main className="min-h-screen relative">
      <div className="fixed inset-0 gradient-bg opacity-5" />
      
      <div className="max-w-7xl mx-auto px-6 py-10 relative">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Header */}
          <div className="flex justify-between items-start mb-8">
            <div>
              <h1 className="text-4xl font-bold mb-2 gradient-text">Task Management</h1>
              <p className="text-neutral-400">Monitor and control background operations</p>
            </div>
            <div className="flex items-center gap-3 mt-2">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setShowNewTaskModal(true)}
                className="btn-primary text-sm px-4 py-2"
              >
                New Task
              </motion.button>
              <button
                onClick={() => router.push("/dashboard")}
                className="btn-ghost btn-sm"
              >
                Back to Dashboard
              </button>
            </div>
          </div>

          {/* Task Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 }}
              className="card"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-neutral-300">Active Tasks</p>
                  <p className="text-3xl font-bold gradient-text">
                    {activeTasks?.stats.total_active || 0}
                  </p>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
              className="card"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-neutral-300">Scheduled</p>
                  <p className="text-3xl font-bold text-blue-400">
                    {activeTasks?.stats.total_scheduled || 0}
                  </p>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3 }}
              className="card"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-neutral-300">Reserved</p>
                  <p className="text-3xl font-bold text-yellow-400">
                    {activeTasks?.stats.total_reserved || 0}
                  </p>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.4 }}
              className="card"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-neutral-300">Total Queued</p>
                  <p className="text-3xl font-bold text-purple-400">
                    {(activeTasks?.stats.total_active || 0) + 
                     (activeTasks?.stats.total_scheduled || 0) + 
                     (activeTasks?.stats.total_reserved || 0)}
                  </p>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Active Tasks List */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="card"
          >
            <h2 className="text-xl font-semibold gradient-text mb-4">Active Tasks</h2>
            
            {loading ? (
              <div className="space-y-4">
                <div className="h-20 skeleton rounded-lg" />
                <div className="h-20 skeleton rounded-lg" />
                <div className="h-20 skeleton rounded-lg" />
              </div>
            ) : error ? (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                <p className="text-red-400">{error}</p>
                <button onClick={fetchActiveTasks} className="btn-secondary btn-sm mt-2">
                  Retry
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <AnimatePresence>
                  {activeTasks?.active && Object.values(activeTasks.active).flat().length > 0 ? (
                    Object.values(activeTasks.active).flat().map((task: any) => {
                      const status = taskStatuses.get(task.id);
                      const progress = getTaskProgress(task.id);
                      
                      return (
                        <motion.div
                          key={task.id}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -20 }}
                          className="bg-white/5 rounded-lg p-4 border border-white/10"
                        >
                          <div className="flex justify-between items-start mb-3">
                            <div>
                              <h4 className="font-medium text-white">{task.name || 'Background Task'}</h4>
                              <p className="text-xs text-neutral-400">ID: {task.id}</p>
                              {task.args && task.args.length > 0 && (
                                <p className="text-xs text-neutral-500 mt-1">
                                  Args: {JSON.stringify(task.args).substring(0, 50)}...
                                </p>
                              )}
                            </div>
                            <span className={`px-2 py-1 rounded text-xs text-white ${
                              status ? getStatusColor(status.status) : 'bg-gray-500'
                            }`}>
                              {status?.status || 'UNKNOWN'}
                            </span>
                          </div>
                          
                          {/* Progress Bar */}
                          <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                            <motion.div
                              className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                              initial={{ width: 0 }}
                              animate={{ width: `${progress}%` }}
                              transition={{ duration: 0.5 }}
                            />
                          </div>
                          
                          <div className="flex justify-between items-center mt-2">
                            <span className="text-xs text-neutral-500">
                              Progress: {progress.toFixed(0)}%
                            </span>
                            {status?.current && status?.total && (
                              <span className="text-xs text-neutral-500">
                                {status.current} / {status.total}
                              </span>
                            )}
                          </div>
                          
                          {status?.error && (
                            <div className="mt-2 p-2 bg-red-500/10 rounded border border-red-500/20">
                              <p className="text-xs text-red-400">{status.error}</p>
                            </div>
                          )}
                        </motion.div>
                      );
                    })
                  ) : (
                    <div className="text-center py-12 text-neutral-400">
                      <p className="text-lg mb-2">No active tasks</p>
                      <p className="text-sm">Background tasks will appear here when running</p>
                    </div>
                  )}
                </AnimatePresence>
              </div>
            )}
          </motion.section>

          {/* Quick Actions */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="card mt-6"
          >
            <h2 className="text-xl font-semibold gradient-text mb-4">Quick Actions</h2>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={async () => {
                  try {
                    await backgroundTaskService.triggerRefresh({ mode: 'smart' });
                    fetchActiveTasks();
                  } catch (err) {
                    alert('Failed to trigger refresh');
                  }
                }}
                className="p-4 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-all"
              >
                <div className="text-2xl mb-2"></div>
                <p className="text-sm font-medium">Smart Refresh</p>
                <p className="text-xs text-neutral-400 mt-1">Update market data</p>
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={async () => {
                  try {
                    await backgroundTaskService.triggerCompute({});
                    fetchActiveTasks();
                  } catch (err) {
                    alert('Failed to trigger computation');
                  }
                }}
                className="p-4 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-all"
              >
                <div className="text-2xl mb-2"></div>
                <p className="text-sm font-medium">Compute Index</p>
                <p className="text-xs text-neutral-400 mt-1">Recalculate portfolio</p>
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={async () => {
                  try {
                    await backgroundTaskService.generateReport({ 
                      report_type: 'performance', 
                      period_days: 30 
                    });
                    fetchActiveTasks();
                  } catch (err) {
                    alert('Failed to generate report');
                  }
                }}
                className="p-4 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-all"
              >
                <div className="text-2xl mb-2"></div>
                <p className="text-sm font-medium">Generate Report</p>
                <p className="text-xs text-neutral-400 mt-1">30-day performance</p>
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={async () => {
                  if (confirm('Clean up data older than 1 year?')) {
                    try {
                      await backgroundTaskService.cleanupData({ days_to_keep: 365 });
                      fetchActiveTasks();
                    } catch (err) {
                      alert('Failed to trigger cleanup');
                    }
                  }
                }}
                className="p-4 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-all"
              >
                <div className="text-2xl mb-2"></div>
                <p className="text-sm font-medium">Cleanup Data</p>
                <p className="text-xs text-neutral-400 mt-1">Remove old records</p>
              </motion.button>
            </div>
          </motion.section>
        </motion.div>
      </div>

      {/* New Task Modal */}
      <AnimatePresence>
        {showNewTaskModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
            onClick={() => setShowNewTaskModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-neutral-900 rounded-xl p-6 max-w-md w-full border border-white/10"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-xl font-semibold gradient-text mb-4">Create New Task</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-neutral-300">Task Type</label>
                  <select
                    value={selectedTaskType}
                    onChange={(e) => setSelectedTaskType(e.target.value as any)}
                    className="input mt-1"
                  >
                    <option value="refresh">Market Data Refresh</option>
                    <option value="compute">Index Computation</option>
                    <option value="report">Generate Report</option>
                    <option value="cleanup">Data Cleanup</option>
                  </select>
                </div>

                <div className="text-sm text-neutral-400">
                  {selectedTaskType === 'refresh' && 'Fetch latest market data and update prices'}
                  {selectedTaskType === 'compute' && 'Recalculate portfolio index and allocations'}
                  {selectedTaskType === 'report' && 'Generate performance report for the last 30 days'}
                  {selectedTaskType === 'cleanup' && 'Remove data older than 1 year'}
                </div>

                <div className="flex gap-3 mt-6">
                  <button
                    onClick={handleCreateTask}
                    disabled={isSubmitting}
                    className="btn-primary flex-1"
                  >
                    {isSubmitting ? 'Creating...' : 'Create Task'}
                  </button>
                  <button
                    onClick={() => setShowNewTaskModal(false)}
                    className="btn-ghost flex-1"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}