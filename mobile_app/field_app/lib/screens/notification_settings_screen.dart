import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../l10n/app_localizations.dart';
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
        SnackBar(
          content: Text(AppLocalizations.of(context).errorLoadingSettings),
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

    final l10n = AppLocalizations.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.notificationSettings),
      ),
      body: ListView(
        children: [
          SwitchListTile(
            title: Text(l10n.pushNotifications),
            subtitle: Text(l10n.pushNotificationsSubtitle),
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
          ListTile(
            title: Text(
              l10n.notificationTypes,
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          SwitchListTile(
            title: Text(l10n.dailyReports),
            subtitle: Text(l10n.dailyReportsSubtitle),
            value: dailyReports,
            onChanged: pushEnabled
                ? (value) {
                    setState(() => dailyReports = value);
                    _updatePreferences();
                  }
                : null,
          ),
          SwitchListTile(
            title: Text(l10n.issues),
            subtitle: Text(l10n.issuesSubtitle),
            value: issueUpdates,
            onChanged: pushEnabled
                ? (value) {
                    setState(() => issueUpdates = value);
                    _updatePreferences();
                  }
                : null,
          ),
          SwitchListTile(
            title: Text(l10n.lowStock),
            subtitle: Text(l10n.lowStockSubtitle),
            value: lowStockAlerts,
            onChanged: pushEnabled
                ? (value) {
                    setState(() => lowStockAlerts = value);
                    _updatePreferences();
                  }
                : null,
          ),
          SwitchListTile(
            title: Text(l10n.projectUpdates),
            subtitle: Text(l10n.projectUpdatesSubtitle),
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
        SnackBar(
          content: Text(AppLocalizations.of(context).errorSavingSettings),
          backgroundColor: Colors.red,
        ),
      );
    }
  }
}
