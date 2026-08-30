export const defaultQuantityInputs = Object.freeze({
  poolCount: 2,
  poolLengthM: 8.18,
  poolWidthM: 4.24,
  poolFinishedDepthM: 0.85,
  copingWidthM: 0.25,
  bathZoneLengthM: 8.68,
  bathZoneWidthM: 6.58,
  supportZoneLengthM: 5.038,
  supportZoneWidthM: 6.58,
  roomCount: 2,
  wallHeightM: 3.2,
  entryCount: 2,
  entryWidthM: 1.48,
  entryHeightM: 2.1,
  poolStepAllowanceM2: 18,
  featureWallTileM2: 16,
  ceilingGrossWidthM: 14.718,
  ceilingGrossLengthM: 13.3,
  woodgrainCeilingRatio: 0.15,
  accessHatchesEach: 6,
  downlightsEach: 32,
  linearLightM: 40,
  wallWashersEach: 4,
  lightingDriversEach: 6,
});

const round4 = (value) =>
  Math.round((value + Number.EPSILON) * 10000) / 10000;

export function calculateQuantities(inputs = defaultQuantityInputs) {
  const poolBottomM2 = inputs.poolCount * inputs.poolLengthM * inputs.poolWidthM;
  const poolWallM2 =
    inputs.poolCount *
    2 *
    (inputs.poolLengthM + inputs.poolWidthM) *
    inputs.poolFinishedDepthM;
  const poolCopingM2 =
    inputs.poolCount *
    ((inputs.poolLengthM + 2 * inputs.copingWidthM) *
      (inputs.poolWidthM + 2 * inputs.copingWidthM) -
      inputs.poolLengthM * inputs.poolWidthM);
  const bathZoneM2 =
    inputs.poolCount * inputs.bathZoneLengthM * inputs.bathZoneWidthM;
  const bathDeckFloorM2 = bathZoneM2 - poolBottomM2 - poolCopingM2;
  const supportFloorM2 =
    inputs.roomCount * inputs.supportZoneLengthM * inputs.supportZoneWidthM;
  const roomLengthM = inputs.supportZoneLengthM + inputs.bathZoneLengthM;
  const tiledPerimeterM =
    inputs.roomCount * 2 * (roomLengthM + inputs.bathZoneWidthM);
  const entryDeductionM2 =
    inputs.entryCount * inputs.entryWidthM * inputs.entryHeightM;
  const wallTileGrossM2 = tiledPerimeterM * inputs.wallHeightM - entryDeductionM2;
  const generalWallTileM2 = wallTileGrossM2 - inputs.featureWallTileM2;
  const ceilingGrossM2 = inputs.ceilingGrossWidthM * inputs.ceilingGrossLengthM;

  return Object.freeze({
    poolBottomM2: round4(poolBottomM2),
    poolWallM2: round4(poolWallM2),
    poolCopingM2: round4(poolCopingM2),
    bathDeckFloorM2: round4(bathDeckFloorM2),
    supportFloorM2: round4(supportFloorM2),
    wallTileGrossM2: round4(wallTileGrossM2),
    generalWallTileM2: round4(generalWallTileM2),
    featureWallTileM2: inputs.featureWallTileM2,
    ceilingGrossM2: round4(ceilingGrossM2),
    woodgrainUpgradeM2: round4(
      ceilingGrossM2 * inputs.woodgrainCeilingRatio,
    ),
    poolStepAllowanceM2: inputs.poolStepAllowanceM2,
    accessHatchesEach: inputs.accessHatchesEach,
    lighting: Object.freeze({
      downlightsEach: inputs.downlightsEach,
      linearLightM: inputs.linearLightM,
      wallWashersEach: inputs.wallWashersEach,
      lightingDriversEach: inputs.lightingDriversEach,
    }),
  });
}
