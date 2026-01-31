import 'package:flutter/material.dart';
import '../services/calendar_service.dart';
import '../models/integration.dart';

class IntegrationSetupDialog extends StatefulWidget {
  final Integration? integration; // null = create new, non-null = edit existing

  const IntegrationSetupDialog({super.key, this.integration});

  @override
  State<IntegrationSetupDialog> createState() => _IntegrationSetupDialogState();
}

class _IntegrationSetupDialogState extends State<IntegrationSetupDialog> {
  final _formKey = GlobalKey<FormState>();
  final CalendarService _calendarService = CalendarService();

  late TextEditingController _nameController;
  late TextEditingController _urlController;
  late TextEditingController _usernameController;
  late TextEditingController _passwordController;
  late TextEditingController _calendarNameController;

  String _integrationType = 'caldav';
  bool _enabled = true;
  String _syncDirection = 'bidirectional';
  bool _autoSync = true;
  int _syncIntervalMinutes = 15;

  bool _isLoading = false;
  bool _isTesting = false;
  bool? _testSuccess;
  String? _testMessage;
  List<dynamic>? _availableCalendars;

  @override
  void initState() {
    super.initState();

    // Initialize controllers with existing data or defaults
    _nameController = TextEditingController(
      text: widget.integration?.name ?? '',
    );
    _urlController = TextEditingController(
      text: widget.integration?.config['url'] ?? '',
    );
    _usernameController = TextEditingController(
      text: widget.integration?.config['username'] ?? '',
    );
    _passwordController = TextEditingController();
    _calendarNameController = TextEditingController(
      text: widget.integration?.config['calendar_name'] ?? '',
    );

    if (widget.integration != null) {
      _integrationType = widget.integration!.integrationType;
      _enabled = widget.integration!.enabled;
      _syncDirection = widget.integration!.syncDirection;
      _autoSync = widget.integration!.autoSync;
      _syncIntervalMinutes = widget.integration!.syncIntervalMinutes;
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _urlController.dispose();
    _usernameController.dispose();
    _passwordController.dispose();
    _calendarNameController.dispose();
    super.dispose();
  }

  Future<void> _testConnection() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isTesting = true;
      _testSuccess = null;
      _testMessage = null;
      _availableCalendars = null;
    });

    try {
      // Create temporary integration for testing
      final tempIntegration = await _calendarService.createIntegration(
        name: 'temp_test',
        integrationType: _integrationType,
        config: {
          'url': _urlController.text.trim(),
          'calendar_name': _calendarNameController.text.trim(),
        },
        credentials: {
          'username': _usernameController.text.trim(),
          'password': _passwordController.text.trim(),
        },
        enabled: false,
      );

      // Test the connection
      final result = await _calendarService.testIntegration(tempIntegration.id);

      // Delete temporary integration
      await _calendarService.deleteIntegration(tempIntegration.id);

      setState(() {
        _testSuccess = result['success'] as bool;
        _testMessage = result['message'] as String?;
        if (result.containsKey('calendars')) {
          _availableCalendars = result['calendars'] as List<dynamic>?;
        }
      });
    } catch (e) {
      setState(() {
        _testSuccess = false;
        _testMessage = 'Verbindungstest fehlgeschlagen: $e';
      });
    } finally {
      setState(() => _isTesting = false);
    }
  }

  Future<void> _saveIntegration() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() => _isLoading = true);

    try {
      final config = {
        'url': _urlController.text.trim(),
        'calendar_name': _calendarNameController.text.trim(),
      };

      final credentials = _passwordController.text.trim().isNotEmpty
          ? {
              'username': _usernameController.text.trim(),
              'password': _passwordController.text.trim(),
            }
          : null;

      if (widget.integration == null) {
        // Create new integration
        await _calendarService.createIntegration(
          name: _nameController.text.trim(),
          integrationType: _integrationType,
          config: config,
          credentials: credentials,
          enabled: _enabled,
          syncDirection: _syncDirection,
          autoSync: _autoSync,
          syncIntervalMinutes: _syncIntervalMinutes,
        );
      } else {
        // Update existing integration
        await _calendarService.updateIntegration(
          widget.integration!.id,
          name: _nameController.text.trim(),
          enabled: _enabled,
          syncDirection: _syncDirection,
          autoSync: _autoSync,
          syncIntervalMinutes: _syncIntervalMinutes,
          config: config,
          credentials: credentials,
        );
      }

      if (mounted) {
        Navigator.pop(context, true); // Return true to indicate success
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              widget.integration == null
                  ? 'Integration erstellt'
                  : 'Integration aktualisiert',
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Fehler: $e')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      child: Container(
        constraints: const BoxConstraints(maxWidth: 600, maxHeight: 700),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Header
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.primaryContainer,
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(12),
                  topRight: Radius.circular(12),
                ),
              ),
              child: Row(
                children: [
                  Icon(
                    Icons.integration_instructions,
                    color: Theme.of(context).colorScheme.onPrimaryContainer,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      widget.integration == null
                          ? 'Neue Integration'
                          : 'Integration bearbeiten',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            color: Theme.of(context).colorScheme.onPrimaryContainer,
                          ),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
            ),

            // Body
            Expanded(
              child: Form(
                key: _formKey,
                child: ListView(
                  padding: const EdgeInsets.all(24),
                  children: [
                    // Name
                    TextFormField(
                      controller: _nameController,
                      decoration: const InputDecoration(
                        labelText: 'Name',
                        hintText: 'z.B. Mein Nextcloud Kalender',
                        border: OutlineInputBorder(),
                      ),
                      validator: (value) {
                        if (value == null || value.trim().isEmpty) {
                          return 'Bitte Namen eingeben';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),

                    // Integration Type
                    DropdownButtonFormField<String>(
                      value: _integrationType,
                      decoration: const InputDecoration(
                        labelText: 'Typ',
                        border: OutlineInputBorder(),
                      ),
                      items: const [
                        DropdownMenuItem(
                          value: 'caldav',
                          child: Text('CalDAV (Nextcloud, iCloud, etc.)'),
                        ),
                        DropdownMenuItem(
                          value: 'google_calendar',
                          child: Text('Google Calendar (coming soon)'),
                        ),
                        DropdownMenuItem(
                          value: 'outlook_calendar',
                          child: Text('Outlook Calendar (coming soon)'),
                        ),
                      ],
                      onChanged: widget.integration == null
                          ? (value) {
                              if (value != null) {
                                setState(() => _integrationType = value);
                              }
                            }
                          : null, // Disable changing type for existing integrations
                    ),
                    const SizedBox(height: 24),

                    // CalDAV specific fields
                    if (_integrationType == 'caldav') ...[
                      const Text(
                        'CalDAV Einstellungen',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 16),

                      TextFormField(
                        controller: _urlController,
                        decoration: const InputDecoration(
                          labelText: 'CalDAV URL',
                          hintText: 'https://nextcloud.example.com/remote.php/dav/',
                          border: OutlineInputBorder(),
                          helperText: 'Vollständige CalDAV URL inklusive /dav/ Pfad',
                        ),
                        validator: (value) {
                          if (value == null || value.trim().isEmpty) {
                            return 'Bitte URL eingeben';
                          }
                          if (!value.startsWith('http')) {
                            return 'URL muss mit http:// oder https:// beginnen';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),

                      TextFormField(
                        controller: _usernameController,
                        decoration: const InputDecoration(
                          labelText: 'Benutzername',
                          border: OutlineInputBorder(),
                        ),
                        validator: (value) {
                          if (value == null || value.trim().isEmpty) {
                            return 'Bitte Benutzername eingeben';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),

                      TextFormField(
                        controller: _passwordController,
                        decoration: InputDecoration(
                          labelText: widget.integration == null
                              ? 'Passwort'
                              : 'Passwort (leer lassen um nicht zu ändern)',
                          border: const OutlineInputBorder(),
                          helperText: 'Für Nextcloud: App-spezifisches Passwort empfohlen',
                        ),
                        obscureText: true,
                        validator: (value) {
                          if (widget.integration == null &&
                              (value == null || value.trim().isEmpty)) {
                            return 'Bitte Passwort eingeben';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),

                      TextFormField(
                        controller: _calendarNameController,
                        decoration: const InputDecoration(
                          labelText: 'Kalender Name',
                          hintText: 'Personal, Work, etc.',
                          border: OutlineInputBorder(),
                          helperText: 'Name des Kalenders auf dem Server',
                        ),
                        validator: (value) {
                          if (value == null || value.trim().isEmpty) {
                            return 'Bitte Kalender Name eingeben';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),

                      // Test Connection Button
                      OutlinedButton.icon(
                        onPressed: _isTesting ? null : _testConnection,
                        icon: _isTesting
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Icon(Icons.wifi_tethering),
                        label: Text(_isTesting ? 'Teste...' : 'Verbindung testen'),
                      ),

                      // Test Result
                      if (_testSuccess != null) ...[
                        const SizedBox(height: 12),
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: (_testSuccess!
                                    ? Colors.green
                                    : Colors.red)
                                .withOpacity(0.1),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(
                              color: _testSuccess! ? Colors.green : Colors.red,
                            ),
                          ),
                          child: Row(
                            children: [
                              Icon(
                                _testSuccess! ? Icons.check_circle : Icons.error,
                                color: _testSuccess! ? Colors.green : Colors.red,
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  _testMessage ?? 'Unbekannter Status',
                                  style: TextStyle(
                                    color: _testSuccess! ? Colors.green.shade700 : Colors.red.shade700,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],

                      // Available Calendars
                      if (_availableCalendars != null && _availableCalendars!.isNotEmpty) ...[
                        const SizedBox(height: 12),
                        const Text(
                          'Verfügbare Kalender:',
                          style: TextStyle(fontWeight: FontWeight.w600),
                        ),
                        const SizedBox(height: 8),
                        ..._availableCalendars!.map((cal) {
                          final name = cal['name'] as String;
                          return ListTile(
                            dense: true,
                            leading: const Icon(Icons.calendar_today, size: 20),
                            title: Text(name),
                            trailing: name == _calendarNameController.text
                                ? const Icon(Icons.check, color: Colors.green)
                                : null,
                            onTap: () {
                              setState(() {
                                _calendarNameController.text = name;
                              });
                            },
                          );
                        }),
                      ],

                      const SizedBox(height: 24),
                    ],

                    // Sync Settings
                    const Text(
                      'Synchronisationseinstellungen',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 16),

                    SwitchListTile(
                      title: const Text('Integration aktiviert'),
                      value: _enabled,
                      onChanged: (value) => setState(() => _enabled = value),
                    ),

                    DropdownButtonFormField<String>(
                      value: _syncDirection,
                      decoration: const InputDecoration(
                        labelText: 'Sync-Richtung',
                        border: OutlineInputBorder(),
                      ),
                      items: const [
                        DropdownMenuItem(
                          value: 'bidirectional',
                          child: Text('Bidirektional (beide Richtungen)'),
                        ),
                        DropdownMenuItem(
                          value: 'to_calendar',
                          child: Text('Nur zu Kalender'),
                        ),
                        DropdownMenuItem(
                          value: 'from_calendar',
                          child: Text('Nur vom Kalender'),
                        ),
                      ],
                      onChanged: (value) {
                        if (value != null) {
                          setState(() => _syncDirection = value);
                        }
                      },
                    ),
                    const SizedBox(height: 16),

                    SwitchListTile(
                      title: const Text('Automatische Synchronisation'),
                      subtitle: const Text('Synchronisiert in regelmäßigen Abständen'),
                      value: _autoSync,
                      onChanged: (value) => setState(() => _autoSync = value),
                    ),

                    if (_autoSync) ...[
                      const SizedBox(height: 16),
                      DropdownButtonFormField<int>(
                        value: _syncIntervalMinutes,
                        decoration: const InputDecoration(
                          labelText: 'Sync-Intervall',
                          border: OutlineInputBorder(),
                        ),
                        items: const [
                          DropdownMenuItem(value: 5, child: Text('5 Minuten')),
                          DropdownMenuItem(value: 15, child: Text('15 Minuten')),
                          DropdownMenuItem(value: 30, child: Text('30 Minuten')),
                          DropdownMenuItem(value: 60, child: Text('1 Stunde')),
                          DropdownMenuItem(value: 120, child: Text('2 Stunden')),
                          DropdownMenuItem(value: 360, child: Text('6 Stunden')),
                        ],
                        onChanged: (value) {
                          if (value != null) {
                            setState(() => _syncIntervalMinutes = value);
                          }
                        },
                      ),
                    ],
                  ],
                ),
              ),
            ),

            // Footer
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                border: Border(
                  top: BorderSide(color: Colors.grey.shade300),
                ),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    onPressed: _isLoading ? null : () => Navigator.pop(context),
                    child: const Text('Abbrechen'),
                  ),
                  const SizedBox(width: 12),
                  FilledButton.icon(
                    onPressed: _isLoading ? null : _saveIntegration,
                    icon: _isLoading
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Icon(Icons.save),
                    label: Text(
                      widget.integration == null ? 'Erstellen' : 'Speichern',
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
