import 'package:flutter_test/flutter_test.dart';
import 'package:field_app/services/qr_service.dart';
import 'package:field_app/services/api_service.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';

@GenerateMocks([ApiService])
import 'qr_service_test.mocks.dart';

void main() {
  late QRService qrService;
  late MockApiService mockApiService;

  setUp(() {
    mockApiService = MockApiService();
    qrService = QRService(apiService: mockApiService);
  });

  group('QRService', () {
    group('handleScan', () {
      test('parses valid material QR code', () async {
        const rawValue = '{"type": "material", "id": 123}';
        when(mockApiService.handleQrScan(any)).thenAnswer(
          (_) async => {'type': 'material', 'data': {'id': 123, 'name': 'Test'}},
        );

        final result = await qrService.handleScan(rawValue);

        expect(result['type'], equals('material'));
        verify(mockApiService.handleQrScan(argThat(
          containsPair('type', 'material'),
        ))).called(1);
      });

      test('parses valid worker QR code', () async {
        const rawValue = '{"type": "worker", "id": 456}';
        when(mockApiService.handleQrScan(any)).thenAnswer(
          (_) async => {'type': 'worker', 'data': {'id': 456, 'name': 'John'}},
        );

        final result = await qrService.handleScan(rawValue);

        expect(result['type'], equals('worker'));
      });

      test('handles string id correctly', () async {
        const rawValue = '{"type": "material", "id": "789"}';
        when(mockApiService.handleQrScan(any)).thenAnswer(
          (_) async => {'type': 'material', 'data': {'id': 789}},
        );

        final result = await qrService.handleScan(rawValue);

        expect(result['type'], equals('material'));
        verify(mockApiService.handleQrScan(argThat(
          containsPair('id', 789),
        ))).called(1);
      });

      test('throws on invalid JSON', () async {
        const rawValue = 'not valid json';

        expect(
          () => qrService.handleScan(rawValue),
          throwsA(isA<Exception>()),
        );
      });

      test('throws on unsupported type', () async {
        const rawValue = '{"type": "unknown", "id": 123}';

        expect(
          () => qrService.handleScan(rawValue),
          throwsA(isA<Exception>()),
        );
      });

      test('throws on missing id', () async {
        const rawValue = '{"type": "material"}';

        expect(
          () => qrService.handleScan(rawValue),
          throwsA(isA<Exception>()),
        );
      });

      test('throws on array payload', () async {
        const rawValue = '[1, 2, 3]';

        expect(
          () => qrService.handleScan(rawValue),
          throwsA(isA<Exception>()),
        );
      });

      test('throws on invalid id type', () async {
        const rawValue = '{"type": "material", "id": null}';

        expect(
          () => qrService.handleScan(rawValue),
          throwsA(isA<Exception>()),
        );
      });
    });

    group('getMaterialQR', () {
      test('calls apiService correctly', () async {
        when(mockApiService.getMaterialQr(any)).thenAnswer(
          (_) async => 'qr_code_data',
        );

        final result = await qrService.getMaterialQR(123);

        expect(result, equals('qr_code_data'));
        verify(mockApiService.getMaterialQr(123)).called(1);
      });
    });
  });
}
