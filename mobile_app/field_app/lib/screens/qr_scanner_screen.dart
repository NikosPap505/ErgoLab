import 'dart:async';
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/qr_service.dart';
import '../widgets/material_detail_sheet.dart';

class QRScannerScreen extends StatefulWidget {
  const QRScannerScreen({super.key});

  @override
  State<QRScannerScreen> createState() => _QRScannerScreenState();
}

class _QRScannerScreenState extends State<QRScannerScreen> {
  late final QRService _qrService;
  final MobileScannerController cameraController = MobileScannerController();
  bool _isProcessing = false;
  bool _cameraReady = false;
  bool _isDisposed = false;
  Timer? _restartTimer;

  @override
  void initState() {
    super.initState();
    final apiService = context.read<AppState>().apiService;
    _qrService = QRService(apiService: apiService);
    _initCamera();
  }

  Future<void> _initCamera() async {
    final granted = await _ensureCameraPermission();
    if (!mounted) return;
    setState(() {
      _cameraReady = granted;
    });
    if (granted) {
      await cameraController.start();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Σάρωση QR Code'),
        actions: [
          IconButton(
            icon: ValueListenableBuilder(
              valueListenable: cameraController.torchState,
              builder: (context, state, child) {
                switch (state) {
                  case TorchState.off:
                    return const Icon(Icons.flash_off);
                  case TorchState.on:
                    return const Icon(Icons.flash_on, color: Colors.yellow);
                }
              },
            ),
            onPressed: () => cameraController.toggleTorch(),
          ),
          IconButton(
            icon: const Icon(Icons.cameraswitch),
            onPressed: () => cameraController.switchCamera(),
          ),
        ],
      ),
      body: Stack(
        children: [
          MobileScanner(
            controller: cameraController,
            onDetect: (capture) {
              if (_isProcessing || !_cameraReady) return;

              final List<Barcode> barcodes = capture.barcodes;
              for (final barcode in barcodes) {
                if (barcode.rawValue != null) {
                  _handleQRCode(barcode.rawValue!);
                  break;
                }
              }
            },
          ),

          Center(
            child: Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                border: Border.all(
                  color: Colors.white,
                  width: 3,
                ),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.black54,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Text(
                      'Σαρώστε το QR code',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
              ),
            ),
          ),

          if (_isProcessing)
            Container(
              color: Colors.black54,
              child: const Center(
                child: CircularProgressIndicator(),
              ),
            ),
        ],
      ),
    );
  }

  Future<void> _handleQRCode(String rawValue) async {
    if (_isProcessing) return;
    setState(() => _isProcessing = true);

    try {
      await cameraController.stop();
      final result = await _qrService.handleScan(rawValue);
      if (!mounted) return;

      final type = result['type'];
      final data = result['data'];

      if (type == 'material' && data is Map<String, dynamic>) {
        _showMaterialDetail(data);
      } else if (type == 'worker' && data is Map<String, dynamic>) {
        _showWorkerDetail(data);
      } else {
        _showError('Μη υποστηριζόμενο QR code');
      }
    } catch (e) {
      _showError('Σφάλμα σάρωσης: $e');
    } finally {
      if (mounted) {
        setState(() => _isProcessing = false);
      }
    }
  }

  void _showMaterialDetail(Map<String, dynamic> materialData) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => MaterialDetailSheet(
        materialData: materialData,
        onClose: () {
          Navigator.pop(context);
          cameraController.start();
        },
        onTransaction: () {
          Navigator.pop(context);
          final id = _parseId(materialData['id']);
          if (id != null) {
            _navigateToStockTransaction(id);
          } else {
            _showError('Μη έγκυρα δεδομένα υλικού');
          }
        },
      ),
    );
  }

  void _showWorkerDetail(Map<String, dynamic> workerData) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(workerData['full_name']?.toString() ?? 'Worker'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Username: ${workerData['username'] ?? '-'}'),
            Text('Role: ${workerData['role'] ?? '-'}'),
            const SizedBox(height: 20),
            const Text('Τι θέλετε να κάνετε;'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              cameraController.start();
            },
            child: const Text('Ακύρωση'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              final id = _parseId(workerData['id']);
              if (id != null) {
                _handleWorkerCheckIn(id);
              } else {
                _showError('Μη έγκυρα δεδομένα εργαζομένου');
              }
            },
            child: const Text('Check In'),
          ),
        ],
      ),
    );
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
      ),
    );

    _restartTimer?.cancel();
    _restartTimer = Timer(const Duration(seconds: 2), () {
      if (mounted && !_isDisposed) {
        cameraController.start();
      }
    });
  }

  void _navigateToStockTransaction(int materialId) {
    Navigator.pushNamed(
      context,
      '/add-stock',
      arguments: {'id': materialId},
    ).then((_) {
      cameraController.start();
    });
  }

  Future<void> _handleWorkerCheckIn(int workerId) async {
    _showError('Worker check-in coming soon');
    cameraController.start();
  }

  @override
  void dispose() {
    _isDisposed = true;
    _restartTimer?.cancel();
    cameraController.stop();
    cameraController.dispose();
    super.dispose();
  }

  Future<bool> _ensureCameraPermission() async {
    final status = await Permission.camera.request();
    if (status.isGranted) return true;

    if (status.isPermanentlyDenied) {
      if (!mounted) return false;
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Άδεια κάμερας'),
          content: const Text(
            'Η πρόσβαση στην κάμερα έχει απενεργοποιηθεί. Ενεργοποιήστε την από τις Ρυθμίσεις.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Άκυρο'),
            ),
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
                openAppSettings();
              },
              child: const Text('Ρυθμίσεις'),
            ),
          ],
        ),
      );
      return false;
    }

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Η άδεια κάμερας απαιτείται για σάρωση QR.'),
          backgroundColor: Colors.orange,
        ),
      );
    }
    return false;
  }

  int? _parseId(dynamic id) {
    if (id is int) return id;
    if (id is String) return int.tryParse(id);
    return null;
  }
}
