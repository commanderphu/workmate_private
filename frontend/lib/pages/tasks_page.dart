import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../models/task.dart';
import '../providers/task_provider.dart';
import 'task_detail_page.dart';

class TasksPage extends StatefulWidget {
  const TasksPage({super.key});

  @override
  State<TasksPage> createState() => _TasksPageState();
}

class _TasksPageState extends State<TasksPage> {
  // Gefiltert wird lokal: Alle Tasks werden einmal geladen, die Chips
  // kombinieren sich (innerhalb einer Gruppe ODER, zwischen Gruppen UND)
  static const _priorities = {
    'critical': 'Kritisch',
    'high': 'Hoch',
    'medium': 'Mittel',
    'low': 'Niedrig',
  };
  static const _priorityRank = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3};

  final Set<String> _statuses = {'open'};
  final Set<String> _priorityFilter = {};
  bool _overdueOnly = false;
  bool _thisWeekOnly = false;
  bool _withAmountOnly = false;

  bool _searching = false;
  String _query = '';
  final _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<TaskProvider>().loadTasks();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _refreshTasks() async {
    await context.read<TaskProvider>().loadTasks();
  }

  bool get _hasActiveFilters =>
      !(_statuses.length == 1 && _statuses.contains('open')) ||
      _priorityFilter.isNotEmpty ||
      _overdueOnly ||
      _thisWeekOnly ||
      _withAmountOnly ||
      _query.isNotEmpty;

  void _resetFilters() {
    setState(() {
      _statuses
        ..clear()
        ..add('open');
      _priorityFilter.clear();
      _overdueOnly = false;
      _thisWeekOnly = false;
      _withAmountOnly = false;
      _query = '';
      _searchController.clear();
      _searching = false;
    });
  }

  List<Task> _applyFilters(List<Task> tasks) {
    final now = DateTime.now();
    final weekEnd = DateTime(now.year, now.month, now.day)
        .add(const Duration(days: 8)); // heute + 7 volle Tage
    final q = _query.trim().toLowerCase();

    final result = tasks.where((t) {
      // Alles, was nicht erledigt ist (open, in_progress …), zählt als offen
      final statusKey = t.isDone ? 'done' : 'open';
      if (_statuses.isNotEmpty && !_statuses.contains(statusKey)) return false;
      if (_priorityFilter.isNotEmpty && !_priorityFilter.contains(t.priority)) {
        return false;
      }
      if (_overdueOnly && !t.isOverdue) return false;
      if (_thisWeekOnly &&
          (t.dueDate == null || !t.dueDate!.isBefore(weekEnd))) {
        return false;
      }
      if (_withAmountOnly && t.amount == null) return false;
      if (q.isNotEmpty &&
          !t.title.toLowerCase().contains(q) &&
          !(t.description?.toLowerCase().contains(q) ?? false)) {
        return false;
      }
      return true;
    }).toList();

    // Offene zuerst, dann nach Fälligkeit (ohne Datum ans Ende), dann Priorität
    result.sort((a, b) {
      if (a.isDone != b.isDone) return a.isDone ? 1 : -1;
      if (a.isDone) {
        return (b.completedAt ?? b.updatedAt)
            .compareTo(a.completedAt ?? a.updatedAt);
      }
      if (a.dueDate != null && b.dueDate == null) return -1;
      if (a.dueDate == null && b.dueDate != null) return 1;
      if (a.dueDate != null && b.dueDate != null) {
        final c = a.dueDate!.compareTo(b.dueDate!);
        if (c != 0) return c;
      }
      return (_priorityRank[a.priority] ?? 9)
          .compareTo(_priorityRank[b.priority] ?? 9);
    });
    return result;
  }

  Widget _buildFilterBar(List<Task> all) {
    final overdueCount = all.where((t) => t.isOverdue).length;

    Widget chip(String label, bool selected, VoidCallback onTap,
        {Color? color}) {
      return FilterChip(
        label: Text(label),
        selected: selected,
        onSelected: (_) => setState(onTap),
        selectedColor: color?.withValues(alpha: 0.25),
        visualDensity: VisualDensity.compact,
      );
    }

    void toggle(Set<String> set, String value) =>
        set.contains(value) ? set.remove(value) : set.add(value);

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
      child: Wrap(
        spacing: 8,
        runSpacing: 4,
        children: [
          chip('Offen', _statuses.contains('open'),
              () => toggle(_statuses, 'open')),
          chip('Erledigt', _statuses.contains('done'),
              () => toggle(_statuses, 'done')),
          chip(
            overdueCount > 0 ? 'Überfällig ($overdueCount)' : 'Überfällig',
            _overdueOnly,
            () => _overdueOnly = !_overdueOnly,
            color: Colors.red,
          ),
          chip('Nächste 7 Tage', _thisWeekOnly,
              () => _thisWeekOnly = !_thisWeekOnly),
          chip('Mit Betrag', _withAmountOnly,
              () => _withAmountOnly = !_withAmountOnly),
          for (final p in _priorities.entries)
            chip(p.value, _priorityFilter.contains(p.key),
                () => toggle(_priorityFilter, p.key),
                color: _TaskCard.priorityColor(p.key)),
        ],
      ),
    );
  }

  void _showCreateTaskDialog() {
    final titleController = TextEditingController();
    final descriptionController = TextEditingController();
    String priority = 'medium';

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Create New Task'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: titleController,
                decoration: const InputDecoration(
                  labelText: 'Title',
                  border: OutlineInputBorder(),
                ),
                textCapitalization: TextCapitalization.sentences,
              ),
              const SizedBox(height: 16),
              TextField(
                controller: descriptionController,
                decoration: const InputDecoration(
                  labelText: 'Description (optional)',
                  border: OutlineInputBorder(),
                ),
                maxLines: 3,
                textCapitalization: TextCapitalization.sentences,
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: priority,
                decoration: const InputDecoration(
                  labelText: 'Priority',
                  border: OutlineInputBorder(),
                ),
                items: const [
                  DropdownMenuItem(value: 'low', child: Text('Low')),
                  DropdownMenuItem(value: 'medium', child: Text('Medium')),
                  DropdownMenuItem(value: 'high', child: Text('High')),
                  DropdownMenuItem(value: 'critical', child: Text('Critical')),
                ],
                onChanged: (value) {
                  if (value != null) priority = value;
                },
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () async {
              if (titleController.text.trim().isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Please enter a title')),
                );
                return;
              }

              final success = await context.read<TaskProvider>().createTask(
                    title: titleController.text.trim(),
                    description: descriptionController.text.trim().isEmpty
                        ? null
                        : descriptionController.text.trim(),
                    priority: priority,
                  );

              if (!context.mounted) return;

              if (success) {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Task created successfully')),
                );
              } else {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(
                      context.read<TaskProvider>().error ??
                          'Failed to create task',
                    ),
                    backgroundColor: Colors.red,
                  ),
                );
              }
            },
            child: const Text('Create'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final taskProvider = context.watch<TaskProvider>();
    final filtered = _applyFilters(taskProvider.tasks);

    return Scaffold(
      appBar: AppBar(
        title: _searching
            ? TextField(
                controller: _searchController,
                autofocus: true,
                decoration: const InputDecoration(
                  hintText: 'Aufgaben durchsuchen …',
                  border: InputBorder.none,
                ),
                onChanged: (v) => setState(() => _query = v),
              )
            : const Text('Tasks'),
        actions: [
          IconButton(
            tooltip: _searching ? 'Suche schließen' : 'Suchen',
            icon: Icon(_searching ? Icons.close : Icons.search),
            onPressed: () => setState(() {
              if (_searching) {
                _query = '';
                _searchController.clear();
              }
              _searching = !_searching;
            }),
          ),
          if (_hasActiveFilters)
            IconButton(
              tooltip: 'Filter zurücksetzen',
              icon: const Icon(Icons.filter_alt_off),
              onPressed: _resetFilters,
            ),
        ],
        bottom: taskProvider.tasks.isEmpty
            ? null
            : PreferredSize(
                preferredSize: const Size.fromHeight(28),
                child: Padding(
                  padding: const EdgeInsets.only(left: 16, bottom: 8),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      '${filtered.length} von ${taskProvider.tasks.length} Aufgaben',
                      style: Theme.of(context)
                          .textTheme
                          .bodySmall
                          ?.copyWith(color: Colors.grey),
                    ),
                  ),
                ),
              ),
      ),
      body: RefreshIndicator(
        onRefresh: _refreshTasks,
        child: taskProvider.isLoading && taskProvider.tasks.isEmpty
            ? const Center(child: CircularProgressIndicator())
            : taskProvider.error != null
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(
                          Icons.error_outline,
                          size: 64,
                          color: Colors.red,
                        ),
                        const SizedBox(height: 16),
                        Text(
                          taskProvider.error!,
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 16),
                        FilledButton(
                          onPressed: _refreshTasks,
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  )
                : taskProvider.tasks.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.task_alt,
                              size: 64,
                              color: Colors.grey.shade400,
                            ),
                            const SizedBox(height: 16),
                            Text(
                              'No tasks yet',
                              style: Theme.of(context).textTheme.titleLarge,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'Create your first task to get started',
                              style: Theme.of(context)
                                  .textTheme
                                  .bodyMedium
                                  ?.copyWith(
                                    color: Colors.grey,
                                  ),
                            ),
                          ],
                        ),
                      )
                    : Column(
                        children: [
                          _buildFilterBar(taskProvider.tasks),
                          Expanded(
                            child: filtered.isEmpty
                                ? ListView(
                                    // ListView, damit Pull-to-Refresh geht
                                    children: [
                                      const SizedBox(height: 80),
                                      Icon(Icons.filter_alt_off,
                                          size: 48,
                                          color: Colors.grey.shade400),
                                      const SizedBox(height: 12),
                                      const Center(
                                        child: Text(
                                            'Keine Aufgaben für diese Filter'),
                                      ),
                                      const SizedBox(height: 8),
                                      Center(
                                        child: TextButton(
                                          onPressed: _resetFilters,
                                          child: const Text(
                                              'Filter zurücksetzen'),
                                        ),
                                      ),
                                    ],
                                  )
                                : ListView.builder(
                                    padding: const EdgeInsets.fromLTRB(
                                        16, 12, 16, 88),
                                    itemCount: filtered.length,
                                    itemBuilder: (context, index) {
                                      final task = filtered[index];
                                      return _TaskCard(
                                        task: task,
                                        onTap: () => _showTaskDetails(task),
                                        onStatusToggle: () =>
                                            _toggleTaskStatus(task),
                                      );
                                    },
                                  ),
                          ),
                        ],
                      ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showCreateTaskDialog,
        icon: const Icon(Icons.add),
        label: const Text('New Task'),
      ),
    );
  }

  void _showTaskDetails(Task task) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => TaskDetailPage(task: task),
      ),
    ); // ← Das fehlte!
  }

  Future<void> _toggleTaskStatus(Task task) async {
    final newStatus = task.isDone ? 'open' : 'done';
    await context.read<TaskProvider>().updateTask(task.id, status: newStatus);
  }
}

class _TaskCard extends StatelessWidget {
  final Task task;
  final VoidCallback onTap;
  final VoidCallback onStatusToggle;

  const _TaskCard({
    required this.task,
    required this.onTap,
    required this.onStatusToggle,
  });

  @override
  Widget build(BuildContext context) {
    final priorityColor = TaskCardColors.of(task.priority);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              // Checkbox
              Checkbox(
                value: task.isDone,
                onChanged: (_) => onStatusToggle(),
              ),
              const SizedBox(width: 12),
              // Task Info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      task.title,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            decoration:
                                task.isDone ? TextDecoration.lineThrough : null,
                          ),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 2,
                          ),
                          decoration: BoxDecoration(
                            color: priorityColor.withValues(alpha: 0.2),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            task.priority.toUpperCase(),
                            style: TextStyle(
                              color: priorityColor,
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                        if (task.dueDate != null) ...[
                          const SizedBox(width: 8),
                          Icon(
                            Icons.calendar_today,
                            size: 14,
                            color: task.isOverdue ? Colors.red : Colors.grey,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            DateFormat('dd.MM.yy').format(task.dueDate!),
                            style: TextStyle(
                              fontSize: 12,
                              color: task.isOverdue ? Colors.red : Colors.grey,
                            ),
                          ),
                        ],
                        if (task.amount != null) ...[
                          const SizedBox(width: 8),
                          Text(
                            '${task.amount!.toStringAsFixed(0)}€',
                            style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ],
                ),
              ),
              // Arrow
              const Icon(Icons.chevron_right, color: Colors.grey),
            ],
          ),
        ),
      ),
    );
  }

  static Color priorityColor(String priority) => TaskCardColors.of(priority);
}

class TaskCardColors {
  static Color of(String priority) {
    switch (priority) {
      case 'critical':
        return Colors.red;
      case 'high':
        return Colors.orange;
      case 'medium':
        return Colors.blue;
      case 'low':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }
}
