import 'package:flutter/foundation.dart';
import '../services/api_service.dart';
import '../services/sync_service.dart';
import '../services/connectivity_service.dart';
import '../services/offline_database.dart';

class AppState with ChangeNotifier {
  final ApiService _apiService = ApiService();
  late final ConnectivityService _connectivityService;
  late final SyncService _syncService;
  
  bool _isLoggedIn = false;
  Map<String, dynamic>? _currentUser;
  List<dynamic> _projects = [];
  List<dynamic> _warehouses = [];
  List<dynamic> _materials = [];
  
  int? _selectedProjectId;
  int? _selectedWarehouseId;
  
  bool _isLoading = false;
  bool _isInitialized = false;

  // Getters
  bool get isLoggedIn => _isLoggedIn;
  Map<String, dynamic>? get currentUser => _currentUser;
  List<dynamic> get projects => _projects;
  List<dynamic> get warehouses => _warehouses;
  List<dynamic> get materials => _materials;
  int? get selectedProjectId => _selectedProjectId;
  int? get selectedWarehouseId => _selectedWarehouseId;
  bool get isLoading => _isLoading;
  bool get isInitialized => _isInitialized;

  ApiService get apiService => _apiService;
  ConnectivityService get connectivityService => _connectivityService;
  SyncService get syncService => _syncService;
  bool get isOnline => _connectivityService.isOnline;

  AppState() {
    _connectivityService = ConnectivityService();
    _syncService = SyncService(
      apiService: _apiService,
      connectivityService: _connectivityService,
    );
  }

  Future<void> initialize() async {
    await _apiService.loadToken();
    if (_apiService.token != null) {
      final user = await _apiService.getCurrentUser();
      if (user != null) {
        _currentUser = user;
        _isLoggedIn = true;
        await loadData();
      }
    }
    _isInitialized = true;
    notifyListeners();
  }

  Future<bool> login(String email, String password) async {
    _isLoading = true;
    notifyListeners();

    final success = await _apiService.login(email, password);
    
    if (success) {
      _currentUser = await _apiService.getCurrentUser();
      _isLoggedIn = true;
      await loadData();
      
      // Trigger initial sync if online
      if (_connectivityService.isOnline) {
        _syncService.syncAll();
      }
    }

    _isLoading = false;
    notifyListeners();
    return success;
  }

  /// Load data using offline-first pattern
  Future<void> loadData() async {
    _isLoading = true;
    notifyListeners();

    try {
      // Use SyncService for offline-first data loading
      _materials = await _syncService.getMaterials();
      _warehouses = await _syncService.getWarehouses();
      _projects = await _syncService.getProjects();
    } catch (e) {
      print('Error loading data: $e');
      // Fall back to cached data
      _materials = await OfflineDatabase.getCachedMaterials();
      _warehouses = await OfflineDatabase.getCachedWarehouses();
      _projects = await OfflineDatabase.getCachedProjects();
    }
    
    _isLoading = false;
    notifyListeners();
  }

  /// Refresh data from server (online only)
  Future<bool> refreshData() async {
    if (!_connectivityService.isOnline) {
      return false;
    }
    
    final success = await _syncService.syncAll();
    if (success) {
      await loadData();
    }
    return success;
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
    await OfflineDatabase.clearAllCache();
    _isLoggedIn = false;
    _currentUser = null;
    _projects = [];
    _warehouses = [];
    _materials = [];
    _selectedProjectId = null;
    _selectedWarehouseId = null;
    notifyListeners();
  }
  
  /// Add stock transaction (offline-first)
  Future<bool> addStockTransaction({
    required int warehouseId,
    required int materialId,
    required String transactionType,
    required int quantity,
    String? notes,
  }) async {
    return await _syncService.addTransaction(
      warehouseId: warehouseId,
      materialId: materialId,
      transactionType: transactionType,
      quantity: quantity,
      notes: notes,
    );
  }
  
  /// Add photo for upload (offline-first)
  Future<bool> addPhoto({
    required String filePath,
    required String title,
    String? description,
    int? projectId,
  }) async {
    return await _syncService.addPhoto(
      filePath: filePath,
      title: title,
      description: description,
      projectId: projectId,
    );
  }
  
  /// Get material by SKU (offline-first)
  Future<Map<String, dynamic>?> getMaterialBySku(String sku) async {
    return await _syncService.getMaterialBySku(sku);
  }
  
  @override
  void dispose() {
    _connectivityService.dispose();
    _syncService.dispose();
    super.dispose();
  }
}
