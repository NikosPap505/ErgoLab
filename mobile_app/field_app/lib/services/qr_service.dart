import 'dart:convert';
import 'api_service.dart';

class QRService {
  final ApiService apiService;
  static const Set<String> _allowedTypes = {'material', 'worker'};

  QRService({required this.apiService});

  Future<Map<String, dynamic>> handleScan(String rawValue) async {
    try {
      final data = _parseQrPayload(rawValue);
      final type = data['type'] as String;
      final id = _parseId(data['id']);
      if (id == null) {
        throw const FormatException('Missing or invalid id');
      }

      final response = await apiService.handleQrScan({
        'type': type,
        'id': id,
        'action': 'view',
        'additional_data': data,
      });

      return response;
    } catch (e) {
      throw Exception('Invalid QR code: $e');
    }
  }

  Future<String> getMaterialQR(int materialId) async {
    return apiService.getMaterialQr(materialId);
  }

  Map<String, dynamic> _parseQrPayload(String rawValue) {
    final dynamic decoded = json.decode(rawValue);
    if (decoded is! Map) {
      throw const FormatException('QR payload must be an object');
    }

    final data = Map<String, dynamic>.from(decoded);
    final type = data['type'];
    if (type is! String || !_allowedTypes.contains(type)) {
      throw const FormatException('Unsupported QR type');
    }

    if (!data.containsKey('id')) {
      throw const FormatException('Missing id');
    }

    return data;
  }

  int? _parseId(dynamic id) {
    if (id is int) return id;
    if (id is String) return int.tryParse(id);
    return null;
  }
}
