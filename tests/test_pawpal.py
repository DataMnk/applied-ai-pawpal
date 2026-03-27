"""Tests for pawpal_system: tasks, pets, scheduling, and conflicts."""

from pawpal_system import Owner, Pet, Scheduler, Task


def _task(
    name: str,
    time: str,
    pet_name: str = "Milo",
    duration: int = 30,
    due_date: str = "2026-03-27",
) -> Task:
    return Task(
        name=name,
        duration=duration,
        time=time,
        frequency="daily",
        priority="medium",
        due_date=due_date,
        pet_name=pet_name,
    )


def test_mark_complete_sets_is_complete_true():
    task = _task("Evening medication", "20:00")
    assert task.is_complete is False

    task.mark_complete()

    assert task.is_complete is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Milo", age=3, breed="Beagle")
    assert len(pet.tasks) == 0

    pet.add_task(_task("Morning walk", "07:30"))
    assert len(pet.tasks) == 1

    pet.add_task(_task("Dinner feeding", "18:00"))
    assert len(pet.tasks) == 2


def test_sort_by_time_returns_tasks_chronologically():
    owner = Owner("Alex")
    pet = Pet(name="Luna", age=2, breed="Tabby")
    owner.add_pet(pet)
    pet.add_task(_task("Afternoon play", "15:00", pet_name="Luna"))
    pet.add_task(_task("Breakfast", "08:00", pet_name="Luna"))
    pet.add_task(_task("Evening brush", "21:00", pet_name="Luna"))

    scheduler = Scheduler(owner)
    ordered = scheduler.sort_by_time(scheduler.get_all_tasks())

    assert [t.time for t in ordered] == ["08:00", "15:00", "21:00"]


def test_detect_conflicts_flags_tasks_at_same_time():
    walk = _task("Neighborhood walk", "09:00")
    vet_dropoff = _task("Vet appointment drop-off", "09:00")
    grooming = _task("Grooming session", "14:00")

    scheduler = Scheduler(Owner("Sam"))
    conflicts = scheduler.detect_conflicts([walk, vet_dropoff, grooming])

    assert len(conflicts) == 2
    assert walk in conflicts and vet_dropoff in conflicts
    assert grooming not in conflicts
