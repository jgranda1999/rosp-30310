import antonioPorlier from './images/antonio-porlier.jpg';
import joseBaquijano from './images/José_Baquijano.jpg';
import pedroSanchez from './images/Pedro_Sanchez.jpg';

// Preload images
const preloadImage = (src: string) => {
  const img = new Image();
  img.src = src;
};

// Preload all images
[antonioPorlier, joseBaquijano, pedroSanchez].forEach(preloadImage);

export const magistrateImages = {
  'antonio-porlier': antonioPorlier,
  'jose-baquijano-y-carrillo': joseBaquijano,
  'pedro-de-tagle-y-bracho': pedroSanchez,
} as const;

export const getImageForMagistrate = (id: string): string => {
  const image = (magistrateImages as Record<string, string>)[id];
  if (!image) {
    console.warn(`No image found for magistrate: ${id}`);
  }
  return image;
}; 