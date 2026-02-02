import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  static const String baseUrl = String.fromEnvironment(
    'API_URL',
    defaultValue: 'http://192.168.2.8:8000',
  );
  // For physical device: set --dart-define=API_URL=http://YOUR_LOCAL_IP:8000
  
  final Dio _dio = Dio();
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();
  String? _token;

  // Getter for token (used by AppState)
  String? get token => _token;

  ApiService() {
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

      _token = response.data['access_token'];
      
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
}
