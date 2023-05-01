import argparse
import asyncio
from dotenv import load_dotenv
import tasks

load_dotenv('db/.env')
# print(tasks.__all__)
parser = argparse.ArgumentParser("Task Runner")
parser.add_argument("--task", choices=tasks.__all__)

if __name__ == "__main__":
    args = parser.parse_args()
    task_to_run = args.task
    try:
        task = getattr(tasks, task_to_run)
    except ImportError as e:
        # TODO: Correct the Import Error
        print(f'Cannot Import {task_to_run}!')
        print(e)
        exit(0)

    asyncio.run(task())
