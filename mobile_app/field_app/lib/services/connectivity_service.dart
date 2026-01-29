import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';

class ConnectivityService with ChangeNotifier {
  final Connectivity _connectivity = Connectivity();
  StreamSubscription<List<ConnectivityResult>>? _subscription;
  
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
      print('Connectivity check error: $e');
      _isOnline = false;
      notifyListeners();
    }
  }

  void _updateConnectionStatus(List<ConnectivityResult> results) {
    final wasOnline = _isOnline;
    
    // Check if any connection is available (not none)
    _isOnline = results.any((result) => result != ConnectivityResult.none);
    
    if (wasOnline != _isOnline) {
      print('Connectivity changed: ${_isOnline ? "Online" : "Offline"}');
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
