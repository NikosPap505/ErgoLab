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

  // Scan History Screen
  String get scanHistory => _get('scanHistory');

  // Common actions
  String get close => _get('close');
  String get cancel => _get('cancel');
  String get save => _get('save');
  String get delete => _get('delete');
  String get edit => _get('edit');
  String get retry => _get('retry');
  String get refresh => _get('refresh');
  String get logout => _get('logout');

  // QR Scanner
  String get scanQrCode => _get('scanQrCode');
  String get scanError => _get('scanError');
  String get unsupportedQrCode => _get('unsupportedQrCode');
  String get cameraPermissionDenied => _get('cameraPermissionDenied');

  // Materials
  String get material => _get('material');
  String get materials => _get('materials');
  String get editMaterial => _get('editMaterial');
  String get materialSaved => _get('materialSaved');
  String get category => _get('category');
  String get unit => _get('unit');
  String get cost => _get('cost');
  String get minStock => _get('minStock');
  String get availableStock => _get('availableStock');
  String get noStockAvailable => _get('noStockAvailable');
  String get recordTransaction => _get('recordTransaction');

  // Workers
  String get worker => _get('worker');
  String get checkIn => _get('checkIn');
  String get checkOut => _get('checkOut');
  String get checkedIn => _get('checkedIn');
  String get checkedOut => _get('checkedOut');
  String get recentHistory => _get('recentHistory');

  // Errors
  String get errorOccurred => _get('errorOccurred');
  String get networkError => _get('networkError');
  String get offlineMode => _get('offlineMode');

  // Login Screen
  String get login => _get('login');
  String get email => _get('email');
  String get password => _get('password');
  String get enterEmailAndPassword => _get('enterEmailAndPassword');
  String get invalidEmail => _get('invalidEmail');
  String get loginError => _get('loginError');
  String get showPassword => _get('showPassword');
  String get hidePassword => _get('hidePassword');

  // Inventory Screen
  String get inventory => _get('inventory');
  String get warehouseInventory => _get('warehouseInventory');
  String get selectWarehouse => _get('selectWarehouse');
  String get stockDepleted => _get('stockDepleted');
  String get stockLow => _get('stockLow');
  String get stockGood => _get('stockGood');
  String get itemsCount => _get('itemsCount');
  String get offlineData => _get('offlineData');

  // Add Stock Screen
  String get addStock => _get('addStock');
  String get stockIn => _get('stockIn');
  String get stockOut => _get('stockOut');
  String get quantity => _get('quantity');
  String get notes => _get('notes');
  String get insufficientStock => _get('insufficientStock');
  String get transactionSuccess => _get('transactionSuccess');
  String get transactionFailed => _get('transactionFailed');

  // Material Edit Sheet
  String get nameRequired => _get('nameRequired');
  String get costNegativeError => _get('costNegativeError');
  String get minStockNegativeError => _get('minStockNegativeError');
  String get materialUpdated => _get('materialUpdated');
  String get saveFailed => _get('saveFailed');
  String get saving => _get('saving');
  String get costLabel => _get('costLabel');

  // Worker Detail Sheet
  String get role => _get('role');
  String get phone => _get('phone');
  String get localStorageNote => _get('localStorageNote');

  // Scan History Screen
  String get loadingError => _get('loadingError');
  String get deleted => _get('deleted');
  String get deleteHistory => _get('deleteHistory');
  String get deleteHistoryConfirm => _get('deleteHistoryConfirm');
  String get historyDeleted => _get('historyDeleted');
  String get deleteAll => _get('deleteAll');
  String get noScanHistory => _get('noScanHistory');
  String get scansWillAppearHere => _get('scansWillAppearHere');
  String get error => _get('error');
  String get scanDetails => _get('scanDetails');
  String get date => _get('date');
  String get type => _get('type');
  String get result => _get('result');
  String get name => _get('name');
  String get qrBarcodeValue => _get('qrBarcodeValue');
  String get data => _get('data');
  String get unknownDate => _get('unknownDate');

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
      'scanHistory': 'Ιστορικό Σαρώσεων',
      // Common actions
      'close': 'Κλείσιμο',
      'cancel': 'Ακύρωση',
      'save': 'Αποθήκευση',
      'delete': 'Διαγραφή',
      'edit': 'Επεξεργασία',
      'retry': 'Επανάληψη',
      'refresh': 'Ανανέωση',
      'logout': 'Αποσύνδεση',
      // QR Scanner
      'scanQrCode': 'Σάρωση QR κωδικού',
      'scanError': 'Σφάλμα σάρωσης',
      'unsupportedQrCode': 'Μη υποστηριζόμενος κωδικός QR',
      'cameraPermissionDenied': 'Απορρίφθηκε η πρόσβαση στην κάμερα',
      // Materials
      'material': 'Υλικό',
      'materials': 'Υλικά',
      'editMaterial': 'Επεξεργασία Υλικού',
      'materialSaved': 'Το υλικό αποθηκεύτηκε',
      'category': 'Κατηγορία',
      'unit': 'Μονάδα',
      'cost': 'Κόστος',
      'minStock': 'Ελάχιστο απόθεμα',
      'availableStock': 'Διαθέσιμο απόθεμα',
      'noStockAvailable': 'Δεν υπάρχει διαθέσιμο απόθεμα',
      'recordTransaction': 'Καταγραφή συναλλαγής',
      // Workers
      'worker': 'Εργαζόμενος',
      'checkIn': 'Είσοδος',
      'checkOut': 'Έξοδος',
      'checkedIn': 'Εισήλθε',
      'checkedOut': 'Εξήλθε',
      'recentHistory': 'Πρόσφατο ιστορικό',
      // Errors
      'errorOccurred': 'Παρουσιάστηκε σφάλμα',
      'networkError': 'Σφάλμα δικτύου',
      'offlineMode': 'Λειτουργία εκτός σύνδεσης',
      // Login Screen
      'login': 'Σύνδεση',
      'email': 'Email',
      'password': 'Κωδικός',
      'enterEmailAndPassword': 'Συμπληρώστε email και κωδικό.',
      'invalidEmail': 'Μη έγκυρο email.',
      'loginError': 'Σφάλμα σύνδεσης. Ελέγξτε τα στοιχεία σας.',
      'showPassword': 'Εμφάνιση κωδικού',
      'hidePassword': 'Απόκρυψη κωδικού',
      // Inventory Screen
      'inventory': 'Απόθεμα',
      'warehouseInventory': 'Απόθεμα Αποθήκης',
      'selectWarehouse': 'Παρακαλώ επιλέξτε αποθήκη από την αρχική σελίδα',
      'stockDepleted': 'Εξαντλημένο',
      'stockLow': 'Χαμηλό',
      'stockGood': 'Καλό',
      'itemsCount': 'είδη υλικών',
      'offlineData': 'Offline mode - προβολή cached δεδομένων',
      // Add Stock Screen
      'addStock': 'Προσθήκη Αποθέματος',
      'stockIn': 'Εισαγωγή',
      'stockOut': 'Εξαγωγή',
      'quantity': 'Ποσότητα',
      'notes': 'Σημειώσεις',
      'insufficientStock': 'Μη επαρκές απόθεμα',
      'transactionSuccess': 'Η συναλλαγή καταχωρήθηκε!',
      'transactionFailed': 'Αποτυχία καταχώρησης συναλλαγής',
      // Material Edit Sheet
      'nameRequired': 'Το όνομα είναι υποχρεωτικό',
      'costNegativeError': 'Το κόστος δεν μπορεί να είναι αρνητικό',
      'minStockNegativeError': 'Το ελάχιστο απόθεμα δεν μπορεί να είναι αρνητικό',
      'materialUpdated': 'Το υλικό ενημερώθηκε επιτυχώς',
      'saveFailed': 'Αποτυχία αποθήκευσης',
      'saving': 'Αποθήκευση...',
      'costLabel': 'Κόστος (€)',
      // Worker Detail Sheet
      'role': 'Ρόλος',
      'phone': 'Τηλέφωνο',
      'localStorageNote': 'Οι εγγραφές αποθηκεύονται τοπικά και θα συγχρονιστούν όταν είναι διαθέσιμο.',
      // Scan History Screen
      'loadingError': 'Σφάλμα φόρτωσης',
      'deleted': 'Διαγράφηκε',
      'deleteHistory': 'Διαγραφή Ιστορικού',
      'deleteHistoryConfirm': 'Είστε σίγουροι ότι θέλετε να διαγράψετε όλο το ιστορικό σαρώσεων;',
      'historyDeleted': 'Το ιστορικό διαγράφηκε',
      'deleteAll': 'Διαγραφή όλων',
      'noScanHistory': 'Δεν υπάρχει ιστορικό σαρώσεων',
      'scansWillAppearHere': 'Οι σαρώσεις σας θα εμφανίζονται εδώ',
      'error': 'Σφάλμα',
      'scanDetails': 'Λεπτομέρειες Σάρωσης',
      'date': 'Ημερομηνία',
      'type': 'Τύπος',
      'result': 'Αποτέλεσμα',
      'name': 'Όνομα',
      'qrBarcodeValue': 'Τιμή QR/Barcode:',
      'data': 'Δεδομένα:',
      'unknownDate': 'Άγνωστη ημερομηνία',
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
      'scanHistory': 'Scan History',
      // Common actions
      'close': 'Close',
      'cancel': 'Cancel',
      'save': 'Save',
      'delete': 'Delete',
      'edit': 'Edit',
      'retry': 'Retry',
      'refresh': 'Refresh',
      'logout': 'Logout',
      // QR Scanner
      'scanQrCode': 'Scan QR Code',
      'scanError': 'Scan Error',
      'unsupportedQrCode': 'Unsupported QR code',
      'cameraPermissionDenied': 'Camera permission denied',
      // Materials
      'material': 'Material',
      'materials': 'Materials',
      'editMaterial': 'Edit Material',
      'materialSaved': 'Material saved',
      'category': 'Category',
      'unit': 'Unit',
      'cost': 'Cost',
      'minStock': 'Min Stock',
      'availableStock': 'Available stock',
      'noStockAvailable': 'No stock available',
      'recordTransaction': 'Record Transaction',
      // Workers
      'worker': 'Worker',
      'checkIn': 'Check In',
      'checkOut': 'Check Out',
      'checkedIn': 'Checked In',
      'checkedOut': 'Checked Out',
      'recentHistory': 'Recent History',
      // Errors
      'errorOccurred': 'An error occurred',
      'networkError': 'Network error',
      'offlineMode': 'Offline Mode',
      // Login Screen
      'login': 'Login',
      'email': 'Email',
      'password': 'Password',
      'enterEmailAndPassword': 'Please enter email and password.',
      'invalidEmail': 'Invalid email.',
      'loginError': 'Login error. Check your credentials.',
      'showPassword': 'Show password',
      'hidePassword': 'Hide password',
      // Inventory Screen
      'inventory': 'Inventory',
      'warehouseInventory': 'Warehouse Inventory',
      'selectWarehouse': 'Please select a warehouse from the home page',
      'stockDepleted': 'Depleted',
      'stockLow': 'Low',
      'stockGood': 'Good',
      'itemsCount': 'material items',
      'offlineData': 'Offline mode - viewing cached data',
      // Add Stock Screen
      'addStock': 'Add Stock',
      'stockIn': 'Stock In',
      'stockOut': 'Stock Out',
      'quantity': 'Quantity',
      'notes': 'Notes',
      'insufficientStock': 'Insufficient stock',
      'transactionSuccess': 'Transaction recorded!',
      'transactionFailed': 'Transaction failed',
      // Material Edit Sheet
      'nameRequired': 'Name is required',
      'costNegativeError': 'Cost cannot be negative',
      'minStockNegativeError': 'Min stock cannot be negative',
      'materialUpdated': 'Material updated successfully',
      'saveFailed': 'Save failed',
      'saving': 'Saving...',
      'costLabel': 'Cost (€)',
      // Worker Detail Sheet
      'role': 'Role',
      'phone': 'Phone',
      'localStorageNote': 'Records are stored locally and will sync when available.',
      // Scan History Screen
      'loadingError': 'Loading error',
      'deleted': 'Deleted',
      'deleteHistory': 'Delete History',
      'deleteHistoryConfirm': 'Are you sure you want to delete all scan history?',
      'historyDeleted': 'History deleted',
      'deleteAll': 'Delete all',
      'noScanHistory': 'No scan history',
      'scansWillAppearHere': 'Your scans will appear here',
      'error': 'Error',
      'scanDetails': 'Scan Details',
      'date': 'Date',
      'type': 'Type',
      'result': 'Result',
      'name': 'Name',
      'qrBarcodeValue': 'QR/Barcode value:',
      'data': 'Data:',
      'unknownDate': 'Unknown date',
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
