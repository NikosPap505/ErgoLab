import 'package:flutter/material.dart';
import '../services/connectivity_service.dart';
import '../services/sync_service.dart';
import 'package:provider/provider.dart';

/// Offline indicator banner that shows at the top of the screen
class OfflineBanner extends StatelessWidget {
  const OfflineBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<ConnectivityService>(
      builder: (context, connectivity, child) {
        if (connectivity.isOnline) return const SizedBox.shrink();
        
        return Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
          decoration: BoxDecoration(
            color: Colors.orange.shade800,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.2),
                blurRadius: 4,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Row(
            children: [
              const Icon(Icons.cloud_off, color: Colors.white, size: 20),
              const SizedBox(width: 8),
              const Expanded(
                child: Text(
                  'Offline Mode - Changes will sync when connected',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
              Consumer<SyncService>(
                builder: (context, sync, child) {
                  if (sync.pendingCount > 0) {
                    return Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        '${sync.pendingCount} pending',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 12,
                        ),
                      ),
                    );
                  }
                  return const SizedBox.shrink();
                },
              ),
            ],
          ),
        );
      },
    );
  }
}

/// Sync status indicator for AppBar
class SyncStatusIndicator extends StatelessWidget {
  const SyncStatusIndicator({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer2<ConnectivityService, SyncService>(
      builder: (context, connectivity, sync, child) {
        return GestureDetector(
          onTap: () => _showSyncDialog(context, sync, connectivity),
          child: Container(
            padding: const EdgeInsets.all(8),
            child: Stack(
              children: [
                // Main icon
                Icon(
                  sync.isSyncing
                      ? Icons.sync
                      : connectivity.isOnline
                          ? Icons.cloud_done
                          : Icons.cloud_off,
                  color: sync.isSyncing
                      ? Colors.blue
                      : connectivity.isOnline
                          ? Colors.green
                          : Colors.orange,
                  size: 24,
                ),
                // Pending badge
                if (sync.pendingCount > 0)
                  Positioned(
                    right: 0,
                    top: 0,
                    child: Container(
                      padding: const EdgeInsets.all(4),
                      decoration: BoxDecoration(
                        color: Colors.red,
                        shape: BoxShape.circle,
                      ),
                      constraints: const BoxConstraints(
                        minWidth: 16,
                        minHeight: 16,
                      ),
                      child: Text(
                        '${sync.pendingCount}',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _showSyncDialog(BuildContext context, SyncService sync, ConnectivityService connectivity) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(
              connectivity.isOnline ? Icons.cloud_done : Icons.cloud_off,
              color: connectivity.isOnline ? Colors.green : Colors.orange,
            ),
            const SizedBox(width: 8),
            const Text('Sync Status'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildStatusRow(
              'Connection',
              connectivity.isOnline ? 'Online' : 'Offline',
              connectivity.isOnline ? Colors.green : Colors.orange,
            ),
            const SizedBox(height: 8),
            _buildStatusRow(
              'Pending items',
              '${sync.pendingCount}',
              sync.pendingCount > 0 ? Colors.orange : Colors.green,
            ),
            const SizedBox(height: 8),
            if (sync.lastSyncTime != null)
              _buildStatusRow(
                'Last sync',
                _formatTime(sync.lastSyncTime!),
                Colors.grey,
              ),
            if (sync.lastSyncError != null) ...[
              const SizedBox(height: 8),
              _buildStatusRow(
                'Last error',
                sync.lastSyncError!,
                Colors.red,
              ),
            ],
            if (sync.isSyncing) ...[
              const SizedBox(height: 16),
              LinearProgressIndicator(value: sync.syncProgress),
              const SizedBox(height: 4),
              Text(
                sync.syncStatus,
                style: const TextStyle(fontSize: 12, color: Colors.grey),
              ),
            ],
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
          if (connectivity.isOnline && !sync.isSyncing)
            ElevatedButton.icon(
              onPressed: () {
                sync.syncAll();
                Navigator.pop(context);
              },
              icon: const Icon(Icons.sync),
              label: const Text('Sync Now'),
            ),
        ],
      ),
    );
  }

  Widget _buildStatusRow(String label, String value, Color color) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(fontWeight: FontWeight.w500)),
        Text(
          value,
          style: TextStyle(color: color, fontWeight: FontWeight.w600),
        ),
      ],
    );
  }

  String _formatTime(DateTime time) {
    final now = DateTime.now();
    final diff = now.difference(time);
    
    if (diff.inMinutes < 1) return 'Just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    return '${diff.inDays}d ago';
  }
}

/// Sync progress overlay
class SyncProgressOverlay extends StatelessWidget {
  final Widget child;

  const SyncProgressOverlay({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        child,
        Consumer<SyncService>(
          builder: (context, sync, child) {
            if (!sync.isSyncing) return const SizedBox.shrink();
            
            return Positioned(
              bottom: 16,
              left: 16,
              right: 16,
              child: Card(
                elevation: 8,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Row(
                        children: [
                          const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              sync.syncStatus,
                              style: const TextStyle(fontWeight: FontWeight.w500),
                            ),
                          ),
                          Text(
                            '${(sync.syncProgress * 100).toInt()}%',
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              color: Colors.blue,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      LinearProgressIndicator(
                        value: sync.syncProgress,
                        backgroundColor: Colors.grey.shade200,
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        ),
      ],
    );
  }
}

/// Pull-to-refresh wrapper with sync
class SyncRefreshIndicator extends StatelessWidget {
  final Widget child;
  
  const SyncRefreshIndicator({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: () async {
        final sync = context.read<SyncService>();
        final connectivity = context.read<ConnectivityService>();
        
        if (connectivity.isOnline) {
          await sync.syncAll();
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Cannot sync - offline'),
              backgroundColor: Colors.orange,
            ),
          );
        }
      },
      child: child,
    );
  }
}
