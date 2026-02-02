import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../l10n/app_localizations.dart';
import '../providers/app_state.dart';

/// Keys for caching notification preferences locally
class _PrefKeys {
  static const prefix = 'notification_';
  static const dailyReports = '${prefix}daily_reports';
  static const issueUpdates = '${prefix}issue_updates';
  static const lowStockAlerts = '${prefix}low_stock';
  static const projectUpdates = '${prefix}project_updates';
  static const lastSync = '${prefix}last_sync';
}

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
  bool _isSyncing = false;

  @override
  void initState() {
    super.initState();
    _loadPreferences();
  }

  Future<void> _loadPreferences() async {
    // First, load from local cache for instant display
    await _loadFromCache();
    
    // Then sync with server in background
    _syncWithServer();
  }

  /// Load cached preferences for instant UI
  Future<void> _loadFromCache() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      if (!mounted) return;
      
      setState(() {
        dailyReports = prefs.getBool(_PrefKeys.dailyReports) ?? false;
        issueUpdates = prefs.getBool(_PrefKeys.issueUpdates) ?? true;
        lowStockAlerts = prefs.getBool(_PrefKeys.lowStockAlerts) ?? false;
        projectUpdates = prefs.getBool(_PrefKeys.projectUpdates) ?? true;
        pushEnabled = dailyReports || issueUpdates || lowStockAlerts || projectUpdates;
        _isLoading = false;
      });
    } catch (e) {
      // Cache failed, will load from server
      debugPrint('Failed to load cached preferences: $e');
    }
  }

  /// Sync with server and update cache
  Future<void> _syncWithServer() async {
    if (_isSyncing) return;
    _isSyncing = true;

    try {
      final api = context.read<AppState>().apiService;
      final serverPrefs = await api.getNotificationPreferences();
      if (!mounted) return;
      
      final newDailyReports = serverPrefs['push_daily_reports'] == true;
      final newIssueUpdates = serverPrefs['push_issue_assigned'] == true;
      final newLowStockAlerts = serverPrefs['push_low_stock'] == true;
      final newProjectUpdates = serverPrefs['push_budget_alerts'] == true;

      // Update UI if server values differ
      setState(() {
        dailyReports = newDailyReports;
        issueUpdates = newIssueUpdates;
        lowStockAlerts = newLowStockAlerts;
        projectUpdates = newProjectUpdates;
        pushEnabled = dailyReports || issueUpdates || lowStockAlerts || projectUpdates;
      });

      // Save to cache
      await _saveToCache();
    } catch (e) {
      // Server sync failed - using cached values is fine
      debugPrint('Server sync failed, using cached values: $e');
    } finally {
      _isSyncing = false;
    }
  }

  /// Save current preferences to local cache
  Future<void> _saveToCache() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(_PrefKeys.dailyReports, dailyReports);
      await prefs.setBool(_PrefKeys.issueUpdates, issueUpdates);
      await prefs.setBool(_PrefKeys.lowStockAlerts, lowStockAlerts);
      await prefs.setBool(_PrefKeys.projectUpdates, projectUpdates);
      await prefs.setInt(_PrefKeys.lastSync, DateTime.now().millisecondsSinceEpoch);
    } catch (e) {
      debugPrint('Failed to cache preferences: $e');
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
    // Get dependencies before any async gap
    final api = context.read<AppState>().apiService;
    final messenger = ScaffoldMessenger.of(context);
    final errorText = AppLocalizations.of(context).errorSavingSettings;

    // Save to cache immediately for responsiveness
    await _saveToCache();

    // Then sync to server
    final prevPushEnabled = pushEnabled;
    final prevDailyReports = dailyReports;
    final prevIssueUpdates = issueUpdates;
    final prevLowStockAlerts = lowStockAlerts;
    final prevProjectUpdates = projectUpdates;
    
    try {
      await api.updateNotificationPreferences({
        'push_daily_reports': dailyReports,
        'push_issue_assigned': issueUpdates,
        'push_low_stock': lowStockAlerts,
        'push_budget_alerts': projectUpdates,
      });
    } catch (e) {
      if (!mounted) return;
      // Revert UI and cache on failure
      setState(() {
        pushEnabled = prevPushEnabled;
        dailyReports = prevDailyReports;
        issueUpdates = prevIssueUpdates;
        lowStockAlerts = prevLowStockAlerts;
        projectUpdates = prevProjectUpdates;
      });
      await _saveToCache(); // Revert cache too
      messenger.showSnackBar(
        SnackBar(
          content: Text(errorText),
          backgroundColor: Colors.red,
        ),
      );
    }
  }
}
