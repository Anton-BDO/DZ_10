from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os


class Task:
    def __init__(self, title, priority, task_id, is_done=False):
        self.title = title
        self.priority = priority
        self.is_done = is_done
        self.id = task_id

    def to_dict(self):
        return {
            'title': self.title,
            'priority': self.priority,
            'isDone': self.is_done,
            'id': self.id
        }


class TaskManager:
    def __init__(self, filename='tasks.txt'):
        self.filename = filename
        self.tasks = []
        self.next_id = 1
        self.load_tasks()

    def load_tasks(self):
        # Проверяем есть ли файл
        if os.path.exists(self.filename):
            try:
                f = open(self.filename, 'r', encoding='utf-8')
                data = json.load(f)
                f.close()

                # Восстанавливаем задачи из файла
                for task_data in data:
                    task = Task(
                        title=task_data['title'],
                        priority=task_data['priority'],
                        task_id=task_data['id'],
                        is_done=task_data['isDone']
                    )
                    self.tasks.append(task)

                # Находим максимальный ID
                if len(self.tasks) > 0:
                    max_id = 0
                    for task in self.tasks:
                        if task.id > max_id:
                            max_id = task.id
                    self.next_id = max_id + 1
            except:
                self.tasks = []

    def save_tasks(self):
        # Сохраняем задачи в файл
        try:
            tasks_list = []
            for task in self.tasks:
                tasks_list.append(task.to_dict())

            f = open(self.filename, 'w', encoding='utf-8')
            json.dump(tasks_list, f, ensure_ascii=False, indent=2)
            f.close()
        except:
            pass

    def create_task(self, title, priority):
        # Создаем новую задачу
        new_task = Task(title, priority, self.next_id, False)
        self.next_id += 1
        self.tasks.append(new_task)
        self.save_tasks()
        return new_task

    def get_all_tasks(self):
        # Получаем все задачи
        result = []
        for task in self.tasks:
            result.append(task.to_dict())
        return result

    def complete_task(self, task_id):
        # Ищем задачу по ID и отмечаем выполненной
        for task in self.tasks:
            if task.id == task_id:
                task.is_done = True
                self.save_tasks()
                return True
        return False


class TaskHTTPRequestHandler(BaseHTTPRequestHandler):
    # Создаем один менеджер задач для всех запросов
    task_manager = TaskManager()

    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        response = json.dumps(data, ensure_ascii=False)
        self.wfile.write(response.encode('utf-8'))

    def do_GET(self):
        # GET /tasks - получить все задачи
        if self.path == '/tasks':
            tasks = self.task_manager.get_all_tasks()
            self.send_json_response(200, tasks)
        else:
            self.send_json_response(404, {'error': 'Not found'})

    def do_POST(self):
        # POST /tasks - создать задачу
        if self.path == '/tasks':
            # Читаем тело запроса
            content_length = self.headers.get('Content-Length')
            if not content_length:
                self.send_json_response(400, {'error': 'No body'})
                return

            body = self.rfile.read(int(content_length))
            data = json.loads(body.decode('utf-8'))

            # Создаем задачу
            task = self.task_manager.create_task(data['title'], data['priority'])
            self.send_json_response(200, task.to_dict())

        # POST /tasks/{id}/complete - отметить задачу выполненной
        elif self.path.startswith('/tasks/') and self.path.endswith('/complete'):
            # Извлекаем ID из пути
            parts = self.path.split('/')
            task_id = int(parts[2])

            # Отмечаем задачу выполненной
            success = self.task_manager.complete_task(task_id)

            if success:
                self.send_response(200)
                self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_json_response(404, {'error': 'Not found'})

    def log_message(self, format, *args):
        # Отключаем логи
        pass


def run_server(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, TaskHTTPRequestHandler)

    print('Task Manager Server')
    print(f'Server running on http://localhost:{port}')

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped')
        httpd.server_close()


if __name__ == '__main__':
    run_server(8080)
