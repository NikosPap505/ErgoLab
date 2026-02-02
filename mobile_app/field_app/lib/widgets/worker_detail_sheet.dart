import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/offline_database.dart';

/// Widget displaying worker details with check-in/check-out functionality.
/// Attendance is stored locally and synced when backend supports it.
class WorkerDetailSheet extends StatefulWidget {
  final Map<String, dynamic> workerData;
  final VoidCallback onClose;

  const WorkerDetailSheet({
    super.key,
    required this.workerData,
    required this.onClose,
  });

  @override
  State<WorkerDetailSheet> createState() => _WorkerDetailSheetState();
}

class _WorkerDetailSheetState extends State<WorkerDetailSheet> {
  bool _isLoading = false;
  String? _lastAction;
  DateTime? _lastActionTime;
  List<Map<String, dynamic>> _recentHistory = [];

  @override
  void initState() {
    super.initState();
    _loadLastAction();
  }

  Future<void> _loadLastAction() async {
    final workerId = _getWorkerId();
    if (workerId == null) return;

    final lastAction = await OfflineDatabase.getLastWorkerAction(workerId);
    final history = await OfflineDatabase.getWorkerAttendance(workerId, limit: 5);

    if (mounted) {
      setState(() {
        _lastAction = lastAction?['action'] as String?;
        final timestamp = lastAction?['timestamp'] as String?;
        _lastActionTime = timestamp != null ? DateTime.tryParse(timestamp) : null;
        _recentHistory = history;
      });
    }
  }

  int? _getWorkerId() {
    final id = widget.workerData['id'];
    if (id is int) return id;
    if (id is String) return int.tryParse(id);
    return null;
  }

  Future<void> _recordAttendance(String action) async {
    final workerId = _getWorkerId();
    final workerName = widget.workerData['full_name']?.toString() ??
        widget.workerData['username']?.toString() ??
        'Unknown';

    if (workerId == null) {
      _showError('Worker ID not found');
      return;
    }

    setState(() => _isLoading = true);

    try {
      await OfflineDatabase.recordWorkerAttendance(
        workerId: workerId,
        workerName: workerName,
        action: action,
      );

      await _loadLastAction();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              action == 'check_in' ? 'Check-in καταγράφηκε!' : 'Check-out καταγράφηκε!',
            ),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      _showError('Σφάλμα: $e');
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  @override
  Widget build(BuildContext context) {
    final fullName = widget.workerData['full_name']?.toString() ?? 'Εργαζόμενος';
    final username = widget.workerData['username']?.toString() ?? '-';
    final role = widget.workerData['role']?.toString() ?? '-';
    final email = widget.workerData['email']?.toString();
    final phone = widget.workerData['phone']?.toString();

    // Determine which button to show based on last action
    final showCheckIn = _lastAction != 'check_in';
    final showCheckOut = _lastAction == 'check_in';

    return DraggableScrollableSheet(
      initialChildSize: 0.7,
      minChildSize: 0.5,
      maxChildSize: 0.95,
      builder: (context, scrollController) => Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Handle
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey[300],
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 20),

            // Header with avatar
            Row(
              children: [
                CircleAvatar(
                  radius: 32,
                  backgroundColor: Colors.green[100],
                  child: Text(
                    fullName.isNotEmpty ? fullName[0].toUpperCase() : '?',
                    style: const TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      color: Colors.green,
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        fullName,
                        style: const TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        '@$username',
                        style: TextStyle(color: Colors.grey[600], fontSize: 14),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: widget.onClose,
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Status indicator
            if (_lastAction != null) ...[
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  color: _lastAction == 'check_in' ? Colors.green[50] : Colors.grey[100],
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    Icon(
                      _lastAction == 'check_in' ? Icons.check_circle : Icons.logout,
                      color: _lastAction == 'check_in' ? Colors.green : Colors.grey,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _lastAction == 'check_in' ? 'Checked In' : 'Checked Out',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              color: _lastAction == 'check_in' ? Colors.green : Colors.grey[700],
                            ),
                          ),
                          if (_lastActionTime != null)
                            Text(
                              DateFormat('dd/MM/yyyy HH:mm').format(_lastActionTime!),
                              style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                            ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
            ],

            // Info section
            Expanded(
              child: SingleChildScrollView(
                controller: scrollController,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildInfoCard([
                      _buildInfoRow(Icons.badge, 'Ρόλος', role),
                      if (email != null && email.isNotEmpty)
                        _buildInfoRow(Icons.email, 'Email', email),
                      if (phone != null && phone.isNotEmpty)
                        _buildInfoRow(Icons.phone, 'Τηλέφωνο', phone),
                    ]),
                    const SizedBox(height: 20),

                    // Recent history
                    if (_recentHistory.isNotEmpty) ...[
                      const Text(
                        'Πρόσφατο Ιστορικό',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 8),
                      ..._recentHistory.map(_buildHistoryItem),
                    ],

                    // Offline notice
                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.blue[50],
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.info_outline, color: Colors.blue[700], size: 20),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Οι εγγραφές αποθηκεύονται τοπικά και θα συγχρονιστούν όταν είναι διαθέσιμο.',
                              style: TextStyle(fontSize: 12, color: Colors.blue[700]),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            // Action buttons
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: widget.onClose,
                    icon: const Icon(Icons.close),
                    label: const Text('Κλείσιμο'),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                if (showCheckIn)
                  Expanded(
                    flex: 2,
                    child: ElevatedButton.icon(
                      onPressed: _isLoading ? null : () => _recordAttendance('check_in'),
                      icon: _isLoading
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.login),
                      label: const Text('Check In'),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        backgroundColor: Colors.green,
                      ),
                    ),
                  ),
                if (showCheckOut)
                  Expanded(
                    flex: 2,
                    child: ElevatedButton.icon(
                      onPressed: _isLoading ? null : () => _recordAttendance('check_out'),
                      icon: _isLoading
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.logout),
                      label: const Text('Check Out'),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        backgroundColor: Colors.orange,
                      ),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoCard(List<Widget> children) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(children: children),
    );
  }

  Widget _buildInfoRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Icon(icon, size: 20, color: Colors.grey[600]),
          const SizedBox(width: 12),
          SizedBox(
            width: 80,
            child: Text(
              label,
              style: TextStyle(color: Colors.grey[600], fontSize: 14),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHistoryItem(Map<String, dynamic> record) {
    final action = record['action'] as String?;
    final timestamp = DateTime.tryParse(record['timestamp'] as String? ?? '');
    final isCheckIn = action == 'check_in';

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey[200]!),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Icon(
            isCheckIn ? Icons.login : Icons.logout,
            size: 18,
            color: isCheckIn ? Colors.green : Colors.orange,
          ),
          const SizedBox(width: 8),
          Text(
            isCheckIn ? 'Check In' : 'Check Out',
            style: TextStyle(
              fontWeight: FontWeight.w500,
              color: isCheckIn ? Colors.green : Colors.orange,
            ),
          ),
          const Spacer(),
          if (timestamp != null)
            Text(
              DateFormat('dd/MM HH:mm').format(timestamp),
              style: TextStyle(fontSize: 12, color: Colors.grey[600]),
            ),
        ],
      ),
    );
  }
}
