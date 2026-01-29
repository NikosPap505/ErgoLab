import 'package:flutter/foundation.dart';
import '../services/api_service.dart';

class AppState with ChangeNotifier {
  final ApiService _apiService = ApiService();
  
  bool _isLoggedIn = false;
  Map<String, dynamic>? _currentUser;
  List<dynamic> _projects = [];
  List<dynamic> _warehouses = [];
  List<dynamic> _materials = [];
  
  int? _selectedProjectId;
  int? _selectedWarehouseId;
  
  bool _isLoading = false;

  // Getters
  bool get isLoggedIn => _isLoggedIn;
  Map<String, dynamic>? get currentUser => _currentUser;
  List<dynamic> get projects => _projects;
  List<dynamic> get warehouses => _warehouses;
  List<dynamic> get materials => _materials;
  int? get selectedProjectId => _selectedProjectId;
  int? get selectedWarehouseId => _selectedWarehouseId;
  bool get isLoading => _isLoading;

  ApiService get apiService => _apiService;

  Future<void> initialize() async {
    await _apiService.loadToken();
    if (_apiService.token != null) {
      final user = await _apiService.getCurrentUser();
      if (user != null) {
        _currentUser = user;
        _isLoggedIn = true;
        await loadData();
        notifyListeners();
      }
    }
  }

  Future<bool> login(String email, String password) async {
    _isLoading = true;
    notifyListeners();

    final success = await _apiService.login(email, password);
    
    if (success) {
      _currentUser = await _apiService.getCurrentUser();
      _isLoggedIn = true;
      await loadData();
    }

    _isLoading = false;
    notifyListeners();
    return success;
  }

  Future<void> loadData() async {
    _projects = await _apiService.getProjects();
    _warehouses = await _apiService.getWarehouses();
    _materials = await _apiService.getMaterials();
    notifyListeners();
  }

  void selectProject(int projectId) {
    _selectedProjectId = projectId;
    // Auto-select project warehouse if exists
    final projectWarehouse = _warehouses.firstWhere(
      (w) => w['project_id'] == projectId,
      orElse: () => null,
    );
    if (projectWarehouse != null) {
      _selectedWarehouseId = projectWarehouse['id'];
    }
    notifyListeners();
  }

  void selectWarehouse(int warehouseId) {
    _selectedWarehouseId = warehouseId;
    notifyListeners();
  }

  Map<String, dynamic>? getMaterialById(int id) {
    try {
      return _materials.firstWhere((m) => m['id'] == id);
    } catch (e) {
      return null;
    }
  }

  Future<void> logout() async {
    await _apiService.logout();
    _isLoggedIn = false;
    _currentUser = null;
    _projects = [];
    _warehouses = [];
    _materials = [];
    _selectedProjectId = null;
    _selectedWarehouseId = null;
    notifyListeners();
  }
}
