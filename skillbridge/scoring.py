def calculate_readiness_score(matched_skills, partial_skills, missing_skills, optional_skills, has_project_evidence=True, experience_years=1):
    """
    Calculates a transparent Job Readiness Score (0-100) based on PRD Section 51 algorithm:
    - Required Skill Coverage: 50%
    - Preferred Skill Coverage: 15%
    - Experience Alignment: 15%
    - Project Evidence: 10%
    - Skill Evidence: 10%
    """
    total_required = len(matched_skills) + len(partial_skills) + len(missing_skills)
    if total_required == 0:
        total_required = 1

    # 1. Required Skill Coverage (50% max)
    # Matched = 100% value, Partial = 50% value, Missing = 0%
    weighted_matched = len(matched_skills) * 1.0 + len(partial_skills) * 0.5
    required_ratio = weighted_matched / total_required
    required_score = required_ratio * 50.0

    # 2. Preferred/Optional Skill Coverage (15% max)
    preferred_score = 15.0 if len(optional_skills) == 0 else min(15.0, (len(matched_skills) / max(1, len(optional_skills))) * 15.0)

    # 3. Experience Alignment (15% max)
    if experience_years >= 2:
        exp_score = 15.0
    elif experience_years == 1:
        exp_score = 12.0
    else:
        exp_score = 9.0  # Fresher default

    # 4. Project Evidence (10% max)
    proj_score = 10.0 if has_project_evidence else 5.0

    # 5. Skill Evidence (10% max)
    skill_evidence_score = min(10.0, (len(matched_skills) / max(1, total_required)) * 10.0)

    final_score = int(round(required_score + preferred_score + exp_score + proj_score + skill_evidence_score))
    return max(0, min(100, final_score))
