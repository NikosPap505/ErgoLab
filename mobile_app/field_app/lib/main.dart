// lib/main.dart - COMPLETE FIX
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import 'package:provider/provider.dart';
import 'providers/app_state.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/scanner_screen.dart';
import 'screens/add_stock_screen.dart';
import 'screens/inventory_screen.dart';
import 'screens/capture_screen.dart';
import 'screens/qr_scanner_screen.dart';
import 'services/notification_service.dart';
import 'screens/notification_settings_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  FlutterError.onError = FirebaseCrashlytics.instance.recordFlutterFatalError;
  PlatformDispatcher.instance.onError = (error, stack) {
    FirebaseCrashlytics.instance.recordError(error, stack, fatal: true);
    return true;
  };
  unawaited(NotificationService().initialize());
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
                  '/qr-scanner': (context) => const QRScannerScreen(),
                  '/notification-settings': (context) => const NotificationSettingsScreen(),
                  '/add-stock': (context) {
                    final material = ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>?;
                    return AddStockScreen(material: material);
                  },
                  '/inventory': (context) => const InventoryScreen(),
                  '/capture': (context) => const CaptureScreen(),
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
