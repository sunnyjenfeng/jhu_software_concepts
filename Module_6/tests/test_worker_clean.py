"""test worker clean module"""
import importlib
import json
import os
import sys

import pytest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)
WORKER_DIR = os.path.join(PROJECT_DIR, "src", "worker")
sys.path.insert(0, WORKER_DIR)

clean = importlib.import_module("clean")

@pytest.mark.worker
def test_clean_helpers_all_branches():
    """test clean helpers for all branches"""
    clean_space = getattr(clean, "_clean_space")
    extract_status = getattr(clean, "_extract_status")
    extract_decision_date = getattr(clean, "_extract_decision_date")
    extract_term = getattr(clean, "_extract_term")
    extract_student_type = getattr(clean, "_extract_student_type")
    extract_gpa = getattr(clean, "_extract_gpa")
    extract_gre_score = getattr(clean, "_extract_gre_score")
    extract_gre_v = getattr(clean, "_extract_gre_v")
    extract_gre_aw = getattr(clean, "_extract_gre_aw")
    extract_degree = getattr(clean, "_extract_degree")

    assert clean_space(None) is None
    assert clean_space("  A   B  ") == "A B"

    assert extract_status("not accepted") is None
    assert extract_status("Accepted on May 1") == "Accepted"
    assert extract_status("Rejected on May 1") == "Rejected"
    assert extract_status("Wait listed on May 1") == "Waitlisted"
    assert extract_status("Interview on May 1") == "Interview"
    assert extract_status(None) is None

    assert extract_decision_date(None) is None
    assert extract_decision_date("Accepted on May 1") == "May 1"
    assert extract_decision_date("No date") is None

    assert extract_term("Fall 2026") == "Fall 2026"
    assert extract_term("no term") is None

    assert extract_student_type(None) is None
    assert extract_student_type("International applicant") == "International"
    assert extract_student_type("American applicant") == "American"
    assert extract_student_type("domestic applicant") == "American"
    assert extract_student_type("Other applicant") == "Other"
    assert extract_student_type("unknown") is None

    assert extract_gpa("GPA 3.95") == "3.95"
    assert extract_gpa("") is None
    assert extract_gre_score("GRE 320") == "320"
    assert extract_gre_score("") is None
    assert extract_gre_v("GRE V 160") == "160"
    assert extract_gre_v("") is None
    assert extract_gre_aw("GRE AW 4.5") == "4.5"
    assert extract_gre_aw("") is None

    assert extract_degree("Computer Science PhD") == "PhD"
    assert extract_degree("Computer Science Masters") == "Masters"
    assert extract_degree("Certificate") is None


@pytest.mark.worker
def test_clean_data_and_json_helpers(tmp_path):
    """test_clean_data_and_json"""
    raw_data = [
        {
            "Program": "Computer Science PhD",
            "School": "Test University",
            "Added On": "May 1, 2026",
            "Decision": "Accepted on May 1",
            "applicant_entry_url": "https://cafe.com/result/1",
            "extra_info": "Fall 2026 International GPA 3.90 GRE 320 GRE V 160 GRE AW 4.5",
            "comments": "Great fit",
            "raw_texts": ["a"],
            "page_number": 1,
        },
        {
            "Program": "Statistics Masters",
            "School": "Other University",
            "Added On": "May 2, 2026",
            "Decision": "Rejected on May 2",
            "applicant_entry_url": "https://cafe.com/result/2",
            "extra_info": "Spring 2027 American",
            "comments": "",
            "raw_texts": ["b"],
            "page_number": 2,
        },
    ]

    cleaned = clean.clean_data(raw_data)

    assert cleaned[0]["Applicant Status"] == "Accepted"
    assert cleaned[0]["Accepted: Acceptance Date"] == "May 1"
    assert cleaned[0]["Semester and Year of Program Start"] == "Fall 2026"
    assert cleaned[0]["International / American Student"] == "International"
    assert cleaned[0]["GPA"] == "3.90"
    assert cleaned[0]["GRE Score"] == "320"
    assert cleaned[0]["GRE V Score"] == "160"
    assert cleaned[0]["GRE AW"] == "4.5"
    assert cleaned[1]["Applicant Status"] == "Rejected"
    assert cleaned[1]["Rejected: Rejection Date"] == "May 2"

    output = tmp_path / "cleaned.json"
    clean.save_data(cleaned, output)
    assert clean.load_data(output) == cleaned


@pytest.mark.worker
def test_clean_main(monkeypatch, tmp_path):
    """test_clean_data main"""
    input_file = tmp_path / "all_scraped_data.json"
    input_file.write_text(
        json.dumps(
            [
                {
                    "Program": "Computer Science PhD",
                    "School": "Test University",
                    "Added On": "May 1, 2026",
                    "Decision": "Accepted on May 1",
                    "applicant_entry_url": "https://cafe.com/result/1",
                    "extra_info": "Fall 2026 International",
                    "comments": None,
                    "raw_texts": ["a"],
                    "page_number": 1,
                }
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    clean.main()

    assert (tmp_path / "applicant_data.json").exists()
