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


def test_sort_by_time_tie_breaks_by_priority_high_first():
    owner = Owner("Alex")
    pet = Pet(name="Luna", age=2, breed="Tabby")
    owner.add_pet(pet)
    pet.add_task(
        Task(
            name="Low priority",
            duration=10,
            time="09:00",
            frequency="daily",
            priority="low",
            due_date="2026-03-27",
            pet_name="Luna",
        )
    )
    pet.add_task(
        Task(
            name="High priority",
            duration=10,
            time="09:00",
            frequency="daily",
            priority="high",
            due_date="2026-03-27",
            pet_name="Luna",
        )
    )
    pet.add_task(
        Task(
            name="Medium priority",
            duration=10,
            time="09:00",
            frequency="daily",
            priority="medium",
            due_date="2026-03-27",
            pet_name="Luna",
        )
    )

    scheduler = Scheduler(owner)
    ordered = scheduler.sort_by_time(scheduler.get_all_tasks())

    assert [t.name for t in ordered] == ["High priority", "Medium priority", "Low priority"]


def test_filter_tasks_matches_pet_name_case_insensitive():
    owner = Owner("Alex")
    pet = Pet(name="Luna", age=2, breed="Tabby")
    owner.add_pet(pet)
    pet.add_task(_task("Walk", "07:00", pet_name="Luna"))

    scheduler = Scheduler(owner)
    assert len(scheduler.filter_tasks("  luna ")) == 1
    assert scheduler.filter_tasks("LUNA")[0].name == "Walk"


def test_reschedule_recurring_once_returns_none_without_adding():
    pet = Pet(name="Milo", age=1, breed="Beagle")
    owner = Owner("Sam", pets=[pet])
    scheduler = Scheduler(owner)
    task = Task(
        name="One shot",
        duration=15,
        time="10:00",
        frequency="once",
        priority="medium",
        due_date="2026-03-27",
        pet_name="Milo",
    )
    pet.add_task(task)

    assert scheduler.reschedule_recurring(task, pet) is None
    assert len(pet.tasks) == 1


def test_reschedule_recurring_daily_adds_copy_with_next_day_due():
    pet = Pet(name="Milo", age=1, breed="Beagle")
    owner = Owner("Sam", pets=[pet])
    scheduler = Scheduler(owner)
    task = Task(
        name="Walk",
        duration=30,
        time="07:00",
        frequency="daily",
        priority="high",
        due_date="2026-03-27",
        pet_name="Milo",
    )
    pet.add_task(task)

    new_task = scheduler.reschedule_recurring(task, pet)

    assert new_task is not None
    assert new_task.due_date == "2026-03-28"
    assert new_task.name == "Walk" and new_task.time == "07:00"
    assert len(pet.tasks) == 2
    assert pet.tasks[-1] is new_task


def test_reschedule_recurring_weekly_adds_copy_seven_days_out():
    pet = Pet(name="Milo", age=1, breed="Beagle")
    owner = Owner("Sam", pets=[pet])
    scheduler = Scheduler(owner)
    task = Task(
        name="Nail trim",
        duration=20,
        time="14:00",
        frequency="weekly",
        priority="low",
        due_date="2026-03-27",
        pet_name="Milo",
    )
    pet.add_task(task)

    new_task = scheduler.reschedule_recurring(task, pet)

    assert new_task is not None
    assert new_task.due_date == "2026-04-03"


def test_detect_conflicts_flags_tasks_at_same_time():
    walk = _task("Neighborhood walk", "09:00")
    vet_dropoff = _task("Vet appointment drop-off", "09:00")
    grooming = _task("Grooming session", "14:00")

    scheduler = Scheduler(Owner("Sam"))
    conflicts = scheduler.detect_conflicts([walk, vet_dropoff, grooming])

    assert len(conflicts) == 2
    assert walk in conflicts and vet_dropoff in conflicts
    assert grooming not in conflicts
