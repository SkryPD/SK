export function fitDistanceForBounds(size, verticalFovDegrees, aspect, padding = 1.12) {
  const dimensions = [size.x, size.y, size.z];
  if (!dimensions.every((value) => Number.isFinite(value) && value > 0)) {
    throw new Error("Bounding dimensions must be positive finite values");
  }
  if (!Number.isFinite(verticalFovDegrees) || verticalFovDegrees <= 0 || verticalFovDegrees >= 179) {
    throw new Error("Vertical field of view must be between 0 and 179 degrees");
  }
  if (!Number.isFinite(aspect) || aspect <= 0) {
    throw new Error("Viewport aspect ratio must be positive");
  }
  if (!Number.isFinite(padding) || padding < 1) {
    throw new Error("Camera padding must be a finite value of at least 1");
  }

  const radius = Math.hypot(...dimensions) / 2;
  const verticalHalfFov = verticalFovDegrees * Math.PI / 360;
  const horizontalHalfFov = Math.atan(Math.tan(verticalHalfFov) * aspect);
  const limitingHalfFov = Math.min(verticalHalfFov, horizontalHalfFov);
  return radius / Math.sin(limitingHalfFov) * padding;
}
