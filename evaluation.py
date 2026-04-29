from rag_engine import (
    agentic_get_care_insight,
    baseline_get_care_insight,
    get_care_insight,
)

FALLBACK_MESSAGE = "Care insight unavailable right now."

TEST_CASE_1 = {
    "pet_name": "Tobi",
    "conditions": ["hip dysplasia"],
    "context": "morning walk at 07:00",
}

TEST_CASE_4 = {
    "pet_name": "Tobi",
    "conditions": ["hip dysplasia"],
    "context": "morning walk at 07:00",
}


def run_evaluation() -> None:
    print("=== PawPal+ Specialization Comparison (Test Case 1) ===")
    print(f"Pet: {TEST_CASE_1['pet_name']}")
    print(f"Conditions: {', '.join(TEST_CASE_1['conditions'])}")
    print(f"Schedule context: {TEST_CASE_1['context']}\n")

    specialized_response, specialized_sources = get_care_insight(
        pet_name=TEST_CASE_1["pet_name"],
        health_conditions=TEST_CASE_1["conditions"],
        schedule_context=TEST_CASE_1["context"],
    )

    baseline_response, _baseline_sources = baseline_get_care_insight(
        pet_name=TEST_CASE_1["pet_name"],
        health_conditions=TEST_CASE_1["conditions"],
        schedule_context=TEST_CASE_1["context"],
    )

    print("=== Specialized (Few-shot + RAG) ===")
    if specialized_response == FALLBACK_MESSAGE:
        print("Care insight unavailable right now.")
    else:
        print(specialized_response)
    print(
        f"\nSources used: {', '.join(specialized_sources) if specialized_sources else 'none'}\n"
    )

    print("=== Baseline (No few-shot, No knowledge context) ===")
    if baseline_response == FALLBACK_MESSAGE:
        print("Care insight unavailable right now.")
    else:
        print(baseline_response)

    print("\n=== Test Case 4: Agentic Workflow (Analyze -> Plan -> Generate) ===")
    print(f"Pet: {TEST_CASE_4['pet_name']}")
    print(f"Conditions: {', '.join(TEST_CASE_4['conditions'])}")
    print(f"Schedule context: {TEST_CASE_4['context']}\n")

    agentic_response, agentic_sources = agentic_get_care_insight(
        pet_name=TEST_CASE_4["pet_name"],
        health_conditions=TEST_CASE_4["conditions"],
        schedule_context=TEST_CASE_4["context"],
    )

    if agentic_response == FALLBACK_MESSAGE:
        print("Care insight unavailable right now.")
    else:
        print(agentic_response)
    print(f"\nSources used: {', '.join(agentic_sources) if agentic_sources else 'none'}")


if __name__ == "__main__":
    run_evaluation()
