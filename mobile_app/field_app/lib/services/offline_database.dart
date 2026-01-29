import 'dart:convert';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'package:path_provider/path_provider.dart';

class OfflineDatabase {
  static Database? _database;

  static Future<Database> get database async {
    _database ??= await _initDatabase();
    return _database!;
  }

  static Future<Database> _initDatabase() async {
    final documentsDirectory = await getApplicationDocumentsDirectory();
    final path = join(documentsDirectory.path, 'ergolab_offline.db');

    return await openDatabase(
      path,
      version: 1,
      onCreate: _onCreate,
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
  }
}
