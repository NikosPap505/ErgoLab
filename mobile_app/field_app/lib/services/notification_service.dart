import 'dart:convert';
import 'dart:io';

import 'package:device_info_plus/device_info_plus.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

import 'api_service.dart';

@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  debugPrint('Background message: ${message.messageId}');
}

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  static final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final FirebaseMessaging _fcm = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications =
      FlutterLocalNotificationsPlugin();
  final ApiService _apiService = ApiService();
  bool _notificationsEnabled = false;

  bool get notificationsEnabled => _notificationsEnabled;

  Future<void> initialize() async {
    await Firebase.initializeApp();

    final settings = await _fcm.requestPermission(
      alert: true,
      badge: true,
      sound: true,
      provisional: false,
    );

    if (settings.authorizationStatus != AuthorizationStatus.authorized) {
      _notificationsEnabled = false;
      debugPrint('Notification permission denied');
      WidgetsBinding.instance.addPostFrameCallback((_) => _showPermissionDeniedMessage());
      return;
    }

    _notificationsEnabled = true;

    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosInit = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );

    const initSettings = InitializationSettings(
      android: androidInit,
      iOS: iosInit,
    );

    await _localNotifications.initialize(
      initSettings,
      onDidReceiveNotificationResponse: _onNotificationTapped,
    );

    await _createNotificationChannels();

    await _apiService.loadToken();
    final token = await _fcm.getToken();
    if (token != null) {
      await _registerToken(token);
    }

    _fcm.onTokenRefresh.listen(_registerToken);

    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
    FirebaseMessaging.onMessageOpenedApp.listen(_handleMessageOpenedApp);
    FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);

    final initialMessage = await _fcm.getInitialMessage();
    if (initialMessage != null) {
      _handleMessageOpenedApp(initialMessage);
    }
  }

  Future<void> _createNotificationChannels() async {
    const defaultChannel = AndroidNotificationChannel(
      'default',
      'Γενικές Ειδοποιήσεις',
      description: 'Γενικές ειδοποιήσεις εφαρμογής',
      importance: Importance.high,
    );

    const criticalChannel = AndroidNotificationChannel(
      'critical_alerts',
      'Κρίσιμες Ειδοποιήσεις',
      description: 'Κρίσιμα προβλήματα που απαιτούν άμεση προσοχή',
      importance: Importance.max,
      playSound: true,
      enableVibration: true,
      enableLights: true,
      ledColor: Color.fromARGB(255, 255, 0, 0),
    );

    await _localNotifications
        .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(defaultChannel);

    await _localNotifications
        .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(criticalChannel);
  }

  Future<void> _registerToken(String token) async {
    try {
      final deviceType = Platform.isIOS
          ? 'ios'
          : Platform.isAndroid
              ? 'android'
              : Platform.operatingSystem;
      final deviceName = await _getDeviceName();
      await _apiService.registerDeviceToken(
        token: token,
        deviceType: deviceType,
        deviceName: deviceName,
      );
      debugPrint('FCM token registered');
    } catch (e) {
      debugPrint('Error registering FCM token: $e');
    }
  }

  Future<String> _getDeviceName() async {
    final deviceInfo = DeviceInfoPlugin();
    try {
      if (Platform.isAndroid) {
        final info = await deviceInfo.androidInfo;
        final manufacturer = info.manufacturer;
        final model = info.model;
        return '$manufacturer $model'.trim();
      }
      if (Platform.isIOS) {
        final info = await deviceInfo.iosInfo;
        // Use user-friendly name: user-set name or localized model
        final name = info.name;
        if (name.isNotEmpty) {
          return name; // e.g., "John's iPhone"
        }
        return info.localizedModel; // e.g., "iPhone"
      }
    } catch (e) {
      debugPrint('Device info error: $e');
    }
    return Platform.localHostname;
  }

  void _handleForegroundMessage(RemoteMessage message) {
    debugPrint('Foreground message: ${message.messageId}');
    _showLocalNotification(message);
  }

  void _handleMessageOpenedApp(RemoteMessage message) {
    debugPrint('Message opened app: ${message.messageId}');
    _navigateToScreen(message.data);
  }

  Future<void> _showLocalNotification(RemoteMessage message) async {
    final notification = message.notification;
    final data = message.data;

    if (notification == null) return;

    String channelId = 'default';
    if (data['type'] == 'critical_issue') {
      channelId = 'critical_alerts';
    }

    final androidDetails = AndroidNotificationDetails(
      channelId,
      channelId == 'critical_alerts' ? 'Κρίσιμες Ειδοποιήσεις' : 'Γενικές Ειδοποιήσεις',
      channelDescription: notification.body ?? '',
      importance: channelId == 'critical_alerts' ? Importance.max : Importance.high,
      priority: channelId == 'critical_alerts' ? Priority.max : Priority.high,
      color: const Color(0xFF667EEA),
      playSound: true,
      enableVibration: true,
    );

    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );

    final details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );

    await _localNotifications.show(
      message.hashCode,
      notification.title,
      notification.body,
      details,
      payload: json.encode(data),
    );
  }

  void _onNotificationTapped(NotificationResponse response) {
    if (response.payload == null) return;
    final data = json.decode(response.payload!);
    _navigateToScreen(Map<String, dynamic>.from(data));
  }

  void _navigateToScreen(Map<String, dynamic> data, {int attempts = 0}) {
    const maxRetries = 3;
    final route = data['screen']?.toString();
    final navigator = navigatorKey.currentState;

    if (navigator == null) {
      if (attempts >= maxRetries) {
        debugPrint('Navigate: navigator not ready after $maxRetries attempts');
        return;
      }
      WidgetsBinding.instance.addPostFrameCallback(
        (_) => _navigateToScreen(data, attempts: attempts + 1),
      );
      return;
    }

    if (route == null || route.isEmpty) {
      debugPrint('Navigate: missing route for data: $data');
      return;
    }

    navigator.pushNamed(route, arguments: data);
  }

  void _showPermissionDeniedMessage() {
    final context = navigatorKey.currentContext;
    if (context == null) return;

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Οι ειδοποιήσεις είναι απενεργοποιημένες. Ενεργοποιήστε τις από τις Ρυθμίσεις.'),
        duration: Duration(seconds: 3),
      ),
    );
  }

  Future<void> unregister() async {
    final token = await _fcm.getToken();
    if (token == null) return;

    try {
      await _apiService.unregisterDeviceToken(token);
      debugPrint('FCM token unregistered');
    } catch (e) {
      debugPrint('Error unregistering FCM token: $e');
    }
  }
}
