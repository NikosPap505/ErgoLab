import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';

class ConnectivityService with ChangeNotifier {
  final Connectivity _connectivity = Connectivity();
  StreamSubscription<dynamic>? _subscription;
  
  bool _isOnline = true;
  bool get isOnline => _isOnline;

  ConnectivityService() {
    _initConnectivity();
    _subscription = _connectivity.onConnectivityChanged.listen(_updateConnectionStatus);
  }

  Future<void> _initConnectivity() async {
    try {
      final result = await _connectivity.checkConnectivity();
      _updateConnectionStatus(result);
    } catch (e) {
      debugPrint('Connectivity check error: $e');
      _isOnline = false;
      notifyListeners();
    }
  }

  void _updateConnectionStatus(dynamic result) {
    final wasOnline = _isOnline;
    
    // Check if connection is available (not none)
    if (result is List<ConnectivityResult>) {
      _isOnline = result.any((r) => r != ConnectivityResult.none);
    } else if (result is ConnectivityResult) {
      _isOnline = result != ConnectivityResult.none;
    } else {
      _isOnline = false;
    }
    
    if (wasOnline != _isOnline) {
      debugPrint('Connectivity changed: ${_isOnline ? "Online" : "Offline"}');
      notifyListeners();
    }
  }

  Future<bool> checkConnectivity() async {
    final result = await _connectivity.checkConnectivity();
    _updateConnectionStatus(result);
    return _isOnline;
  }

  @override
  void dispose() {
    _subscription?.cancel();
    super.dispose();
  }
}
