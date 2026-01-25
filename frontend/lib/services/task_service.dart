import '../config/api_config.dart';
import '../models/task.dart';
import 'api_service.dart';

class TaskService {
  final ApiService _apiService = ApiService();

  static final TaskService _instance = TaskService._internal();
  factory TaskService() => _instance;
  TaskService._internal();

  // Get all tasks
  Future<List<Task>> getTasks({String? status}) async {
    final queryParams = status != null ? {'status': status} : null;
    final response = await _apiService.get(
      ApiConfig.tasks,
      queryParameters: queryParams,
    );

    final List<dynamic> data = response.data;
    return data.map((json) => Task.fromJson(json)).toList();
  }

  // Get single task
  Future<Task> getTask(String id) async {
    final response = await _apiService.get(ApiConfig.taskById(id));
    return Task.fromJson(response.data);
  }

  // Create task
  Future<Task> createTask({
    required String title,
    String? description,
    DateTime? dueDate,
    String? priority,
    double? amount,
  }) async {
    final response = await _apiService.post(
      ApiConfig.tasks,
      data: {
        'title': title,
        if (description != null) 'description': description,
        if (dueDate != null) 'due_date': dueDate.toIso8601String(),
        if (priority != null) 'priority': priority,
        if (amount != null) 'amount': amount,
      },
    );

    return Task.fromJson(response.data);
  }

  // Update task
  Future<Task> updateTask(
    String id, {
    String? title,
    String? description,
    DateTime? dueDate,
    String? status,
    String? priority,
    double? amount,
  }) async {
    final data = <String, dynamic>{};

    if (title != null) data['title'] = title;
    if (description != null) data['description'] = description;
    if (dueDate != null) data['due_date'] = dueDate.toIso8601String();
    if (status != null) data['status'] = status;
    if (priority != null) data['priority'] = priority;
    if (amount != null) data['amount'] = amount;

    final response = await _apiService.patch(
      ApiConfig.taskById(id),
      data: data,
    );

    return Task.fromJson(response.data);
  }

  // Delete task
  Future<void> deleteTask(String id) async {
    await _apiService.delete(ApiConfig.taskById(id));
  }

  // Mark task as done
  Future<Task> markAsDone(String id) async {
    return updateTask(id, status: 'done');
  }

  // Mark task as in progress
  Future<Task> markAsInProgress(String id) async {
    return updateTask(id, status: 'in_progress');
  }
}
