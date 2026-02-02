import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
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

  @override
  void initState() {
    super.initState();
    final apiService = context.read<AppState>().apiService;
    _qrService = QRService(apiService: apiService);
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
              if (_isProcessing) return;

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
    setState(() => _isProcessing = true);

    try {
      final result = await _qrService.handleScan(rawValue);

      cameraController.stop();

      if (!mounted) return;

      if (result['type'] == 'material') {
        _showMaterialDetail(result['data']);
      } else if (result['type'] == 'worker') {
        _showWorkerDetail(result['data']);
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
          _navigateToStockTransaction(materialData['id'] as int);
        },
      ),
    );
  }

  void _showWorkerDetail(Map<String, dynamic> workerData) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(workerData['full_name'] ?? 'Worker'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Username: ${workerData['username']}'),
            Text('Role: ${workerData['role']}'),
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
              _handleWorkerCheckIn(workerData['id'] as int);
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

    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) {
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
    cameraController.dispose();
    super.dispose();
  }
}
