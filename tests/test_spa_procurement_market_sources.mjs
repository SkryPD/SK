import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import {
  requiredCategoryUnits,
  validateMarketSources,
} from "../src/spa_procurement/market_sources.mjs";

const requiredCategories = Object.keys(requiredCategoryUnits);

test("market source validator rejects missing evidence and tier coverage", () => {
  const invalid = [{
    category: "pool_floor_tile",
    tier: "mid",
    brand: "示例品牌",
    productOrEquivalent: "示例产品",
    unit: "m²",
    priceLow: 100,
    priceHigh: 80,
    sourceUrl: "http://invalid.example",
    checkedOn: "2025-01-01",
    priceBasis: "示例",
    regionNote: "示例",
  }];
  const result = validateMarketSources(
    invalid,
    requiredCategoryUnits,
    "2026-08-30",
  );
  assert.ok(result.errors.some((error) => error.includes("invalid price range")));
  assert.ok(result.errors.some((error) => error.includes("sourceUrl must use https")));
  assert.ok(result.errors.some((error) => error.includes("missing economy option")));
});

test("market source validator accepts complete two-tier evidence", () => {
  const records = requiredCategories.flatMap((category) =>
    ["mid", "economy"].map((tier) => ({
      category,
      tier,
      brand: `${category}-${tier}`,
      productOrEquivalent: "合同测试产品",
      unit: requiredCategoryUnits[category],
      priceLow: 80,
      priceHigh: 120,
      sourceUrl: `https://example.com/${category}/${tier}`,
      checkedOn: "2026-08-30",
      priceBasis: "合同测试价格口径",
      regionNote: "合同测试区域说明",
    })),
  );
  const result = validateMarketSources(
    records,
    requiredCategoryUnits,
    "2026-08-30",
  );
  assert.deepEqual(result.errors, []);
});

test("market source validator permits an explicitly excluded zero-cost option", () => {
  const records = Object.keys(requiredCategoryUnits).flatMap((category) =>
    ["mid", "economy"].map((tier) => ({
      category,
      tier,
      brand: `${category}-${tier}`,
      productOrEquivalent: "合同测试产品",
      unit: requiredCategoryUnits[category],
      priceLow: category === "woodgrain_upgrade" && tier === "economy" ? 0 : 80,
      priceHigh: category === "woodgrain_upgrade" && tier === "economy" ? 0 : 120,
      included: !(category === "woodgrain_upgrade" && tier === "economy"),
      sourceUrl: `https://example.com/${category}/${tier}`,
      checkedOn: "2026-08-30",
      priceBasis: "合同测试价格口径",
      regionNote: "合同测试区域说明",
    })),
  );
  const result = validateMarketSources(
    records,
    requiredCategoryUnits,
    "2026-08-30",
  );
  assert.deepEqual(result.errors, []);
});

test("researched market data covers both tiers with traceable sources", async () => {
  const raw = await fs.readFile(
    new URL("../data/spa_procurement/market_sources.json", import.meta.url),
    "utf8",
  );
  const records = JSON.parse(raw);
  const result = validateMarketSources(
    records,
    requiredCategoryUnits,
    "2026-08-30",
  );
  assert.deepEqual(result.errors, []);
  assert.ok(result.records.length >= requiredCategories.length * 2);
});
