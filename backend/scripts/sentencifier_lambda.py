import json

LABEL_KO = {
    'acne': '여드름', 'blackhead': '블랙헤드', 'whitehead': '화이트헤드',
    'papule': '구진', 'pustule': '농포', 'nodule': '결절',
    'cyst': '낭종', 'pigmentation': '색소침착', 'scar': '흉터',
    'normal': '정상', 'abnormal': '피부 이상',
}

RISK_KO = {'mild': '경미', 'moderate': '보통', 'suspicious': '의심', 'danger': '위험'}


def _try_parse_json(text: str):
    """에이전트 출력 텍스트에서 JSON 파싱 시도"""
    if not isinstance(text, str):
        return text if isinstance(text, dict) else {}
    text = text.strip()
    # 마크다운 코드블록 제거
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(l for l in lines if not l.startswith("```"))
    try:
        return json.loads(text)
    except Exception:
        return {}


def _handle_structured(body: dict) -> list[str]:
    """
    직접 Lambda 호출 경로 (백엔드 → API Gateway → Lambda)
    agent_a_result / agent_b_result / agent_c_result 형식
    """
    a = body.get('agent_a_result', {})
    b = body.get('agent_b_result', {})
    c = body.get('agent_c_result', {})

    report_lines = []

    # Agent A: 병변/피부 분석
    ko_lesion = a.get('추정병변')
    ko_prob   = a.get('확률')
    ko_desc   = a.get('병변설명', '')
    ko_treat  = a.get('권장처치', '')

    if not ko_lesion:
        conditions = a.get('conditions', [])
        if conditions:
            top = conditions[0]
            label = top.get('label', 'abnormal')
            score = top.get('score', 0)
            ko_lesion = LABEL_KO.get(label, label)
            ko_prob   = int(score * 100)

    if ko_lesion and ko_prob is not None:
        report_lines.append(f"분석 결과 {ko_lesion}일 가능성이 {ko_prob}%입니다.")
    if ko_desc:
        report_lines.append(ko_desc)
    if ko_treat:
        report_lines.append(ko_treat)

    risk = a.get('risk_level', '')
    if risk and risk != 'normal':
        report_lines.append(f"위험도: {RISK_KO.get(risk, risk)}")

    # Agent B: 과거 기록 분석
    if b.get('has_past_data') and b.get('progress_analysis'):
        report_lines.append(f"\n{b['progress_analysis']}")
        suspected = b.get('suspected_product', {})
        if suspected.get('added_date') and suspected.get('product_name'):
            report_lines.append(
                f"{suspected['added_date']} 전후 추가된 {suspected['product_name']}의 "
                f"{suspected.get('ingredient', '성분')}이 자극을 주었을 가능성이 있습니다."
            )
    elif b.get('past_records'):
        report_lines.append(f"\n과거 {len(b['past_records'])}건의 분석 기록이 있습니다.")

    # Agent C: 화장품 궁합
    if c.get('is_incompatible_found'):
        issue = c.get('current_issue_product', {})
        alt   = c.get('alternative_recommendation', {})
        if issue.get('product_name') and issue.get('ingredient'):
            reason = issue.get('reason', '피부와 맞지 않을 수 있음')
            sentence = f"\n현재 사용 중인 {issue['product_name']}의 {issue['ingredient']} 성분이 {reason}"
            rec_name = alt.get('recommend_product_name')
            rec_ing  = alt.get('recommend_ingredient')
            if rec_name and rec_ing:
                sentence += f" {rec_ing} 성분이 들어간 {rec_name}으로 교체를 고려해보세요."
            report_lines.append(sentence)
    elif c.get('skin_type'):
        report_lines.append(f"\n{c['skin_type']} 피부 타입에 맞는 제품 사용을 권장합니다.")

    symptom = c.get('symptom_description', '')
    if symptom:
        report_lines.append(f"입력하신 증상({symptom})을 참고하여 전문의 상담을 권장합니다.")

    return report_lines


def _handle_agent_results(body: dict) -> list[str]:
    """
    Step Functions 경로 (에이전트 출력 텍스트)
    results_a / results_b / results_c 형식
    에이전트가 JSON을 반환하면 파싱 후 구조화 처리, 아니면 텍스트 그대로 사용
    """
    raw_a = body.get('results_a', '')
    raw_b = body.get('results_b', '')
    raw_c = body.get('results_c', '')

    a = _try_parse_json(raw_a)
    b = _try_parse_json(raw_b)
    c = _try_parse_json(raw_c)

    report_lines = []

    # Agent A JSON 파싱 성공
    if a:
        ko_lesion = a.get('추정병변')
        ko_prob   = a.get('확률')
        if not ko_lesion:
            conditions = a.get('conditions', [])
            if conditions:
                top = conditions[0]
                ko_lesion = LABEL_KO.get(top.get('label', ''), top.get('label', ''))
                ko_prob   = int(top.get('score', 0) * 100)
        if ko_lesion and ko_prob is not None:
            report_lines.append(f"분석 결과 {ko_lesion}일 가능성이 {ko_prob}%입니다.")
        if a.get('병변설명'):
            report_lines.append(a['병변설명'])
        if a.get('권장처치'):
            report_lines.append(a['권장처치'])
        risk = a.get('risk_level', '')
        if risk and risk != 'normal':
            report_lines.append(f"위험도: {RISK_KO.get(risk, risk)}")
    elif raw_a:
        # 텍스트 그대로 포함
        report_lines.append(raw_a.strip())

    # Agent B JSON 파싱 성공
    if b:
        if b.get('has_past_data') and b.get('progress_analysis'):
            report_lines.append(f"\n{b['progress_analysis']}")
            suspected = b.get('suspected_product', {})
            if suspected and suspected.get('product_name'):
                report_lines.append(
                    f"{suspected.get('added_date', '')} 전후 추가된 {suspected['product_name']}의 "
                    f"{suspected.get('ingredient', '성분')}이 자극을 주었을 가능성이 있습니다."
                )
    elif raw_b:
        report_lines.append(f"\n{raw_b.strip()}")

    # Agent C JSON 파싱 성공
    if c:
        if c.get('is_incompatible_found'):
            issue = c.get('current_issue_product', {})
            alt   = c.get('alternative_recommendation', {})
            if issue.get('product_name'):
                sentence = f"\n현재 사용 중인 {issue['product_name']}의 {issue.get('ingredient', '성분')} 성분이 {issue.get('reason', '피부와 맞지 않을 수 있음')}"
                if alt.get('recommend_product_name'):
                    sentence += f" {alt.get('recommend_ingredient', '')} 성분이 들어간 {alt['recommend_product_name']}으로 교체를 고려해보세요."
                report_lines.append(sentence)
        elif c.get('skin_type'):
            report_lines.append(f"\n{c['skin_type']} 피부 타입에 맞는 제품 사용을 권장합니다.")
    elif raw_c:
        report_lines.append(f"\n{raw_c.strip()}")

    return report_lines


def lambda_handler(event, context):
    body = event
    if isinstance(event.get('body'), str):
        body = json.loads(event['body'])
    elif isinstance(event.get('body'), dict):
        body = event['body']

    # Step Functions 경로 vs 직접 호출 경로 구분
    if 'results_a' in body or 'results_b' in body or 'results_c' in body:
        report_lines = _handle_agent_results(body)
    else:
        report_lines = _handle_structured(body)

    report_lines.append(
        "\n본 결과는 AI 보조 분석이며 의학적 진단이 아닙니다. "
        "증상이 지속되거나 심해지면 전문의와 상담하세요."
    )

    return {
        "final_report": "\n".join(report_lines),
        "uuid": body.get('uuid'),
    }
