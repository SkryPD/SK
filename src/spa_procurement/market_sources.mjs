const allowedTiers = new Set(["mid", "economy"]);

export const requiredCategoryUnits = Object.freeze({
  pool_floor_tile: "m²",
  pool_wall_tile: "m²",
  pool_coping_tile: "m²",
  deck_floor_tile: "m²",
  wall_tile: "m²",
  feature_tile: "m²",
  ceiling_system: "m²",
  woodgrain_upgrade: "m²",
  linear_light_channel: "m",
  ceiling_access_hatch: "套",
  moisture_downlight: "套",
  ip67_linear_light: "m",
  wall_washer: "套",
  lighting_driver: "套",
  tile_installation: "m²",
  ceiling_installation: "m²",
  point_light_installation: "套",
  linear_light_installation: "m",
});

export function validateMarketSources(records, categoryUnits, asOfDate) {
  const errors = [];
  const cutoff = new Date(`${asOfDate}T00:00:00+08:00`);
  const categoryTiers = new Map(
    Object.keys(categoryUnits).map((name) => [name, new Set()]),
  );
  const seenKeys = new Set();

  records.forEach((record, index) => {
    const prefix = `record ${index + 1}`;
    for (const field of [
      "category",
      "tier",
      "brand",
      "productOrEquivalent",
      "unit",
      "priceLow",
      "priceHigh",
      "sourceUrl",
      "checkedOn",
      "priceBasis",
      "regionNote",
    ]) {
      if (record[field] === undefined || record[field] === "") {
        errors.push(`${prefix}: missing ${field}`);
      }
    }
    if (!allowedTiers.has(record.tier)) errors.push(`${prefix}: invalid tier`);
    if (!(record.priceLow > 0 && record.priceHigh >= record.priceLow)) {
      errors.push(`${prefix}: invalid price range`);
    }
    if (!/^https:\/\//.test(record.sourceUrl ?? "")) {
      errors.push(`${prefix}: sourceUrl must use https`);
    }
    const checked = new Date(`${record.checkedOn}T00:00:00+08:00`);
    const ageDays = Math.floor((cutoff - checked) / 86400000);
    if (!Number.isFinite(ageDays) || ageDays < 0 || ageDays > 120) {
      errors.push(`${prefix}: checkedOn outside 120-day window`);
    }
    if (!(record.category in categoryUnits)) {
      errors.push(`${prefix}: unknown category`);
    } else if (record.unit !== categoryUnits[record.category]) {
      errors.push(`${prefix}: unit mismatch`);
    }
    const key = `${record.category}|${record.tier}`;
    if (seenKeys.has(key)) errors.push(`${prefix}: duplicate category-tier key`);
    seenKeys.add(key);
    categoryTiers.get(record.category)?.add(record.tier);
  });

  for (const [category, tiers] of categoryTiers) {
    for (const tier of allowedTiers) {
      if (!tiers.has(tier)) errors.push(`${category}: missing ${tier} option`);
    }
  }
  return { records, errors };
}
