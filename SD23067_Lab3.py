import json
import operator
import streamlit as st


DEFAULT_RULES_JSON = """[
 {
 "name": "Top merit candidate",
 "priority": 100,
 "conditions": [
 ["cgpa", ">=", 3.7],
 ["co_curricular_score", ">=", 80],
 ["family_income", "<=", 8000],
 ["disciplinary_actions", "==", 0]
 ],
 "action": {
 "decision": "AWARD_FULL",
 "reason": "Excellent academic & co-curricular performance, with acceptable need"
 }
 },
 {
 "name": "Good candidate - partial scholarship",
 "priority": 80,
 "conditions": [
 ["cgpa", ">=", 3.3],
 ["co_curricular_score", ">=", 60],
 ["family_income", "<=", 12000],
 ["disciplinary_actions", "<=", 1]
 ],
 "action": {
 "decision": "AWARD_PARTIAL",
 "reason": "Good academic & involvement record with moderate need"
 }
 },
 {
 "name": "Need-based review",
 "priority": 70,
 "conditions": [
 ["cgpa", ">=", 2.5],
 ["family_income", "<=", 4000]
 ],
 "action": {
 "decision": "REVIEW",
 "reason": "High need but borderline academic score"
 }
 },
 {
 "name": "Low CGPA – not eligible",
 "priority": 95,
 "conditions": [
 ["cgpa", "<", 2.5]
 ],
 "action": {
 "decision": "REJECT",
 "reason": "CGPA below minimum scholarship requirement"
 }
 },
 {
 "name": "Serious disciplinary record",
 "priority": 90,
 "conditions": [
 ["disciplinary_actions", ">=", 2]
 ],
 "action": {
 "decision": "REJECT",
 "reason": "Too many disciplinary records"
 }
 }
]"""



OPERATORS = {
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
    "==": operator.eq,
}

def rule_matches(rule: dict, facts: dict) -> bool:
    """
    Check whether a single rule's conditions are satisfied by the facts.
    rule["conditions"] is a list of [field, operator_str, value]
    """
    for cond in rule.get("conditions", []):
        if len(cond) != 3:
            return False  # malformed condition
        field, op_str, expected_value = cond

        if field not in facts:
            return False

        actual_value = facts[field]
        op_func = OPERATORS.get(op_str)
        if op_func is None:
            return False  # unsupported operator

        try:
            if not op_func(actual_value, expected_value):
                return False
        except Exception:
            # In case of type mismatch or comparison error
            return False

    return True


def evaluate_applicant(facts: dict, rules: list) -> dict:
    """
    Evaluate an applicant against a list of rules.
    Returns a dictionary with decision, reason, matched rules, and selected rule.
    """
    matched_rules = []

    for rule in rules:
        if rule_matches(rule, facts):
            matched_rules.append(rule)

    if not matched_rules:
        return {
            "decision": "REVIEW",
            "reason": "No rules matched for this applicant. Rules may need review.",
            "matched_rules": [],
            "selected_rule": None,
        }

    # Conflict resolution: choose the rule with the highest 'priority'
    best_rule = max(matched_rules, key=lambda r: r.get("priority", 0))
    action = best_rule.get("action", {})

    return {
        "decision": action.get("decision", "REVIEW"),
        "reason": action.get("reason", ""),
        "matched_rules": [r.get("name", "Unnamed rule") for r in matched_rules],
        "selected_rule": best_rule.get("name", "Unnamed rule"),
    }

   #streamlit

def main():
    st.set_page_config(
        page_title="Scholarship Advisory System",
        page_icon="🎓",
        layout="centered",
    )

    st.title("🎓 Scholarship Advisory – Rule-Based Decision Support")
    st.markdown(
        """
This app demonstrates a **rule-based expert system** for scholarship advisory.

Enter an applicant's details on the left. On the right, you can see and edit
the **JSON rule base** used by the rule engine. The system then evaluates
the applicant and recommends the scholarship decision.
        """
    )

    # Layout: two columns – inputs on the left, rule editor on the right
    col_inputs, col_rules = st.columns([1.1, 1])

    with col_inputs:
        st.header("Applicant details")

        cgpa = st.number_input(
            "Cumulative GPA (CGPA)",
            min_value=0.0,
            max_value=4.0,
            step=0.01,
            value=3.5,
        )

        family_income = st.number_input(
            "Monthly family income (RM)",
            min_value=0.0,
            step=100.0,
            value=5000.0,
        )

        co_curricular_score = st.slider(
            "Co-curricular involvement score (0–100)",
            min_value=0,
            max_value=100,
            value=70,
        )

        community_service_hours = st.number_input(
            "Community service hours",
            min_value=0,
            step=1,
            value=20,
        )

        current_semester = st.number_input(
            "Current semester of study",
            min_value=1,
            step=1,
            value=3,
        )

        disciplinary_actions = st.number_input(
            "Number of disciplinary actions on record",
            min_value=0,
            step=1,
            value=0,
        )

        applicant_facts = {
            "cgpa": float(cgpa),
            "family_income": float(family_income),
            "co_curricular_score": int(co_curricular_score),
            "community_service_hours": int(community_service_hours),
            "current_semester": int(current_semester),
            "disciplinary_actions": int(disciplinary_actions),
        }

    with col_rules:
        st.header("Rule configuration (JSON)")
        st.caption(
            "Use EXACTLY these rules as the base configuration. "
            "They can be inspected or adjusted here to study different scenarios."
        )

        rules_json = st.text_area(
            "Edit rules below (JSON list of rule objects):",
            value=DEFAULT_RULES_JSON,
            height=350,
        )

        rules = None
        rules_valid = True
        try:
            rules = json.loads(rules_json)
            if not isinstance(rules, list):
                st.error("The root JSON element must be a list of rules.")
                rules_valid = False
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON in rule editor: {e}")
            rules_valid = False

    st.markdown("---")

    if st.button("Evaluate Scholarship Eligibility"):
        if not rules_valid or rules is None:
            st.error("Cannot evaluate: rules are invalid. Please fix the JSON.")
        else:
            result = evaluate_applicant(applicant_facts, rules)

            st.subheader("Decision")
            decision = result["decision"]

            if decision == "AWARD_FULL":
                st.success("✅ Decision: AWARD_FULL")
            elif decision == "AWARD_PARTIAL":
                st.success("✅ Decision: AWARD_PARTIAL")
            elif decision == "REVIEW":
                st.warning("⚠️ Decision: REVIEW")
            elif decision == "REJECT":
                st.error("❌ Decision: REJECT")
            else:
                st.info(f"ℹ️ Decision: {decision}")

            st.markdown(f"**Reason:** {result['reason']}")

            st.markdown("### Rule engine details")
            st.write(f"**Selected rule (highest priority match):** {result['selected_rule']}")
            st.write("**All matched rules:**")
            if result["matched_rules"]:
                for rname in result["matched_rules"]:
                    st.write(f"- {rname}")
            else:
                st.write("- (No rules matched)")

            st.markdown("### Applicant facts used")
            st.json(applicant_facts)


if __name__ == "__main__":
    main()

    applicant_facts = {
    "cgpa": 3.6,
    "family_income": 5000.0,
    "co_curricular_score": 70,
    "community_service_hours": 20,
    "current_semester": 3,
    "disciplinary_actions": 0,
}
