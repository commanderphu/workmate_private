import 'package:flutter/foundation.dart';
import '../models/task.dart';
import '../services/task_service.dart';

class TaskProvider with ChangeNotifier {
  final TaskService _taskService = TaskService();

  List<Task> _tasks = [];
  bool _isLoading = false;
  String? _error;

  List<Task> get tasks => _tasks;
  bool get isLoading => _isLoading;
  String? get error => _error;

  // Filter helpers
  List<Task> get openTasks => _tasks.where((t) => t.status == 'open').toList();
  List<Task> get doneTasks => _tasks.where((t) => t.status == 'done').toList();
  List<Task> get overdueTasks => _tasks.where((t) => t.isOverdue).toList();

  List<Task> tasksByPriority(String priority) {
    return _tasks.where((t) => t.priority == priority).toList();
  }

  // Load all tasks
  Future<void> loadTasks({String? status}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _tasks = await _taskService.getTasks(status: status);
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Create task
  Future<bool> createTask({
    required String title,
    String? description,
    DateTime? dueDate,
    String? priority,
    double? amount,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final newTask = await _taskService.createTask(
        title: title,
        description: description,
        dueDate: dueDate,
        priority: priority,
        amount: amount,
      );
      _tasks.insert(0, newTask);
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

  // Update task
  Future<bool> updateTask(
    String id, {
    String? title,
    String? description,
    DateTime? dueDate,
    String? status,
    String? priority,
    double? amount,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final updatedTask = await _taskService.updateTask(
        id,
        title: title,
        description: description,
        dueDate: dueDate,
        status: status,
        priority: priority,
        amount: amount,
      );

      final index = _tasks.indexWhere((t) => t.id == id);
      if (index != -1) {
        _tasks[index] = updatedTask;
      }

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

  // Delete task
  Future<bool> deleteTask(String id) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      await _taskService.deleteTask(id);
      _tasks.removeWhere((t) => t.id == id);
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

  // Mark as done
  Future<bool> markAsDone(String id) async {
    return updateTask(id, status: 'done');
  }

  // Mark as in progress
  Future<bool> markAsInProgress(String id) async {
    return updateTask(id, status: 'in_progress');
  }

  // Clear error
  void clearError() {
    _error = null;
    notifyListeners();
  }
}
