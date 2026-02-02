import 'dart:io' show Platform;
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  // API_URL must be provided via --dart-define=API_URL=https://your-api.com
  // In debug mode, falls back to platform-appropriate localhost
  static const String _envUrl = String.fromEnvironment('API_URL');
  
  static String get baseUrl {
    if (_envUrl.isNotEmpty) {
      return _envUrl;
    }
    
    // Debug-only fallbacks for local development
    if (kDebugMode) {
      // Android emulator uses 10.0.2.2 to reach host machine
      // iOS simulator and physical devices use localhost/127.0.0.1
      if (!kIsWeb && Platform.isAndroid) {
        return 'http://10.0.2.2:8000';
      }
      return 'http://127.0.0.1:8000';
    }
    
    // Release mode requires explicit API_URL
    return '';
  }

  static void validateBaseUrl() {
    if (kReleaseMode) {
      if (baseUrl.isEmpty) {
        throw StateError(
          'API_URL must be provided via --dart-define for release builds. '
          'Example: --dart-define=API_URL=https://api.example.com',
        );
      }
      final uri = Uri.tryParse(baseUrl);
      if (uri == null || uri.scheme != 'https') {
        throw StateError(
          'API_URL must use HTTPS in release builds. '
          'Current value: $baseUrl',
        );
      }
    } else if (kDebugMode && baseUrl.isNotEmpty) {
      debugPrint('ApiService: Using baseUrl=$baseUrl');
    }
  }
  
  final Dio _dio = Dio();
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();
  String? _token;

  // Getter for token (used by AppState)
  String? get token => _token;

  ApiService() {
    // Validate baseUrl before using it - throws in release if invalid
    validateBaseUrl();
    
    _dio.options.baseUrl = baseUrl;
    _dio.options.connectTimeout = const Duration(seconds: 30);
    _dio.options.receiveTimeout = const Duration(seconds: 30);
    
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          if (_token != null) {
            options.headers['Authorization'] = 'Bearer $_token';
          }
          return handler.next(options);
        },
        onError: (error, handler) {
          debugPrint('API Error: ${error.message}');
          return handler.next(error);
        },
      ),
    );
  }

  void dispose() {
    _dio.close(force: true);
  }

  Future<void> loadToken() async {
    _token = await _secureStorage.read(key: 'auth_token');
  }

  Future<bool> login(String email, String password) async {
    try {
      final response = await _dio.post(
        '/api/auth/login',
        data: {
          'username': email,
          'password': password,
        },
        options: Options(
          contentType: Headers.formUrlEncodedContentType,
        ),
      );

      final accessToken = response.data['access_token'];
      if (accessToken == null) {
        debugPrint('Login error: access_token missing from response');
        return false;
      }
      if (accessToken is! String) {
        debugPrint('Login error: access_token is not a String (got ${accessToken.runtimeType})');
        return false;
      }
      _token = accessToken;
      
      await _secureStorage.write(key: 'auth_token', value: _token!);
      
      return true;
    } catch (e) {
      debugPrint('Login error: $e');
      return false;
    }
  }

  Future<Map<String, dynamic>?> getCurrentUser() async {
    try {
      final response = await _dio.get('/api/users/me');
      return response.data;
    } catch (e) {
      debugPrint('Get user error: $e');
      return null;
    }
  }

  Future<List<dynamic>> getProjects() async {
    try {
      final response = await _dio.get('/api/projects/');
      return response.data;
    } catch (e) {
      debugPrint('Get projects error: $e');
      return [];
    }
  }

  Future<List<dynamic>> getWarehouses() async {
    try {
      final response = await _dio.get('/api/warehouses/');
      return response.data;
    } catch (e) {
      debugPrint('Get warehouses error: $e');
      return [];
    }
  }

  Future<List<dynamic>> getMaterials() async {
    try {
      final response = await _dio.get('/api/materials/');
      return response.data;
    } catch (e) {
      debugPrint('Get materials error: $e');
      return [];
    }
  }

  Future<Map<String, dynamic>?> getMaterialBySku(String sku) async {
    try {
      final materials = await getMaterials();
      return materials.firstWhere(
        (m) => m['sku'] == sku,
        orElse: () => null,
      );
    } catch (e) {
      debugPrint('Get material by SKU error: $e');
      return null;
    }
  }

  /// Updates a material's information
  Future<Map<String, dynamic>?> updateMaterial({
    required int materialId,
    String? name,
    String? category,
    String? unit,
    num? cost,
    int? minStock,
  }) async {
    try {
      final data = <String, dynamic>{};
      if (name != null) data['name'] = name;
      if (category != null) data['category'] = category;
      if (unit != null) data['unit'] = unit;
      if (cost != null) data['cost'] = cost;
      if (minStock != null) data['min_stock'] = minStock;

      final response = await _dio.put(
        '/api/materials/$materialId',
        data: data,
      );
      return response.data as Map<String, dynamic>?;
    } catch (e) {
      debugPrint('Update material error: $e');
      return null;
    }
  }

  Future<bool> addStockTransaction({
    required int warehouseId,
    required int materialId,
    required String transactionType,
    required int quantity,
    String? notes,
  }) async {
    try {
      await _dio.post(
        '/api/inventory/transaction',
        data: {
          'warehouse_id': warehouseId,
          'material_id': materialId,
          'transaction_type': transactionType,
          'quantity': quantity,
          'notes': notes,
        },
      );
      return true;
    } catch (e) {
      debugPrint('Add transaction error: $e');
      return false;
    }
  }

  Future<List<dynamic>> getWarehouseInventory(int warehouseId) async {
    try {
      final response = await _dio.get('/api/inventory/warehouse/$warehouseId');
      return response.data;
    } catch (e) {
      debugPrint('Get inventory error: $e');
      return [];
    }
  }

  Future<String?> uploadDocument({
    required String filePath,
    required String fileName,
    required String fileType,
    int? projectId,
    String? description,
  }) async {
    try {
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(filePath, filename: fileName),
        'title': fileName,
        'file_type': fileType,
        if (projectId != null) 'project_id': projectId,
        if (description != null) 'description': description,
      });

      final response = await _dio.post(
        '/api/documents/',
        data: formData,
      );

      return response.data['id'].toString();
    } catch (e) {
      debugPrint('Upload document error: $e');
      return null;
    }
  }

  Future<void> logout() async {
    _token = null;
    await _secureStorage.delete(key: 'auth_token');
  }

  Future<Map<String, dynamic>> handleQrScan(Map<String, dynamic> payload) async {
    try {
      final response = await _dio.post('/api/inventory/scan', data: payload);
      return Map<String, dynamic>.from(response.data as Map);
    } catch (e) {
      debugPrint('QR scan error: $e');
      rethrow;
    }
  }

  Future<String> getMaterialQr(int materialId) async {
    try {
      final response = await _dio.get('/api/materials/$materialId/qr');
      final data = Map<String, dynamic>.from(response.data as Map);
      return data['qr_code'] as String;
    } catch (e) {
      debugPrint('Get material QR error: $e');
      rethrow;
    }
  }

  Future<void> registerDeviceToken({
    required String token,
    required String deviceType,
    String? deviceName,
  }) async {
    try {
      await _dio.post('/api/notifications/register-device', data: {
        'token': token,
        'device_type': deviceType,
        'device_name': deviceName,
      });
    } catch (e) {
      debugPrint('Register device token error: $e');
      rethrow;
    }
  }

  Future<void> unregisterDeviceToken(String token) async {
    try {
      await _dio.delete('/api/notifications/unregister-device/$token');
    } catch (e) {
      debugPrint('Unregister device token error: $e');
      rethrow;
    }
  }

  Future<Map<String, dynamic>> getNotificationPreferences() async {
    try {
      final response = await _dio.get('/api/notifications/preferences');
      return Map<String, dynamic>.from(response.data as Map);
    } catch (e) {
      debugPrint('Get notification preferences error: $e');
      rethrow;
    }
  }

  Future<Map<String, dynamic>> updateNotificationPreferences(
    Map<String, dynamic> payload,
  ) async {
    try {
      final response = await _dio.put('/api/notifications/preferences', data: payload);
      return Map<String, dynamic>.from(response.data as Map);
    } catch (e) {
      debugPrint('Update notification preferences error: $e');
      rethrow;
    }
  }

  /// Syncs a single worker attendance record to the backend
  /// Returns true if sync was successful
  Future<bool> syncWorkerAttendance({
    required int workerId,
    required String action,
    required DateTime timestamp,
    String? notes,
  }) async {
    try {
      await _dio.post(
        '/api/workers/$workerId/attendance',
        data: {
          'action': action,
          'timestamp': timestamp.toIso8601String(),
          if (notes != null) 'notes': notes,
        },
      );
      return true;
    } catch (e) {
      debugPrint('Sync worker attendance error: $e');
      return false;
    }
  }

  /// Syncs multiple worker attendance records in bulk
  /// Returns a map of local_id -> sync_status
  Future<Map<int, bool>> bulkSyncWorkerAttendance(
    List<Map<String, dynamic>> records,
  ) async {
    final results = <int, bool>{};
    
    try {
      // Try bulk sync first
      final response = await _dio.post(
        '/api/workers/attendance/bulk-sync',
        data: {
          'records': records.map((r) => {
            'worker_id': r['worker_id'],
            'action': r['action'],
            'timestamp': r['timestamp'],
            if (r['notes'] != null) 'notes': r['notes'],
          }).toList(),
        },
      );
      
      // Parse bulk response
      final data = response.data as Map<String, dynamic>;
      final syncedIds = (data['synced_ids'] as List?)?.cast<int>() ?? [];
      
      for (var i = 0; i < records.length; i++) {
        final localId = records[i]['id'] as int;
        results[localId] = syncedIds.contains(i);
      }
    } catch (e) {
      debugPrint('Bulk sync failed, falling back to individual sync: $e');
      
      // Fallback to individual sync
      for (final record in records) {
        final localId = record['id'] as int;
        final success = await syncWorkerAttendance(
          workerId: record['worker_id'] as int,
          action: record['action'] as String,
          timestamp: DateTime.parse(record['timestamp'] as String),
          notes: record['notes'] as String?,
        );
        results[localId] = success;
      }
    }
    
    return results;
  }
}
