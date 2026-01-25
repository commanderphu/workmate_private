import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../models/document.dart';
import '../providers/document_provider.dart';
import 'dart:html' as html;

class DocumentsPage extends StatefulWidget {
  const DocumentsPage({super.key});

  @override
  State<DocumentsPage> createState() => _DocumentsPageState();
}

class _DocumentsPageState extends State<DocumentsPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<DocumentProvider>().loadDocuments();
    });
  }

  Future<void> _uploadDocument({bool useCamera = false}) async {
    // Create HTML file input element
    final html.FileUploadInputElement uploadInput = html.FileUploadInputElement();
    uploadInput.accept = 'image/*,.pdf';

    // On mobile, this will open the camera directly
    if (useCamera) {
      uploadInput.setAttribute('capture', 'environment');
    }

    uploadInput.click();

    uploadInput.onChange.listen((e) async {
      final files = uploadInput.files;
      if (files == null || files.isEmpty) return;

      final file = files[0];
      final reader = html.FileReader();

      reader.readAsArrayBuffer(file);
      reader.onLoadEnd.listen((e) async {
        final bytes = reader.result as Uint8List;

        // Show type selection dialog
        if (!mounted) return;
        final type = await _showTypeSelectionDialog();
        if (type == null) return;

        // Upload
        final success = await context.read<DocumentProvider>().uploadDocument(
              fileBytes: bytes,
              filename: file.name,
              type: type,
              title: file.name,
            );

        if (!mounted) return;

        if (success) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Dokument erfolgreich hochgeladen')),
          );
        } else {
          final error = context.read<DocumentProvider>().error;
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(error ?? 'Fehler beim Hochladen'),
              backgroundColor: Colors.red,
            ),
          );
        }
      });
    });
  }

  void _showUploadOptions() {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt),
              title: const Text('Mit Kamera aufnehmen'),
              onTap: () {
                Navigator.pop(context);
                _uploadDocument(useCamera: true);
              },
            ),
            ListTile(
              leading: const Icon(Icons.folder),
              title: const Text('Datei auswählen'),
              onTap: () {
                Navigator.pop(context);
                _uploadDocument(useCamera: false);
              },
            ),
          ],
        ),
      ),
    );
  }

  Future<String?> _showTypeSelectionDialog() async {
    return showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Dokumenttyp auswählen'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.receipt_long),
              title: const Text('Rechnung'),
              onTap: () => Navigator.pop(context, 'invoice'),
            ),
            ListTile(
              leading: const Icon(Icons.warning),
              title: const Text('Mahnung'),
              onTap: () => Navigator.pop(context, 'reminder'),
            ),
            ListTile(
              leading: const Icon(Icons.description),
              title: const Text('Vertrag'),
              onTap: () => Navigator.pop(context, 'contract'),
            ),
            ListTile(
              leading: const Icon(Icons.receipt),
              title: const Text('Quittung'),
              onTap: () => Navigator.pop(context, 'receipt'),
            ),
            ListTile(
              leading: const Icon(Icons.folder),
              title: const Text('Sonstiges'),
              onTap: () => Navigator.pop(context, 'other'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final documentProvider = context.watch<DocumentProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Dokumente'),
      ),
      body: RefreshIndicator(
        onRefresh: () => documentProvider.loadDocuments(),
        child: documentProvider.isLoading && documentProvider.documents.isEmpty
            ? const Center(child: CircularProgressIndicator())
            : documentProvider.error != null
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.error_outline, size: 64, color: Colors.red),
                        const SizedBox(height: 16),
                        Text(documentProvider.error!),
                        const SizedBox(height: 16),
                        FilledButton(
                          onPressed: () => documentProvider.loadDocuments(),
                          child: const Text('Erneut versuchen'),
                        ),
                      ],
                    ),
                  )
                : documentProvider.documents.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.cloud_upload,
                              size: 64,
                              color: Colors.grey.shade400,
                            ),
                            const SizedBox(height: 16),
                            Text(
                              'Noch keine Dokumente',
                              style: Theme.of(context).textTheme.titleLarge,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'Lade dein erstes Dokument hoch',
                              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                    color: Colors.grey,
                                  ),
                            ),
                          ],
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: documentProvider.documents.length,
                        itemBuilder: (context, index) {
                          final document = documentProvider.documents[index];
                          return _DocumentCard(
                            document: document,
                            onDelete: () async {
                              final confirmed = await _confirmDelete(document);
                              if (confirmed == true && mounted) {
                                await context.read<DocumentProvider>().deleteDocument(document.id);
                              }
                            },
                          );
                        },
                      ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showUploadOptions,
        icon: const Icon(Icons.add),
        label: const Text('Hochladen'),
      ),
    );
  }

  Future<bool?> _confirmDelete(Document document) {
    return showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Dokument löschen'),
        content: Text('Möchtest du "${document.title}" wirklich löschen?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Abbrechen'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Löschen'),
          ),
        ],
      ),
    );
  }
}

class _DocumentCard extends StatelessWidget {
  final Document document;
  final VoidCallback onDelete;

  const _DocumentCard({
    required this.document,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: _buildStatusIcon(),
        title: Text(
          document.title,
          style: const TextStyle(fontWeight: FontWeight.w600),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: _getTypeColor().withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    document.typeLabel,
                    style: TextStyle(
                      color: _getTypeColor(),
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                if (document.file != null) ...[
                  const Icon(Icons.insert_drive_file, size: 12, color: Colors.grey),
                  const SizedBox(width: 4),
                  Text(
                    document.file!.sizeFormatted,
                    style: const TextStyle(fontSize: 11, color: Colors.grey),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 4),
            Text(
              DateFormat('dd.MM.yyyy HH:mm').format(document.uploadedAt),
              style: const TextStyle(fontSize: 11, color: Colors.grey),
            ),
          ],
        ),
        trailing: IconButton(
          icon: const Icon(Icons.delete_outline, color: Colors.red),
          onPressed: onDelete,
        ),
      ),
    );
  }

  Widget _buildStatusIcon() {
    IconData icon;
    Color color;

    switch (document.processingStatus) {
      case 'pending':
        icon = Icons.schedule;
        color = Colors.orange;
        break;
      case 'processing':
        icon = Icons.sync;
        color = Colors.blue;
        break;
      case 'done':
        icon = Icons.check_circle;
        color = Colors.green;
        break;
      case 'failed':
        icon = Icons.error;
        color = Colors.red;
        break;
      default:
        icon = Icons.help;
        color = Colors.grey;
    }

    return Icon(icon, color: color, size: 32);
  }

  Color _getTypeColor() {
    switch (document.type) {
      case 'invoice':
        return Colors.blue;
      case 'reminder':
        return Colors.red;
      case 'contract':
        return Colors.purple;
      case 'receipt':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }
}
