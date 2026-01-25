import 'dart:typed_data';
import 'package:dio/dio.dart';
import '../config/api_config.dart';
import '../models/document.dart';
import 'api_service.dart';

class DocumentService {
  final ApiService _apiService = ApiService();

  static final DocumentService _instance = DocumentService._internal();
  factory DocumentService() => _instance;
  DocumentService._internal();

  // Upload document
  Future<Document> uploadDocument({
    required Uint8List fileBytes,
    required String filename,
    required String type,
    String? title,
  }) async {
    final formData = FormData.fromMap({
      'file': MultipartFile.fromBytes(
        fileBytes,
        filename: filename,
      ),
      'type': type,
      if (title != null) 'title': title,
    });

    final response = await _apiService.post(
      ApiConfig.documents,
      data: formData,
    );

    return Document.fromJson(response.data);
  }

  // Get all documents
  Future<List<Document>> getDocuments({
    String? type,
    String? processingStatus,
  }) async {
    final queryParams = <String, dynamic>{};
    if (type != null) queryParams['type'] = type;
    if (processingStatus != null) queryParams['processing_status'] = processingStatus;

    final response = await _apiService.get(
      ApiConfig.documents,
      queryParameters: queryParams,
    );

    final List<dynamic> data = response.data;
    return data.map((json) => Document.fromJson(json)).toList();
  }

  // Get single document
  Future<Document> getDocument(String id) async {
    final response = await _apiService.get(ApiConfig.documentById(id));
    return Document.fromJson(response.data);
  }

  // Update document
  Future<Document> updateDocument(
    String id, {
    String? title,
    String? type,
  }) async {
    final data = <String, dynamic>{};
    if (title != null) data['title'] = title;
    if (type != null) data['type'] = type;

    final response = await _apiService.patch(
      ApiConfig.documentById(id),
      data: data,
    );

    return Document.fromJson(response.data);
  }

  // Delete document
  Future<void> deleteDocument(String id) async {
    await _apiService.delete(ApiConfig.documentById(id));
  }
}
