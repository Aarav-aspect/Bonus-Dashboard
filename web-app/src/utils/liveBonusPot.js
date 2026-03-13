export function calculateLiveBonusPot(data) {
    if (!data) return { liveBasePot: 0, liveBonusPot: 0 };

    // Base Pot = from Google Sheet (Excel); fall back to bonuspot.json value
    const liveBasePot = data.bonus?.gsheet_pot ?? data.bonus?.pot ?? 0;

    // Current Bonus = Base Pot with adjustment multiplier applied
    const liveBonusPot = liveBasePot * (1 + (data.bonus?.multiplier || 0));

    return { liveBasePot, liveBonusPot };
}
