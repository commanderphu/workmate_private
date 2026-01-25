class Document {
  final String id;
  final String userId;
  final String fileId;
  final String title;
  final String type;
  final Map<String, dynamic> docMetadata;
  final String processingStatus;
  final double? confidenceScore;
  final String? extractedText;
  final DateTime uploadedAt;
  final DateTime? processedAt;
  final DocumentFile? file;

  Document({
    required this.id,
    required this.userId,
    required this.fileId,
    required this.title,
    required this.type,
    required this.docMetadata,
    required this.processingStatus,
    this.confidenceScore,
    this.extractedText,
    required this.uploadedAt,
    this.processedAt,
    this.file,
  });

  factory Document.fromJson(Map<String, dynamic> json) {
    return Document(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      fileId: json['file_id'] as String,
      title: json['title'] as String? ?? 'Untitled',
      type: json['type'] as String,
      docMetadata: (json['doc_metadata'] as Map<String, dynamic>?) ?? {},
      processingStatus: json['processing_status'] as String? ?? 'pending',
      confidenceScore: json['confidence_score'] != null
          ? (json['confidence_score'] as num).toDouble()
          : null,
      extractedText: json['extracted_text'] as String?,
      uploadedAt: DateTime.parse(json['uploaded_at']),
      processedAt: json['processed_at'] != null
          ? DateTime.parse(json['processed_at'])
          : null,
      file: json['file'] != null
          ? DocumentFile.fromJson(json['file'])
          : null,
    );
  }

  bool get isPending => processingStatus == 'pending';
  bool get isProcessing => processingStatus == 'processing';
  bool get isDone => processingStatus == 'done';
  bool get isFailed => processingStatus == 'failed';

  String get typeLabel {
    switch (type) {
      case 'invoice':
        return 'Rechnung';
      case 'reminder':
        return 'Mahnung';
      case 'contract':
        return 'Vertrag';
      case 'receipt':
        return 'Quittung';
      default:
        return 'Sonstiges';
    }
  }
}

class DocumentFile {
  final String id;
  final String originalFilename;
  final int sizeBytes;
  final String mimeType;
  final String path;
  final DateTime createdAt;

  DocumentFile({
    required this.id,
    required this.originalFilename,
    required this.sizeBytes,
    required this.mimeType,
    required this.path,
    required this.createdAt,
  });

  factory DocumentFile.fromJson(Map<String, dynamic> json) {
    return DocumentFile(
      id: json['id'] as String,
      originalFilename: json['original_filename'] as String,
      sizeBytes: json['size_bytes'] as int,
      mimeType: json['mime_type'] as String,
      path: json['path'] as String,
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  String get sizeFormatted {
    if (sizeBytes < 1024) return '$sizeBytes B';
    if (sizeBytes < 1024 * 1024) return '${(sizeBytes / 1024).toStringAsFixed(1)} KB';
    return '${(sizeBytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
}
