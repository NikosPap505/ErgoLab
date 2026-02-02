import 'dart:convert';

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
  factory NotificationService() => _instance;
  NotificationService._internal();

  final FirebaseMessaging _fcm = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications =
      FlutterLocalNotificationsPlugin();
  final ApiService _apiService = ApiService();

  Future<void> initialize() async {
    await Firebase.initializeApp();

    final settings = await _fcm.requestPermission(
      alert: true,
      badge: true,
      sound: true,
      provisional: false,
    );

    if (settings.authorizationStatus != AuthorizationStatus.authorized) {
      debugPrint('Notification permission denied');
      return;
    }

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
      await _apiService.registerDeviceToken(
        token: token,
        deviceType: 'android',
        deviceName: 'Android Device',
      );
      debugPrint('FCM token registered');
    } catch (e) {
      debugPrint('Error registering FCM token: $e');
    }
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

  void _navigateToScreen(Map<String, dynamic> data) {
    debugPrint('Navigate to: ${data['screen']} with data: $data');
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
