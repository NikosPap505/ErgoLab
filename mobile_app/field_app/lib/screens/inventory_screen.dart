import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/connectivity_service.dart';
import '../services/offline_database.dart';
import '../widgets/offline_widgets.dart';

class InventoryScreen extends StatefulWidget {
  const InventoryScreen({super.key});

  @override
  State<InventoryScreen> createState() => _InventoryScreenState();
}

class _InventoryScreenState extends State<InventoryScreen> {
  List<dynamic> _inventory = [];
  bool _isLoading = true;
  bool _isOfflineData = false;
  String _searchQuery = '';
  final _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadInventory();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadInventory() async {
    final appState = context.read<AppState>();
    final connectivity = context.read<ConnectivityService>();
    
    if (appState.selectedWarehouseId == null) {
      setState(() {
        _isLoading = false;
      });
      return;
    }

    setState(() {
      _isLoading = true;
    });

    List<dynamic> inventory = [];
    bool isOffline = false;

    if (connectivity.isOnline) {
      // Try to load from API
      try {
        inventory = await appState.apiService.getWarehouseInventory(
          appState.selectedWarehouseId!,
        );
        // Cache for offline use
        await OfflineDatabase.cacheInventory(appState.selectedWarehouseId!, inventory);
      } catch (e) {
        debugPrint('Error loading inventory from API: $e');
        // Fall back to cached data
        inventory = await _loadCachedInventory(appState.selectedWarehouseId!);
        isOffline = true;
      }
    } else {
      // Load from cache
      inventory = await _loadCachedInventory(appState.selectedWarehouseId!);
      isOffline = true;
    }

    if (mounted) {
      setState(() {
        _inventory = inventory;
        _isLoading = false;
        _isOfflineData = isOffline;
      });
    }
  }

  Future<List<dynamic>> _loadCachedInventory(int warehouseId) async {
    // Load from SQLite cache
    final cached = await OfflineDatabase.getCachedInventory(warehouseId);
    return cached;
  }

  List<dynamic> get _filteredInventory {
    if (_searchQuery.isEmpty) return _inventory;
    
    return _inventory.where((item) {
      final material = item['material'] ?? {};
      final name = material['name']?.toString().toLowerCase() ?? '';
      final sku = material['sku']?.toString().toLowerCase() ?? '';
      final query = _searchQuery.toLowerCase();
      
      return name.contains(query) || sku.contains(query);
    }).toList();
  }

  Color _getStockLevelColor(int quantity, int minLevel) {
    if (quantity == 0) return Colors.red;
    if (quantity <= minLevel) return Colors.orange;
    return Colors.green;
  }

  String _getStockLevelLabel(int quantity, int minLevel) {
    if (quantity == 0) return '⚠️ Εξαντλημένο';
    if (quantity <= minLevel) return '⚠️ Χαμηλό';
    return '✓ Καλό';
  }

  IconData _getStockLevelIcon(int quantity, int minLevel) {
    if (quantity == 0) return Icons.error;
    if (quantity <= minLevel) return Icons.warning;
    return Icons.check_circle;
  }

  @override
  Widget build(BuildContext context) {
    final appState = context.watch<AppState>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Απόθεμα Αποθήκης'),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadInventory,
          ),
        ],
      ),
      body: Column(
        children: [
          // Warehouse Info Header
          if (appState.selectedWarehouseId != null)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.green.shade50,
                border: Border(
                  bottom: BorderSide(color: Colors.green.shade200),
                ),
              ),
              child: Builder(
                builder: (context) {
                  final warehouse = appState.warehouses.firstWhere(
                    (w) => w['id'] == appState.selectedWarehouseId,
                    orElse: () => {'name': 'Unknown', 'code': ''},
                  );
                  return Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.green.shade100,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(Icons.warehouse, color: Colors.green, size: 28),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              warehouse['name'] ?? 'Αποθήκη',
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 18,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              '${_inventory.length} είδη υλικών',
                              style: TextStyle(
                                color: Colors.grey.shade600,
                                fontSize: 14,
                              ),
                            ),
                          ],
                        ),
                      ),
                      // Summary badges
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          _buildSummaryBadge(
                            _inventory.where((i) {
                              final qty = i['quantity'] ?? 0;
                              final min = i['material']?['min_stock'] ?? 0;
                              return qty <= min && qty > 0;
                            }).length,
                            Colors.orange,
                            'Χαμηλά',
                          ),
                          const SizedBox(height: 4),
                          _buildSummaryBadge(
                            _inventory.where((i) => (i['quantity'] ?? 0) == 0).length,
                            Colors.red,
                            'Εξαντλ.',
                          ),
                        ],
                      ),
                    ],
                  );
                },
              ),
            ),

          // Search Bar
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Αναζήτηση υλικών...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchQuery.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _searchController.clear();
                          setState(() {
                            _searchQuery = '';
                          });
                        },
                      )
                    : null,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                filled: true,
                fillColor: Colors.grey.shade100,
              ),
              onChanged: (value) {
                setState(() {
                  _searchQuery = value;
                });
              },
            ),
          ),

          // Inventory List
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _filteredInventory.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.inventory_2_outlined,
                              size: 80,
                              color: Colors.grey.shade400,
                            ),
                            const SizedBox(height: 16),
                            Text(
                              _searchQuery.isEmpty
                                  ? 'Δεν υπάρχουν υλικά στην αποθήκη'
                                  : 'Δεν βρέθηκαν αποτελέσματα για "$_searchQuery"',
                              style: TextStyle(
                                color: Colors.grey.shade600,
                                fontSize: 16,
                              ),
                              textAlign: TextAlign.center,
                            ),
                            if (_searchQuery.isEmpty) ...[
                              const SizedBox(height: 24),
                              ElevatedButton.icon(
                                onPressed: () {
                                  Navigator.of(context).pushNamed('/add-stock');
                                },
                                icon: const Icon(Icons.add),
                                label: const Text('Προσθήκη Υλικού'),
                              ),
                            ],
                          ],
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _loadInventory,
                        child: ListView.builder(
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          itemCount: _filteredInventory.length,
                          itemBuilder: (context, index) {
                            final item = _filteredInventory[index];
                            final material = item['material'] ?? {};
                            final quantity = item['quantity'] ?? 0;
                            final minStock = material['min_stock'] ?? 0;
                            
                            return Card(
                              margin: const EdgeInsets.only(bottom: 12),
                              elevation: 2,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                                side: BorderSide(
                                  color: _getStockLevelColor(quantity, minStock).withOpacity(0.3),
                                  width: 1,
                                ),
                              ),
                              child: InkWell(
                                onTap: () {
                                  Navigator.of(context).pushNamed(
                                    '/add-stock',
                                    arguments: material,
                                  );
                                },
                                borderRadius: BorderRadius.circular(12),
                                child: Padding(
                                  padding: const EdgeInsets.all(12),
                                  child: Row(
                                    children: [
                                      // Leading icon with stock level color
                                      Container(
                                        width: 56,
                                        height: 56,
                                        decoration: BoxDecoration(
                                          color: _getStockLevelColor(quantity, minStock).withOpacity(0.1),
                                          borderRadius: BorderRadius.circular(12),
                                        ),
                                        child: Icon(
                                          _getStockLevelIcon(quantity, minStock),
                                          color: _getStockLevelColor(quantity, minStock),
                                          size: 28,
                                        ),
                                      ),
                                      const SizedBox(width: 12),
                                      // Material info
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              material['name'] ?? 'Unknown',
                                              style: const TextStyle(
                                                fontWeight: FontWeight.bold,
                                                fontSize: 16,
                                              ),
                                            ),
                                            const SizedBox(height: 4),
                                            Text(
                                              'SKU: ${material['sku'] ?? '-'}',
                                              style: TextStyle(
                                                color: Colors.grey.shade600,
                                                fontSize: 13,
                                              ),
                                            ),
                                            const SizedBox(height: 6),
                                            // Stock level badge
                                            Container(
                                              padding: const EdgeInsets.symmetric(
                                                horizontal: 8,
                                                vertical: 4,
                                              ),
                                              decoration: BoxDecoration(
                                                color: _getStockLevelColor(quantity, minStock).withOpacity(0.1),
                                                borderRadius: BorderRadius.circular(6),
                                              ),
                                              child: Text(
                                                _getStockLevelLabel(quantity, minStock),
                                                style: TextStyle(
                                                  color: _getStockLevelColor(quantity, minStock),
                                                  fontSize: 12,
                                                  fontWeight: FontWeight.bold,
                                                ),
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                      // Quantity display
                                      Column(
                                        crossAxisAlignment: CrossAxisAlignment.end,
                                        children: [
                                          Text(
                                            '$quantity',
                                            style: TextStyle(
                                              fontSize: 28,
                                              fontWeight: FontWeight.bold,
                                              color: _getStockLevelColor(quantity, minStock),
                                            ),
                                          ),
                                          Text(
                                            material['unit'] ?? 'τεμ',
                                            style: TextStyle(
                                              fontSize: 12,
                                              color: Colors.grey.shade600,
                                            ),
                                          ),
                                          if (minStock > 0) ...[
                                            const SizedBox(height: 4),
                                            Text(
                                              'min: $minStock',
                                              style: TextStyle(
                                                fontSize: 11,
                                                color: Colors.grey.shade500,
                                              ),
                                            ),
                                          ],
                                        ],
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            );
                          },
                        ),
                      ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          Navigator.of(context).pushNamed('/scanner');
        },
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        icon: const Icon(Icons.qr_code_scanner),
        label: const Text('Σάρωση'),
      ),
    );
  }

  Widget _buildSummaryBadge(int count, Color color, String label) {
    if (count == 0) return const SizedBox.shrink();
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Text(
        '$count $label',
        style: TextStyle(
          color: color,
          fontSize: 11,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}
