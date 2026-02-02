import 'dart:convert';
import 'api_service.dart';

class QRService {
  final ApiService apiService;

  QRService({required this.apiService});

  Future<Map<String, dynamic>> handleScan(String rawValue) async {
    try {
      final data = json.decode(rawValue) as Map<String, dynamic>;

      final response = await apiService.handleQrScan({
        'type': data['type'],
        'id': data['id'],
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
}
