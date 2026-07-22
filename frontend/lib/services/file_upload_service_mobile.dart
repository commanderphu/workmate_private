import 'dart:io';
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:image_picker/image_picker.dart';
import 'package:permission_handler/permission_handler.dart';

import 'file_upload_service_stub.dart';

/// Mobile implementation of FileUploadService using image_picker and file_picker
class FileUploadService {
  final ImagePicker _imagePicker = ImagePicker();

  /// Request camera permission
  Future<bool> _requestCameraPermission() async {
    final status = await Permission.camera.request();
    return status.isGranted;
  }

  /// Request photos permission (Android 13+)
  Future<bool> _requestPhotosPermission() async {
    if (Platform.isAndroid) {
      // Android 13+ uses granular media permissions
      final status = await Permission.photos.request();
      return status.isGranted || status.isLimited;
    }
    return true;
  }

  /// Pick a file from the camera
  Future<FileUploadResult?> pickFromCamera() async {
    try {
      // Request camera permission
      final hasPermission = await _requestCameraPermission();
      if (!hasPermission) {
        debugPrint('Camera permission denied');
        throw Exception('Kamera-Berechtigung wurde verweigert');
      }

      final XFile? photo = await _imagePicker.pickImage(
        source: ImageSource.camera,
        preferredCameraDevice: CameraDevice.rear,
        imageQuality: 85,
      );

      if (photo == null) return null;

      final File file = File(photo.path);
      final bytes = await file.readAsBytes();

      return FileUploadResult(
        bytes: bytes,
        filename: photo.name,
      );
    } catch (e) {
      debugPrint('Error picking from camera: $e');
      rethrow;
    }
  }

  /// Pick a file from the gallery
  Future<FileUploadResult?> pickFromGallery() async {
    try {
      // Request photos permission
      final hasPermission = await _requestPhotosPermission();
      if (!hasPermission) {
        debugPrint('Photos permission denied');
        throw Exception('Foto-Berechtigung wurde verweigert');
      }

      final XFile? image = await _imagePicker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 85,
      );

      if (image == null) return null;

      final File file = File(image.path);
      final bytes = await file.readAsBytes();

      return FileUploadResult(
        bytes: bytes,
        filename: image.name,
      );
    } catch (e) {
      debugPrint('Error picking from gallery: $e');
      rethrow;
    }
  }

  /// Pick any file (PDF, images)
  Future<FileUploadResult?> pickFile() async {
    try {
      // Request storage permission for file access
      final hasPermission = await _requestPhotosPermission();
      if (!hasPermission) {
        debugPrint('Storage permission denied');
        throw Exception('Speicher-Berechtigung wurde verweigert');
      }

      final FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'jpg', 'jpeg', 'png'],
      );

      if (result == null || result.files.isEmpty) return null;

      final pickedFile = result.files.first;

      // Get bytes
      Uint8List? bytes;
      if (pickedFile.bytes != null) {
        bytes = pickedFile.bytes;
      } else if (pickedFile.path != null) {
        final File file = File(pickedFile.path!);
        bytes = await file.readAsBytes();
      }

      if (bytes == null) {
        throw Exception('Datei konnte nicht gelesen werden');
      }

      return FileUploadResult(
        bytes: bytes,
        filename: pickedFile.name,
      );
    } catch (e) {
      debugPrint('Error picking file: $e');
      rethrow;
    }
  }
}
