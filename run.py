from app import create_app
from app.tasks import start_background_tasks

app = create_app()

# 启动后台任务
background_thread = None
background_started = False

@app.before_request
def before_request():
    global background_thread, background_started
    if not background_started:
        background_started = True
        if background_thread is None:
            background_thread = start_background_tasks()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)