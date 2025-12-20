from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from datetime import datetime


class Task:
    def __init__(self, title, priority, task_id=None, is_done=False):
        self.title = title
        self.priority = priority
        self.is_done = is_done
        self.id = task_id
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        return {
            'title': self.title,
            'priority': self.priority,
            'isDone': self.is_done,
            'id': self.id,
            'createdAt': self.created_at
        }

    @staticmethod
    def from_dict(data):
        task = Task(
            title=data['title'],
            priority=data['priority'],
            task_id=data['id'],
            is_done=data['isDone']
        )
        if 'createdAt' in data:
            task.created_at = data['createdAt']
        return task


class TaskManager:
    def __init__(self, filename='tasks.txt'):
        self.filename = filename
        self.tasks = []
        self.next_id = 1
        self.load_tasks()

    def load_tasks(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for task_data in data:
                        task = Task.from_dict(task_data)
                        self.tasks.append(task)

                    if len(self.tasks) > 0:
                        max_id = max(task.id for task in self.tasks)
                        self.next_id = max_id + 1
            except Exception:
                self.tasks = []

    def save_tasks(self):
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                tasks_list = [task.to_dict() for task in self.tasks]
                json.dump(tasks_list, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def create_task(self, title, priority):
        new_task = Task(title, priority, self.next_id)
        self.next_id += 1
        self.tasks.append(new_task)
        self.save_tasks()
        return new_task

    def get_all_tasks(self):
        return [task.to_dict() for task in self.tasks]

    def complete_task(self, task_id):
        for task in self.tasks:
            if task.id == task_id:
                task.is_done = True
                self.save_tasks()
                return True
        return False

    def delete_task(self, task_id):
        for i in range(len(self.tasks)):
            if self.tasks[i].id == task_id:
                self.tasks.pop(i)
                self.save_tasks()
                return True
        return False

    def get_stats(self):
        total = len(self.tasks)
        completed = 0

        for task in self.tasks:
            if task.is_done:
                completed += 1

        by_priority = {}
        for task in self.tasks:
            if task.priority not in by_priority:
                by_priority[task.priority] = 0
            by_priority[task.priority] += 1

        return {
            'total': total,
            'completed': completed,
            'pending': total - completed,
            'by_priority': by_priority
        }


class TaskHTTPRequestHandler(BaseHTTPRequestHandler):
    task_manager = TaskManager()

    def get_html_page(self):
        return '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Manager</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background-color: white;
            font-family: Arial, sans-serif;
            padding: 20px;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
        }

        h1 {
            color: #333;
            margin-bottom: 20px;
        }

        .stats {
            background-color: #f0f8ff;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }

        .stats-item {
            display: inline-block;
            margin-right: 20px;
        }

        .form-section {
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }

        .form-group {
            margin-bottom: 15px;
        }

        label {
            display: block;
            margin-bottom: 5px;
            color: #333;
        }

        input[type="text"], select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }

        .btn {
            background-color: #87CEEB;
            color: black;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-right: 10px;
        }

        .btn:hover {
            background-color: #6CB4D6;
        }

        .btn-small {
            padding: 5px 15px;
            font-size: 12px;
        }

        .tasks-container {
            margin-top: 20px;
        }

        .task-block {
            background-color: #f5f5f5;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: start;
        }

        .task-info {
            flex: 1;
        }

        .task-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }

        .task-details {
            font-size: 14px;
            color: #666;
            margin-bottom: 5px;
        }

        .priority-high {
            color: #d32f2f;
            font-weight: bold;
        }

        .priority-normal {
            color: #1976d2;
        }

        .priority-low {
            color: #388e3c;
        }

        .task-done {
            text-decoration: line-through;
            opacity: 0.6;
        }

        .task-actions {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }

        .error {
            background-color: #ffebee;
            color: #c62828;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 10px;
        }

        .success {
            background-color: #e8f5e9;
            color: #2e7d32;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Task Manager</h1>

        <div class="stats" id="stats">
            <div class="stats-item">Total: <strong>0</strong></div>
            <div class="stats-item">Completed: <strong>0</strong></div>
            <div class="stats-item">Pending: <strong>0</strong></div>
        </div>

        <div class="form-section">
            <h2>Add New Task</h2>
            <div id="message"></div>
            <form id="taskForm">
                <div class="form-group">
                    <label for="title">Task Title:</label>
                    <input type="text" id="title" required>
                </div>
                <div class="form-group">
                    <label for="priority">Priority:</label>
                    <select id="priority" required>
                        <option value="low">Low</option>
                        <option value="normal" selected>Normal</option>
                        <option value="high">High</option>
                    </select>
                </div>
                <button type="submit" class="btn">Add Task</button>
            </form>
        </div>

        <div class="tasks-container" id="tasksContainer">
        </div>
    </div>

    <script>
        function showMessage(message, isError = false) {
            const msgDiv = document.getElementById('message');
            msgDiv.textContent = message;
            msgDiv.className = isError ? 'error' : 'success';
            setTimeout(() => msgDiv.textContent = '', 3000);
        }

        async function loadStats() {
            try {
                const response = await fetch('/tasks/stats');
                const stats = await response.json();

                const statsDiv = document.getElementById('stats');
                statsDiv.innerHTML = `
                    <div class="stats-item">Total: <strong>${stats.total}</strong></div>
                    <div class="stats-item">Completed: <strong>${stats.completed}</strong></div>
                    <div class="stats-item">Pending: <strong>${stats.pending}</strong></div>
                `;
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }

        async function loadTasks() {
            try {
                const response = await fetch('/tasks');
                const tasks = await response.json();
                displayTasks(tasks);
                loadStats();
            } catch (error) {
                showMessage('Error loading tasks', true);
            }
        }

        function displayTasks(tasks) {
            const container = document.getElementById('tasksContainer');

            if (tasks.length === 0) {
                container.innerHTML = '<p>No tasks found</p>';
                return;
            }

            container.innerHTML = tasks.map(task => `
                <div class="task-block">
                    <div class="task-info">
                        <div class="task-title ${task.isDone ? 'task-done' : ''}">${task.title}</div>
                        <div class="task-details">ID: ${task.id}</div>
                        <div class="task-details">Priority: <span class="priority-${task.priority}">${task.priority}</span></div>
                        <div class="task-details">Status: ${task.isDone ? 'Completed' : 'Pending'}</div>
                        <div class="task-details">Created: ${task.createdAt}</div>
                    </div>
                    <div class="task-actions">
                        ${!task.isDone ? `<button class="btn btn-small" onclick="completeTask(${task.id})">Complete</button>` : ''}
                        <button class="btn btn-small" onclick="deleteTask(${task.id})">Delete</button>
                    </div>
                </div>
            `).join('');
        }

        document.getElementById('taskForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const title = document.getElementById('title').value;
            const priority = document.getElementById('priority').value;

            try {
                const response = await fetch('/tasks', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({title, priority})
                });

                if (response.ok) {
                    showMessage('Task added successfully!');
                    document.getElementById('taskForm').reset();
                    loadTasks();
                } else {
                    showMessage('Error adding task', true);
                }
            } catch (error) {
                showMessage('Error adding task', true);
            }
        });

        async function completeTask(id) {
            try {
                const response = await fetch(`/tasks/${id}/complete`, {method: 'POST'});

                if (response.ok) {
                    showMessage('Task completed!');
                    loadTasks();
                } else {
                    showMessage('Error completing task', true);
                }
            } catch (error) {
                showMessage('Error completing task', true);
            }
        }

        async function deleteTask(id) {
            if (!confirm('Are you sure you want to delete this task?')) return;

            try {
                const response = await fetch(`/tasks/${id}`, {method: 'DELETE'});

                if (response.ok) {
                    showMessage('Task deleted!');
                    loadTasks();
                } else {
                    showMessage('Error deleting task', true);
                }
            } catch (error) {
                showMessage('Error deleting task', true);
            }
        }

        loadTasks();
    </script>
</body>
</html>'''

    def send_json_response(self, status_code, data=None):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        if data is not None:
            if isinstance(data, dict) or isinstance(data, list):
                response = json.dumps(data, ensure_ascii=False)
                self.wfile.write(response.encode('utf-8'))
            else:
                self.wfile.write(b'')

    def send_html_response(self, html):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def parse_request_body(self):
        content_length = self.headers.get('Content-Length')

        if not content_length:
            return None

        try:
            length = int(content_length)
            body = self.rfile.read(length)
            data = json.loads(body.decode('utf-8'))
            return data
        except Exception:
            return None

    def extract_id_from_path(self, path):
        try:
            parts = path.split('/')
            return int(parts[2])
        except (ValueError, IndexError):
            return None

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            html = self.get_html_page()
            self.send_html_response(html)

        elif self.path == '/tasks':
            tasks = self.task_manager.get_all_tasks()
            self.send_json_response(200, tasks)

        elif self.path == '/tasks/stats':
            stats = self.task_manager.get_stats()
            self.send_json_response(200, stats)

        else:
            self.send_json_response(404, {'error': 'Not found'})

    def do_POST(self):
        if self.path == '/tasks':
            data = self.parse_request_body()

            if not data:
                self.send_json_response(400, {'error': 'Invalid body'})
                return

            if 'title' not in data or 'priority' not in data:
                self.send_json_response(400, {'error': 'Missing title or priority'})
                return

            if data['priority'] not in ['low', 'normal', 'high']:
                self.send_json_response(400, {'error': 'Priority must be low, normal or high'})
                return

            task = self.task_manager.create_task(data['title'], data['priority'])
            self.send_json_response(200, task.to_dict())

        elif '/tasks/' in self.path and self.path.endswith('/complete'):
            task_id = self.extract_id_from_path(self.path)

            if task_id is None:
                self.send_json_response(400, {'error': 'Invalid task ID'})
                return

            success = self.task_manager.complete_task(task_id)

            if success:
                self.send_json_response(200, b'')
            else:
                self.send_json_response(404, b'')

        else:
            self.send_json_response(404, {'error': 'Not found'})

    def do_DELETE(self):
        if '/tasks/' in self.path:
            task_id = self.extract_id_from_path(self.path)

            if task_id is None:
                self.send_json_response(400, {'error': 'Invalid task ID'})
                return

            success = self.task_manager.delete_task(task_id)

            if success:
                self.send_json_response(200, {'message': 'Task deleted'})
            else:
                self.send_json_response(404, {'error': 'Task not found'})
        else:
            self.send_json_response(404, {'error': 'Not found'})

    def log_message(self, format, *args):
        pass


def run_server(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, TaskHTTPRequestHandler)

    print("=" * 60)
    print("Task Manager Server")
    print("=" * 60)
    print(f"Running on: http://localhost:{port}")
    print(f"Storage file: {TaskHTTPRequestHandler.task_manager.filename}")
    print()
    print("Open in browser: http://localhost:{0}".format(port))
    print()
    print("API Endpoints:")
    print("  GET    /tasks              - get all tasks")
    print("  GET    /tasks/stats        - get statistics")
    print("  POST   /tasks              - create new task")
    print("  POST   /tasks/{id}/complete - mark task as done")
    print("  DELETE /tasks/{id}         - delete task")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        httpd.server_close()


if __name__ == '__main__':
    run_server(8080)