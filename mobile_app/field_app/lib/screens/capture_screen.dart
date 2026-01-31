import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/connectivity_service.dart';
import '../services/offline_database.dart';
import '../services/image_compression_service.dart';

class CaptureScreen extends StatefulWidget {
  const CaptureScreen({super.key});

  @override
  State<CaptureScreen> createState() => _CaptureScreenState();
}

class _CaptureScreenState extends State<CaptureScreen> {
  final ImagePicker _picker = ImagePicker();
  XFile? _capturedImage;
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();
  bool _isUploading = false;
  bool _isCompressing = false;
  String? _compressedPath;

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _captureImage(ImageSource source) async {
    try {
      final XFile? image = await _picker.pickImage(
        source: source,
        maxWidth: 1920,
        maxHeight: 1080,
        imageQuality: 85,
      );

      if (image != null) {
        setState(() {
          _capturedImage = image;
          _isCompressing = true;
          // Auto-generate title from timestamp
          if (_titleController.text.isEmpty) {
            final now = DateTime.now();
            _titleController.text =
                'Φωτο_${now.day}-${now.month}-${now.year}_${now.hour}${now.minute}';
          }
        });
        
        // Compress image in background
        final compressed = await ImageCompressionService.compressImage(image.path);
        if (mounted) {
          setState(() {
            _compressedPath = compressed;
            _isCompressing = false;
          });
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isCompressing = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Σφάλμα: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _uploadImage() async {
    if (_capturedImage == null) return;

    if (_titleController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Εισάγετε τίτλο'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    setState(() {
      _isUploading = true;
    });

    final appState = context.read<AppState>();
    final connectivity = context.read<ConnectivityService>();
    final pathToUpload = _compressedPath ?? _capturedImage!.path;
    
    bool success = false;
    bool savedOffline = false;

    if (connectivity.isOnline) {
      // Try online upload
      final result = await appState.apiService.uploadDocument(
        filePath: pathToUpload,
        fileName: _titleController.text,
        fileType: 'photo',
        projectId: appState.selectedProjectId,
        description: _descriptionController.text.isEmpty
            ? null
            : _descriptionController.text,
      );
      success = result != null;
    }
    
    if (!success) {
      // Save for offline sync
      await OfflineDatabase.addPendingUpload(
        filePath: pathToUpload,
        title: _titleController.text,
        description: _descriptionController.text.isEmpty 
            ? null 
            : _descriptionController.text,
        projectId: appState.selectedProjectId,
        fileType: 'photo',
      );
      savedOffline = true;
      success = true;
    }

    if (mounted) {
      setState(() {
        _isUploading = false;
      });

      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                Icon(
                  savedOffline ? Icons.cloud_off : Icons.cloud_done,
                  color: Colors.white,
                  size: 20,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    savedOffline
                        ? 'Αποθηκεύτηκε τοπικά - θα συγχρονιστεί'
                        : 'Η φωτογραφία αποθηκεύτηκε επιτυχώς!',
                  ),
                ),
              ],
            ),
            backgroundColor: savedOffline ? Colors.orange : Colors.green,
          ),
        );
        Navigator.of(context).pop();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Σφάλμα κατά την αποθήκευση'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Λήψη Φωτογραφίας'),
        backgroundColor: Colors.purple,
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Image Preview / Capture Buttons
            if (_capturedImage == null) ...[
              // Capture options
              const Text(
                'Επιλέξτε τρόπο λήψης:',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: _CaptureOptionCard(
                      icon: Icons.camera_alt,
                      title: 'Κάμερα',
                      subtitle: 'Λήψη νέας φωτογραφίας',
                      color: Colors.purple,
                      onTap: () => _captureImage(ImageSource.camera),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: _CaptureOptionCard(
                      icon: Icons.photo_library,
                      title: 'Γκαλερί',
                      subtitle: 'Επιλογή από συσκευή',
                      color: Colors.blue,
                      onTap: () => _captureImage(ImageSource.gallery),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 32),
              
              // Placeholder
              Container(
                width: double.infinity,
                height: 300,
                decoration: BoxDecoration(
                  color: Colors.grey.shade200,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: Colors.grey.shade300,
                    width: 2,
                    style: BorderStyle.solid,
                  ),
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.add_a_photo,
                      size: 64,
                      color: Colors.grey.shade400,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Δεν έχει επιλεγεί φωτογραφία',
                      style: TextStyle(
                        color: Colors.grey.shade600,
                        fontSize: 16,
                      ),
                    ),
                  ],
                ),
              ),
            ] else ...[
              // Image Preview
              ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: Stack(
                  children: [
                    Image.file(
                      File(_capturedImage!.path),
                      width: double.infinity,
                      height: 300,
                      fit: BoxFit.cover,
                    ),
                    Positioned(
                      top: 8,
                      right: 8,
                      child: Row(
                        children: [
                          CircleAvatar(
                            backgroundColor: Colors.black54,
                            child: IconButton(
                              icon: const Icon(Icons.camera_alt, color: Colors.white),
                              onPressed: () => _captureImage(ImageSource.camera),
                            ),
                          ),
                          const SizedBox(width: 8),
                          CircleAvatar(
                            backgroundColor: Colors.red,
                            child: IconButton(
                              icon: const Icon(Icons.close, color: Colors.white),
                              onPressed: () {
                                setState(() {
                                  _capturedImage = null;
                                });
                              },
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // Title
              TextField(
                controller: _titleController,
                decoration: const InputDecoration(
                  labelText: 'Τίτλος *',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.title),
                ),
              ),
              const SizedBox(height: 16),

              // Description
              TextField(
                controller: _descriptionController,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'Περιγραφή (προαιρετικά)',
                  border: OutlineInputBorder(),
                  alignLabelWithHint: true,
                  prefixIcon: Icon(Icons.description),
                ),
              ),
              const SizedBox(height: 24),

              // Upload button
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton.icon(
                  onPressed: _isUploading ? null : _uploadImage,
                  icon: _isUploading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            color: Colors.white,
                            strokeWidth: 2,
                          ),
                        )
                      : const Icon(Icons.cloud_upload),
                  label: Text(
                    _isUploading ? 'Αποθήκευση...' : 'Αποθήκευση Φωτογραφίας',
                    style: const TextStyle(fontSize: 16),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.purple,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _CaptureOptionCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final Color color;
  final VoidCallback onTap;

  const _CaptureOptionCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(20),
          child: Column(
            children: [
              Icon(
                icon,
                size: 48,
                color: color,
              ),
              const SizedBox(height: 12),
              Text(
                title,
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                subtitle,
                style: TextStyle(
                  color: Colors.grey.shade600,
                  fontSize: 12,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
