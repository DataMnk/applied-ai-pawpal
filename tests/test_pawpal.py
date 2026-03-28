"""Tests for pawpal_system: tasks, pets, scheduling, and conflicts."""

from pathlib import Path
import tempfile

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


def test_find_next_available_slot_empty_calendar_returns_start_time():
    owner = Owner("Alex")
    owner.add_pet(Pet(name="Milo", age=2, breed="Beagle"))
    scheduler = Scheduler(owner)

    assert scheduler.find_next_available_slot(30, "09:00") == "09:00"


def test_find_next_available_slot_steps_past_overlap():
    owner = Owner("Alex")
    pet = Pet(name="Milo", age=2, breed="Beagle")
    owner.add_pet(pet)
    pet.add_task(_task("Block", "09:00", duration=45))
    scheduler = Scheduler(owner)

    assert scheduler.find_next_available_slot(30, "09:00", step=15) == "09:45"


def test_find_next_available_slot_returns_none_after_end_of_day():
    owner = Owner("Alex")
    pet = Pet(name="Milo", age=2, breed="Beagle")
    owner.add_pet(pet)
    pet.add_task(_task("All day", "00:00", duration=24 * 60))
    scheduler = Scheduler(owner)

    assert scheduler.find_next_available_slot(15, "08:00", step=15) is None


def test_find_next_available_slot_exclude_ignores_that_task():
    owner = Owner("Alex")
    pet = Pet(name="Milo", age=2, breed="Beagle")
    owner.add_pet(pet)
    move_me = _task("Move me", "09:00", duration=30)
    pet.add_task(move_me)
    scheduler = Scheduler(owner)

    assert (
        scheduler.find_next_available_slot(30, "09:00", exclude_tasks=[move_me])
        == "09:00"
    )


def test_detect_conflicts_flags_tasks_at_same_time():
    walk = _task("Neighborhood walk", "09:00")
    vet_dropoff = _task("Vet appointment drop-off", "09:00")
    grooming = _task("Grooming session", "14:00")

    scheduler = Scheduler(Owner("Sam"))
    conflicts = scheduler.detect_conflicts([walk, vet_dropoff, grooming])

    assert len(conflicts) == 2
    assert walk in conflicts and vet_dropoff in conflicts
    assert grooming not in conflicts


def test_detect_conflicts_catches_interval_overlap():
    """08:00–08:30 overlaps 08:15–08:35; both tasks should be flagged."""
    t1 = _task("Task 1", "08:00", duration=30)
    t2 = _task("Task 2", "08:15", duration=20)

    scheduler = Scheduler(Owner("Sam"))
    conflicts = scheduler.detect_conflicts([t1, t2])

    assert len(conflicts) == 2
    assert t1 in conflicts and t2 in conflicts


def test_generate_schedule_two_pets_interleaved_times_chronological():
    owner = Owner("Alex")
    pet_a = Pet(name="Milo", age=3, breed="Beagle")
    pet_b = Pet(name="Luna", age=2, breed="Tabby")
    owner.add_pet(pet_a)
    owner.add_pet(pet_b)
    pet_a.add_task(_task("Milo mid", "12:00", pet_name="Milo"))
    pet_a.add_task(_task("Milo late", "18:00", pet_name="Milo"))
    pet_b.add_task(_task("Luna early", "08:00", pet_name="Luna"))
    pet_b.add_task(_task("Luna afternoon", "15:00", pet_name="Luna"))

    scheduler = Scheduler(owner)
    ordered = scheduler.generate_schedule()

    assert [t.time for t in ordered] == ["08:00", "12:00", "15:00", "18:00"]
    assert [t.name for t in ordered] == ["Luna early", "Milo mid", "Luna afternoon", "Milo late"]


def test_filter_tasks_complete_and_pending_after_marking_some_done():
    owner = Owner("Alex")
    pet = Pet(name="Milo", age=3, breed="Beagle")
    owner.add_pet(pet)
    t1 = _task("Walk", "07:00")
    t2 = _task("Feed", "08:00")
    t3 = _task("Meds", "20:00")
    pet.add_task(t1)
    pet.add_task(t2)
    pet.add_task(t3)
    t1.mark_complete()
    t3.mark_complete()

    scheduler = Scheduler(owner)
    complete = scheduler.filter_tasks("complete")
    pending = scheduler.filter_tasks("pending")

    assert len(complete) == 2 and t1 in complete and t3 in complete
    assert len(pending) == 1 and pending[0] is t2


def test_owner_no_pets_get_all_tasks_and_generate_schedule_empty():
    owner = Owner("Nobody")
    scheduler = Scheduler(owner)

    assert scheduler.get_all_tasks() == []
    assert scheduler.generate_schedule() == []


def test_pet_no_tasks_get_all_tasks_empty():
    owner = Owner("Alex")
    owner.add_pet(Pet(name="Solo", age=1, breed="Hamster"))

    scheduler = Scheduler(owner)
    assert scheduler.get_all_tasks() == []


def test_reschedule_recurring_unknown_frequency_returns_none_without_adding():
    pet = Pet(name="Milo", age=1, breed="Beagle")
    owner = Owner("Sam", pets=[pet])
    scheduler = Scheduler(owner)
    task = Task(
        name="Grooming",
        duration=60,
        time="11:00",
        frequency="monthly",
        priority="medium",
        due_date="2026-03-27",
        pet_name="Milo",
    )
    pet.add_task(task)

    assert scheduler.reschedule_recurring(task, pet) is None
    assert len(pet.tasks) == 1


def test_reschedule_recurring_daily_new_task_is_not_complete():
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
    task.mark_complete()

    new_task = scheduler.reschedule_recurring(task, pet)

    assert new_task is not None
    assert new_task.is_complete is False


def test_detect_conflicts_three_tasks_same_time_all_included():
    a = _task("Task A", "09:00")
    b = _task("Task B", "09:00")
    c = _task("Task C", "09:00")

    scheduler = Scheduler(Owner("Sam"))
    conflicts = scheduler.detect_conflicts([a, b, c])

    assert len(conflicts) == 3
    assert a in conflicts and b in conflicts and c in conflicts


def test_owner_save_and_load_json_roundtrip():
    owner = Owner("Jamie")
    pet = Pet(name="Milo", age=4, breed="Beagle", health_conditions=["pollen"])
    t = _task("Morning walk", "07:00")
    pet.add_task(t)
    owner.add_pet(pet)

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "data.json"
        owner.save_to_json(path)
        loaded = Owner.load_from_json(path)

    assert loaded.name == "Jamie"
    assert len(loaded.pets) == 1
    assert loaded.pets[0].name == "Milo"
    assert loaded.pets[0].age == 4
    assert loaded.pets[0].breed == "Beagle"
    assert loaded.pets[0].health_conditions == ["pollen"]
    assert len(loaded.pets[0].tasks) == 1
    assert loaded.pets[0].tasks[0].name == "Morning walk"
    assert loaded.pets[0].tasks[0].time == "07:00"
    assert loaded.pets[0].tasks[0].is_complete is False


def test_owner_load_json_preserves_task_is_complete():
    owner = Owner("Alex")
    pet = Pet(name="Luna", age=2, breed="Tabby")
    t = _task("Feed", "08:00", pet_name="Luna")
    t.mark_complete()
    pet.add_task(t)
    owner.add_pet(pet)

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "snap.json"
        owner.save_to_json(path)
        loaded = Owner.load_from_json(path)

    assert loaded.pets[0].tasks[0].is_complete is True


def test_owner_save_load_empty_pets():
    owner = Owner("Solo")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "empty.json"
        owner.save_to_json(path)
        loaded = Owner.load_from_json(path)
    assert loaded.name == "Solo"
    assert loaded.pets == []
