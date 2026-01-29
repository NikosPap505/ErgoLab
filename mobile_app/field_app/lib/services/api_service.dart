import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String baseUrl = 'http://192.168.2.8:8000';
  // For physical device: 'http://YOUR_LOCAL_IP:8000'
  
  final Dio _dio = Dio();
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
          print('API Error: ${error.message}');
          return handler.next(error);
        },
      ),
    );
  }

  Future<void> loadToken() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString('auth_token');
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
      
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('auth_token', _token!);
      
      return true;
    } catch (e) {
      print('Login error: $e');
      return false;
    }
  }

  Future<Map<String, dynamic>?> getCurrentUser() async {
    try {
      final response = await _dio.get('/api/users/me');
      return response.data;
    } catch (e) {
      print('Get user error: $e');
      return null;
    }
  }

  Future<List<dynamic>> getProjects() async {
    try {
      final response = await _dio.get('/api/projects/');
      return response.data;
    } catch (e) {
      print('Get projects error: $e');
      return [];
    }
  }

  Future<List<dynamic>> getWarehouses() async {
    try {
      final response = await _dio.get('/api/warehouses/');
      return response.data;
    } catch (e) {
      print('Get warehouses error: $e');
      return [];
    }
  }

  Future<List<dynamic>> getMaterials() async {
    try {
      final response = await _dio.get('/api/materials/');
      return response.data;
    } catch (e) {
      print('Get materials error: $e');
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
      print('Get material by SKU error: $e');
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
      print('Add transaction error: $e');
      return false;
    }
  }

  Future<List<dynamic>> getWarehouseInventory(int warehouseId) async {
    try {
      final response = await _dio.get('/api/inventory/warehouse/$warehouseId');
      return response.data;
    } catch (e) {
      print('Get inventory error: $e');
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
      print('Upload document error: $e');
      return null;
    }
  }

  Future<void> logout() async {
    _token = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
  }
}
