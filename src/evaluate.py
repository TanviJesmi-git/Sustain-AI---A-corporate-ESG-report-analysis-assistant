import json
from embed_store import get_model, create_session_collection, get_known_companies
from ingest import ingest_uploaded_pdf
from qa_engine import answer_query

def load_eval_set(path="data/eval_set.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_case(case: dict, result: dict) -> dict:
    answer_text = result["answer"].lower()
    checks = {}

    if "expected_value_contains" in case:
        checks["value_found"] = any(v.lower() in answer_text for v in case["expected_value_contains"])

    if "expected_behavior_contains" in case:
        checks["behavior_found"] = any(v.lower() in answer_text for v in case["expected_behavior_contains"])

    if "must_not_contain" in case:
        checks["avoided_bad_phrasing"] = not any(v.lower() in answer_text for v in case["must_not_contain"])

    if "expected_page" in case:
        retrieved_pages = [c["page_number"] for c in result["chunks"]]
        checks["page_retrieved"] = case["expected_page"] in retrieved_pages

    checks["overall_pass"] = all(checks.values()) if checks else None
    return checks


def run_evaluation():
    collection = create_session_collection()
    embed_model = get_model()

    for filename, company, year in [
        ("data/pdfs/TCS_2023_2024.pdf", "TCS", "2023-2024"),
        ("data/pdfs/wipro_2023_2024.pdf", "WIPRO", "2023-2024"),
    ]:
        with open(filename, "rb") as f:
            file_bytes = f.read()
        result = ingest_uploaded_pdf(file_bytes, filename.split("/")[-1], company, year, collection, embed_model)
        print(result["message"])

    known_companies = get_known_companies(collection)
    eval_cases = load_eval_set()

    results = []
    for case in eval_cases:
        result = answer_query(case["question"], known_companies, collection, embed_model)
        checks = check_case(case, result)
        results.append({"id": case["id"], "category": case["category"], "checks": checks,
                         "answer_preview": result["answer"][:150]})

        status = "PASS" if checks.get("overall_pass") else "FAIL"
        print(f"\n[{status}] {case['id']} ({case['category']})")
        print(f"  Checks: {checks}")
        print(f"  Answer preview: {result['answer'][:150]}")

    total = len(results)
    passed = sum(1 for r in results if r["checks"].get("overall_pass"))
    print(f"\n{'='*50}\nOverall: {passed}/{total} passed ({passed/total*100:.0f}%)")

    with open("data/eval_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    run_evaluation()