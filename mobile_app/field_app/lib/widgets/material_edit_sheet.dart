import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../l10n/app_localizations.dart';

/// Editable bottom sheet for material details.
/// Allows editing name, category, unit, cost, and min_stock.
class MaterialEditSheet extends StatefulWidget {
  final Map<String, dynamic> materialData;
  final VoidCallback onClose;
  final void Function(Map<String, dynamic> updatedData)? onSaved;

  const MaterialEditSheet({
    super.key,
    required this.materialData,
    required this.onClose,
    this.onSaved,
  });

  @override
  State<MaterialEditSheet> createState() => _MaterialEditSheetState();
}

class _MaterialEditSheetState extends State<MaterialEditSheet> {
  late final TextEditingController _nameController;
  late final TextEditingController _categoryController;
  late final TextEditingController _unitController;
  late final TextEditingController _costController;
  late final TextEditingController _minStockController;

  bool _isLoading = false;
  String? _errorMessage;

  // Sheet sizing constants
  static const double _initialSheetSize = 0.7;
  static const double _minSheetSize = 0.5;
  static const double _maxSheetSize = 0.95;

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(
      text: widget.materialData['name']?.toString() ?? '',
    );
    _categoryController = TextEditingController(
      text: widget.materialData['category']?.toString() ?? '',
    );
    _unitController = TextEditingController(
      text: widget.materialData['unit']?.toString() ?? '',
    );
    _costController = TextEditingController(
      text: _formatCostForInput(widget.materialData['cost']),
    );
    _minStockController = TextEditingController(
      text: widget.materialData['min_stock']?.toString() ?? '0',
    );
  }

  @override
  void dispose() {
    _nameController.dispose();
    _categoryController.dispose();
    _unitController.dispose();
    _costController.dispose();
    _minStockController.dispose();
    super.dispose();
  }

  String _formatCostForInput(dynamic cost) {
    if (cost is num) return cost.toStringAsFixed(2);
    if (cost is String) {
      final parsed = num.tryParse(cost);
      if (parsed != null) return parsed.toStringAsFixed(2);
    }
    return '0.00';
  }

  Future<void> _saveChanges() async {
    final l10n = AppLocalizations.of(context);
    
    if (_nameController.text.trim().isEmpty) {
      setState(() => _errorMessage = l10n.nameRequired);
      return;
    }

    final cost = num.tryParse(_costController.text);
    final minStock = int.tryParse(_minStockController.text);

    // Validate non-negative values
    if (cost != null && cost < 0) {
      setState(() => _errorMessage = l10n.costNegativeError);
      return;
    }
    if (minStock != null && minStock < 0) {
      setState(() => _errorMessage = l10n.minStockNegativeError);
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    // Capture l10n strings before async gap
    final materialUpdatedText = l10n.materialUpdated;
    final saveFailedText = l10n.saveFailed;

    try {
      final materialId = widget.materialData['id'];
      if (materialId == null) {
        throw Exception('Material ID not found');
      }

      final apiService = context.read<AppState>().apiService;

      final result = await apiService.updateMaterial(
        materialId: materialId is int ? materialId : int.parse(materialId.toString()),
        name: _nameController.text.trim(),
        category: _categoryController.text.trim().isEmpty
            ? null
            : _categoryController.text.trim(),
        unit: _unitController.text.trim().isEmpty
            ? null
            : _unitController.text.trim(),
        cost: cost,
        minStock: minStock,
      );

      if (!mounted) return;

      if (result != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(materialUpdatedText),
            backgroundColor: Colors.green,
          ),
        );
        widget.onSaved?.call(result);
        widget.onClose();
      } else {
        setState(() => _errorMessage = saveFailedText);
      }
    } catch (e) {
      if (mounted) {
        setState(() => _errorMessage = '${l10n.errorOccurred}: $e');
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final sku = widget.materialData['sku']?.toString() ?? '-';

    return DraggableScrollableSheet(
      initialChildSize: _initialSheetSize,
      minChildSize: _minSheetSize,
      maxChildSize: _maxSheetSize,
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
              // Handle bar
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

              // Header
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.orange[50],
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.edit,
                      color: Colors.orange,
                      size: 32,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          l10n.editMaterial,
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
                    onPressed: widget.onClose,
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Error message
              if (_errorMessage != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.red[50],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline, color: Colors.red),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _errorMessage!,
                          style: const TextStyle(color: Colors.red),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // Form fields
              Expanded(
                child: SingleChildScrollView(
                  controller: scrollController,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildTextField(
                        controller: _nameController,
                        label: '${l10n.material} *',
                        icon: Icons.label,
                      ),
                      const SizedBox(height: 16),
                      _buildTextField(
                        controller: _categoryController,
                        label: l10n.category,
                        icon: Icons.category,
                      ),
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          Expanded(
                            child: _buildTextField(
                              controller: _unitController,
                              label: l10n.unit,
                              icon: Icons.straighten,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: _buildTextField(
                              controller: _costController,
                              label: l10n.costLabel,
                              icon: Icons.euro,
                              keyboardType: const TextInputType.numberWithOptions(decimal: true),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      _buildTextField(
                        controller: _minStockController,
                        label: l10n.minStock,
                        icon: Icons.warning_amber,
                        keyboardType: TextInputType.number,
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 16),

              // Action buttons
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _isLoading ? null : widget.onClose,
                      icon: const Icon(Icons.close),
                      label: Text(l10n.cancel),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: ElevatedButton.icon(
                      onPressed: _isLoading ? null : _saveChanges,
                      icon: _isLoading
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                valueColor: AlwaysStoppedAnimation(Colors.white),
                              ),
                            )
                          : const Icon(Icons.save),
                      label: Text(_isLoading ? l10n.saving : l10n.save),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        backgroundColor: Colors.orange,
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

  Widget _buildTextField({
    required TextEditingController controller,
    required String label,
    required IconData icon,
    TextInputType keyboardType = TextInputType.text,
  }) {
    return TextField(
      controller: controller,
      keyboardType: keyboardType,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        filled: true,
        fillColor: Colors.grey[50],
      ),
    );
  }
}
