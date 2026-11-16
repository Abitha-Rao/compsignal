from compsignal.signals import analyze_job
from compsignal.score import comp_activity_score, incumbent_tool_signal

def job(title, text, url="https://x/1"):
    return {"title": title, "text": text, "url": url}

def kinds(j):
    return [(s.kind, s.detail) for s in analyze_job(j)]

def test_exactly_is_not_xactly():
    assert kinds(job("AE", "We know exactly what we want")) == []

def test_spiff_bonus_is_not_vendor():
    assert ("tool", "Spiff") not in kinds(job("AE", "Earn SPIFFs and bonuses"))
    assert ("tool", "Spiff") in kinds(job("Analyst", "Run commission plans; experience with Spiff preferred"))

def test_comp_role_title_and_tool_in_comp_role():
    s = analyze_job(job("Senior Commissions Manager", "Experience with CaptivateIQ or Xactly"))
    assert any(x.kind == "comp_role_title" for x in s)
    strength, tools = incumbent_tool_signal(s)
    assert strength == "listed" and tools == ["CaptivateIQ", "Xactly"]

def test_tool_outside_comp_role_is_possible_only():
    s = analyze_job(job("Sales Operations Analyst", "Support commission payouts; experience with Varicent is a plus"))
    assert incumbent_tool_signal(s)[0] == "specific"

def test_excel_commission_signal():
    s = analyze_job(job("RevOps Analyst", "You will manage commissions in Excel each month"))
    assert any(x.kind == "excel_commission" for x in s)

def test_plain_ae_posting_has_no_signal():
    assert kinds(job("Account Executive", "Competitive OTE, uncapped commission, hit your quota")) == []

def test_score_is_capped_and_monotonic():
    one = analyze_job(job("Commissions Analyst", ""))
    two = one + analyze_job(job("Sales Compensation Manager", ""))
    assert 40 <= comp_activity_score(one) < comp_activity_score(two) <= 100

def test_excel_and_commission_must_share_a_sentence():
    far = job("Payroll Accountant", "Support bonus and commissions. Proficient with Microsoft Excel.")
    assert not any(x.kind == "excel_commission" for x in analyze_job(far))

def test_html_entities_cleaned_in_snippets():
    s = analyze_job(job("Analyst", "Own the&nbsp;process. Experience with Xactly&nbsp;Incent"))
    assert all("&nbsp;" not in x.snippet for x in s)

def test_single_platform_is_specific_and_list_is_not():
    one = analyze_job(job("Commissions Manager", "You will own plan logic in Xactly and run monthly close"))
    assert incumbent_tool_signal(one)[0] == "specific"
    many = analyze_job(job("Commissions Manager", "Experience with platforms such as CaptivateIQ, Spiff, Varicent or Xactly"))
    assert incumbent_tool_signal(many)[0] == "listed"

def test_vendor_named_as_customer_in_unrelated_posting_is_ignored():
    s = analyze_job(job("Business Development Representative", "delivering predictions for enterprises like Cisco and Xactly. Trust you to evangelize"))
    assert s == []

def test_commission_accounting_is_not_commission_operations():
    s = analyze_job(job("Manager, Corporate Accounting", "Own deferred commission accounting under ASC 340-40, including capitalization"))
    assert not any(x.kind == "comp_duty" for x in s)

def test_pay_benchmarking_cycle_is_not_commission_operations():
    s = analyze_job(job("Senior Compensation Manager, Sales", "Own Sales compensation-cycle execution end-to-end, including market benchmarking"))
    assert not any(x.kind == "comp_duty" for x in s)

def test_real_commission_duties_still_detected():
    a = analyze_job(job("Revenue Operations Analyst", "Support recurring sales compensation processes, including payout validation"))
    b = analyze_job(job("Director, Revenue Operations", "Direct experience owning incentive compensation design for AE and SDR organizations"))
    assert any(x.kind == "comp_duty" for x in a) and any(x.kind == "comp_duty" for x in b)
