// lib/main.dart - COMPLETE FIX
import 'dart:async';
import 'dart:ui';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import 'package:provider/provider.dart';
import 'l10n/app_localizations.dart';
import 'providers/app_state.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/scanner_screen.dart';
import 'screens/add_stock_screen.dart';
import 'screens/inventory_screen.dart';
import 'screens/capture_screen.dart';
import 'screens/qr_scanner_screen.dart';
import 'services/api_service.dart';
import 'services/notification_service.dart';
import 'screens/notification_settings_screen.dart';
import 'screens/scan_history_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Validate API URL configuration before app starts
  ApiService.validateBaseUrl();
  
  await Firebase.initializeApp();
  
  // Set up global error handlers
  FlutterError.onError = (details) {
    FirebaseCrashlytics.instance.recordFlutterFatalError(details);
  };
  PlatformDispatcher.instance.onError = (error, stack) {
    FirebaseCrashlytics.instance.recordError(error, stack, fatal: true);
    return true;
  };
  
  // Custom error widget for release mode - shows user-friendly error
  if (kReleaseMode) {
    ErrorWidget.builder = (FlutterErrorDetails details) {
      return const MaterialApp(
        home: Scaffold(
          body: SafeArea(
            child: Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.error_outline, size: 64, color: Colors.red),
                    SizedBox(height: 16),
                    Text(
                      'Παρουσιάστηκε σφάλμα',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                      textAlign: TextAlign.center,
                    ),
                    SizedBox(height: 8),
                    Text(
                      'Παρακαλώ επανεκκινήστε την εφαρμογή.',
                      style: TextStyle(color: Colors.grey),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      );
    };
  }
  
  unawaited(NotificationService().initialize().catchError((e, stack) {
    FirebaseCrashlytics.instance.recordError(e, stack, fatal: false);
  }));
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AppState()..initialize(),
      child: Consumer<AppState>(
        builder: (context, appState, child) {
          // Provide nested providers for connectivity and sync services
          return MultiProvider(
            providers: [
              ChangeNotifierProvider.value(value: appState.connectivityService),
              ChangeNotifierProvider.value(value: appState.syncService),
            ],
            child: MaterialApp(
              title: 'ErgoLab Field',
              debugShowCheckedModeBanner: false,
              navigatorKey: NotificationService.navigatorKey,
              localizationsDelegates: const [
                AppLocalizations.delegate,
                GlobalMaterialLocalizations.delegate,
                GlobalWidgetsLocalizations.delegate,
                GlobalCupertinoLocalizations.delegate,
              ],
              supportedLocales: AppLocalizations.supportedLocales,
              // Let Flutter auto-detect device locale; falls back to first
              // supported locale (Greek) if device locale isn't supported
              localeResolutionCallback: (deviceLocale, supportedLocales) {
                if (deviceLocale != null) {
                  for (final locale in supportedLocales) {
                    if (locale.languageCode == deviceLocale.languageCode) {
                      return locale;
                    }
                  }
                }
                return supportedLocales.first; // Default to Greek (el)
              },
              theme: ThemeData(
                colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
                useMaterial3: true,
              ),
              initialRoute: '/login',
              onGenerateRoute: (settings) {
                final routes = <String, WidgetBuilder>{
                  '/login': (context) => const LoginScreen(),
                  '/home': (context) => const HomeScreen(),
                  '/scanner': (context) => const ScannerScreen(),
                  '/add-stock': (context) {
                    final material = settings.arguments as Map<String, dynamic>?;
                    return AddStockScreen(material: material);
                  },
                  '/inventory': (context) => const InventoryScreen(),
                  '/capture': (context) => const CaptureScreen(),
                  '/qr-scanner': (context) => const QRScannerScreen(),
                  '/scan-history': (context) => const ScanHistoryScreen(),
                  '/notification-settings': (context) => const NotificationSettingsScreen(),
                };

                final name = settings.name ?? '/login';
                final isLoggedIn = appState.isLoggedIn;

                if (!isLoggedIn && name != '/login') {
                  return MaterialPageRoute(
                    builder: routes['/login']!,
                    settings: const RouteSettings(name: '/login'),
                  );
                }

                final builder = routes[name] ?? routes['/login']!;
                return MaterialPageRoute(builder: builder, settings: settings);
              },
            ),
          );
        },
      ),
    );
  }
}
