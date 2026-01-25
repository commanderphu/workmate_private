import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import '../models/document.dart';
import '../services/document_service.dart';

class DocumentProvider with ChangeNotifier {
  final DocumentService _documentService = DocumentService();

  List<Document> _documents = [];
  bool _isLoading = false;
  String? _error;

  List<Document> get documents => _documents;
  bool get isLoading => _isLoading;
  String? get error => _error;

  // Filter helpers
  List<Document> get pendingDocuments =>
      _documents.where((d) => d.isPending).toList();
  List<Document> get processedDocuments =>
      _documents.where((d) => d.isDone).toList();

  // Load documents
  Future<void> loadDocuments({String? type, String? status}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _documents = await _documentService.getDocuments(
        type: type,
        processingStatus: status,
      );
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Upload document
  Future<bool> uploadDocument({
    required Uint8List fileBytes,
    required String filename,
    required String type,
    String? title,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final newDoc = await _documentService.uploadDocument(
        fileBytes: fileBytes,
        filename: filename,
        type: type,
        title: title,
      );
      _documents.insert(0, newDoc);
      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  // Delete document
  Future<bool> deleteDocument(String id) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      await _documentService.deleteDocument(id);
      _documents.removeWhere((d) => d.id == id);
      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  // Clear error
  void clearError() {
    _error = null;
    notifyListeners();
  }
}
