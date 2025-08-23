"use client";

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { backgroundTaskService, TaskStatus } from '../../services/api';

interface TaskNotification {
  id: string;
  name: string;
  status: TaskStatus['status'];
  progress?: number;
  message?: string;
  timestamp: Date;
  error?: string;
}

interface TaskNotificationsProps {
  className?: string;
  maxNotifications?: number;
}

export default function TaskNotifications({ 
  className = '', 
  maxNotifications = 5 
}: TaskNotificationsProps) {
  const [notifications, setNotifications] = useState<TaskNotification[]>([]);
  const [activeTasks, setActiveTasks] = useState<Set<string>>(new Set());
  const [isMinimized, setIsMinimized] = useState(false);

  // Polling function to check for active tasks
  const pollActiveTasks = useCallback(async () => {
    try {
      const activeTasksData = await backgroundTaskService.getActiveTasks();
      const allActiveTasks = Object.values(activeTasksData.active).flat();
      
      // Track new tasks
      const currentTaskIds = new Set(allActiveTasks.map((task: any) => task.id));
      const newTasks = allActiveTasks.filter((task: any) => !activeTasks.has(task.id));
      
      // Add notifications for new tasks
      newTasks.forEach((task: any) => {
        addNotification({
          id: task.id,
          name: task.name || 'Background Task',
          status: 'STARTED',
          timestamp: new Date(),
          message: 'Task started'
        });
      });
      
      // Update active tasks set
      setActiveTasks(currentTaskIds);
      
      // Poll status for each active task
      for (const task of allActiveTasks) {
        try {
          const status = await backgroundTaskService.getTaskStatus(task.id);
          updateTaskStatus(task.id, status);
        } catch (error) {
          console.error(`Failed to get status for task ${task.id}:`, error);
        }
      }
      
    } catch (error) {
      console.error('Failed to poll active tasks:', error);
    }
  }, [activeTasks]);

  useEffect(() => {
    // Initial poll
    pollActiveTasks();
    
    // Set up polling interval
    const interval = setInterval(pollActiveTasks, 3000); // Poll every 3 seconds
    
    return () => clearInterval(interval);
  }, [pollActiveTasks]);

  const addNotification = (notification: TaskNotification) => {
    setNotifications(prev => {
      const filtered = prev.filter(n => n.id !== notification.id);
      const updated = [notification, ...filtered].slice(0, maxNotifications);
      return updated;
    });
  };

  const updateTaskStatus = (taskId: string, status: TaskStatus) => {
    const progress = status.current && status.total 
      ? (status.current / status.total) * 100 
      : undefined;

    const notification: TaskNotification = {
      id: taskId,
      name: `Task ${taskId.slice(0, 8)}`,
      status: status.status,
      progress,
      timestamp: new Date(),
      error: status.error,
      message: getStatusMessage(status.status, progress)
    };

    addNotification(notification);

    // Remove from active tasks if completed
    if (status.status === 'SUCCESS' || status.status === 'FAILURE') {
      setActiveTasks(prev => {
        const updated = new Set(prev);
        updated.delete(taskId);
        return updated;
      });
    }
  };

  const getStatusMessage = (status: TaskStatus['status'], progress?: number): string => {
    switch (status) {
      case 'PENDING': return 'Waiting to start...';
      case 'STARTED': return progress ? `${progress.toFixed(0)}% complete` : 'In progress...';
      case 'SUCCESS': return 'Completed successfully';
      case 'FAILURE': return 'Failed to complete';
      case 'RETRY': return 'Retrying...';
      case 'REVOKED': return 'Cancelled';
      default: return 'Unknown status';
    }
  };

  const getStatusColor = (status: TaskStatus['status']): string => {
    switch (status) {
      case 'SUCCESS': return 'text-green-400 bg-green-500/10 border-green-500/30';
      case 'FAILURE': return 'text-red-400 bg-red-500/10 border-red-500/30';
      case 'STARTED': return 'text-blue-400 bg-blue-500/10 border-blue-500/30';
      case 'PENDING': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30';
      case 'RETRY': return 'text-orange-400 bg-orange-500/10 border-orange-500/30';
      default: return 'text-gray-400 bg-gray-500/10 border-gray-500/30';
    }
  };

  const getStatusIcon = (status: TaskStatus['status']): string => {
    switch (status) {
      case 'SUCCESS': return '';
      case 'FAILURE': return '';
      case 'STARTED': return '●';
      case 'PENDING': return '○';
      case 'RETRY': return '↻';
      case 'REVOKED': return '⊘';
      default: return '?';
    }
  };

  const dismissNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const clearAllNotifications = () => {
    setNotifications([]);
  };

  if (notifications.length === 0) {
    return null;
  }

  return (
    <div className={`fixed top-4 right-4 z-50 w-80 ${className}`}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, x: 100 }}
        animate={{ opacity: 1, x: 0 }}
        className="mb-2"
      >
        <div className="flex items-center justify-between p-3 bg-gray-900/95 backdrop-blur-sm rounded-lg border border-gray-700">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-white">
              Task Activity ({notifications.length})
            </span>
            {activeTasks.size > 0 && (
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ repeat: Infinity, duration: 2 }}
                className="w-2 h-2 bg-blue-400 rounded-full"
              />
            )}
          </div>
          <div className="flex gap-1">
            <button
              onClick={() => setIsMinimized(!isMinimized)}
              className="p-1 text-gray-400 hover:text-white transition-colors"
            >
              {isMinimized ? '▲' : '▼'}
            </button>
            <button
              onClick={clearAllNotifications}
              className="p-1 text-gray-400 hover:text-white transition-colors"
            >
              
            </button>
          </div>
        </div>
      </motion.div>

      {/* Notifications */}
      <AnimatePresence>
        {!isMinimized && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-2 max-h-96 overflow-y-auto"
          >
            <AnimatePresence mode="popLayout">
              {notifications.map(notification => (
                <motion.div
                  key={notification.id}
                  initial={{ opacity: 0, x: 100, scale: 0.9 }}
                  animate={{ opacity: 1, x: 0, scale: 1 }}
                  exit={{ opacity: 0, x: 100, scale: 0.9 }}
                  layout
                  className={`p-3 rounded-lg border backdrop-blur-sm ${getStatusColor(notification.status)}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-2 flex-1">
                      <span className="text-lg leading-none mt-0.5">
                        {getStatusIcon(notification.status)}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white truncate">
                          {notification.name}
                        </p>
                        <p className="text-xs text-gray-300 mt-1">
                          {notification.message}
                        </p>
                        {notification.error && (
                          <p className="text-xs text-red-300 mt-1 bg-red-500/10 p-1 rounded">
                            {notification.error}
                          </p>
                        )}
                        {notification.progress !== undefined && (
                          <div className="mt-2">
                            <div className="w-full bg-gray-700 rounded-full h-1.5">
                              <motion.div
                                className="bg-current h-1.5 rounded-full"
                                initial={{ width: 0 }}
                                animate={{ width: `${notification.progress}%` }}
                                transition={{ duration: 0.3 }}
                              />
                            </div>
                          </div>
                        )}
                        <p className="text-xs text-gray-500 mt-1">
                          {notification.timestamp.toLocaleTimeString([], { 
                            hour: '2-digit', 
                            minute: '2-digit',
                            second: '2-digit'
                          })}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => dismissNotification(notification.id)}
                      className="p-1 text-gray-400 hover:text-white transition-colors ml-2"
                    >
                      
                    </button>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}