import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:field_app/widgets/error_boundary.dart';

void main() {
  group('SafeBuilder', () {
    testWidgets('renders child when no error', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: SafeBuilder(
            builder: _buildValidWidget,
          ),
        ),
      );

      expect(find.text('Valid Content'), findsOneWidget);
    });

    testWidgets('renders error widget when builder throws', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: SafeBuilder(
            builder: (_) => throw Exception('Test error'),
            errorBuilder: (_, error) => Text('Error: $error'),
          ),
        ),
      );

      expect(find.textContaining('Error:'), findsOneWidget);
    });

    testWidgets('renders default error widget when no errorBuilder', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: SafeBuilder(
            builder: (_) => throw Exception('Test error'),
          ),
        ),
      );

      expect(find.byIcon(Icons.warning_amber), findsOneWidget);
    });
  });

  group('ErrorBoundary', () {
    testWidgets('renders child when no error', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: ErrorBoundary(
            child: Text('Child Content'),
          ),
        ),
      );

      expect(find.text('Child Content'), findsOneWidget);
    });
  });
}

Widget _buildValidWidget(BuildContext context) {
  return const Text('Valid Content');
}
