import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';

class NotificationSettingsScreen extends StatefulWidget {
  const NotificationSettingsScreen({super.key});

  @override
  State<NotificationSettingsScreen> createState() => _NotificationSettingsScreenState();
}

class _NotificationSettingsScreenState extends State<NotificationSettingsScreen> {
  bool pushEnabled = true;
  bool dailyReports = false;
  bool issueUpdates = true;
  bool lowStockAlerts = false;
  bool projectUpdates = true;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadPreferences();
  }

  Future<void> _loadPreferences() async {
    try {
      final api = context.read<AppState>().apiService;
      final prefs = await api.getNotificationPreferences();
      if (!mounted) return;
      setState(() {
        dailyReports = prefs['push_daily_reports'] == true;
        issueUpdates = prefs['push_issue_assigned'] == true;
        lowStockAlerts = prefs['push_low_stock'] == true;
        projectUpdates = prefs['push_budget_alerts'] == true;
        pushEnabled = dailyReports || issueUpdates || lowStockAlerts || projectUpdates;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isLoading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Αποτυχία φόρτωσης ρυθμίσεων.'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Ρυθμίσεις Ειδοποιήσεων'),
      ),
      body: ListView(
        children: [
          SwitchListTile(
            title: const Text('Push Notifications'),
            subtitle: const Text('Λήψη ειδοποιήσεων στη συσκευή'),
            value: pushEnabled,
            onChanged: (value) {
              setState(() {
                pushEnabled = value;
                if (!value) {
                  dailyReports = false;
                  issueUpdates = false;
                  lowStockAlerts = false;
                  projectUpdates = false;
                }
              });
              _updatePreferences();
            },
          ),
          const Divider(),
          const ListTile(
            title: Text(
              'Τύποι Ειδοποιήσεων',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          SwitchListTile(
            title: const Text('Ημερήσιες Αναφορές'),
            subtitle: const Text('Ειδοποιήσεις για νέες αναφορές'),
            value: dailyReports,
            onChanged: pushEnabled
                ? (value) {
                    setState(() => dailyReports = value);
                    _updatePreferences();
                  }
                : null,
          ),
          SwitchListTile(
            title: const Text('Issues'),
            subtitle: const Text('Ενημερώσεις για προβλήματα'),
            value: issueUpdates,
            onChanged: pushEnabled
                ? (value) {
                    setState(() => issueUpdates = value);
                    _updatePreferences();
                  }
                : null,
          ),
          SwitchListTile(
            title: const Text('Χαμηλά Αποθέματα'),
            subtitle: const Text('Ειδοποιήσεις για χαμηλά αποθέματα'),
            value: lowStockAlerts,
            onChanged: pushEnabled
                ? (value) {
                    setState(() => lowStockAlerts = value);
                    _updatePreferences();
                  }
                : null,
          ),
          SwitchListTile(
            title: const Text('Ενημερώσεις Έργων/Οικονομικά'),
            subtitle: const Text('Ειδοποιήσεις για budget & έργα'),
            value: projectUpdates,
            onChanged: pushEnabled
                ? (value) {
                    setState(() => projectUpdates = value);
                    _updatePreferences();
                  }
                : null,
          ),
        ],
      ),
    );
  }

  Future<void> _updatePreferences() async {
    final prevPushEnabled = pushEnabled;
    final prevDailyReports = dailyReports;
    final prevIssueUpdates = issueUpdates;
    final prevLowStockAlerts = lowStockAlerts;
    final prevProjectUpdates = projectUpdates;
    try {
      final api = context.read<AppState>().apiService;
      await api.updateNotificationPreferences({
        'push_daily_reports': dailyReports,
        'push_issue_assigned': issueUpdates,
        'push_low_stock': lowStockAlerts,
        'push_budget_alerts': projectUpdates,
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        pushEnabled = prevPushEnabled;
        dailyReports = prevDailyReports;
        issueUpdates = prevIssueUpdates;
        lowStockAlerts = prevLowStockAlerts;
        projectUpdates = prevProjectUpdates;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Αποτυχία αποθήκευσης ρυθμίσεων.'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }
}
