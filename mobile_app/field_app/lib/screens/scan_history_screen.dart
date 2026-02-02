import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/offline_database.dart';
import '../l10n/app_localizations.dart';

class ScanHistoryScreen extends StatefulWidget {
  const ScanHistoryScreen({super.key});

  @override
  State<ScanHistoryScreen> createState() => _ScanHistoryScreenState();
}

class _ScanHistoryScreenState extends State<ScanHistoryScreen> {
  List<Map<String, dynamic>> _scans = [];
  bool _isLoading = true;
  bool _hasMore = true;
  int _offset = 0;
  static const int _pageSize = 20;
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _loadScans();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.removeListener(_onScroll);
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      _loadMore();
    }
  }

  Future<void> _loadScans() async {
    setState(() => _isLoading = true);
    try {
      final scans = await OfflineDatabase.getScanHistory(
        limit: _pageSize,
        offset: 0,
      );
      if (mounted) {
        setState(() {
          _scans = scans;
          _offset = scans.length;
          _hasMore = scans.length == _pageSize;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        final l10n = AppLocalizations.of(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${l10n.loadingError}: $e')),
        );
      }
    }
  }

  Future<void> _loadMore() async {
    if (_isLoading || !_hasMore) return;

    final scans = await OfflineDatabase.getScanHistory(
      limit: _pageSize,
      offset: _offset,
    );
    if (mounted) {
      setState(() {
        _scans.addAll(scans);
        _offset += scans.length;
        _hasMore = scans.length == _pageSize;
      });
    }
  }

  Future<void> _deleteScan(int id, int index) async {
    await OfflineDatabase.deleteScanFromHistory(id);
    if (mounted) {
      setState(() {
        _scans.removeAt(index);
      });
      final l10n = AppLocalizations.of(context);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.deleted)),
      );
    }
  }

  Future<void> _clearAllHistory() async {
    final l10n = AppLocalizations.of(context);
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(l10n.deleteHistory),
        content: Text(l10n.deleteHistoryConfirm),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(l10n.cancel),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: Text(l10n.delete),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await OfflineDatabase.clearScanHistory();
      if (mounted) {
        setState(() {
          _scans = [];
          _offset = 0;
          _hasMore = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.historyDeleted)),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.scanHistory),
        actions: [
          if (_scans.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.delete_sweep),
              onPressed: _clearAllHistory,
              tooltip: l10n.deleteAll,
            ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading && _scans.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_scans.isEmpty) {
      final l10n = AppLocalizations.of(context);
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.history, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text(
              l10n.noScanHistory,
              style: TextStyle(fontSize: 16, color: Colors.grey[600]),
            ),
            const SizedBox(height: 8),
            Text(
              l10n.scansWillAppearHere,
              style: TextStyle(color: Colors.grey[500]),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadScans,
      child: ListView.builder(
        controller: _scrollController,
        itemCount: _scans.length + (_hasMore ? 1 : 0),
        itemBuilder: (context, index) {
          if (index == _scans.length) {
            return const Padding(
              padding: EdgeInsets.all(16),
              child: Center(child: CircularProgressIndicator()),
            );
          }
          return _buildScanTile(_scans[index], index);
        },
      ),
    );
  }

  Widget _buildScanTile(Map<String, dynamic> scan, int index) {
    final l10n = AppLocalizations.of(context);
    final scannedAt = DateTime.tryParse(scan['scanned_at'] ?? '');
    final formattedDate = scannedAt != null
        ? DateFormat('dd/MM/yyyy HH:mm').format(scannedAt)
        : l10n.unknownDate;

    final resultType = scan['result_type'] as String?;
    final resultName = scan['result_name'] as String?;

    IconData icon;
    Color iconColor;

    switch (resultType) {
      case 'material':
        icon = Icons.inventory_2;
        iconColor = Colors.blue;
        break;
      case 'worker':
        icon = Icons.person;
        iconColor = Colors.green;
        break;
      case 'error':
        icon = Icons.error_outline;
        iconColor = Colors.red;
        break;
      default:
        icon = Icons.qr_code;
        iconColor = Colors.grey;
    }

    return Dismissible(
      key: Key('scan_${scan['id']}'),
      direction: DismissDirection.endToStart,
      background: Container(
        color: Colors.red,
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 16),
        child: const Icon(Icons.delete, color: Colors.white),
      ),
      onDismissed: (_) => _deleteScan(scan['id'] as int, index),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: iconColor.withAlpha(25),
          child: Icon(icon, color: iconColor),
        ),
        title: Text(
          resultName ?? _truncateRawValue(scan['raw_value'] as String? ?? ''),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (resultType != null && resultName != null)
              Text(
                _getResultTypeLabel(resultType),
                style: TextStyle(color: iconColor, fontSize: 12),
              ),
            Text(formattedDate, style: const TextStyle(fontSize: 12)),
          ],
        ),
        trailing: const Icon(Icons.chevron_right),
        onTap: () => _showScanDetails(scan),
      ),
    );
  }

  String _truncateRawValue(String value) {
    if (value.length <= 30) return value;
    return '${value.substring(0, 27)}...';
  }

  String _getResultTypeLabel(String type) {
    final l10n = AppLocalizations.of(context);
    switch (type) {
      case 'material':
        return l10n.material;
      case 'worker':
        return l10n.worker;
      case 'error':
        return l10n.error;
      default:
        return type;
    }
  }

  void _showScanDetails(Map<String, dynamic> scan) {
    final l10n = AppLocalizations.of(context);
    final scannedAt = DateTime.tryParse(scan['scanned_at'] ?? '');
    final formattedDate = scannedAt != null
        ? DateFormat('dd/MM/yyyy HH:mm:ss').format(scannedAt)
        : l10n.unknownDate;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.5,
        minChildSize: 0.3,
        maxChildSize: 0.8,
        expand: false,
        builder: (context, scrollController) => SingleChildScrollView(
          controller: scrollController,
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
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
              Text(
                l10n.scanDetails,
                style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 20),
              _buildDetailRow(l10n.date, formattedDate),
              _buildDetailRow(l10n.type, scan['scan_type'] ?? 'N/A'),
              _buildDetailRow(
                l10n.result,
                _getResultTypeLabel(scan['result_type'] ?? 'unknown'),
              ),
              if (scan['result_name'] != null)
                _buildDetailRow(l10n.name, scan['result_name']),
              const SizedBox(height: 16),
              Text(
                l10n.qrBarcodeValue,
                style: const TextStyle(fontWeight: FontWeight.w500),
              ),
              const SizedBox(height: 8),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.grey[100],
                  borderRadius: BorderRadius.circular(8),
                ),
                child: SelectableText(
                  scan['raw_value'] ?? '',
                  style: const TextStyle(fontFamily: 'monospace'),
                ),
              ),
              if (scan['result_data'] != null) ...[
                const SizedBox(height: 16),
                Text(
                  l10n.data,
                  style: const TextStyle(fontWeight: FontWeight.w500),
                ),
                const SizedBox(height: 8),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    _formatResultData(scan['result_data']),
                    style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
                  ),
                ),
              ],
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: () {
                    Navigator.pop(context);
                    _deleteScan(scan['id'] as int, _scans.indexOf(scan));
                  },
                  icon: const Icon(Icons.delete, color: Colors.red),
                  label: Text(
                    l10n.delete,
                    style: const TextStyle(color: Colors.red),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: TextStyle(color: Colors.grey[600]),
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

  String _formatResultData(dynamic data) {
    if (data is Map) {
      return data.entries
          .map((e) => '${e.key}: ${e.value}')
          .join('\n');
    }
    return data.toString();
  }
}
