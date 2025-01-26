from time import sleep
from .task import Task


class Pool:
    def __init__(
        self, tasks: list[Task], pool_size: int = 9999, sleep_time: float = 30
    ):
        self.tasks_to_do = tasks
        self.pool_size = pool_size
        self.sleep_time = sleep_time
        self.pool: list[Task] = []

    def remove_finished_tasks_from_pool(self):
        self.pool = [task for task in self.pool if not task.is_finished()]

    def fill_the_pool(self):
        while len(self.pool) < self.pool_size and len(self.tasks_to_do) > 0:
            task = self.tasks_to_do[0]
            self.tasks_to_do.pop(0)
            self.pool.append(task)
            task.run()

    def run(self):
        while len(self.tasks_to_do) > 0 or len(self.pool) > 0:
            self.remove_finished_tasks_from_pool()
            self.fill_the_pool()
            sleep(self.sleep_time)
