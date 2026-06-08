# %%
import re
import json
import time

# %%
def _clean_space(value):
    """ 
    this function collapses multiple white spaces into one
    remove leading space and trailing space
    """
    if value is None:
        return None
    value = re.sub(r"\s+", " ", str(value)).strip()
    return value if value else None


def _extract_status(text):
    """ 
    this function detects the applicant status from the text, and return one of 
    the following categories
    """
    if text is not None: 
        text_lower = text.lower()

        if "not accepted" in text_lower:
            return None
        if "accepted" in text_lower:
            return "Accepted"
        if "rejected" in text_lower:
            return "Rejected"
        if "wait listed" in text_lower or "waitlisted" in text_lower:
            return "Waitlisted"
        if "interview" in text_lower:
            return "Interview"
    return None


def _extract_decision_date(text):
    if text is None:
        return None

    match = re.search(
        r"\b(?:Accepted|Rejected|Interview|Wait listed|Waitlisted)\s+on\s+([A-Za-z]{3,9}\s+\d{1,2})",
        text,
        re.IGNORECASE)
    return match.group(1) if match else None


def _extract_term(text):
    text = text or ""
    match = re.search(r"\b(Fall|Spring|Summer|Winter)\s+(20\d{2})\b", text, re.IGNORECASE)
    if match:
        return f"{match.group(1).title()} {match.group(2)}"
    return None


def _extract_student_type(text):
    if text is None:
        return None
    
    text_lower = text.lower()

    if "international" in text_lower:
        return "International"
    if "american" in text_lower or "domestic" in text_lower:
        return "American"
    if "other" in text_lower:
        return "Other"
    return None


def _extract_gpa(text):
    text = text or ""
    match = re.search(r"\bGPA\s*[: ]\s*([0-4](?:\.\d{1,3})?)\b", text, re.IGNORECASE)
    return match.group(1) if match else None


def _extract_gre_score(text):
    text = text or ""
    match = re.search(r"\bGRE\s+(\d{2,3})\b", text, re.IGNORECASE)
    return match.group(1) if match else None


def _extract_gre_v(text):
    text = text or ""
    match = re.search(r"\bGRE V\s+(\d{2,3})\b", text, re.IGNORECASE)
    return match.group(1) if match else None


def _extract_gre_aw(text):
    text = text or ""
    match = re.search(r"\bGRE AW\s+(\d(?:\.\d{1,2})?)\b", text, re.IGNORECASE)
    return match.group(1) if match else None


def _extract_degree(program):
    program = program or ""

    if "phd" in program.lower():
        return "PhD"
    if "masters" in program.lower() or "master" in program.lower():
        return "Masters"

    return None

def clean_data(raw_data):
    """
    this is the function to clean the raw data
    """
    cleaned_data = []

    for data in raw_data:
        extra_info = _clean_space(data["extra_info"])
        comments = _clean_space(data["comments"])
        decision_clean = _clean_space(data["Decision"])

        combined_text = " ".join([
            text for text in [decision_clean, extra_info, comments]
            if text])
        # two possible places to extract status
        status = _extract_status(decision_clean) or _extract_status(extra_info)
        decision_date = _extract_decision_date(decision_clean) or _extract_decision_date(extra_info)

        cleaned_data.append({
            "Program Name": _clean_space(data["Program"]),
            "University": _clean_space(data["School"]),
            "Comments": comments,
            "Date of Information Added to Grad Cafe": _clean_space(data["Added On"]),
            "URL link to applicant entry": data["applicant_entry_url"],
            "Applicant Status": status,
            "Accepted: Acceptance Date": decision_date if status == "Accepted" else None,
            "Rejected: Rejection Date": decision_date if status == "Rejected" else None,
            "Semester and Year of Program Start": _extract_term(combined_text),
            "International / American Student": _extract_student_type(combined_text),
            "GRE Score": _extract_gre_score(combined_text),
            "GRE V Score": _extract_gre_v(combined_text),
            "Masters or PhD": _extract_degree(data["Program"]),
            "GPA": _extract_gpa(combined_text),
            "GRE AW": _extract_gre_aw(combined_text),
            "extra_info": extra_info,
            "raw_texts": data["raw_texts"],
            "page_number": data["page_number"]
        })
    return cleaned_data


# %%
def save_data(cleaned_data, filename):
    """
    Saves cleaned data into a JSON file.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=4, ensure_ascii=False)

    print(f"Saved {len(cleaned_data)} records to {filename}")


def load_data(filename):
    """
    Loads cleaned data from a JSON file.
    """
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

# %%
def main():
    start_time = time.time()

    # load data
    # scraped_data_test = load_data("all_scraped_data_test.json")
    scraped_data= load_data("all_scraped_data.json")

    # clean data
    cleaned_data = clean_data(scraped_data)

    # save data
    # save_data(cleaned_data=cleaned_data, filename="applicant_test0.json")
    save_data(cleaned_data=cleaned_data, filename="applicant_data.json")

    elapsed = time.time() - start_time
    print(f"Elapsed time: {elapsed:.2f} seconds")

# %%
if __name__ == "__main__":
    main()

# %%



