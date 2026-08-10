from langgraph.graph import END, StateGraph

from graph.nodes.diagnosis import diagnosis_node
from graph.nodes.investigation import investigation_node
from graph.nodes.plan_of_action import plan_of_action_node
from graph.nodes.rule_engine import rule_engine_node
from graph.nodes.treatment import treatment_node
from graph.nodes.validation import make_validation_node
from schemas.state_object import AssessmentState


def build_graph():
    graph = StateGraph(AssessmentState)

    graph.add_node("rule_engine", rule_engine_node)
    graph.add_node("diagnosis", diagnosis_node)
    graph.add_node("validate_diagnosis", make_validation_node("diagnosis"))
    graph.add_node("investigation", investigation_node)
    graph.add_node("validate_investigation", make_validation_node("investigation"))
    graph.add_node("treatment_protocol", treatment_node)
    graph.add_node("validate_treatment", make_validation_node("treatment_protocol"))
    graph.add_node("plan_of_action", plan_of_action_node)
    graph.add_node("validate_plan", make_validation_node("plan_of_action"))

    graph.set_entry_point("rule_engine")
    graph.add_edge("rule_engine", "diagnosis")
    graph.add_edge("diagnosis", "validate_diagnosis")
    graph.add_edge("validate_diagnosis", "investigation")
    graph.add_edge("investigation", "validate_investigation")
    graph.add_edge("validate_investigation", "treatment_protocol")
    graph.add_edge("treatment_protocol", "validate_treatment")
    graph.add_edge("validate_treatment", "plan_of_action")
    graph.add_edge("plan_of_action", "validate_plan")
    graph.add_edge("validate_plan", END)

    return graph.compile()


assessment_graph = build_graph()