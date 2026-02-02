import 'package:flutter/material.dart';

/// Simple localization class for the ErgoLab Field App.
/// Currently supports Greek (default) with fallback English.
class AppLocalizations {
  AppLocalizations(this.locale);

  final Locale locale;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations) ??
        AppLocalizations(const Locale('el'));
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  static const List<Locale> supportedLocales = [
    Locale('el'), // Greek
    Locale('en'), // English
  ];

  /// Default locale for fallback when key is missing
  static const String _defaultLocale = 'el';

  /// Null-safe lookup with fallback to default locale, then to key name
  String _get(String key) {
    return _localizedValues[locale.languageCode]?[key] ??
        _localizedValues[_defaultLocale]?[key] ??
        key;
  }

  // Notification Settings Screen
  String get notificationSettings => _get('notificationSettings');
  String get errorLoadingSettings => _get('errorLoadingSettings');
  String get errorSavingSettings => _get('errorSavingSettings');
  String get pushNotifications => _get('pushNotifications');
  String get pushNotificationsSubtitle => _get('pushNotificationsSubtitle');
  String get notificationTypes => _get('notificationTypes');
  String get dailyReports => _get('dailyReports');
  String get dailyReportsSubtitle => _get('dailyReportsSubtitle');
  String get issues => _get('issues');
  String get issuesSubtitle => _get('issuesSubtitle');
  String get lowStock => _get('lowStock');
  String get lowStockSubtitle => _get('lowStockSubtitle');
  String get projectUpdates => _get('projectUpdates');
  String get projectUpdatesSubtitle => _get('projectUpdatesSubtitle');

  static const Map<String, Map<String, String>> _localizedValues = {
    'el': {
      'notificationSettings': 'Ρυθμίσεις Ειδοποιήσεων',
      'errorLoadingSettings': 'Αποτυχία φόρτωσης ρυθμίσεων.',
      'errorSavingSettings': 'Αποτυχία αποθήκευσης ρυθμίσεων.',
      'pushNotifications': 'Ειδοποιήσεις Push',
      'pushNotificationsSubtitle': 'Λήψη ειδοποιήσεων στη συσκευή',
      'notificationTypes': 'Τύποι Ειδοποιήσεων',
      'dailyReports': 'Ημερήσιες Αναφορές',
      'dailyReportsSubtitle': 'Ειδοποιήσεις για νέες αναφορές',
      'issues': 'Θέματα',
      'issuesSubtitle': 'Ενημερώσεις για προβλήματα',
      'lowStock': 'Χαμηλά Αποθέματα',
      'lowStockSubtitle': 'Ειδοποιήσεις για χαμηλά αποθέματα',
      'projectUpdates': 'Ενημερώσεις Έργων/Οικονομικά',
      'projectUpdatesSubtitle': 'Ειδοποιήσεις για budget & έργα',
    },
    'en': {
      'notificationSettings': 'Notification Settings',
      'errorLoadingSettings': 'Failed to load settings.',
      'errorSavingSettings': 'Failed to save settings.',
      'pushNotifications': 'Push Notifications',
      'pushNotificationsSubtitle': 'Receive notifications on device',
      'notificationTypes': 'Notification Types',
      'dailyReports': 'Daily Reports',
      'dailyReportsSubtitle': 'Notifications for new reports',
      'issues': 'Issues',
      'issuesSubtitle': 'Updates for issues',
      'lowStock': 'Low Stock',
      'lowStockSubtitle': 'Notifications for low stock alerts',
      'projectUpdates': 'Project Updates / Financials',
      'projectUpdatesSubtitle': 'Notifications for budget & projects',
    },
  };
}

class _AppLocalizationsDelegate extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  /// Single source of truth for supported language codes
  static const Set<String> supportedLanguageCodes = {'el', 'en'};

  @override
  bool isSupported(Locale locale) {
    return supportedLanguageCodes.contains(locale.languageCode);
  }

  @override
  Future<AppLocalizations> load(Locale locale) async {
    // Normalize to supported locale, fall back to default if unsupported
    final languageCode = supportedLanguageCodes.contains(locale.languageCode)
        ? locale.languageCode
        : AppLocalizations._defaultLocale;
    return AppLocalizations(Locale(languageCode));
  }

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}
