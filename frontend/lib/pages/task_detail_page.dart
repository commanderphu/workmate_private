import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../models/task.dart';
import '../providers/task_provider.dart';

class TaskDetailPage extends StatefulWidget {
  final Task task;

  const TaskDetailPage({
    super.key,
    required this.task,
  });

  @override
  State<TaskDetailPage> createState() => _TaskDetailPageState();
}

class _TaskDetailPageState extends State<TaskDetailPage> {
  late Task _currentTask;
  bool _isEditing = false;

  // Controllers
  late TextEditingController _titleController;
  late TextEditingController _descriptionController;

  @override
  void initState() {
    super.initState();
    _currentTask = widget.task;
    _titleController = TextEditingController(text: _currentTask.title);
    _descriptionController = TextEditingController(
      text: _currentTask.description ?? '',
    );
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final taskProvider = context.watch<TaskProvider>();

    return Scaffold(
      appBar: _buildAppBar(),
      body: taskProvider.isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildHeader(),
                  const SizedBox(height: 24),
                  _buildDetailsSection(),
                  const SizedBox(height: 24),
                  if (!_currentTask.isDone) _buildActionButtons(),
                ],
              ),
            ),
    );
  }

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      title: Text(_isEditing ? 'Edit Task' : 'Task Details'),
      actions: [
        if (!_isEditing && !_currentTask.isDone)
          IconButton(
            icon: const Icon(Icons.edit),
            onPressed: () => setState(() => _isEditing = true),
          )
        else if (_isEditing)
          IconButton(
            icon: const Icon(Icons.check),
            onPressed: _saveTask,
          ),
        IconButton(
          icon: const Icon(Icons.delete),
          onPressed: _confirmDelete,
        ),
      ],
    );
  }

  Widget _buildHeader() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            // Priority Badge
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: _getPriorityColor().withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                _currentTask.priority.toUpperCase(),
                style: TextStyle(
                  color: _getPriorityColor(),
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
              ),
            ),
            const Spacer(),
            // Status Badge
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: _getStatusColor().withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                _formatStatus(_currentTask.status),
                style: TextStyle(
                  color: _getStatusColor(),
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Title
        if (_isEditing)
          TextField(
            controller: _titleController,
            decoration: const InputDecoration(
              labelText: 'Title',
              border: OutlineInputBorder(),
            ),
            style: Theme.of(context).textTheme.titleLarge,
          )
        else
          Text(
            _currentTask.title,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  decoration:
                      _currentTask.isDone ? TextDecoration.lineThrough : null,
                ),
          ),

        const SizedBox(height: 16),

        // Description
        if (_isEditing)
          TextField(
            controller: _descriptionController,
            decoration: const InputDecoration(
              labelText: 'Description',
              border: OutlineInputBorder(),
            ),
            maxLines: 5,
          )
        else if (_currentTask.description != null &&
            _currentTask.description!.isNotEmpty)
          Text(
            _currentTask.description!,
            style: Theme.of(context).textTheme.bodyLarge,
          )
        else
          Text(
            'No description',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Colors.grey,
                  fontStyle: FontStyle.italic,
                ),
          ),

        const SizedBox(height: 16),

        // Priority Selector (Edit Mode)
        if (_isEditing) _buildPrioritySelector(),

        const SizedBox(height: 16),

        // Due Date
        _buildDueDateCard(),

        // Amount
        if (_currentTask.amount != null) ...[
          const SizedBox(height: 16),
          _buildAmountCard(),
        ],

        // Timestamps
        const SizedBox(height: 16),
        _buildTimestamps(),
      ],
    );
  }

  Widget _buildPrioritySelector() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Priority',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              children: ['low', 'medium', 'high', 'critical'].map((priority) {
                final isSelected = _currentTask.priority == priority;
                return ChoiceChip(
                  label: Text(priority.toUpperCase()),
                  selected: isSelected,
                  onSelected: (selected) {
                    if (selected) {
                      setState(() {
                        _currentTask =
                            _currentTask.copyWith(priority: priority);
                      });
                    }
                  },
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDueDateCard() {
    return Card(
      child: ListTile(
        leading: Icon(
          Icons.calendar_today,
          color: _currentTask.isOverdue ? Colors.red : Colors.blue,
        ),
        title: const Text('Due Date'),
        subtitle: _currentTask.dueDate != null
            ? Text(
                DateFormat('dd.MM.yyyy HH:mm').format(_currentTask.dueDate!),
                style: TextStyle(
                  color: _currentTask.isOverdue ? Colors.red : null,
                  fontWeight: _currentTask.isOverdue ? FontWeight.bold : null,
                ),
              )
            : const Text('No due date set'),
        trailing: _isEditing
            ? IconButton(
                icon: const Icon(Icons.edit),
                onPressed: _selectDueDate,
              )
            : null,
      ),
    );
  }

  Widget _buildAmountCard() {
    return Card(
      child: ListTile(
        leading: const Icon(Icons.attach_money, color: Colors.green),
        title: const Text('Amount'),
        subtitle: Text(
          '${_currentTask.amount!.toStringAsFixed(2)} ${_currentTask.currency ?? 'EUR'}',
          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
      ),
    );
  }

  Widget _buildTimestamps() {
    return Card(
      color: Colors.grey.shade100,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            Row(
              children: [
                const Icon(Icons.add_circle_outline,
                    size: 16, color: Colors.grey),
                const SizedBox(width: 8),
                Text(
                  'Created: ${DateFormat('dd.MM.yyyy HH:mm').format(_currentTask.createdAt)}',
                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                const Icon(Icons.update, size: 16, color: Colors.grey),
                const SizedBox(width: 8),
                Text(
                  'Updated: ${DateFormat('dd.MM.yyyy HH:mm').format(_currentTask.updatedAt)}',
                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                ),
              ],
            ),
            if (_currentTask.completedAt != null) ...[
              const SizedBox(height: 4),
              Row(
                children: [
                  const Icon(Icons.check_circle, size: 16, color: Colors.green),
                  const SizedBox(width: 8),
                  Text(
                    'Completed: ${DateFormat('dd.MM.yyyy HH:mm').format(_currentTask.completedAt!)}',
                    style: const TextStyle(fontSize: 12, color: Colors.green),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildActionButtons() {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton.icon(
        onPressed: _markAsDone,
        icon: const Icon(Icons.check_circle),
        label: const Text('Mark as Done'),
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.green,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.all(16),
        ),
      ),
    );
  }

  // Actions
  Future<void> _saveTask() async {
    final success = await context.read<TaskProvider>().updateTask(
          _currentTask.id,
          title: _titleController.text,
          description: _descriptionController.text,
          priority: _currentTask.priority,
          dueDate: _currentTask.dueDate,
        );

    if (success && mounted) {
      // Refresh task from provider
      final updatedTasks = context.read<TaskProvider>().tasks;
      final updated = updatedTasks.firstWhere((t) => t.id == _currentTask.id);

      setState(() {
        _currentTask = updated;
        _isEditing = false;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('✅ Task saved!'),
          backgroundColor: Colors.green,
        ),
      );
    } else if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('❌ Error: ${context.read<TaskProvider>().error}'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Future<void> _markAsDone() async {
    final success =
        await context.read<TaskProvider>().markAsDone(_currentTask.id);

    if (success && mounted) {
      final updatedTasks = context.read<TaskProvider>().tasks;
      final updated = updatedTasks.firstWhere((t) => t.id == _currentTask.id);

      setState(() {
        _currentTask = updated;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('✅ Task completed!'),
          backgroundColor: Colors.green,
        ),
      );
    }
  }

  Future<void> _confirmDelete() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Task'),
        content:
            Text('Are you sure you want to delete "${_currentTask.title}"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Delete'),
          ),
        ],
      ),
    );

    if (confirmed == true && mounted) {
      final success =
          await context.read<TaskProvider>().deleteTask(_currentTask.id);

      if (success && mounted) {
        Navigator.pop(context); // Go back
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('✅ Task deleted')),
        );
      }
    }
  }

  Future<void> _selectDueDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _currentTask.dueDate ?? DateTime.now(),
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );

    if (picked != null && mounted) {
      final pickedTime = await showTimePicker(
        context: context,
        initialTime:
            TimeOfDay.fromDateTime(_currentTask.dueDate ?? DateTime.now()),
      );

      if (pickedTime != null) {
        setState(() {
          _currentTask = _currentTask.copyWith(
            dueDate: DateTime(
              picked.year,
              picked.month,
              picked.day,
              pickedTime.hour,
              pickedTime.minute,
            ),
          );
        });
      }
    }
  }

  // Helpers
  Color _getPriorityColor() {
    switch (_currentTask.priority) {
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

  Color _getStatusColor() {
    switch (_currentTask.status) {
      case 'done':
        return Colors.green;
      case 'in_progress':
        return Colors.blue;
      default:
        return Colors.orange;
    }
  }

  String _formatStatus(String status) {
    switch (status) {
      case 'open':
        return 'Open';
      case 'in_progress':
        return 'In Progress';
      case 'done':
        return 'Done';
      default:
        return status;
    }
  }
}
