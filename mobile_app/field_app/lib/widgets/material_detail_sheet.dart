import 'package:flutter/material.dart';

class MaterialDetailSheet extends StatelessWidget {
  final Map<String, dynamic> materialData;
  final VoidCallback onClose;
  final VoidCallback onTransaction;

  const MaterialDetailSheet({
    super.key,
    required this.materialData,
    required this.onClose,
    required this.onTransaction,
  });

  @override
  Widget build(BuildContext context) {
    final name = materialData['name']?.toString() ?? '-';
    final sku = materialData['sku']?.toString() ?? '-';
    final category = materialData['category']?.toString() ?? '-';
    final unit = materialData['unit']?.toString() ?? '-';
    final costValue = materialData['cost'];
    final cost = _formatCost(costValue);
    final stocks = materialData['stocks'];
    final stockList = stocks is List ? stocks : const [];

    return DraggableScrollableSheet(
      initialChildSize: 0.6,
      minChildSize: 0.4,
      maxChildSize: 0.9,
      builder: (context, scrollController) {
        return Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: Colors.grey[300],
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 20),

              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.blue[50],
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.inventory_2,
                      color: Colors.blue,
                      size: 32,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          name,
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          'SKU: $sku',
                          style: TextStyle(
                            color: Colors.grey[600],
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: onClose,
                  ),
                ],
              ),
              const SizedBox(height: 24),

              Expanded(
                child: ListView(
                  controller: scrollController,
                  children: [
                    _buildInfoRow('Κατηγορία', materialData['category'] ?? '-'),
                    _buildInfoRow('Κατηγορία', category),
                    _buildInfoRow('Μονάδα', unit),
                    _buildInfoRow(
                      'Κόστος',
                      cost,
                    ),
                    const SizedBox(height: 20),

                    const Text(
                      'Διαθέσιμα Αποθέματα',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 12),

                    if (stockList.isNotEmpty)
                      ...List.generate(
                        stockList.length,
                        (index) {
                          final stock = stockList[index] as Map<String, dynamic>? ?? {};
                          return Card(
                            margin: const EdgeInsets.only(bottom: 8),
                            child: ListTile(
                              leading: const Icon(Icons.warehouse),
                              title: Text(stock['warehouse_name']?.toString() ?? '-'),
                              trailing: Text(
                                '${stock['quantity'] ?? '-'} $unit',
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 16,
                                ),
                              ),
                            ),
                          );
                        },
                      ),
                  ],
                ),
              ),

              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: onClose,
                      icon: const Icon(Icons.close),
                      label: const Text('Κλείσιμο'),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: ElevatedButton.icon(
                      onPressed: onTransaction,
                      icon: const Icon(Icons.add_shopping_cart),
                      label: const Text('Καταχώρηση Κίνησης'),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(
              color: Colors.grey[600],
              fontSize: 14,
            ),
          ),
          Text(
            value,
            style: const TextStyle(
              fontWeight: FontWeight.w500,
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }

  String _formatCost(dynamic costValue) {
    if (costValue is num) {
      return '€${costValue.toStringAsFixed(2)}';
    }
    if (costValue is String) {
      final parsed = num.tryParse(costValue);
      if (parsed != null) {
        return '€${parsed.toStringAsFixed(2)}';
      }
    }
    return '-';
  }
}
