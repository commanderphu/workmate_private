import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/integration.dart';
import '../services/calendar_service.dart';
import '../widgets/integration_setup_dialog.dart';

class IntegrationsPage extends StatefulWidget {
  const IntegrationsPage({super.key});

  @override
  State<IntegrationsPage> createState() => _IntegrationsPageState();
}

class _IntegrationsPageState extends State<IntegrationsPage> {
  final CalendarService _calendarService = CalendarService();

  List<Integration> _integrations = [];
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadIntegrations();
  }

  Future<void> _loadIntegrations() async {
    setState(() => _isLoading = true);
    try {
      final integrations = await _calendarService.getIntegrations();
      setState(() => _integrations = integrations);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Fehler beim Laden: $e')),
        );
      }
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _syncIntegration(Integration integration) async {
    try {
      final result = await _calendarService.syncIntegration(integration.id);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result['message'] ?? 'Synchronisation abgeschlossen'),
          ),
        );
        _loadIntegrations();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Sync fehlgeschlagen: $e')),
        );
      }
    }
  }

  Future<void> _deleteIntegration(Integration integration) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Integration löschen?'),
        content: Text(
          'Möchtest du "${integration.name}" wirklich löschen?\n\n'
          'Alle verknüpften Events werden von dieser Integration getrennt.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Abbrechen'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            style: FilledButton.styleFrom(
              backgroundColor: Colors.red,
            ),
            child: const Text('Löschen'),
          ),
        ],
      ),
    );

    if (confirm == true) {
      try {
        await _calendarService.deleteIntegration(integration.id);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Integration gelöscht')),
          );
          _loadIntegrations();
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Löschen fehlgeschlagen: $e')),
          );
        }
      }
    }
  }

  Future<void> _showIntegrationDialog([Integration? integration]) async {
    final result = await showDialog<bool>(
      context: context,
      builder: (context) => IntegrationSetupDialog(integration: integration),
    );

    if (result == true) {
      _loadIntegrations();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Kalender-Integrationen'),
      ),
      body: RefreshIndicator(
        onRefresh: _loadIntegrations,
        child: _isLoading && _integrations.isEmpty
            ? const Center(child: CircularProgressIndicator())
            : _buildBody(),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showIntegrationDialog(),
        icon: const Icon(Icons.add),
        label: const Text('Integration'),
      ),
    );
  }

  Widget _buildBody() {
    if (_integrations.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.cloud_off,
              size: 64,
              color: Colors.grey[400],
            ),
            const SizedBox(height: 16),
            Text(
              'Keine Integrationen',
              style: TextStyle(
                fontSize: 18,
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 8),
            TextButton.icon(
              onPressed: () => _showIntegrationDialog(),
              icon: const Icon(Icons.add),
              label: const Text('Integration hinzufügen'),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      itemCount: _integrations.length,
      padding: const EdgeInsets.all(16),
      itemBuilder: (context, index) {
        final integration = _integrations[index];
        return _buildIntegrationCard(integration);
      },
    );
  }

  Widget _buildIntegrationCard(Integration integration) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Column(
        children: [
          ListTile(
            leading: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: integration.enabled
                    ? Colors.green.withOpacity(0.1)
                    : Colors.grey.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(
                _getIntegrationIcon(integration.integrationType),
                color: integration.enabled ? Colors.green : Colors.grey,
              ),
            ),
            title: Text(
              integration.name,
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(integration.typeDisplayName),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Icon(
                      integration.enabled ? Icons.cloud_done : Icons.cloud_off,
                      size: 14,
                      color: integration.enabled ? Colors.green : Colors.grey,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      integration.enabled ? 'Aktiv' : 'Deaktiviert',
                      style: TextStyle(
                        fontSize: 12,
                        color: integration.enabled ? Colors.green : Colors.grey,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Icon(
                      Icons.sync,
                      size: 14,
                      color: Colors.grey[600],
                    ),
                    const SizedBox(width: 4),
                    Text(
                      integration.syncDirectionDisplayName,
                      style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                    ),
                  ],
                ),
              ],
            ),
            trailing: PopupMenuButton(
              itemBuilder: (context) => [
                PopupMenuItem(
                  value: 'sync',
                  enabled: integration.enabled,
                  child: const Row(
                    children: [
                      Icon(Icons.sync, size: 20),
                      SizedBox(width: 12),
                      Text('Synchronisieren'),
                    ],
                  ),
                ),
                const PopupMenuItem(
                  value: 'edit',
                  child: Row(
                    children: [
                      Icon(Icons.edit, size: 20),
                      SizedBox(width: 12),
                      Text('Bearbeiten'),
                    ],
                  ),
                ),
                const PopupMenuItem(
                  value: 'delete',
                  child: Row(
                    children: [
                      Icon(Icons.delete, size: 20, color: Colors.red),
                      SizedBox(width: 12),
                      Text('Löschen', style: TextStyle(color: Colors.red)),
                    ],
                  ),
                ),
              ],
              onSelected: (value) {
                switch (value) {
                  case 'sync':
                    _syncIntegration(integration);
                    break;
                  case 'edit':
                    _showIntegrationDialog(integration);
                    break;
                  case 'delete':
                    _deleteIntegration(integration);
                    break;
                }
              },
            ),
          ),
          if (integration.lastSyncAt != null || integration.hasError)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: Column(
                children: [
                  const Divider(),
                  const SizedBox(height: 8),
                  if (integration.lastSyncAt != null)
                    Row(
                      children: [
                        Icon(Icons.history, size: 14, color: Colors.grey[600]),
                        const SizedBox(width: 8),
                        Text(
                          'Letzte Sync: ${DateFormat('dd.MM.yyyy HH:mm').format(integration.lastSyncAt!)}',
                          style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                        ),
                      ],
                    ),
                  if (integration.hasError) ...[
                    if (integration.lastSyncAt != null) const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.red.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Icon(Icons.error, size: 14, color: Colors.red),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              integration.errorLog!,
                              style: const TextStyle(fontSize: 12, color: Colors.red),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
        ],
      ),
    );
  }

  IconData _getIntegrationIcon(String type) {
    switch (type) {
      case 'caldav':
        return Icons.cloud;
      case 'google_calendar':
        return Icons.calendar_today;
      case 'outlook_calendar':
        return Icons.event;
      default:
        return Icons.integration_instructions;
    }
  }
}
