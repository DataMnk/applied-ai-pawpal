from rag_engine import get_care_insight

FALLBACK_MESSAGE = "Care insight unavailable right now."

TEST_CASES = [
    {
        "pet_name": "Tobi",
        "conditions": ["hip dysplasia"],
        "context": "morning walk at 07:00",
    },
    {
        "pet_name": "Luna",
        "conditions": ["diabetes"],
        "context": "insulin injection at 08:00",
    },
    {
        "pet_name": "Max",
        "conditions": [],
        "context": "feeding at 09:00",
    },
    {
        "pet_name": "Bella",
        "conditions": ["hip dysplasia", "arthritis"],
        "context": "evening walk at 18:00",
    },
]


def _preview_response(text: str, length: int = 100) -> str:
    return text.replace("\n", " ")[:length]


def run_evaluation() -> None:
    total_tests = len(TEST_CASES)
    passed = 0
    confidence_scores: list[float] = []

    print("=== PawPal+ RAG Evaluation ===")
    for idx, case in enumerate(TEST_CASES, start=1):
        response, _sources = get_care_insight(
            pet_name=case["pet_name"],
            health_conditions=case["conditions"],
            schedule_context=case["context"],
        )

        is_pass = response != FALLBACK_MESSAGE
        confidence = 1.0 if is_pass else 0.0
        status = "PASS" if is_pass else "FAIL"

        if is_pass:
            passed += 1
        confidence_scores.append(confidence)

        print(
            f"Test {idx} | Pet: {case['pet_name']} | {status} | "
            f"Response: {_preview_response(response)}"
        )

    failed = total_tests - passed
    average_confidence = sum(confidence_scores) / total_tests if total_tests else 0.0

    print("\n=== Summary ===")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Average confidence score: {average_confidence:.2f}")


if __name__ == "__main__":
    run_evaluation()
