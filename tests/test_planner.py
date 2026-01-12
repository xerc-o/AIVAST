import pytest
from src.ai.planner import plan_scan_rule_based

def test_plan_scan_rule_based_nmap():
    """
    Tests that the rule-based planner correctly chooses nmap for a hostname.
    """
    plan = plan_scan_rule_based("example.com")
    assert plan["tool"] == "nmap"
    assert isinstance(plan["command"], list)
    assert plan["command"] == ["nmap", "-sV", "-T4", "-oX", "-", "example.com"]

def test_plan_scan_rule_based_nikto():
    """
    Tests that the rule-based planner correctly chooses nikto for an HTTP URL.
    """
    plan = plan_scan_rule_based("http://example.com")
    assert plan["tool"] == "nikto"
    assert isinstance(plan["command"], list)
    assert plan["command"] == ["nikto", "-h", "http://example.com", "-Format", "xml"]
