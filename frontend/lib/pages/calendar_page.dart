import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/calendar_event.dart';
import '../models/integration.dart';
import '../services/calendar_service.dart';
import 'integrations_page.dart';

class CalendarPage extends StatefulWidget {
  const CalendarPage({super.key});

  @override
  State<CalendarPage> createState() => _CalendarPageState();
}

class _CalendarPageState extends State<CalendarPage> {
  final CalendarService _calendarService = CalendarService();

  List<CalendarEvent> _events = [];
  List<Integration> _integrations = [];
  bool _isLoading = false;
  String _filterType = 'upcoming'; // 'upcoming', 'today', 'all'

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      await Future.wait([
        _loadEvents(),
        _loadIntegrations(),
      ]);
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _loadEvents() async {
    try {
      DateTime? startDate;
      DateTime? endDate;

      if (_filterType == 'today') {
        final now = DateTime.now();
        startDate = DateTime(now.year, now.month, now.day);
        endDate = DateTime(now.year, now.month, now.day, 23, 59, 59);
      } else if (_filterType == 'upcoming') {
        startDate = DateTime.now();
        endDate = DateTime.now().add(const Duration(days: 30));
      }

      final events = await _calendarService.getEvents(
        startDate: startDate,
        endDate: endDate,
      );

      setState(() {
        _events = events;
        _events.sort((a, b) => a.startTime.compareTo(b.startTime));
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Fehler beim Laden der Events: $e')),
        );
      }
    }
  }

  Future<void> _loadIntegrations() async {
    try {
      final integrations = await _calendarService.getIntegrations();
      setState(() => _integrations = integrations);
    } catch (e) {
      // Silent fail for integrations
    }
  }

  Future<void> _syncAllIntegrations() async {
    setState(() => _isLoading = true);
    try {
      for (var integration in _integrations.where((i) => i.enabled)) {
        await _calendarService.syncIntegration(integration.id);
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Synchronisation erfolgreich')),
        );
      }

      await _loadEvents();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Sync fehlgeschlagen: $e')),
        );
      }
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showCreateEventDialog() {
    final titleController = TextEditingController();
    final descriptionController = TextEditingController();
    final locationController = TextEditingController();
    DateTime selectedDate = DateTime.now();
    TimeOfDay selectedStartTime = TimeOfDay.now();
    TimeOfDay selectedEndTime = TimeOfDay(
      hour: TimeOfDay.now().hour + 1,
      minute: TimeOfDay.now().minute,
    );
    bool allDay = false;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Neues Event erstellen'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                TextField(
                  controller: titleController,
                  decoration: const InputDecoration(
                    labelText: 'Titel',
                    border: OutlineInputBorder(),
                  ),
                  textCapitalization: TextCapitalization.sentences,
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: descriptionController,
                  decoration: const InputDecoration(
                    labelText: 'Beschreibung (optional)',
                    border: OutlineInputBorder(),
                  ),
                  maxLines: 3,
                  textCapitalization: TextCapitalization.sentences,
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: locationController,
                  decoration: const InputDecoration(
                    labelText: 'Ort (optional)',
                    border: OutlineInputBorder(),
                  ),
                  textCapitalization: TextCapitalization.words,
                ),
                const SizedBox(height: 16),
                CheckboxListTile(
                  title: const Text('Ganztägig'),
                  value: allDay,
                  onChanged: (value) {
                    setDialogState(() => allDay = value ?? false);
                  },
                ),
                const SizedBox(height: 8),
                ListTile(
                  title: const Text('Datum'),
                  subtitle: Text(DateFormat('dd.MM.yyyy').format(selectedDate)),
                  trailing: const Icon(Icons.calendar_today),
                  onTap: () async {
                    final date = await showDatePicker(
                      context: context,
                      initialDate: selectedDate,
                      firstDate: DateTime.now().subtract(const Duration(days: 365)),
                      lastDate: DateTime.now().add(const Duration(days: 365 * 2)),
                    );
                    if (date != null) {
                      setDialogState(() => selectedDate = date);
                    }
                  },
                ),
                if (!allDay) ...[
                  ListTile(
                    title: const Text('Startzeit'),
                    subtitle: Text(selectedStartTime.format(context)),
                    trailing: const Icon(Icons.access_time),
                    onTap: () async {
                      final time = await showTimePicker(
                        context: context,
                        initialTime: selectedStartTime,
                      );
                      if (time != null) {
                        setDialogState(() => selectedStartTime = time);
                      }
                    },
                  ),
                  ListTile(
                    title: const Text('Endzeit'),
                    subtitle: Text(selectedEndTime.format(context)),
                    trailing: const Icon(Icons.access_time),
                    onTap: () async {
                      final time = await showTimePicker(
                        context: context,
                        initialTime: selectedEndTime,
                      );
                      if (time != null) {
                        setDialogState(() => selectedEndTime = time);
                      }
                    },
                  ),
                ],
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Abbrechen'),
            ),
            FilledButton(
              onPressed: () async {
                if (titleController.text.trim().isEmpty) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Bitte Titel eingeben')),
                  );
                  return;
                }

                final startDateTime = allDay
                    ? DateTime(selectedDate.year, selectedDate.month, selectedDate.day)
                    : DateTime(
                        selectedDate.year,
                        selectedDate.month,
                        selectedDate.day,
                        selectedStartTime.hour,
                        selectedStartTime.minute,
                      );

                final endDateTime = allDay
                    ? DateTime(selectedDate.year, selectedDate.month, selectedDate.day, 23, 59, 59)
                    : DateTime(
                        selectedDate.year,
                        selectedDate.month,
                        selectedDate.day,
                        selectedEndTime.hour,
                        selectedEndTime.minute,
                      );

                if (endDateTime.isBefore(startDateTime)) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Endzeit muss nach Startzeit liegen')),
                  );
                  return;
                }

                try {
                  await _calendarService.createEvent(
                    title: titleController.text.trim(),
                    description: descriptionController.text.trim().isEmpty
                        ? null
                        : descriptionController.text.trim(),
                    startTime: startDateTime,
                    endTime: endDateTime,
                    allDay: allDay,
                    location: locationController.text.trim().isEmpty
                        ? null
                        : locationController.text.trim(),
                  );

                  if (mounted) {
                    Navigator.pop(context);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Event erstellt')),
                    );
                    _loadEvents();
                  }
                } catch (e) {
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Fehler: $e')),
                    );
                  }
                }
              },
              child: const Text('Erstellen'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Kalender'),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.filter_list),
            onSelected: (value) {
              setState(() => _filterType = value);
              _loadEvents();
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'today',
                child: Text('Heute'),
              ),
              const PopupMenuItem(
                value: 'upcoming',
                child: Text('Kommende 30 Tage'),
              ),
              const PopupMenuItem(
                value: 'all',
                child: Text('Alle'),
              ),
            ],
          ),
          if (_integrations.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.sync),
              onPressed: _isLoading ? null : _syncAllIntegrations,
              tooltip: 'Synchronisieren',
            ),
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const IntegrationsPage()),
              ).then((_) => _loadData()); // Reload data when returning
            },
            tooltip: 'Einstellungen',
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadData,
        child: _isLoading && _events.isEmpty
            ? const Center(child: CircularProgressIndicator())
            : _buildBody(),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showCreateEventDialog,
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildBody() {
    if (_events.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.event_available,
              size: 64,
              color: Colors.grey[400],
            ),
            const SizedBox(height: 16),
            Text(
              _filterType == 'today'
                  ? 'Keine Events für heute'
                  : _filterType == 'upcoming'
                      ? 'Keine kommenden Events'
                      : 'Keine Events',
              style: TextStyle(
                fontSize: 18,
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 8),
            TextButton.icon(
              onPressed: _showCreateEventDialog,
              icon: const Icon(Icons.add),
              label: const Text('Event erstellen'),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      itemCount: _events.length,
      padding: const EdgeInsets.all(16),
      itemBuilder: (context, index) {
        final event = _events[index];
        final showDateHeader = index == 0 ||
            !_isSameDay(_events[index - 1].startTime, event.startTime);

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (showDateHeader) _buildDateHeader(event.startTime),
            _buildEventCard(event),
          ],
        );
      },
    );
  }

  Widget _buildDateHeader(DateTime date) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final eventDay = DateTime(date.year, date.month, date.day);

    String label;
    if (eventDay == today) {
      label = 'Heute';
    } else if (eventDay == today.add(const Duration(days: 1))) {
      label = 'Morgen';
    } else if (eventDay == today.subtract(const Duration(days: 1))) {
      label = 'Gestern';
    } else {
      label = DateFormat('EEEE, dd. MMMM yyyy', 'de_DE').format(date);
    }

    return Padding(
      padding: const EdgeInsets.only(top: 16, bottom: 8),
      child: Text(
        label,
        style: const TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.bold,
          color: Colors.blue,
        ),
      ),
    );
  }

  Widget _buildEventCard(CalendarEvent event) {
    final Color statusColor = event.hasConflict
        ? Colors.orange
        : event.isSynced
            ? Colors.green
            : event.hasFailed
                ? Colors.red
                : Colors.grey;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: () => _showEventDetails(event),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 4,
                    height: 40,
                    decoration: BoxDecoration(
                      color: statusColor,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          event.title,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            Icon(
                              event.allDay ? Icons.calendar_today : Icons.access_time,
                              size: 14,
                              color: Colors.grey[600],
                            ),
                            const SizedBox(width: 4),
                            Text(
                              event.allDay
                                  ? 'Ganztägig'
                                  : '${DateFormat('HH:mm').format(event.startTime)} - ${DateFormat('HH:mm').format(event.endTime)}',
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors.grey[600],
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  if (event.taskId != null)
                    const Padding(
                      padding: EdgeInsets.only(left: 8),
                      child: Icon(Icons.task_alt, size: 20, color: Colors.blue),
                    ),
                ],
              ),
              if (event.location != null && event.location!.isNotEmpty) ...[
                const SizedBox(height: 8),
                Row(
                  children: [
                    Icon(Icons.location_on, size: 14, color: Colors.grey[600]),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Text(
                        event.location!,
                        style: TextStyle(fontSize: 13, color: Colors.grey[600]),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ],
              if (event.hasConflict) ...[
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.orange.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.warning, size: 14, color: Colors.orange),
                      SizedBox(width: 4),
                      Text(
                        'Konflikt - Auflösung erforderlich',
                        style: TextStyle(fontSize: 12, color: Colors.orange),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  void _showEventDetails(CalendarEvent event) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.4,
        maxChildSize: 0.9,
        expand: false,
        builder: (context, scrollController) => Container(
          padding: const EdgeInsets.all(24),
          child: ListView(
            controller: scrollController,
            children: [
              Text(
                event.title,
                style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 16),
              _buildDetailRow(
                Icons.access_time,
                event.allDay
                    ? 'Ganztägig'
                    : '${DateFormat('dd.MM.yyyy HH:mm').format(event.startTime)} - ${DateFormat('HH:mm').format(event.endTime)}',
              ),
              if (event.location != null && event.location!.isNotEmpty)
                _buildDetailRow(Icons.location_on, event.location!),
              if (event.description != null && event.description!.isNotEmpty) ...[
                const SizedBox(height: 16),
                const Text(
                  'Beschreibung',
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 8),
                Text(event.description!),
              ],
              const SizedBox(height: 24),
              const Divider(),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  FilledButton.icon(
                    onPressed: () {
                      Navigator.pop(context);
                      // TODO: Edit event
                    },
                    icon: const Icon(Icons.edit),
                    label: const Text('Bearbeiten'),
                  ),
                  OutlinedButton.icon(
                    onPressed: () async {
                      final confirm = await showDialog<bool>(
                        context: context,
                        builder: (context) => AlertDialog(
                          title: const Text('Event löschen?'),
                          content: const Text('Möchtest du dieses Event wirklich löschen?'),
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

                      if (confirm == true && mounted) {
                        try {
                          await _calendarService.deleteEvent(event.id);
                          if (mounted) {
                            Navigator.pop(context);
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('Event gelöscht')),
                            );
                            _loadEvents();
                          }
                        } catch (e) {
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Fehler: $e')),
                            );
                          }
                        }
                      }
                    },
                    icon: const Icon(Icons.delete),
                    label: const Text('Löschen'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.red,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDetailRow(IconData icon, String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Icon(icon, size: 20, color: Colors.grey[700]),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(fontSize: 16),
            ),
          ),
        ],
      ),
    );
  }

  bool _isSameDay(DateTime a, DateTime b) {
    return a.year == b.year && a.month == b.month && a.day == b.day;
  }
}
