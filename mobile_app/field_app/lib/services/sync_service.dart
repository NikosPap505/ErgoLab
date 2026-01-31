import 'dart:async';
import 'package:flutter/foundation.dart';
import 'api_service.dart';
import 'offline_database.dart';
import 'connectivity_service.dart';

/// SyncService manages data synchronization between local SQLite and remote API
/// 
/// Key features:
/// - Auto-sync when connection restored
/// - Upload pending transactions
/// - Download fresh master data
/// - Background sync support
/// - Conflict resolution (server wins by default)
class SyncService with ChangeNotifier {
  final ApiService apiService;
  final ConnectivityService connectivityService;
  
  bool _isSyncing = false;
  DateTime? _lastSyncTime;
  String? _lastSyncError;
  int _pendingCount = 0;
  
  // Sync status
  bool get isSyncing => _isSyncing;
  DateTime? get lastSyncTime => _lastSyncTime;
  String? get lastSyncError => _lastSyncError;
  int get pendingCount => _pendingCount;
  bool get hasPendingItems => _pendingCount > 0;
  
  // Sync progress
  double _syncProgress = 0.0;
  String _syncStatus = '';
  double get syncProgress => _syncProgress;
  String get syncStatus => _syncStatus;
  
  SyncService({
    required this.apiService,
    required this.connectivityService,
  }) {
    // Listen for connectivity changes
    connectivityService.addListener(_onConnectivityChanged);
    
    // Load initial pending count
    _updatePendingCount();
  }
  
  void _onConnectivityChanged() {
    if (connectivityService.isOnline && !_isSyncing) {
      // Auto-sync when connection restored
      print('📶 Connection restored - starting auto-sync');
      syncAll();
    }
  }
  
  Future<void> _updatePendingCount() async {
    _pendingCount = await OfflineDatabase.getPendingCount();
    notifyListeners();
  }
  
  /// Full sync: upload pending, download fresh data
  Future<bool> syncAll() async {
    if (_isSyncing) {
      print('⚠️ Sync already in progress');
      return false;
    }
    
    if (!connectivityService.isOnline) {
      print('⚠️ Cannot sync - offline');
      _lastSyncError = 'No internet connection';
      notifyListeners();
      return false;
    }
    
    _isSyncing = true;
    _lastSyncError = null;
    _syncProgress = 0.0;
    _syncStatus = 'Starting sync...';
    notifyListeners();
    
    try {
      // Step 1: Sync pending transactions (30%)
      _syncStatus = 'Uploading pending transactions...';
      _syncProgress = 0.1;
      notifyListeners();
      await _syncPendingTransactions();
      _syncProgress = 0.3;
      notifyListeners();
      
      // Step 2: Sync pending uploads (50%)
      _syncStatus = 'Uploading pending photos...';
      notifyListeners();
      await _syncPendingUploads();
      _syncProgress = 0.5;
      notifyListeners();
      
      // Step 3: Download materials (65%)
      _syncStatus = 'Downloading materials...';
      notifyListeners();
      await _downloadMaterials();
      _syncProgress = 0.65;
      notifyListeners();
      
      // Step 4: Download warehouses (80%)
      _syncStatus = 'Downloading warehouses...';
      notifyListeners();
      await _downloadWarehouses();
      _syncProgress = 0.8;
      notifyListeners();
      
      // Step 5: Download projects (100%)
      _syncStatus = 'Downloading projects...';
      notifyListeners();
      await _downloadProjects();
      _syncProgress = 1.0;
      _syncStatus = 'Sync complete!';
      notifyListeners();
      
      _lastSyncTime = DateTime.now();
      _lastSyncError = null;
      await _updatePendingCount();
      
      print('✅ Full sync completed at $_lastSyncTime');
      
      _isSyncing = false;
      notifyListeners();
      return true;
      
    } catch (e) {
      print('❌ Sync error: $e');
      _lastSyncError = e.toString();
      _syncStatus = 'Sync failed';
      _isSyncing = false;
      notifyListeners();
      return false;
    }
  }
  
  /// Upload pending stock transactions to server
  Future<void> _syncPendingTransactions() async {
    final pending = await OfflineDatabase.getPendingTransactions();
    
    if (pending.isEmpty) {
      print('  ✓ No pending transactions');
      return;
    }
    
    print('  📤 Syncing ${pending.length} pending transactions...');
    
    for (final transaction in pending) {
      try {
        final success = await apiService.addStockTransaction(
          warehouseId: transaction['warehouse_id'] as int,
          materialId: transaction['material_id'] as int,
          transactionType: transaction['transaction_type'] as String,
          quantity: transaction['quantity'] as int,
          notes: transaction['notes'] as String?,
        );
        
        if (success) {
          await OfflineDatabase.markTransactionSynced(transaction['id'] as int);
          print('    ✅ Transaction ${transaction['id']} synced');
        } else {
          print('    ⚠️ Transaction ${transaction['id']} failed - will retry');
        }
      } catch (e) {
        print('    ❌ Transaction ${transaction['id']} error: $e');
        // Don't throw - continue with other transactions
      }
    }
    
    // Clean up synced transactions
    await OfflineDatabase.deleteSyncedTransactions();
  }
  
  /// Upload pending photos/documents to server
  Future<void> _syncPendingUploads() async {
    final pending = await OfflineDatabase.getPendingUploads();
    
    if (pending.isEmpty) {
      print('  ✓ No pending uploads');
      return;
    }
    
    print('  📤 Syncing ${pending.length} pending uploads...');
    
    for (final upload in pending) {
      try {
        final result = await apiService.uploadDocument(
          filePath: upload['file_path'] as String,
          fileName: upload['title'] as String,
          fileType: upload['file_type'] as String,
          projectId: upload['project_id'] as int?,
          description: upload['description'] as String?,
        );
        
        if (result != null) {
          await OfflineDatabase.markUploadSynced(upload['id'] as int);
          print('    ✅ Upload ${upload['id']} synced');
        } else {
          print('    ⚠️ Upload ${upload['id']} failed - will retry');
        }
      } catch (e) {
        print('    ❌ Upload ${upload['id']} error: $e');
      }
    }
  }
  
  /// Download fresh materials list from server
  Future<void> _downloadMaterials() async {
    try {
      final materials = await apiService.getMaterials();
      if (materials.isNotEmpty) {
        await OfflineDatabase.cacheMaterials(materials);
        print('  ✅ Downloaded ${materials.length} materials');
      }
    } catch (e) {
      print('  ❌ Download materials error: $e');
      rethrow;
    }
  }
  
  /// Download fresh warehouses list from server
  Future<void> _downloadWarehouses() async {
    try {
      final warehouses = await apiService.getWarehouses();
      if (warehouses.isNotEmpty) {
        await OfflineDatabase.cacheWarehouses(warehouses);
        print('  ✅ Downloaded ${warehouses.length} warehouses');
      }
    } catch (e) {
      print('  ❌ Download warehouses error: $e');
      rethrow;
    }
  }
  
  /// Download fresh projects list from server
  Future<void> _downloadProjects() async {
    try {
      final projects = await apiService.getProjects();
      if (projects.isNotEmpty) {
        await OfflineDatabase.cacheProjects(projects);
        print('  ✅ Downloaded ${projects.length} projects');
      }
    } catch (e) {
      print('  ❌ Download projects error: $e');
      rethrow;
    }
  }
  
  /// Quick sync - only upload pending items
  Future<bool> quickSync() async {
    if (_isSyncing || !connectivityService.isOnline) return false;
    
    _isSyncing = true;
    notifyListeners();
    
    try {
      await _syncPendingTransactions();
      await _syncPendingUploads();
      await _updatePendingCount();
      
      _isSyncing = false;
      notifyListeners();
      return true;
    } catch (e) {
      _isSyncing = false;
      notifyListeners();
      return false;
    }
  }
  
  /// Add a transaction (offline-first)
  /// Returns true if saved locally, false on error
  Future<bool> addTransaction({
    required int warehouseId,
    required int materialId,
    required String transactionType,
    required int quantity,
    String? notes,
  }) async {
    try {
      // Always save locally first
      await OfflineDatabase.addPendingTransaction(
        warehouseId: warehouseId,
        materialId: materialId,
        transactionType: transactionType,
        quantity: quantity,
        notes: notes,
      );
      
      print('💾 Transaction saved locally');
      await _updatePendingCount();
      
      // Try to sync immediately if online
      if (connectivityService.isOnline) {
        quickSync();  // Don't await - fire and forget
      }
      
      return true;
    } catch (e) {
      print('❌ Failed to save transaction: $e');
      return false;
    }
  }
  
  /// Add a photo for upload (offline-first)
  Future<bool> addPhoto({
    required String filePath,
    required String title,
    String? description,
    int? projectId,
    String fileType = 'photo',
  }) async {
    try {
      await OfflineDatabase.addPendingUpload(
        filePath: filePath,
        title: title,
        description: description,
        projectId: projectId,
        fileType: fileType,
      );
      
      print('💾 Photo saved locally: $filePath');
      await _updatePendingCount();
      
      // Try to sync immediately if online
      if (connectivityService.isOnline) {
        quickSync();
      }
      
      return true;
    } catch (e) {
      print('❌ Failed to save photo: $e');
      return false;
    }
  }
  
  /// Get materials (offline-first)
  Future<List<Map<String, dynamic>>> getMaterials() async {
    // Try to get fresh data if online
    if (connectivityService.isOnline) {
      try {
        final materials = await apiService.getMaterials();
        if (materials.isNotEmpty) {
          await OfflineDatabase.cacheMaterials(materials);
          return materials.cast<Map<String, dynamic>>();
        }
      } catch (e) {
        print('⚠️ Failed to fetch materials online: $e');
      }
    }
    
    // Fall back to cached data
    return await OfflineDatabase.getCachedMaterials();
  }
  
  /// Get warehouses (offline-first)
  Future<List<Map<String, dynamic>>> getWarehouses() async {
    if (connectivityService.isOnline) {
      try {
        final warehouses = await apiService.getWarehouses();
        if (warehouses.isNotEmpty) {
          await OfflineDatabase.cacheWarehouses(warehouses);
          return warehouses.cast<Map<String, dynamic>>();
        }
      } catch (e) {
        print('⚠️ Failed to fetch warehouses online: $e');
      }
    }
    
    return await OfflineDatabase.getCachedWarehouses();
  }
  
  /// Get projects (offline-first)
  Future<List<Map<String, dynamic>>> getProjects() async {
    if (connectivityService.isOnline) {
      try {
        final projects = await apiService.getProjects();
        if (projects.isNotEmpty) {
          await OfflineDatabase.cacheProjects(projects);
          return projects.cast<Map<String, dynamic>>();
        }
      } catch (e) {
        print('⚠️ Failed to fetch projects online: $e');
      }
    }
    
    return await OfflineDatabase.getCachedProjects();
  }
  
  /// Get material by SKU (offline-first)
  Future<Map<String, dynamic>?> getMaterialBySku(String sku) async {
    // First check local cache (faster)
    final cached = await OfflineDatabase.getCachedMaterialBySku(sku);
    if (cached != null) return cached;
    
    // If not found and online, try API
    if (connectivityService.isOnline) {
      return await apiService.getMaterialBySku(sku);
    }
    
    return null;
  }
  
  /// Force refresh all data from server
  Future<bool> forceRefresh() async {
    if (!connectivityService.isOnline) {
      _lastSyncError = 'Cannot refresh - offline';
      notifyListeners();
      return false;
    }
    
    // Clear cache and sync fresh
    await OfflineDatabase.clearAllCache();
    return await syncAll();
  }
  
  @override
  void dispose() {
    connectivityService.removeListener(_onConnectivityChanged);
    super.dispose();
  }
}
