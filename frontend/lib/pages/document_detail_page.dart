import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/document.dart';
import '../providers/document_provider.dart';
import '../config/api_config.dart';
import 'package:intl/intl.dart';

class DocumentDetailPage extends StatefulWidget {
  final String documentId;

  const DocumentDetailPage({
    super.key,
    required this.documentId,
  });

  @override
  State<DocumentDetailPage> createState() => _DocumentDetailPageState();
}

class _DocumentDetailPageState extends State<DocumentDetailPage> {
  Document? _document;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadDocument();
  }

  Future<void> _loadDocument() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final documentProvider = context.read<DocumentProvider>();
      await documentProvider.loadDocuments();

      final doc = documentProvider.documents.firstWhere(
        (d) => d.id == widget.documentId,
        orElse: () => throw Exception('Document not found'),
      );

      setState(() {
        _document = doc;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  String _getImageUrl(String path) {
    // Remove /api/v1 from base URL for image serving
    final baseUrl = ApiConfig.baseUrl.replaceAll('/api/v1', '');
    return '$baseUrl/files/$path';
  }

  Color _getStatusColor() {
    if (_document == null) return Colors.grey;

    switch (_document!.processingStatus) {
      case 'done':
        return Colors.green;
      case 'processing':
        return Colors.orange;
      case 'failed':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  IconData _getStatusIcon() {
    if (_document == null) return Icons.help_outline;

    switch (_document!.processingStatus) {
      case 'done':
        return Icons.check_circle;
      case 'processing':
        return Icons.hourglass_empty;
      case 'failed':
        return Icons.error;
      default:
        return Icons.pending;
    }
  }

  String _getStatusLabel() {
    if (_document == null) return 'Unbekannt';

    switch (_document!.processingStatus) {
      case 'done':
        return 'Verarbeitet';
      case 'processing':
        return 'Wird verarbeitet...';
      case 'failed':
        return 'Fehler';
      default:
        return 'Ausstehend';
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(
          title: const Text('Dokument wird geladen...'),
        ),
        body: const Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    if (_error != null) {
      return Scaffold(
        appBar: AppBar(
          title: const Text('Fehler'),
        ),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 64, color: Colors.red),
              const SizedBox(height: 16),
              Text('Fehler: $_error'),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _loadDocument,
                child: const Text('Erneut versuchen'),
              ),
            ],
          ),
        ),
      );
    }

    if (_document == null) {
      return Scaffold(
        appBar: AppBar(
          title: const Text('Dokument nicht gefunden'),
        ),
        body: const Center(
          child: Text('Dokument nicht gefunden'),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(_document!.title),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadDocument,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadDocument,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Document Preview
              if (_document!.file != null)
                _buildDocumentPreview()
              else if (_document!.docMetadata['paperless_id'] != null)
                _buildPaperlessPlaceholder(),

              // Status Section
              _buildStatusSection(),

              // Metadata Section
              if (_document!.docMetadata.isNotEmpty)
                _buildMetadataSection(),

              // Extracted Text Section
              if (_document!.extractedText != null && _document!.extractedText!.isNotEmpty)
                _buildExtractedTextSection(),

              // File Info Section
              if (_document!.file != null)
                _buildFileInfoSection(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPaperlessPlaceholder() {
    final paperlessId = _document!.docMetadata['paperless_id'];
    return Container(
      height: 160,
      color: Colors.grey[100],
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.cloud_outlined, size: 48, color: Colors.grey[400]),
            const SizedBox(height: 8),
            Text(
              'Aus Paperless-ngx importiert',
              style: TextStyle(color: Colors.grey[600], fontSize: 14),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              icon: const Icon(Icons.open_in_new, size: 16),
              label: const Text('In Paperless öffnen'),
              onPressed: () {
                // TODO: url_launcher öffnen
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Paperless Dokument #$paperlessId')),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDocumentPreview() {
    final file = _document!.file!;

    return Container(
      height: 400,
      color: Colors.grey[200],
      child: file.mimeType.startsWith('image/')
          ? Image.network(
              _getImageUrl(file.path),
              fit: BoxFit.contain,
              loadingBuilder: (context, child, loadingProgress) {
                if (loadingProgress == null) return child;
                return Center(
                  child: CircularProgressIndicator(
                    value: loadingProgress.expectedTotalBytes != null
                        ? loadingProgress.cumulativeBytesLoaded /
                            loadingProgress.expectedTotalBytes!
                        : null,
                  ),
                );
              },
              errorBuilder: (context, error, stackTrace) {
                return Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline, size: 64, color: Colors.red),
                      const SizedBox(height: 8),
                      Text('Bild konnte nicht geladen werden'),
                      Text('${error}', style: TextStyle(fontSize: 12, color: Colors.grey)),
                    ],
                  ),
                );
              },
            )
          : Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.insert_drive_file, size: 64, color: Colors.grey[400]),
                  const SizedBox(height: 16),
                  Text(
                    file.originalFilename,
                    style: const TextStyle(fontSize: 16),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    file.mimeType,
                    style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                  ),
                ],
              ),
            ),
    );
  }

  Widget _buildStatusSection() {
    return Card(
      margin: const EdgeInsets.all(16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(_getStatusIcon(), color: _getStatusColor(), size: 28),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _getStatusLabel(),
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: _getStatusColor(),
                        ),
                      ),
                      if (_document!.confidenceScore != null)
                        Text(
                          'Konfidenz: ${(_document!.confidenceScore! * 100).toStringAsFixed(0)}%',
                          style: TextStyle(fontSize: 14, color: Colors.grey[600]),
                        ),
                    ],
                  ),
                ),
              ],
            ),
            const Divider(height: 24),
            _buildInfoRow('Typ', _document!.typeLabel),
            _buildInfoRow('Hochgeladen', DateFormat('dd.MM.yyyy HH:mm').format(_document!.uploadedAt)),
            if (_document!.processedAt != null)
              _buildInfoRow('Verarbeitet', DateFormat('dd.MM.yyyy HH:mm').format(_document!.processedAt!)),
          ],
        ),
      ),
    );
  }

  Widget _buildMetadataSection() {
    final metadata = _document!.docMetadata;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Extrahierte Informationen',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),

            // Sender
            if (metadata['sender'] != null) ...[
              _buildMetadataItem('Absender', metadata['sender']['name']),
              if (metadata['sender']['address'] != null)
                _buildMetadataItem('Adresse', metadata['sender']['address']),
            ],

            // Amount
            if (metadata['amount'] != null)
              _buildMetadataItem(
                'Betrag',
                '${metadata['amount']} ${metadata['currency'] ?? 'EUR'}',
                highlight: true,
              ),

            // Dates
            if (metadata['due_date'] != null)
              _buildMetadataItem('Fällig am', metadata['due_date']),
            if (metadata['issue_date'] != null)
              _buildMetadataItem('Ausgestellt am', metadata['issue_date']),

            // Invoice Number
            if (metadata['invoice_number'] != null)
              _buildMetadataItem('Rechnungsnummer', metadata['invoice_number']),

            // IBAN
            if (metadata['iban'] != null)
              _buildMetadataItem('IBAN', metadata['iban']),

            // Payment Reference
            if (metadata['payment_reference'] != null)
              _buildMetadataItem('Verwendungszweck', metadata['payment_reference']),

            // Description
            if (metadata['description'] != null)
              _buildMetadataItem('Beschreibung', metadata['description']),

            // Priority
            if (metadata['priority'] != null)
              _buildPriorityChip(metadata['priority']),
          ],
        ),
      ),
    );
  }

  Widget _buildExtractedTextSection() {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Extrahierter Text',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.grey[100],
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                _document!.extractedText!,
                style: TextStyle(
                  fontSize: 13,
                  fontFamily: 'monospace',
                  color: Colors.grey[800],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFileInfoSection() {
    final file = _document!.file!;

    return Card(
      margin: const EdgeInsets.all(16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Dateiinformationen',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            _buildInfoRow('Dateiname', file.originalFilename),
            _buildInfoRow('Dateigröße', file.sizeFormatted),
            _buildInfoRow('Dateityp', file.mimeType),
            _buildInfoRow('Erstellt', DateFormat('dd.MM.yyyy HH:mm').format(file.createdAt)),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              '$label:',
              style: TextStyle(
                fontWeight: FontWeight.w500,
                color: Colors.grey[700],
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontSize: 15),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetadataItem(String label, dynamic value, {bool highlight = false}) {
    if (value == null) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 140,
            child: Text(
              '$label:',
              style: TextStyle(
                fontWeight: FontWeight.w500,
                color: Colors.grey[700],
              ),
            ),
          ),
          Expanded(
            child: Text(
              value.toString(),
              style: TextStyle(
                fontSize: 15,
                fontWeight: highlight ? FontWeight.bold : FontWeight.normal,
                color: highlight ? Colors.green[700] : Colors.black,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPriorityChip(String priority) {
    Color bgColor;
    Color textColor;
    String label;

    switch (priority.toLowerCase()) {
      case 'critical':
        bgColor = Colors.red.withOpacity(0.2);
        textColor = Colors.red.shade800;
        label = 'Kritisch';
        break;
      case 'high':
        bgColor = Colors.orange.withOpacity(0.2);
        textColor = Colors.orange.shade800;
        label = 'Hoch';
        break;
      case 'medium':
        bgColor = Colors.blue.withOpacity(0.2);
        textColor = Colors.blue.shade800;
        label = 'Mittel';
        break;
      case 'low':
        bgColor = Colors.grey.withOpacity(0.2);
        textColor = Colors.grey.shade800;
        label = 'Niedrig';
        break;
      default:
        bgColor = Colors.grey.withOpacity(0.2);
        textColor = Colors.grey.shade800;
        label = priority;
    }

    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: Chip(
        label: Text(label),
        backgroundColor: bgColor,
        labelStyle: TextStyle(
          color: textColor,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}
