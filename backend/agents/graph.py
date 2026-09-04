from langgraph.graph import StateGraph, END
from agents.state import PipelineState
from agents.nodes.classify_reviews import classify_reviews_node
from agents.nodes.cluster_themes import cluster_themes_node
from agents.nodes.rank_themes import rank_themes_node
from agents.nodes.detect_fee import detect_fee_node
from agents.nodes.extract_quotes import extract_quotes_node
from agents.nodes.analyze_trends import analyze_trends_node
from agents.nodes.verify_sources import verify_sources
from agents.nodes.generate_pulse import generate_pulse
from agents.nodes.generate_explainer import generate_explainer

def route_after_trends(state: PipelineState):
    if state.get("fee_issue"):
        return "verify_sources"
    return "generate_pulse"

def build_graph():
    builder = StateGraph(PipelineState)
    
    builder.add_node("classify_reviews", classify_reviews_node)
    builder.add_node("cluster_themes", cluster_themes_node)
    builder.add_node("rank_themes", rank_themes_node)
    builder.add_node("detect_fee", detect_fee_node)
    builder.add_node("extract_quotes", extract_quotes_node)
    builder.add_node("analyze_trends", analyze_trends_node)
    
    # Phase 4 nodes
    builder.add_node("verify_sources", verify_sources)
    builder.add_node("generate_pulse", generate_pulse)
    builder.add_node("generate_explainer", generate_explainer)
    
    builder.set_entry_point("classify_reviews")
    
    builder.add_edge("classify_reviews", "cluster_themes")
    builder.add_edge("cluster_themes", "rank_themes")
    builder.add_edge("rank_themes", "detect_fee")
    builder.add_edge("detect_fee", "extract_quotes")
    builder.add_edge("extract_quotes", "analyze_trends")
    
    # Conditional edge
    builder.add_conditional_edges("analyze_trends", route_after_trends, {
        "verify_sources": "verify_sources",
        "generate_pulse": "generate_pulse"
    })
    
    builder.add_edge("verify_sources", "generate_explainer")
    builder.add_edge("generate_explainer", "generate_pulse")
    builder.add_edge("generate_pulse", END)
    
    return builder.compile()
