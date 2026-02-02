import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as path;
import 'package:image/image.dart' as img;

/// Service for compressing images before upload
/// Reduces bandwidth usage and improves offline performance
class ImageCompressionService {
  // Compression settings
  static const int maxWidth = 1920;
  static const int maxHeight = 1920;
  static const int quality = 85;
  static const int thumbnailSize = 200;
  static const Duration _tempRetention = Duration(days: 7);
  
  // Cleanup tracking (class-level statics)
  static DateTime? _lastCleanup;
  static const Duration _cleanupInterval = Duration(hours: 1);
  static Future<void>? _cleanupTask;

  /// Periodic cleanup of temp files (throttled to once per hour)
  /// Synchronized to prevent concurrent cleanup from compressMultiple
  static Future<void> _maybeCleanupTempFiles(Directory tempDir) async {
    final now = DateTime.now();
    
    // Check timestamp first (fast path)
    if (_lastCleanup != null && 
        now.difference(_lastCleanup!) < _cleanupInterval) {
      return;
    }
    
    // If cleanup is already in progress, await it instead of starting another
    if (_cleanupTask != null) {
      await _cleanupTask;
      return;
    }
    
    // Start cleanup with synchronization
    _cleanupTask = _runCleanup(tempDir, now);
    try {
      await _cleanupTask;
    } finally {
      _cleanupTask = null;
    }
  }

  /// Internal cleanup runner - only one instance runs at a time
  static Future<void> _runCleanup(Directory tempDir, DateTime timestamp) async {
    try {
      _lastCleanup = timestamp;
      await _cleanupTempFiles(tempDir);
    } catch (e) {
      debugPrint('Cleanup task error: $e');
    }
  }

  /// Compress an image file for upload
  /// Returns the path to the compressed file
  static Future<String> compressImage(String sourcePath) async {
    try {
      final sourceFile = File(sourcePath);
      if (!await sourceFile.exists()) {
        throw Exception('Source file does not exist: $sourcePath');
      }

      // Read the image
      final bytes = await sourceFile.readAsBytes();
      final image = await compute(_decodeImage, bytes);
      
      if (image == null) {
        debugPrint('⚠️ Could not decode image, returning original');
        return sourcePath;
      }

      // Resize if needed
      img.Image resizedImage = image;
      if (image.width > maxWidth || image.height > maxHeight) {
        resizedImage = img.copyResize(
          image,
          width: image.width > image.height ? maxWidth : null,
          height: image.height >= image.width ? maxHeight : null,
          interpolation: img.Interpolation.linear,
        );
        debugPrint('📐 Resized image from ${image.width}x${image.height} to ${resizedImage.width}x${resizedImage.height}');
      }

      // Compress to JPEG
      final compressedBytes = img.encodeJpg(resizedImage, quality: quality);

      // Save to temp directory
      final tempDir = await getTemporaryDirectory();
      await _maybeCleanupTempFiles(tempDir);
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final compressedPath = path.join(tempDir.path, 'compressed_$timestamp.jpg');
      
      final compressedFile = File(compressedPath);
      await compressedFile.writeAsBytes(compressedBytes);

      // Log compression ratio
      final originalSize = await sourceFile.length();
      final compressedSize = compressedBytes.length;
      final ratio = ((1 - compressedSize / originalSize) * 100).toStringAsFixed(1);
      debugPrint('✅ Compressed image: ${_formatFileSize(originalSize)} → ${_formatFileSize(compressedSize)} ($ratio% reduction)');

      return compressedPath;
    } catch (e) {
      debugPrint('❌ Image compression error: $e');
      return sourcePath; // Return original on error
    }
  }

  /// Create a thumbnail for quick preview
  static Future<String> createThumbnail(String sourcePath) async {
    try {
      final sourceFile = File(sourcePath);
      final bytes = await sourceFile.readAsBytes();
      final image = await compute(_decodeImage, bytes);
      
      if (image == null) {
        throw Exception('Could not decode image');
      }

      // Create thumbnail
      final thumbnail = img.copyResizeCropSquare(image, size: thumbnailSize);
      final thumbnailBytes = img.encodeJpg(thumbnail, quality: 70);

      // Save thumbnail
      final tempDir = await getTemporaryDirectory();
      await _cleanupTempFiles(tempDir);
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final thumbnailPath = path.join(tempDir.path, 'thumb_$timestamp.jpg');
      
      final thumbnailFile = File(thumbnailPath);
      await thumbnailFile.writeAsBytes(thumbnailBytes);

      debugPrint('✅ Created thumbnail: ${_formatFileSize(thumbnailBytes.length)}');
      return thumbnailPath;
    } catch (e) {
      debugPrint('❌ Thumbnail creation error: $e');
      return sourcePath;
    }
  }

  /// Compress multiple images in parallel
  static Future<List<String>> compressMultiple(List<String> paths) async {
    final futures = paths.map((p) => compressImage(p));
    return await Future.wait(futures);
  }

  /// Get image dimensions without loading full image
  static Future<Map<String, int>?> getImageDimensions(String filePath) async {
    try {
      final file = File(filePath);
      final bytes = await file.readAsBytes();
      final image = await compute(_decodeImage, bytes);
      
      if (image == null) return null;
      
      return {
        'width': image.width,
        'height': image.height,
      };
    } catch (e) {
      debugPrint('Error getting dimensions: $e');
      return null;
    }
  }

  /// Estimate compressed file size
  static Future<int> estimateCompressedSize(String filePath) async {
    final file = File(filePath);
    final originalSize = await file.length();
    
    // Rough estimation based on typical compression ratios
    // JPEG at 85% quality typically achieves 60-80% of original
    return (originalSize * 0.4).round();
  }

  // Helper to decode image in isolate
  static img.Image? _decodeImage(Uint8List bytes) {
    return img.decodeImage(bytes);
  }

  static Future<void> _cleanupTempFiles(Directory tempDir) async {
    try {
      final cutoff = DateTime.now().subtract(_tempRetention);
      await for (final entity in tempDir.list()) {
        if (entity is! File) continue;
        final name = path.basename(entity.path);
        if (!name.startsWith('compressed_') && !name.startsWith('thumb_')) {
          continue;
        }
        final stat = await entity.stat();
        if (stat.modified.isBefore(cutoff)) {
          await entity.delete();
        }
      }
    } catch (e) {
      debugPrint('Temp cleanup error: $e');
    }
  }

  // Format file size for logging
  static String _formatFileSize(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
}
