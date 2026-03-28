from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional

_COMPLETE_CRITERIA = frozenset({"complete", "completed", "done", "true", "yes"})
_INCOMPLETE_CRITERIA = frozenset({"incomplete", "pending", "false", "no", "todo"})

_PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def _parse_time_key(time_str: str) -> tuple[int, int]:
    parts = time_str.split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0
    return (hour, minute)


def _total_minutes_from_hhmm(time_str: str) -> int:
    h, m = _parse_time_key(time_str)
    return h * 60 + m


def _hhmm_from_total_minutes(total: int) -> str:
    return f"{total // 60:02d}:{total % 60:02d}"


def _intervals_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    """True if [a_start, a_end) and [b_start, b_end) intersect."""
    return not (a_end <= b_start or a_start >= b_end)


def _priority_rank(priority: str) -> int:
    return _PRIORITY_RANK.get(priority.strip().lower(), 99)


def _task_sort_key(task: Task) -> tuple[tuple[int, int], int]:
    return (_parse_time_key(task.time), _priority_rank(task.priority))


def _priority_then_time_sort_key(task: Task) -> tuple[int, tuple[int, int]]:
    return (_priority_rank(task.priority), _parse_time_key(task.time))


@dataclass
class Task:
    name: str
    duration: int  # minutes
    time: str  # "HH:MM"
    frequency: str  # daily/weekly/once
    priority: str  # low/medium/high
    due_date: str  # "YYYY-MM-DD" for once/weekly tasks
    pet_name: str
    is_complete: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.is_complete = True


@dataclass
class Pet:
    name: str
    age: int
    breed: str
    health_conditions: List[str] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        self.tasks.append(task)


class Owner:
    def __init__(self, name: str, pets: List[Pet] | None = None) -> None:
        """Initialize owner with a name and optional list of pets."""
        self.name = name
        self.pets = pets if pets is not None else []

    def add_pet(self, pet: Pet) -> None:
        """Append a pet to this owner's pet list."""
        self.pets.append(pet)

    def save_to_json(self, filepath: str | Path) -> None:
        """Serialize this owner, all pets, and their tasks to a JSON file."""
        path = Path(filepath)
        payload = {
            "name": self.name,
            "pets": [
                {
                    "name": pet.name,
                    "age": pet.age,
                    "breed": pet.breed,
                    "health_conditions": list(pet.health_conditions),
                    "tasks": [
                        {
                            "name": task.name,
                            "duration": task.duration,
                            "time": task.time,
                            "frequency": task.frequency,
                            "priority": task.priority,
                            "due_date": task.due_date,
                            "pet_name": task.pet_name,
                            "is_complete": task.is_complete,
                        }
                        for task in pet.tasks
                    ],
                }
                for pet in self.pets
            ],
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load_from_json(cls, filepath: str | Path) -> Owner:
        """Load an owner with pets and tasks from a JSON file."""
        path = Path(filepath)
        raw = json.loads(path.read_text(encoding="utf-8"))
        pets_out: List[Pet] = []
        for p_raw in raw.get("pets", []):
            task_objs = [
                Task(
                    name=t["name"],
                    duration=int(t["duration"]),
                    time=t["time"],
                    frequency=t["frequency"],
                    priority=t["priority"],
                    due_date=t["due_date"],
                    pet_name=t["pet_name"],
                    is_complete=bool(t.get("is_complete", False)),
                )
                for t in p_raw.get("tasks", [])
            ]
            pets_out.append(
                Pet(
                    name=p_raw["name"],
                    age=int(p_raw["age"]),
                    breed=p_raw["breed"],
                    health_conditions=list(p_raw.get("health_conditions", [])),
                    tasks=task_objs,
                )
            )
        return cls(name=raw["name"], pets=pets_out)


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        """Bind this scheduler to an owner whose pets' tasks it will manage."""
        self.owner = owner

    def get_all_tasks(self) -> List[Task]:
        """Collect every task from all of the owner's pets."""
        all_tasks: List[Task] = []
        for pet in self.owner.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Return tasks ordered by scheduled time (hour and minute).
        Same time breaks ties by priority (high first).
        """
        return sorted(tasks, key=_task_sort_key)

    def sort_by_priority_then_time(self, tasks: List[Task]) -> List[Task]:
        """Return tasks ordered by priority (high → medium → low), then by time."""
        return sorted(tasks, key=_priority_then_time_sort_key)

    def filter_tasks(self, criteria: str) -> List[Task]:
        """Return tasks matching completion keywords or a pet name."""
        tasks = self.get_all_tasks()
        key = criteria.strip().lower()
        if key in _COMPLETE_CRITERIA:
            return [t for t in tasks if t.is_complete]
        if key in _INCOMPLETE_CRITERIA:
            return [t for t in tasks if not t.is_complete]
        return [t for t in tasks if t.pet_name.strip().lower() == key]

    def reschedule_recurring(self, task: Task, pet: Pet) -> Optional[Task]:
        """Roll a recurring task forward; add the new task to ``pet``. ``once`` → ``None``."""
        freq = task.frequency.strip().lower()
        if freq == "once":
            return None
        if freq == "daily":
            delta = timedelta(days=1)
        elif freq == "weekly":
            delta = timedelta(days=7)
        else:
            return None

        base = date.fromisoformat(task.due_date)
        new_task = replace(
            task,
            due_date=(base + delta).isoformat(),
            is_complete=False,
        )
        pet.add_task(new_task)
        return new_task

    def detect_conflicts(self, tasks: List[Task]) -> List[Task]:
        """Return tasks whose interval [time, time + duration) overlaps another's."""
        conflicted: set[int] = set()
        n = len(tasks)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = tasks[i], tasks[j]
                a0 = _total_minutes_from_hhmm(a.time)
                a1 = a0 + int(a.duration)
                b0 = _total_minutes_from_hhmm(b.time)
                b1 = b0 + int(b.duration)
                if _intervals_overlap(a0, a1, b0, b1):
                    conflicted.add(id(a))
                    conflicted.add(id(b))
        return [t for t in tasks if id(t) in conflicted]

    def _task_blocks_interval(self, task: Task, cand_start: int, cand_end: int) -> bool:
        t0 = _total_minutes_from_hhmm(task.time)
        t1 = t0 + int(task.duration)
        return _intervals_overlap(cand_start, cand_end, t0, t1)

    def find_next_available_slot(
        self,
        duration: int,
        start_time: str,
        step: int = 15,
        *,
        exclude_tasks: Optional[List[Task]] = None,
    ) -> Optional[str]:
        """Return the next start time (\"HH:MM\") with no overlapping tasks, or None.

        Tries ``start_time`` first, then advances by ``step`` minutes until after
        23:59. A slot [start, start + duration) must not overlap any existing
        task interval. Pass ``exclude_tasks`` when the slot is for a task already
        on the schedule (e.g. suggesting a move for a conflicting task).
        """
        excluded_ids = {id(t) for t in (exclude_tasks or [])}
        blockers = [t for t in self.get_all_tasks() if id(t) not in excluded_ids]
        dur = int(duration)
        cur = _total_minutes_from_hhmm(start_time)
        last_start = 23 * 60 + 59

        while cur <= last_start:
            cand_end = cur + dur
            if not any(
                self._task_blocks_interval(t, cur, cand_end) for t in blockers
            ):
                return _hhmm_from_total_minutes(cur)
            cur += int(step)

        return None

    def generate_schedule(self) -> List[Task]:
        """Return all tasks across pets, sorted by scheduled time."""
        return self.sort_by_time(self.get_all_tasks())
