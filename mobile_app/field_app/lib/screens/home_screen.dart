import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/connectivity_service.dart';
import '../services/sync_service.dart';
import '../widgets/offline_widgets.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final appState = context.watch<AppState>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('ErgoLab Field'),
        backgroundColor: Colors.blue,
        foregroundColor: Colors.white,
        actions: [
          // Sync status indicator
          const SyncStatusIndicator(),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () async {
              final success = await appState.refreshData();
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(success 
                      ? 'Δεδομένα ανανεώθηκαν' 
                      : 'Offline - χρήση cached δεδομένων'),
                    duration: const Duration(seconds: 2),
                    backgroundColor: success ? Colors.green : Colors.orange,
                  ),
                );
              }
            },
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await appState.logout();
              if (context.mounted) {
                Navigator.of(context).pushReplacementNamed('/login');
              }
            },
          ),
        ],
      ),
      body: SyncProgressOverlay(
        child: Column(
          children: [
            // Offline banner
            const OfflineBanner(),
            
            // User Info
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              color: Colors.blue.shade50,
              child: Row(
                children: [
                  CircleAvatar(
                    backgroundColor: Colors.blue,
                    child: Text(
                      appState.currentUser?['full_name']?.substring(0, 1) ?? 'U',
                      style: const TextStyle(color: Colors.white),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          appState.currentUser?['full_name'] ?? 'User',
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                        ),
                        Text(
                          appState.currentUser?['email'] ?? '',
                          style: TextStyle(
                            color: Colors.grey.shade600,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                  // Pending items badge
                  Consumer<SyncService>(
                    builder: (context, sync, child) {
                      if (sync.pendingCount == 0) return const SizedBox.shrink();
                      return Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.orange,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          '${sync.pendingCount} pending',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      );
                    },
                  ),
                ],
              ),
            ),

          // Project & Warehouse Selection
          if (appState.projects.isNotEmpty)
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  DropdownButtonFormField<int>(
                    decoration: const InputDecoration(
                      labelText: 'Έργο',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.construction),
                    ),
                    value: appState.selectedProjectId,
                    items: appState.projects.map<DropdownMenuItem<int>>((project) {
                      return DropdownMenuItem<int>(
                        value: project['id'],
                        child: Text('${project['code']} - ${project['name']}'),
                      );
                    }).toList(),
                    onChanged: (value) {
                      if (value != null) {
                        appState.selectProject(value);
                      }
                    },
                  ),
                  const SizedBox(height: 12),
                  
                  DropdownButtonFormField<int>(
                    decoration: const InputDecoration(
                      labelText: 'Αποθήκη',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.warehouse),
                    ),
                    value: appState.selectedWarehouseId,
                    items: appState.warehouses.map<DropdownMenuItem<int>>((warehouse) {
                      return DropdownMenuItem<int>(
                        value: warehouse['id'],
                        child: Text('${warehouse['code']} - ${warehouse['name']}'),
                      );
                    }).toList(),
                    onChanged: (value) {
                      if (value != null) {
                        appState.selectWarehouse(value);
                      }
                    },
                  ),
                ],
              ),
            ),

          // Main Actions
          Expanded(
            child: GridView.count(
              crossAxisCount: 2,
              padding: const EdgeInsets.all(16),
              mainAxisSpacing: 16,
              crossAxisSpacing: 16,
              children: [
                _ActionCard(
                  icon: Icons.qr_code_scanner,
                  title: 'Σάρωση',
                  subtitle: 'Barcode/QR',
                  color: Colors.blue,
                  onTap: () {
                    Navigator.of(context).pushNamed('/scanner');
                  },
                ),
                _ActionCard(
                  icon: Icons.inventory,
                  title: 'Απόθεμα',
                  subtitle: 'Προβολή',
                  color: Colors.green,
                  onTap: () {
                    if (appState.selectedWarehouseId == null) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Επιλέξτε πρώτα αποθήκη'),
                          backgroundColor: Colors.orange,
                        ),
                      );
                      return;
                    }
                    Navigator.of(context).pushNamed('/inventory');
                  },
                ),
                _ActionCard(
                  icon: Icons.add_box,
                  title: 'Προσθήκη',
                  subtitle: 'Υλικών',
                  color: Colors.orange,
                  onTap: () {
                    if (appState.selectedWarehouseId == null) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Επιλέξτε πρώτα αποθήκη'),
                          backgroundColor: Colors.orange,
                        ),
                      );
                      return;
                    }
                    Navigator.of(context).pushNamed('/add-stock');
                  },
                ),
                _ActionCard(
                  icon: Icons.camera_alt,
                  title: 'Φωτογραφία',
                  subtitle: 'Έγγραφο',
                  color: Colors.purple,
                  onTap: () {
                    Navigator.of(context).pushNamed('/capture');
                  },
                ),
              ],
            ),
          ),
        ],
      ),
      ),  // Close SyncProgressOverlay
    );
  }
}

class _ActionCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final Color color;
  final VoidCallback onTap;

  const _ActionCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 48,
                color: color,
              ),
              const SizedBox(height: 12),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                subtitle,
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey.shade600,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
