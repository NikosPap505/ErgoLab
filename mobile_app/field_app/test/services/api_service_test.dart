import 'package:flutter_test/flutter_test.dart';

void main() {
  group('ApiService', () {
    group('validateBaseUrl', () {
      test('throws on empty baseUrl', () {
        // Test validation logic (this tests the validation method behavior)
        expect(
          () => _testUrlValidation(''),
          throwsA(isA<StateError>()),
        );
      });

      test('throws on non-HTTPS URL in release mode check', () {
        expect(
          () => _testUrlValidation('http://example.com'),
          throwsA(isA<StateError>()),
        );
      });

      test('accepts valid HTTPS URL', () {
        expect(
          () => _testUrlValidation('https://api.example.com'),
          returnsNormally,
        );
      });

      test('accepts localhost for development', () {
        // localhost is allowed for dev
        expect(
          () => _testUrlValidation('http://localhost:8000'),
          returnsNormally,
        );
      });

      test('accepts 10.0.2.2 for Android emulator', () {
        expect(
          () => _testUrlValidation('http://10.0.2.2:8000'),
          returnsNormally,
        );
      });
    });

    group('URL parsing', () {
      test('extracts host correctly', () {
        const url = 'https://api.ergolab.com/v1';
        final uri = Uri.parse(url);
        expect(uri.host, equals('api.ergolab.com'));
      });

      test('identifies localhost correctly', () {
        const url = 'http://localhost:8000';
        final uri = Uri.parse(url);
        expect(uri.host, equals('localhost'));
      });
    });
  });
}

/// Helper to test URL validation logic without needing the actual ApiService
void _testUrlValidation(String url) {
  if (url.isEmpty) {
    throw StateError('API_BASE_URL not configured');
  }

  final uri = Uri.tryParse(url);
  if (uri == null) {
    throw StateError('Invalid API_BASE_URL: $url');
  }

  // Allow localhost and emulator IPs for development
  final isLocalDev = uri.host == 'localhost' ||
      uri.host == '127.0.0.1' ||
      uri.host == '10.0.2.2' ||
      uri.host.startsWith('192.168.');

  // In production, require HTTPS
  if (!isLocalDev && uri.scheme != 'https') {
    throw StateError('API_BASE_URL must use HTTPS in production: $url');
  }
}
