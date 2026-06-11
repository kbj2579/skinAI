from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import CLASS_DISPLAY_KO, CLASS_GROUPS, Prediction
from .retriever import RetrievedChunk


CLASS_MEANINGS = {
    "Blackheads": "모공이 열려 있는 면포성 여드름 양상과 관련될 수 있습니다.",
    "Whiteheads": "모공이 닫힌 면포성 여드름 양상과 관련될 수 있습니다.",
    "Papules": "붉고 단단한 염증성 여드름 양상과 관련될 수 있습니다.",
    "Pustules": "고름이 보이는 염증성 여드름 양상과 관련될 수 있습니다.",
    "Cyst": "깊고 통증이 있거나 흉터 위험이 큰 염증성 병변 가능성을 보수적으로 고려해야 합니다.",
    "blackhead": "모공이 열려 있고 산화된 각질·피지가 보이는 면포성 여드름 양상과 관련될 수 있습니다.",
    "whitehead": "모공이 닫힌 작은 면포성 여드름 양상과 관련될 수 있습니다.",
    "papule": "붉고 단단한 염증성 여드름 병변 양상과 관련될 수 있습니다.",
    "pustule": "고름이 보이는 염증성 여드름 병변 양상과 관련될 수 있습니다.",
    "cystnnodule": "깊고 아프거나 단단한 결절·낭종성 여드름 병변 가능성을 보수적으로 고려해야 합니다.",
    "complexacne": "단일 여드름 병변으로 명확히 나누기 어렵거나 여러 양상이 섞인 상태로 볼 수 있습니다.",
    "milia": "작고 흰 돔 모양의 각질성 낭종인 비립종 양상과 감별이 필요할 수 있습니다.",
    "rosacea": "중앙 얼굴의 반복적 홍조, 붉음, 화끈거림, 염증성 구진·농포 양상과 관련될 수 있습니다.",
    "seborrheic": "피지 분비가 많은 부위의 번들거림이나 비늘·각질 경향과 관련될 수 있습니다.",
    "sebdermatitis": "피지선이 많은 부위의 붉음, 가려움, 기름진 인설을 보이는 지루성 피부염 양상과 관련될 수 있습니다.",
    "atopic": "가려움, 건조, 붉음, 피부 장벽 손상과 관련된 아토피 피부염 양상과 관련될 수 있습니다.",
    "psoriasis": "경계가 비교적 뚜렷하고 두꺼운 인설성 판을 보이는 건선 양상과 관련될 수 있습니다.",
    "normal": "현재 이미지 기준으로 뚜렷한 병변이 관찰되지 않는 정상 범주로 분류된 상태입니다.",
    "abnormal": "지원 클래스 중 하나로 확정하기 어려운 비정상 또는 미분류 상태입니다.",
}


GENERAL_CARE = {
    "comedonal_acne": [
        "순한 세안제를 사용하고 과도한 문지르기나 스크럽은 피합니다.",
        "모공을 막을 수 있는 무거운 유분 제품은 줄이고, 비면포성 또는 모공을 막지 않는다고 표시된 제품을 우선 고려합니다.",
        "여러 화장품이나 세안제를 한꺼번에 바꾸지 말고, 피부 변화를 단계적으로 관찰합니다.",
        "병변을 손으로 짜거나 긁어 제거하려고 하지 않습니다.",
    ],
    "inflammatory_acne": [
        "붉거나 고름이 보이는 부위를 반복적으로 만지거나 짜지 않습니다.",
        "세안과 보습은 자극을 줄이는 방향으로 유지하고, 강한 필링이나 스크럽은 피합니다.",
        "통증, 붓기, 고름 증가, 빠른 확산이 있으면 자가 관리보다 진료 판단을 우선합니다.",
        "새로운 제품은 한 번에 하나씩 도입해 악화 여부를 확인합니다.",
    ],
    "deep_inflammatory_acne": [
        "깊고 아픈 병변은 흉터 위험이 있어 피부과 상담을 우선 권고합니다.",
        "자가 압출, 강한 마사지, 반복적인 자극은 피합니다.",
        "같은 부위에 반복되면 사진과 증상 변화를 기록해 진료 때 설명할 수 있게 합니다.",
        "진료 전까지는 순한 세안, 비면포성 보습, 자외선 차단처럼 자극을 줄이는 관리에 집중합니다.",
    ],
    "complex_acne": [
        "복합 양상은 단일 병변 기준 관리보다 전체 악화 요인과 반복 패턴을 같이 보는 것이 중요합니다.",
        "면포, 붉은 병변, 고름, 깊은 통증이 섞이면 손으로 짜지 말고 사진 기록을 남깁니다.",
        "여러 병변이 동시에 악화되거나 흉터가 남는다면 피부과 상담을 우선합니다.",
        "제품을 한꺼번에 많이 바꾸는 방식은 원인 추적을 어렵게 하므로 단계적으로 조정합니다.",
    ],
    "milia": [
        "비립종처럼 보이는 작은 흰 병변은 손으로 짜거나 바늘로 제거하려고 하지 않습니다.",
        "눈 주변이나 얇은 피부 부위에 있으면 자가 제거를 피하고 전문 진료를 우선합니다.",
        "두껍고 자극적인 제형을 줄이고, 순한 세안과 가벼운 보습을 유지합니다.",
        "갑자기 많아지거나 붉음·통증·출혈이 동반되면 다른 병변과 감별이 필요합니다.",
    ],
    "rosacea": [
        "홍조와 화끈거림이 반복되면 뜨거운 환경, 음주, 매운 음식, 강한 자외선 등 개인 유발 요인을 기록합니다.",
        "향료가 적은 순한 세안제와 보습제를 사용하고, 자외선 차단을 꾸준히 유지합니다.",
        "스크럽, 강한 필링, 고농도 활성 성분처럼 따가움을 유발할 수 있는 관리는 피합니다.",
        "눈 충혈, 이물감, 지속적 화끈거림, 반복 악화가 있으면 진료 상담을 권고합니다.",
    ],
    "seborrheic_condition": [
        "피지와 각질이 많은 부위는 과도하게 문지르기보다 순한 세안으로 자극을 줄입니다.",
        "기름진 인설, 붉음, 가려움이 반복되면 지루성 피부염 등과 감별이 필요할 수 있습니다.",
        "두피, 눈썹, 코 주변, 귀 주변처럼 반복되는 위치를 기록합니다.",
        "넓게 번지거나 오래 지속되면 자가 관리만으로 판단하지 말고 진료를 권고합니다.",
    ],
    "seborrheic_dermatitis": [
        "기름진 인설과 붉음이 있는 부위는 긁거나 떼어내기보다 자극을 줄이는 관리가 우선입니다.",
        "두피, 눈썹, 콧방울 주변, 귀 주변 등 반복 부위를 기록합니다.",
        "재발이 잦은 만성 경향이 있어 악화 요인을 기록하고 증상이 심하면 진료 상담을 받습니다.",
        "눈 주변 염증, 진물, 심한 가려움, 넓은 확산이 있으면 빠른 진료가 필요합니다.",
    ],
    "atopic_dermatitis": [
        "피부 건조와 가려움이 중심이면 보습을 규칙적으로 하고, 긁는 자극을 줄입니다.",
        "향료, 강한 세정제, 뜨거운 물, 거친 섬유처럼 자극이 되는 요인을 줄입니다.",
        "진물, 딱지, 통증, 급격한 악화가 있으면 감염이나 악화 가능성을 고려해 진료를 권고합니다.",
        "반복되는 부위와 유발 상황을 기록하면 관리 방향을 정하는 데 도움이 됩니다.",
    ],
    "psoriasis": [
        "두꺼운 인설성 병변은 억지로 떼어내거나 긁지 않습니다.",
        "피부 손상, 스트레스, 감염 등 악화 요인을 기록하고 보습으로 건조와 균열을 줄입니다.",
        "넓은 범위, 손발톱 변화, 관절 통증이나 뻣뻣함이 있으면 진료 상담을 권고합니다.",
        "건선은 만성·재발성 경향이 있어 단기 자가 관리보다 정확한 진단과 장기 관리 계획이 중요합니다.",
    ],
    "normal_skin": [
        "뚜렷한 병변이 없더라도 새로 생긴 변화는 사진과 날짜를 함께 기록합니다.",
        "순한 세안, 보습, 자외선 차단처럼 기본적인 피부 장벽 관리 중심으로 유지합니다.",
        "갑자기 커지거나 색·모양이 바뀌는 병변, 통증, 출혈이 생기면 정상 분류와 관계없이 진료가 필요합니다.",
    ],
    "abnormal_uncertain": [
        "지원 클래스 중 하나로 단정하기 어려우므로 구체 진단명보다 진료 필요성 판단을 우선합니다.",
        "색, 크기, 모양, 통증, 출혈, 빠른 변화 여부를 기록합니다.",
        "빠르게 커지거나 피가 나거나 통증이 심한 경우, 또는 비대칭·색 변화가 뚜렷하면 의료진 평가를 권고합니다.",
    ],
}


INGREDIENT_GUIDANCE = {
    "comedonal_acne": [
        "면포성 병변에서는 살리실산(BHA)이나 레티노이드 계열 성분이 근거 문헌에서 자주 언급되지만, 피부 자극 여부를 먼저 확인해야 합니다.",
        "비면포성 보습제와 자외선차단제처럼 모공을 막지 않는다고 표시된 기본 제품을 우선 고려합니다.",
        "여러 활성 성분을 동시에 시작하지 말고, 임신 중이거나 피부질환 치료 중이면 성분 선택 전에 진료 상담을 권합니다.",
    ],
    "inflammatory_acne": [
        "염증성 병변에서는 벤조일퍼옥사이드, 아젤라익산, 아다팔렌 계열 성분이 문헌에서 자주 언급됩니다.",
        "고름, 통증, 붓기가 있으면 성분을 늘리기보다 자극 최소화와 진료 기준 확인을 우선합니다.",
        "활성 성분을 겹치면 건조와 따가움이 심해질 수 있어 단계적으로 관찰합니다.",
    ],
    "deep_inflammatory_acne": [
        "깊고 아픈 결절·낭종성 병변은 일반 화장품 성분만으로 해결하려고 안내하지 않습니다.",
        "자가 압출, 고농도 활성 성분의 반복 사용은 흉터와 자극 위험을 높일 수 있습니다.",
        "진료 전까지는 순한 세안제, 비면포성 보습제, 자외선차단제처럼 자극을 줄이는 성분 선택을 중심으로 안내합니다.",
    ],
    "complex_acne": [
        "복합 양상에서는 하나의 성분을 정답처럼 제시하지 않고, 면포성·염증성·깊은 병변 중 어떤 양상이 우세한지 확인합니다.",
        "기본 관리는 순한 세안제, 비면포성 보습제, 자외선차단제 중심으로 단순화합니다.",
        "활성 성분을 여러 개 동시에 쓰면 악화 원인을 알기 어려우므로 단계적으로 도입합니다.",
    ],
    "milia": [
        "비립종 의심 병변에는 강한 압출이나 바늘 제거를 권하지 않습니다.",
        "두껍고 밀폐감이 큰 제형이 부담된다면 가벼운 보습제와 순한 세안제로 단순화합니다.",
        "눈 주변 병변, 반복·다발 병변, 염증 동반 병변은 성분 추천보다 전문 진료가 우선입니다.",
    ],
    "rosacea": [
        "주사 의심 양상에는 향료가 적고 자극이 낮은 보습제와 자외선차단제가 기본입니다.",
        "알코올감이 강한 제품, 스크럽, 강한 산 성분은 화끈거림을 악화시킬 수 있어 주의합니다.",
        "항염 성분이나 처방 성분은 병변 유형과 눈 증상 여부에 따라 달라지므로 진료 상담 없이 단정하지 않습니다.",
    ],
    "seborrheic_condition": [
        "지루 경향은 과도한 세정보다 피부 장벽을 해치지 않는 세안과 보습 균형이 중요합니다.",
        "기름진 인설과 붉음이 반복되면 일반 화장품보다 지루성 피부염 감별과 진료 상담이 우선일 수 있습니다.",
        "향료와 강한 각질 제거제는 가려움과 붉음을 악화시킬 수 있어 주의합니다.",
    ],
    "seborrheic_dermatitis": [
        "지루성 피부염 의심 양상에서는 자극이 적은 세정과 보습을 기본으로 안내합니다.",
        "항진균·항염 치료 성분은 부위와 중증도에 따라 달라질 수 있어 약물명·용량 지시는 하지 않습니다.",
        "눈 주변, 두피 전반, 넓은 얼굴 부위의 반복 악화는 진료 상담을 권합니다.",
    ],
    "atopic_dermatitis": [
        "아토피 피부염 의심 양상에서는 세라마이드 등 장벽 보조 보습 성분을 포함한 순한 보습제를 우선 고려합니다.",
        "향료, 에센셜오일, 강한 산 성분, 고농도 레티노이드처럼 따가움을 유발할 수 있는 성분은 주의합니다.",
        "진물, 딱지, 감염 의심 소견이 있으면 성분 추천보다 진료가 우선입니다.",
    ],
    "psoriasis": [
        "건선 의심 병변에는 건조와 균열을 줄이는 보습 관리가 기본입니다.",
        "두꺼운 인설을 강제로 제거하거나 강한 필링 성분을 반복 사용하는 것은 피합니다.",
        "치료 성분 선택은 병변 범위, 위치, 관절 증상 여부에 따라 달라지므로 진료 기반으로 결정해야 합니다.",
    ],
    "normal_skin": [
        "정상 분류에서는 새로운 활성 성분을 추가하기보다 순한 세안제, 보습제, 자외선차단제 중심의 기본 루틴을 유지합니다.",
        "불필요한 고농도 활성 성분을 늘리면 자극성 피부염이 생길 수 있어 주의합니다.",
    ],
    "abnormal_uncertain": [
        "미분류 병변에는 특정 성분을 추천하기보다 자극을 줄이고 변화 기록을 남깁니다.",
        "출혈, 빠른 변화, 통증, 색 변화가 있으면 성분 사용보다 의료진 평가가 우선입니다.",
    ],
}


VISIT_CRITERIA = [
    "통증이 심하거나 병변이 빠르게 커지는 경우",
    "발열, 심한 붓기, 넓게 퍼지는 고름 등 감염이 의심되는 경우",
    "흉터가 생기고 있거나 색소침착이 심해지는 경우",
    "깊고 반복되는 결절·낭종성 병변이 의심되는 경우",
    "눈 주변 증상, 출혈, 급격한 색·크기·모양 변화가 있는 경우",
    "자가 관리 중 악화되거나 일상생활에 영향을 주는 경우",
]


@dataclass(frozen=True)
class SolutionResult:
    prediction: dict[str, Any]
    retrieved_evidence: list[dict[str, str]]
    sections: dict[str, Any]
    markdown: str
    llm_prompt: str


def build_solution(
    prediction: Prediction,
    retrieved: list[RetrievedChunk],
    user_symptoms: str = "",
) -> SolutionResult:
    if not retrieved:
        raise ValueError("cannot generate a solution without retrieved evidence")

    class_group = CLASS_GROUPS[prediction.pred_label]
    label_ko = prediction.pred_label_ko or CLASS_DISPLAY_KO[prediction.pred_label]
    confidence_pct = (
        f"{prediction.confidence * 100:.1f}%" if prediction.confidence is not None else None
    )
    meaning = CLASS_MEANINGS[prediction.pred_label]
    care = GENERAL_CARE[class_group]

    citations = [item.chunk.citation() for item in retrieved]
    sections = {
        "모델 분류 결과": {
            "pred_label": prediction.pred_label,
            "pred_label_ko": label_ko,
            "confidence": prediction.confidence,
            "model_version": prediction.model_version,
            "image_id": prediction.image_id,
        },
        "가능한 의미": meaning,
        "일반 관리 방법": care,
        "성분 선택 참고": INGREDIENT_GUIDANCE[class_group],
        "피부과 방문이 필요한 경우": VISIT_CRITERIA,
        "근거 출처": citations,
        "주의": "이 결과는 의료 진단이나 처방이 아닙니다. 이미지 분류와 근거 문서를 바탕으로 한 참고 안내이며, 증상이 심하거나 변화가 빠르면 의료진 상담이 필요합니다.",
    }
    markdown = render_markdown(sections, user_symptoms=user_symptoms, confidence_pct=confidence_pct)
    llm_prompt = build_llm_prompt(prediction, retrieved, user_symptoms=user_symptoms)
    return SolutionResult(
        prediction=prediction.to_standard_dict(),
        retrieved_evidence=citations,
        sections=sections,
        markdown=markdown,
        llm_prompt=llm_prompt,
    )


def render_markdown(sections: dict[str, Any], user_symptoms: str, confidence_pct: str | None) -> str:
    result = sections["모델 분류 결과"]
    lines = [
        "## 모델 분류 결과",
        f"- 예측 클래스: {result['pred_label_ko']} (`{result['pred_label']}`)",
        f"- 모델 버전: {result['model_version']}",
        f"- 이미지 ID: {result['image_id']}",
    ]
    if confidence_pct is not None:
        lines.insert(2, f"- 신뢰도(참고): {confidence_pct}")
    if user_symptoms:
        lines.append(f"- 사용자 입력 증상: {user_symptoms}")

    lines.extend(["", "## 가능한 의미", str(sections["가능한 의미"])])
    lines.extend(["", "## 일반 관리 방법"])
    lines.extend(f"- {item}" for item in sections["일반 관리 방법"])
    lines.extend(["", "## 성분 선택 참고"])
    lines.extend(f"- {item}" for item in sections["성분 선택 참고"])
    lines.extend(["", "## 피부과 방문이 필요한 경우"])
    lines.extend(f"- {item}" for item in sections["피부과 방문이 필요한 경우"])
    lines.extend(["", "## 근거 출처"])
    for citation in sections["근거 출처"]:
        lines.append(
            f"- {citation['title']} ({citation['source']}), {citation['url']} "
            f"[{citation['license']}; {citation['allowed_use']}]"
        )
    lines.extend(["", "## 주의", str(sections["주의"])])
    return "\n".join(lines)


def build_llm_prompt(
    prediction: Prediction,
    retrieved: list[RetrievedChunk],
    user_symptoms: str = "",
) -> str:
    evidence_blocks = []
    for item in retrieved:
        chunk = item.chunk
        evidence_blocks.append(
            "\n".join(
                [
                    f"[{chunk.id}] {chunk.title}",
                    f"source={chunk.source}",
                    f"url={chunk.url}",
                    f"license={chunk.license}",
                    f"allowed_use={chunk.allowed_use}",
                    f"text={chunk.chunk_text}",
                ]
            )
        )
    return "\n\n".join(
        [
            "역할: 피부 병변 이미지 분류 결과와 사용자 증상 설명을 바탕으로 근거 기반 한국어 안내를 작성한다.",
            "전제: confidence로 분기하지 않고 pred_label 병변 클래스와 사용자 증상만 사용한다.",
            "금지: 진단 확정, 처방, 용량 안내, 약물 변경 지시, 출처 없는 주장, 응급 증상 축소.",
            "필수: 불확실성 표시, 병원 방문 기준, 근거 출처 링크, 의료 고지.",
            "출력 형식: Markdown으로 작성하고, 섹션 제목은 '모델 분류 결과', '가능한 의미', '일반 관리 방법', '성분 선택 참고', '피부과 방문이 필요한 경우', '근거 출처', '주의'를 사용한다.",
            "성분 안내는 후보 성분과 주의점만 설명하고, 처방·용량·사용 횟수·특정 제품명은 제시하지 않는다.",
            "근거 출처: 제공된 evidence의 title과 url만 사용한다. 새로운 출처를 만들지 않는다.",
            "분량 제한: 각 섹션은 1~3개 bullet 또는 2문장 이내로 간결하게 작성한다.",
            "문자 제한: 이모지, 경고 아이콘, 장식 특수문자, 하이프 남발을 사용하지 않는다.",
            f"prediction={prediction.to_standard_dict()}",
            f"user_symptoms={user_symptoms or 'none'}",
            "evidence:\n" + "\n\n".join(evidence_blocks),
        ]
    )
