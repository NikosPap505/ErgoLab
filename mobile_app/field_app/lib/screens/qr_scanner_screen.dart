import 'dart:async';
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/qr_service.dart';
import '../services/offline_database.dart';
import '../widgets/material_detail_sheet.dart';
import '../widgets/material_edit_sheet.dart';
import '../widgets/worker_detail_sheet.dart';

class QRScannerScreen extends StatefulWidget {
  const QRScannerScreen({super.key});

  @override
  State<QRScannerScreen> createState() => _QRScannerScreenState();
}

class _QRScannerScreenState extends State<QRScannerScreen> {
  late final QRService _qrService;
  // Optimized scanner configuration:
  // - Lower resolution for faster processing
  // - Specific formats to reduce CPU work
  // - Return image disabled to save memory
  late final MobileScannerController cameraController = MobileScannerController(
    detectionSpeed: DetectionSpeed.normal,
    facing: CameraFacing.back,
    torchEnabled: false,
    formats: const [BarcodeFormat.qrCode, BarcodeFormat.dataMatrix],
    returnImage: false,
  );
  bool _isProcessing = false;
  bool _cameraReady = false;
  bool _isDisposed = false;
  Timer? _restartTimer;
  DateTime? _lastScanTime;
  static const _scanCooldown = Duration(milliseconds: 500);

  @override
  void initState() {
    super.initState();
    final apiService = context.read<AppState>().apiService;
    _qrService = QRService(apiService: apiService);
    _initCamera();
  }

  Future<void> _initCamera() async {
    final granted = await _ensureCameraPermission();
    if (!mounted || _isDisposed) return;
    
    if (!granted) {
      setState(() {
        _cameraReady = false;
      });
      return;
    }
    
    try {
      await cameraController.start();
      if (!mounted || _isDisposed) return;
      setState(() {
        _cameraReady = true;
      });
    } catch (e) {
      debugPrint('QRScannerScreen: Failed to start camera: $e');
      if (!mounted || _isDisposed) return;
      setState(() {
        _cameraReady = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Σάρωση QR Code'),
        actions: [
          IconButton(
            icon: const Icon(Icons.history),
            tooltip: 'Ιστορικό σαρώσεων',
            onPressed: () => Navigator.pushNamed(context, '/scan-history'),
          ),
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

              // Debounce rapid scans to prevent duplicate processing
              final now = DateTime.now();
              if (_lastScanTime != null &&
                  now.difference(_lastScanTime!) < _scanCooldown) {
                return;
              }
              _lastScanTime = now;

              final List<Barcode> barcodes = capture.barcodes;
              for (final barcode in barcodes) {
                if (barcode.rawValue != null && barcode.rawValue!.isNotEmpty) {
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

  Future<void> _handleQRCode(String rawValue, {int retryCount = 0}) async {
    const maxRetries = 2;
    
    if (_isProcessing) return;
    setState(() => _isProcessing = true);

    try {
      await cameraController.stop();
      final result = await _qrService.handleScan(rawValue);
      if (!mounted) return;

      final type = result['type'];
      final data = result['data'];

      // Save to scan history
      await _saveScanToHistory(
        rawValue: rawValue,
        resultType: type as String?,
        resultData: data is Map<String, dynamic> ? data : null,
      );

      if (type == 'material' && data is Map<String, dynamic>) {
        _showMaterialDetail(data);
      } else if (type == 'worker' && data is Map<String, dynamic>) {
        _showWorkerDetail(data);
      } else {
        _showError('Μη υποστηριζόμενο QR code');
      }
    } catch (e) {
      // Save error to history
      await _saveScanToHistory(
        rawValue: rawValue,
        resultType: 'error',
        resultData: {'error': e.toString()},
      );

      if (retryCount < maxRetries) {
        // Retry after a short delay
        await Future.delayed(const Duration(milliseconds: 500));
        if (mounted && !_isDisposed) {
          setState(() => _isProcessing = false);
          return _handleQRCode(rawValue, retryCount: retryCount + 1);
        }
      } else {
        _showErrorWithRetry(
          'Σφάλμα σάρωσης: $e',
          () => _handleQRCode(rawValue, retryCount: 0),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isProcessing = false);
      }
    }
  }

  void _showErrorWithRetry(String message, VoidCallback onRetry) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
        duration: const Duration(seconds: 5),
        action: SnackBarAction(
          label: 'Επανάληψη',
          textColor: Colors.white,
          onPressed: () {
            if (mounted && !_isDisposed) {
              onRetry();
            }
          },
        ),
      ),
    );

    _restartTimer?.cancel();
    _restartTimer = Timer(const Duration(seconds: 5), () {
      if (mounted && !_isDisposed) {
        cameraController.start();
      }
    });
  }

  /// Saves a scan to local history database
  Future<void> _saveScanToHistory({
    required String rawValue,
    String? resultType,
    Map<String, dynamic>? resultData,
  }) async {
    try {
      String? resultName;
      if (resultData != null) {
        resultName = resultData['name'] as String? ??
            resultData['full_name'] as String? ??
            resultData['sku'] as String?;
      }

      await OfflineDatabase.addScanToHistory(
        rawValue: rawValue,
        scanType: 'qr',
        resultType: resultType,
        resultName: resultName,
        resultData: resultData,
      );
    } catch (e) {
      // Silently fail - scan history is non-critical
      debugPrint('Failed to save scan to history: $e');
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
          if (!mounted || _isDisposed) return;
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
        onEdit: () {
          Navigator.pop(context);
          _showMaterialEdit(materialData);
        },
      ),
    );
  }

  void _showMaterialEdit(Map<String, dynamic> materialData) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => MaterialEditSheet(
        materialData: materialData,
        onClose: () {
          Navigator.pop(context);
          if (!mounted || _isDisposed) return;
          cameraController.start();
        },
        onSaved: (updatedData) {
          // Could refresh or show updated data
          _showMaterialDetail(updatedData);
        },
      ),
    );
  }

  void _showWorkerDetail(Map<String, dynamic> workerData) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => WorkerDetailSheet(
        workerData: workerData,
        onClose: () {
          Navigator.pop(context);
          if (!mounted || _isDisposed) return;
          cameraController.start();
        },
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
      if (!mounted || _isDisposed) return;
      cameraController.start();
    });
  }

  @override
  void dispose() {
    _isDisposed = true;
    _restartTimer?.cancel();
    cameraController.stop();
    cameraController.dispose();
    // QRService cleanup (stateless, but mark as disposed)
    _qrService.dispose();
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
