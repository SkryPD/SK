export function setLayerVisibility(layer, visible) {
  layer.visible = visible;
  for (const child of layer.children ?? []) {
    setLayerVisibility(child, visible);
  }
}
