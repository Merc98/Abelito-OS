from __future__ import annotations

from abel_os.schemas import DecisionOutcome, MobileDecision, MobileMode, MobileOffer


class MobileDecisionEngine:
    def __init__(
        self,
        *,
        min_pay_per_mile: float = 1.75,
        max_pickup_eta_minutes: int = 12,
        blocked_zones: set[str] | None = None,
    ) -> None:
        self.min_pay_per_mile = min_pay_per_mile
        self.max_pickup_eta_minutes = max_pickup_eta_minutes
        self.blocked_zones = {zone.lower() for zone in (blocked_zones or set())}

    def evaluate(self, offer: MobileOffer, mode: MobileMode = MobileMode.RECOMMEND_ONLY) -> MobileDecision:
        reasons: list[str] = []

        if not offer.accept_button_visible:
            return MobileDecision(
                decision=DecisionOutcome.HUMAN,
                recommended_action="ESCALATE",
                execution_allowed=False,
                confidence=0.2,
                reasons=["No se detectó el botón de aceptación."],
                mode_applied=mode,
            )

        if offer.fare is None:
            return MobileDecision(
                decision=DecisionOutcome.HUMAN,
                recommended_action="ESCALATE",
                execution_allowed=False,
                confidence=0.3,
                reasons=["La tarifa no está disponible."],
                mode_applied=mode,
            )

        total_miles = (offer.pickup_miles or 0.0) + (offer.trip_miles or 0.0)
        pay_per_mile = round(offer.fare / max(total_miles, 0.1), 2)

        score = 0
        if pay_per_mile >= self.min_pay_per_mile:
            score += 2
            reasons.append(f"Pay per mile aceptable: {pay_per_mile}.")
        else:
            score -= 2
            reasons.append(f"Pay per mile bajo: {pay_per_mile}.")

        if offer.pickup_eta_minutes is not None:
            if offer.pickup_eta_minutes <= self.max_pickup_eta_minutes:
                score += 1
                reasons.append("ETA de recogida dentro de umbral.")
            else:
                score -= 1
                reasons.append("ETA de recogida demasiado alto.")

        zone = (offer.destination_zone or "").strip().lower()
        if zone and zone in self.blocked_zones:
            score -= 3
            reasons.append("Destino en zona bloqueada.")

        if offer.surge_multiplier and offer.surge_multiplier >= 1.5:
            score += 1
            reasons.append("Multiplicador de tarifa favorable.")

        confidence = min(0.95, max(0.45, offer.source_confidence + (0.1 if total_miles > 0 else -0.05)))

        recommended_action = "ACCEPT" if score >= 1 else "REJECT"
        raw_decision = DecisionOutcome.ACCEPT if score >= 1 else DecisionOutcome.REJECT

        if confidence < 0.65:
            return MobileDecision(
                decision=DecisionOutcome.HUMAN,
                recommended_action="ESCALATE",
                execution_allowed=False,
                confidence=confidence,
                pay_per_mile=pay_per_mile,
                reasons=reasons + ["Confianza insuficiente para actuar."],
                mode_applied=mode,
            )

        if mode == MobileMode.RECOMMEND_ONLY:
            return MobileDecision(
                decision=DecisionOutcome.RECOMMEND_ONLY,
                recommended_action=recommended_action,
                execution_allowed=False,
                confidence=confidence,
                pay_per_mile=pay_per_mile,
                reasons=reasons,
                mode_applied=mode,
            )

        if mode == MobileMode.SEMI_AUTO and raw_decision == DecisionOutcome.ACCEPT:
            return MobileDecision(
                decision=DecisionOutcome.RECOMMEND_ONLY,
                recommended_action="ACCEPT",
                execution_allowed=False,
                confidence=confidence,
                pay_per_mile=pay_per_mile,
                reasons=reasons + ["Modo semi-auto: requiere confirmación antes de aceptar."],
                mode_applied=mode,
            )

        return MobileDecision(
            decision=raw_decision,
            recommended_action=recommended_action,
            execution_allowed=True,
            confidence=confidence,
            pay_per_mile=pay_per_mile,
            reasons=reasons,
            mode_applied=mode,
        )
