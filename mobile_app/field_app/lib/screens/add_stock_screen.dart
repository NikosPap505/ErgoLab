import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';

class AddStockScreen extends StatefulWidget {
  final Map<String, dynamic>? material;
  
  const AddStockScreen({super.key, this.material});

  @override
  State<AddStockScreen> createState() => _AddStockScreenState();
}

class _AddStockScreenState extends State<AddStockScreen> {
  final _formKey = GlobalKey<FormState>();
  final _quantityController = TextEditingController();
  final _notesController = TextEditingController();
  
  int? _selectedMaterialId;
  String _transactionType = 'in';
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    if (widget.material != null) {
      _selectedMaterialId = widget.material!['id'];
    }
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // Check if material was passed from scanner via route arguments
    if (_selectedMaterialId == null) {
      final args = ModalRoute.of(context)?.settings.arguments;
      if (args != null && args is Map<String, dynamic>) {
        setState(() {
          _selectedMaterialId = args['id'];
        });
      }
    }
  }

  @override
  void dispose() {
    _quantityController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) return;

    final appState = context.read<AppState>();
    
    if (appState.selectedWarehouseId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Παρακαλώ επιλέξτε αποθήκη από την αρχική σελίδα'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    setState(() {
      _isSubmitting = true;
    });

    final success = await appState.apiService.addStockTransaction(
      warehouseId: appState.selectedWarehouseId!,
      materialId: _selectedMaterialId!,
      transactionType: _transactionType,
      quantity: int.parse(_quantityController.text),
      notes: _notesController.text.isEmpty ? null : _notesController.text,
    );

    setState(() {
      _isSubmitting = false;
    });

    if (mounted) {
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              _transactionType == 'in'
                  ? 'Προστέθηκαν ${_quantityController.text} τεμάχια επιτυχώς'
                  : 'Αφαιρέθηκαν ${_quantityController.text} τεμάχια επιτυχώς',
            ),
            backgroundColor: Colors.green,
          ),
        );
        Navigator.of(context).pop();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Σφάλμα καταχώρησης. Δοκιμάστε ξανά.'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final appState = context.watch<AppState>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Κίνηση Αποθέματος'),
        backgroundColor: Colors.orange,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.qr_code_scanner),
            onPressed: () {
              Navigator.of(context).pushReplacementNamed('/scanner');
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Transaction Type Card
              Card(
                elevation: 2,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Τύπος Κίνησης',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          Expanded(
                            child: GestureDetector(
                              onTap: () => setState(() => _transactionType = 'in'),
                              child: Container(
                                padding: const EdgeInsets.all(16),
                                decoration: BoxDecoration(
                                  color: _transactionType == 'in'
                                      ? Colors.green.shade100
                                      : Colors.grey.shade100,
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(
                                    color: _transactionType == 'in'
                                        ? Colors.green
                                        : Colors.grey.shade300,
                                    width: 2,
                                  ),
                                ),
                                child: Column(
                                  children: [
                                    Icon(
                                      Icons.add_circle,
                                      size: 40,
                                      color: _transactionType == 'in'
                                          ? Colors.green
                                          : Colors.grey,
                                    ),
                                    const SizedBox(height: 8),
                                    Text(
                                      'Εισαγωγή',
                                      style: TextStyle(
                                        fontWeight: FontWeight.bold,
                                        color: _transactionType == 'in'
                                            ? Colors.green.shade700
                                            : Colors.grey,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: GestureDetector(
                              onTap: () => setState(() => _transactionType = 'out'),
                              child: Container(
                                padding: const EdgeInsets.all(16),
                                decoration: BoxDecoration(
                                  color: _transactionType == 'out'
                                      ? Colors.red.shade100
                                      : Colors.grey.shade100,
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(
                                    color: _transactionType == 'out'
                                        ? Colors.red
                                        : Colors.grey.shade300,
                                    width: 2,
                                  ),
                                ),
                                child: Column(
                                  children: [
                                    Icon(
                                      Icons.remove_circle,
                                      size: 40,
                                      color: _transactionType == 'out'
                                          ? Colors.red
                                          : Colors.grey,
                                    ),
                                    const SizedBox(height: 8),
                                    Text(
                                      'Εξαγωγή',
                                      style: TextStyle(
                                        fontWeight: FontWeight.bold,
                                        color: _transactionType == 'out'
                                            ? Colors.red.shade700
                                            : Colors.grey,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Material Selection Card
              Card(
                elevation: 2,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Υλικό',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<int>(
                        decoration: const InputDecoration(
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.inventory_2),
                          hintText: 'Επιλέξτε υλικό',
                        ),
                        value: _selectedMaterialId,
                        isExpanded: true,
                        items: appState.materials.map<DropdownMenuItem<int>>((material) {
                          return DropdownMenuItem<int>(
                            value: material['id'],
                            child: Text(
                              '${material['sku']} - ${material['name']}',
                              overflow: TextOverflow.ellipsis,
                            ),
                          );
                        }).toList(),
                        onChanged: (value) {
                          setState(() {
                            _selectedMaterialId = value;
                          });
                        },
                        validator: (value) {
                          if (value == null) {
                            return 'Παρακαλώ επιλέξτε υλικό';
                          }
                          return null;
                        },
                      ),
                      
                      // Show material details if selected
                      if (_selectedMaterialId != null) ...[
                        const SizedBox(height: 12),
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.blue.shade50,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Builder(
                            builder: (context) {
                              final material = appState.materials.firstWhere(
                                (m) => m['id'] == _selectedMaterialId,
                                orElse: () => {},
                              );
                              if (material.isEmpty) return const SizedBox.shrink();
                              return Row(
                                children: [
                                  Container(
                                    width: 50,
                                    height: 50,
                                    decoration: BoxDecoration(
                                      color: Colors.blue.shade100,
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: const Icon(
                                      Icons.inventory_2,
                                      color: Colors.blue,
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          material['name'] ?? '',
                                          style: const TextStyle(
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                        Text(
                                          'Κατηγορία: ${material['category'] ?? 'N/A'}',
                                          style: TextStyle(
                                            fontSize: 12,
                                            color: Colors.grey.shade600,
                                          ),
                                        ),
                                        Text(
                                          'Μονάδα: ${material['unit'] ?? 'τεμ'}',
                                          style: TextStyle(
                                            fontSize: 12,
                                            color: Colors.grey.shade600,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              );
                            },
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Quantity Card
              Card(
                elevation: 2,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _transactionType == 'out' 
                            ? 'Ποσότητα (θα αφαιρεθεί)'
                            : 'Ποσότητα (θα προστεθεί)',
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          IconButton(
                            onPressed: () {
                              final current = int.tryParse(_quantityController.text) ?? 1;
                              if (current > 1) {
                                _quantityController.text = (current - 1).toString();
                              }
                            },
                            icon: const Icon(Icons.remove_circle),
                            iconSize: 40,
                            color: Colors.orange,
                          ),
                          Expanded(
                            child: TextFormField(
                              controller: _quantityController,
                              keyboardType: TextInputType.number,
                              textAlign: TextAlign.center,
                              style: const TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.bold,
                              ),
                              decoration: InputDecoration(
                                border: const OutlineInputBorder(),
                                prefixIcon: Icon(
                                  _transactionType == 'out' 
                                      ? Icons.remove 
                                      : Icons.add,
                                  color: _transactionType == 'out' 
                                      ? Colors.red 
                                      : Colors.green,
                                ),
                                hintText: '0',
                              ),
                              validator: (value) {
                                if (value == null || value.isEmpty) {
                                  return 'Εισάγετε ποσότητα';
                                }
                                final quantity = int.tryParse(value);
                                if (quantity == null || quantity <= 0) {
                                  return 'Μη έγκυρη ποσότητα';
                                }
                                return null;
                              },
                            ),
                          ),
                          IconButton(
                            onPressed: () {
                              final current = int.tryParse(_quantityController.text) ?? 0;
                              _quantityController.text = (current + 1).toString();
                            },
                            icon: const Icon(Icons.add_circle),
                            iconSize: 40,
                            color: Colors.orange,
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      // Quick quantity buttons
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [5, 10, 20, 50, 100].map((qty) {
                          return ActionChip(
                            label: Text('+$qty'),
                            onPressed: () {
                              final current = int.tryParse(_quantityController.text) ?? 0;
                              _quantityController.text = (current + qty).toString();
                            },
                          );
                        }).toList(),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Notes Card
              Card(
                elevation: 2,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Σημειώσεις (προαιρετικό)',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _notesController,
                        maxLines: 3,
                        decoration: const InputDecoration(
                          border: OutlineInputBorder(),
                          hintText: 'π.χ. Παραλαβή από προμηθευτή',
                          alignLabelWithHint: true,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Submit Button
              SizedBox(
                height: 56,
                child: ElevatedButton(
                  onPressed: _isSubmitting ? null : _handleSubmit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: _transactionType == 'out' 
                        ? Colors.red 
                        : Colors.green,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: _isSubmitting
                      ? const SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(
                            color: Colors.white,
                            strokeWidth: 2,
                          ),
                        )
                      : Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              _transactionType == 'out'
                                  ? Icons.remove_circle
                                  : Icons.add_box,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              _transactionType == 'out'
                                  ? 'Αφαίρεση από Αποθήκη'
                                  : 'Προσθήκη στην Αποθήκη',
                              style: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
