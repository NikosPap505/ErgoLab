import 'dart:convert';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'package:path_provider/path_provider.dart';

class OfflineDatabase {
  static Database? _database;
  static const int _dbVersion = 3;

  static Future<Database> get database async {
    _database ??= await _initDatabase();
    return _database!;
  }

  static Future<Database> _initDatabase() async {
    final documentsDirectory = await getApplicationDocumentsDirectory();
    final path = join(documentsDirectory.path, 'ergolab_offline.db');

    return await openDatabase(
      path,
      version: _dbVersion,
      onCreate: _onCreate,
      onUpgrade: _onUpgrade,
    );
  }

  static Future<void> _onCreate(Database db, int version) async {
    // Pending transactions (for offline sync)
    await db.execute('''
      CREATE TABLE pending_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse_id INTEGER NOT NULL,
        material_id INTEGER NOT NULL,
        transaction_type TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        notes TEXT,
        created_at TEXT NOT NULL,
        synced INTEGER DEFAULT 0
      )
    ''');

    // Cached materials
    await db.execute('''
      CREATE TABLE cached_materials (
        id INTEGER PRIMARY KEY,
        sku TEXT NOT NULL,
        name TEXT NOT NULL,
        unit TEXT,
        min_stock INTEGER,
        data TEXT NOT NULL,
        updated_at TEXT NOT NULL
      )
    ''');

    // Cached warehouses
    await db.execute('''
      CREATE TABLE cached_warehouses (
        id INTEGER PRIMARY KEY,
        code TEXT NOT NULL,
        name TEXT NOT NULL,
        data TEXT NOT NULL,
        updated_at TEXT NOT NULL
      )
    ''');

    // Cached projects
    await db.execute('''
      CREATE TABLE cached_projects (
        id INTEGER PRIMARY KEY,
        code TEXT NOT NULL,
        name TEXT NOT NULL,
        data TEXT NOT NULL,
        updated_at TEXT NOT NULL
      )
    ''');

    // Pending uploads (photos)
    await db.execute('''
      CREATE TABLE pending_uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        project_id INTEGER,
        file_type TEXT NOT NULL,
        created_at TEXT NOT NULL,
        synced INTEGER DEFAULT 0
      )
    ''');

    // Cached inventory
    await db.execute('''
      CREATE TABLE cached_inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse_id INTEGER NOT NULL,
        material_id INTEGER NOT NULL,
        quantity INTEGER DEFAULT 0,
        data TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(warehouse_id, material_id)
      )
    ''');

    // Scan history
    await _createScanHistoryTable(db);

    // Worker attendance (local tracking)
    await _createWorkerAttendanceTable(db);
  }

  static Future<void> _createScanHistoryTable(Database db) async {
    await db.execute('''
      CREATE TABLE IF NOT EXISTS scan_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_value TEXT NOT NULL,
        scan_type TEXT NOT NULL,
        result_type TEXT,
        result_name TEXT,
        result_data TEXT,
        scanned_at TEXT NOT NULL
      )
    ''');
    await db.execute('CREATE INDEX IF NOT EXISTS idx_scan_history_date ON scan_history(scanned_at DESC)');
  }

  static Future<void> _createWorkerAttendanceTable(Database db) async {
    await db.execute('''
      CREATE TABLE IF NOT EXISTS worker_attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        worker_id INTEGER NOT NULL,
        worker_name TEXT NOT NULL,
        action TEXT NOT NULL,
        location TEXT,
        notes TEXT,
        timestamp TEXT NOT NULL,
        synced INTEGER DEFAULT 0
      )
    ''');
    await db.execute('CREATE INDEX IF NOT EXISTS idx_attendance_worker ON worker_attendance(worker_id)');
    await db.execute('CREATE INDEX IF NOT EXISTS idx_attendance_date ON worker_attendance(timestamp DESC)');
  }

  static Future<void> _onUpgrade(Database db, int oldVersion, int newVersion) async {
    // Migration for scan history table
    if (oldVersion < 2) {
      await _createScanHistoryTable(db);
    }
    // Migration for worker attendance
    if (oldVersion < 3) {
      await _createWorkerAttendanceTable(db);
    }
  }

  static Future<void> close() async {
    final db = _database;
    if (db != null && db.isOpen) {
      await db.close();
      _database = null;
    }
  }

  // === Pending Transactions ===
  
  static Future<int> addPendingTransaction({
    required int warehouseId,
    required int materialId,
    required String transactionType,
    required int quantity,
    String? notes,
  }) async {
    final db = await database;
    return await db.insert('pending_transactions', {
      'warehouse_id': warehouseId,
      'material_id': materialId,
      'transaction_type': transactionType,
      'quantity': quantity,
      'notes': notes,
      'created_at': DateTime.now().toIso8601String(),
      'synced': 0,
    });
  }

  static Future<List<Map<String, dynamic>>> getPendingTransactions() async {
    final db = await database;
    return await db.query(
      'pending_transactions',
      where: 'synced = ?',
      whereArgs: [0],
    );
  }

  static Future<void> markTransactionSynced(int id) async {
    final db = await database;
    await db.update(
      'pending_transactions',
      {'synced': 1},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  static Future<void> deleteSyncedTransactions() async {
    final db = await database;
    await db.delete(
      'pending_transactions',
      where: 'synced = ?',
      whereArgs: [1],
    );
  }

  // === Cached Materials ===
  
  static Future<void> cacheMaterials(List<dynamic> materials) async {
    final db = await database;
    final batch = db.batch();
    
    for (final material in materials) {
      batch.insert(
        'cached_materials',
        {
          'id': material['id'],
          'sku': material['sku'],
          'name': material['name'],
          'unit': material['unit'],
          'min_stock': material['min_stock'],
          'data': jsonEncode(material),
          'updated_at': DateTime.now().toIso8601String(),
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }
    
    await batch.commit(noResult: true);
  }

  static Future<List<Map<String, dynamic>>> getCachedMaterials() async {
    final db = await database;
    final results = await db.query('cached_materials');
    return results.map((row) => jsonDecode(row['data'] as String) as Map<String, dynamic>).toList();
  }

  static Future<Map<String, dynamic>?> getCachedMaterialBySku(String sku) async {
    final db = await database;
    final results = await db.query(
      'cached_materials',
      where: 'sku = ?',
      whereArgs: [sku],
    );
    if (results.isEmpty) return null;
    return jsonDecode(results.first['data'] as String);
  }

  // === Cached Warehouses ===
  
  static Future<void> cacheWarehouses(List<dynamic> warehouses) async {
    final db = await database;
    final batch = db.batch();
    
    for (final warehouse in warehouses) {
      batch.insert(
        'cached_warehouses',
        {
          'id': warehouse['id'],
          'code': warehouse['code'],
          'name': warehouse['name'],
          'data': jsonEncode(warehouse),
          'updated_at': DateTime.now().toIso8601String(),
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }
    
    await batch.commit(noResult: true);
  }

  static Future<List<Map<String, dynamic>>> getCachedWarehouses() async {
    final db = await database;
    final results = await db.query('cached_warehouses');
    return results.map((row) => jsonDecode(row['data'] as String) as Map<String, dynamic>).toList();
  }

  // === Cached Projects ===
  
  static Future<void> cacheProjects(List<dynamic> projects) async {
    final db = await database;
    final batch = db.batch();
    
    for (final project in projects) {
      batch.insert(
        'cached_projects',
        {
          'id': project['id'],
          'code': project['code'],
          'name': project['name'],
          'data': jsonEncode(project),
          'updated_at': DateTime.now().toIso8601String(),
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }
    
    await batch.commit(noResult: true);
  }

  static Future<List<Map<String, dynamic>>> getCachedProjects() async {
    final db = await database;
    final results = await db.query('cached_projects');
    return results.map((row) => jsonDecode(row['data'] as String) as Map<String, dynamic>).toList();
  }

  // === Pending Uploads ===
  
  static Future<int> addPendingUpload({
    required String filePath,
    required String title,
    String? description,
    int? projectId,
    required String fileType,
  }) async {
    final db = await database;
    return await db.insert('pending_uploads', {
      'file_path': filePath,
      'title': title,
      'description': description,
      'project_id': projectId,
      'file_type': fileType,
      'created_at': DateTime.now().toIso8601String(),
      'synced': 0,
    });
  }

  static Future<List<Map<String, dynamic>>> getPendingUploads() async {
    final db = await database;
    return await db.query(
      'pending_uploads',
      where: 'synced = ?',
      whereArgs: [0],
    );
  }

  static Future<void> markUploadSynced(int id) async {
    final db = await database;
    await db.update(
      'pending_uploads',
      {'synced': 1},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  // === Cached Inventory ===
  
  static Future<void> cacheInventory(int warehouseId, List<dynamic> inventory) async {
    final db = await database;
    
    // First delete old inventory for this warehouse
    await db.delete(
      'cached_inventory',
      where: 'warehouse_id = ?',
      whereArgs: [warehouseId],
    );
    
    // Insert new inventory
    final batch = db.batch();
    for (final item in inventory) {
      batch.insert(
        'cached_inventory',
        {
          'warehouse_id': warehouseId,
          'material_id': item['material_id'] ?? item['material']?['id'],
          'quantity': item['quantity'] ?? 0,
          'data': jsonEncode(item),
          'updated_at': DateTime.now().toIso8601String(),
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }
    
    await batch.commit(noResult: true);
  }

  static Future<List<Map<String, dynamic>>> getCachedInventory(int warehouseId) async {
    final db = await database;
    final results = await db.query(
      'cached_inventory',
      where: 'warehouse_id = ?',
      whereArgs: [warehouseId],
    );
    return results.map((row) => jsonDecode(row['data'] as String) as Map<String, dynamic>).toList();
  }

  // === Scan History ===

  /// Saves a scan to the local history
  static Future<int> addScanToHistory({
    required String rawValue,
    required String scanType,
    String? resultType,
    String? resultName,
    Map<String, dynamic>? resultData,
  }) async {
    final db = await database;
    return await db.insert('scan_history', {
      'raw_value': rawValue,
      'scan_type': scanType,
      'result_type': resultType,
      'result_name': resultName,
      'result_data': resultData != null ? jsonEncode(resultData) : null,
      'scanned_at': DateTime.now().toIso8601String(),
    });
  }

  /// Gets recent scan history, optionally limited
  static Future<List<Map<String, dynamic>>> getScanHistory({
    int limit = 50,
    int offset = 0,
  }) async {
    final db = await database;
    final results = await db.query(
      'scan_history',
      orderBy: 'scanned_at DESC',
      limit: limit,
      offset: offset,
    );
    return results.map((row) {
      final data = Map<String, dynamic>.from(row);
      if (data['result_data'] != null) {
        data['result_data'] = jsonDecode(data['result_data'] as String);
      }
      return data;
    }).toList();
  }

  /// Gets total count of scan history entries
  static Future<int> getScanHistoryCount() async {
    final db = await database;
    final result = await db.rawQuery('SELECT COUNT(*) as count FROM scan_history');
    return (result.first['count'] as int?) ?? 0;
  }

  /// Deletes a specific scan from history
  static Future<void> deleteScanFromHistory(int id) async {
    final db = await database;
    await db.delete('scan_history', where: 'id = ?', whereArgs: [id]);
  }

  /// Clears all scan history
  static Future<void> clearScanHistory() async {
    final db = await database;
    await db.delete('scan_history');
  }

  // === Worker Attendance ===

  /// Records a worker check-in or check-out
  static Future<int> recordWorkerAttendance({
    required int workerId,
    required String workerName,
    required String action, // 'check_in' or 'check_out'
    String? location,
    String? notes,
  }) async {
    final db = await database;
    return await db.insert('worker_attendance', {
      'worker_id': workerId,
      'worker_name': workerName,
      'action': action,
      'location': location,
      'notes': notes,
      'timestamp': DateTime.now().toIso8601String(),
      'synced': 0,
    });
  }

  /// Gets attendance records for a worker
  static Future<List<Map<String, dynamic>>> getWorkerAttendance(
    int workerId, {
    int limit = 10,
  }) async {
    final db = await database;
    return await db.query(
      'worker_attendance',
      where: 'worker_id = ?',
      whereArgs: [workerId],
      orderBy: 'timestamp DESC',
      limit: limit,
    );
  }

  /// Gets the last attendance action for a worker
  static Future<Map<String, dynamic>?> getLastWorkerAction(int workerId) async {
    final db = await database;
    final results = await db.query(
      'worker_attendance',
      where: 'worker_id = ?',
      whereArgs: [workerId],
      orderBy: 'timestamp DESC',
      limit: 1,
    );
    return results.isNotEmpty ? results.first : null;
  }

  /// Gets all unsynced attendance records
  static Future<List<Map<String, dynamic>>> getUnsyncedAttendance() async {
    final db = await database;
    return await db.query(
      'worker_attendance',
      where: 'synced = ?',
      whereArgs: [0],
    );
  }

  /// Marks attendance record as synced
  static Future<void> markAttendanceSynced(int id) async {
    final db = await database;
    await db.update(
      'worker_attendance',
      {'synced': 1},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  /// Gets today's attendance records
  static Future<List<Map<String, dynamic>>> getTodayAttendance() async {
    final db = await database;
    final today = DateTime.now();
    final startOfDay = DateTime(today.year, today.month, today.day).toIso8601String();
    final endOfDay = DateTime(today.year, today.month, today.day, 23, 59, 59).toIso8601String();
    
    return await db.query(
      'worker_attendance',
      where: 'timestamp BETWEEN ? AND ?',
      whereArgs: [startOfDay, endOfDay],
      orderBy: 'timestamp DESC',
    );
  }

  // === Utility ===
  
  static Future<int> getPendingCount() async {
    final transactions = await getPendingTransactions();
    final uploads = await getPendingUploads();
    return transactions.length + uploads.length;
  }

  static Future<void> clearAllCache() async {
    final db = await database;
    await db.delete('cached_materials');
    await db.delete('cached_warehouses');
    await db.delete('cached_projects');
    await db.delete('cached_inventory');
  }
}
