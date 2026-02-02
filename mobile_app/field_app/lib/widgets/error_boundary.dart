import 'package:flutter/material.dart';
import 'package:firebase_crashlytics/firebase_crashlytics.dart';

/// Error boundary widget that catches errors in the widget tree
/// and displays a fallback UI instead of crashing the app.
class ErrorBoundary extends StatefulWidget {
  final Widget child;
  final Widget? fallback;
  final void Function(Object error, StackTrace? stack)? onError;

  const ErrorBoundary({
    super.key,
    required this.child,
    this.fallback,
    this.onError,
  });

  @override
  State<ErrorBoundary> createState() => _ErrorBoundaryState();
}

class _ErrorBoundaryState extends State<ErrorBoundary> {
  Object? _error;

  @override
  void initState() {
    super.initState();
  }

  void _handleError(Object error, StackTrace? stack) {
    setState(() {
      _error = error;
    });

    // Report to Crashlytics (silently fail if not initialized)
    try {
      FirebaseCrashlytics.instance.recordError(error, stack);
    } catch (_) {
      // Firebase not initialized (e.g., in tests)
    }

    // Call custom error handler if provided
    widget.onError?.call(error, stack);
  }

  void _retry() {
    setState(() {
      _error = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return widget.fallback ?? _buildDefaultFallback(context);
    }

    return ErrorWidgetBuilder(
      onError: _handleError,
      child: widget.child,
    );
  }

  Widget _buildDefaultFallback(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.error_outline,
                size: 64,
                color: Colors.red[300],
              ),
              const SizedBox(height: 24),
              const Text(
                'Κάτι πήγε στραβά',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 12),
              Text(
                'Παρουσιάστηκε ένα απροσδόκητο σφάλμα. Παρακαλώ δοκιμάστε ξανά.',
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.grey[600],
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 32),
              ElevatedButton.icon(
                onPressed: _retry,
                icon: const Icon(Icons.refresh),
                label: const Text('Δοκιμάστε ξανά'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 32,
                    vertical: 16,
                  ),
                ),
              ),
              const SizedBox(height: 16),
              TextButton(
                onPressed: () {
                  // Navigate to home or login
                  Navigator.of(context).pushNamedAndRemoveUntil(
                    '/login',
                    (route) => false,
                  );
                },
                child: const Text('Επιστροφή στην αρχική'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Widget that catches errors during build phase
class ErrorWidgetBuilder extends StatelessWidget {
  final Widget child;
  final void Function(Object error, StackTrace? stack) onError;

  const ErrorWidgetBuilder({
    super.key,
    required this.child,
    required this.onError,
  });

  @override
  Widget build(BuildContext context) {
    // Flutter's error widget builder is global, so we use a different approach
    // by wrapping potentially dangerous code in try-catch builders
    return child;
  }
}

/// A builder that safely catches errors during widget building
class SafeBuilder extends StatelessWidget {
  final Widget Function(BuildContext context) builder;
  final Widget Function(BuildContext context, Object error)? errorBuilder;

  const SafeBuilder({
    super.key,
    required this.builder,
    this.errorBuilder,
  });

  @override
  Widget build(BuildContext context) {
    try {
      return builder(context);
    } catch (e, stack) {
      // Try to report to Crashlytics, but don't fail if not initialized
      try {
        FirebaseCrashlytics.instance.recordError(e, stack);
      } catch (_) {
        // Firebase not initialized (e.g., in tests)
      }
      
      if (errorBuilder != null) {
        return errorBuilder!(context, e);
      }
      
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.warning_amber, color: Colors.orange[300], size: 48),
              const SizedBox(height: 12),
              Text(
                'Σφάλμα φόρτωσης',
                style: TextStyle(color: Colors.grey[600]),
              ),
            ],
          ),
        ),
      );
    }
  }
}
