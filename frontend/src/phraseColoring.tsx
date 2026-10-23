import React from "react";
import { AspectItem, ColorClasses } from "./types";

// Type definition for color entries
interface ColorEntry {
  bg300: string;
  bg200: string;
  aspectBg: string;
  opinionBg: string;
  aspectRgb: [number, number, number];
  opinionRgb: [number, number, number];
  name: string;
}

// Type definition for text highlights
interface TextHighlight {
  start: number;
  end: number;
  type: "aspect" | "opinion";
  colorClasses: ColorEntry;
  index: number;
  text?: string;
  annotationIndex?: number;
}

// Predefined colors with RGB values for mathematical mixing
export const tailwindColorClasses: ColorEntry[] = [
  {
    bg300: "bg-purple-400",
    bg200: "bg-purple-200",
    aspectBg: "bg-purple-400/70",
    opinionBg: "bg-purple-200/50",
    aspectRgb: [196, 141, 255],
    opinionRgb: [233, 213, 255],
    name: "purple",
  },
  {
    bg300: "bg-emerald-400",
    bg200: "bg-emerald-200",
    aspectBg: "bg-emerald-400/70",
    opinionBg: "bg-emerald-200/50",
    aspectRgb: [52, 211, 153],
    opinionRgb: [167, 243, 208],
    name: "emerald",
  },
  {
    bg300: "bg-orange-400",
    bg200: "bg-orange-200",
    aspectBg: "bg-orange-400/70",
    opinionBg: "bg-orange-200/50",
    aspectRgb: [251, 146, 60],
    opinionRgb: [254, 215, 170],
    name: "orange",
  },
  {
    bg300: "bg-pink-400",
    bg200: "bg-pink-200",
    aspectBg: "bg-pink-400/70",
    opinionBg: "bg-pink-200/50",
    aspectRgb: [244, 114, 182],
    opinionRgb: [251, 207, 232],
    name: "pink",
  },
  {
    bg300: "bg-cyan-400",
    bg200: "bg-cyan-200",
    aspectBg: "bg-cyan-400/70",
    opinionBg: "bg-cyan-200/50",
    aspectRgb: [34, 211, 238],
    opinionRgb: [165, 243, 252],
    name: "cyan",
  },
  {
    bg300: "bg-amber-400",
    bg200: "bg-amber-200",
    aspectBg: "bg-amber-400/70",
    opinionBg: "bg-amber-200/50",
    aspectRgb: [251, 191, 36],
    opinionRgb: [253, 230, 138],
    name: "amber",
  },
  {
    bg300: "bg-teal-400",
    bg200: "bg-teal-200",
    aspectBg: "bg-teal-400/70",
    opinionBg: "bg-teal-200/50",
    aspectRgb: [45, 212, 191],
    opinionRgb: [153, 246, 228],
    name: "teal",
  },
  {
    bg300: "bg-indigo-400",
    bg200: "bg-indigo-200",
    aspectBg: "bg-indigo-400/70",
    opinionBg: "bg-indigo-200/50",
    aspectRgb: [129, 140, 248],
    opinionRgb: [196, 181, 253],
    name: "indigo",
  },
  {
    bg300: "bg-lime-400",
    bg200: "bg-lime-200",
    aspectBg: "bg-lime-400/70",
    opinionBg: "bg-lime-200/50",
    aspectRgb: [163, 230, 53],
    opinionRgb: [217, 249, 157],
    name: "lime",
  },
  {
    bg300: "bg-rose-400",
    bg200: "bg-rose-200",
    aspectBg: "bg-rose-400/70",
    opinionBg: "bg-rose-200/50",
    aspectRgb: [251, 113, 133],
    opinionRgb: [253, 164, 175],
    name: "rose",
  },
  {
    bg300: "bg-violet-400",
    bg200: "bg-violet-200",
    aspectBg: "bg-violet-400/70",
    opinionBg: "bg-violet-200/50",
    aspectRgb: [167, 139, 250],
    opinionRgb: [221, 214, 254],
    name: "violet",
  },
  {
    bg300: "bg-fuchsia-400",
    bg200: "bg-fuchsia-200",
    aspectBg: "bg-fuchsia-400/70",
    opinionBg: "bg-fuchsia-200/50",
    aspectRgb: [232, 121, 249],
    opinionRgb: [245, 208, 254],
    name: "fuchsia",
  },
  {
    bg300: "bg-sky-400",
    bg200: "bg-sky-200",
    aspectBg: "bg-sky-400/70",
    opinionBg: "bg-sky-200/50",
    aspectRgb: [96, 165, 250],
    opinionRgb: [186, 230, 253],
    name: "sky",
  },
  {
    bg300: "bg-red-400",
    bg200: "bg-red-200",
    aspectBg: "bg-red-400/70",
    opinionBg: "bg-red-200/50",
    aspectRgb: [248, 113, 113],
    opinionRgb: [254, 202, 202],
    name: "red",
  },
  {
    bg300: "bg-yellow-400",
    bg200: "bg-yellow-200",
    aspectBg: "bg-yellow-400/70",
    opinionBg: "bg-yellow-200/50",
    aspectRgb: [250, 204, 21],
    opinionRgb: [254, 240, 138],
    name: "yellow",
  },
  {
    bg300: "bg-green-400",
    bg200: "bg-green-200",
    aspectBg: "bg-green-400/70",
    opinionBg: "bg-green-200/50",
    aspectRgb: [74, 222, 128],
    opinionRgb: [187, 247, 208],
    name: "green",
  },
  {
    bg300: "bg-slate-400",
    bg200: "bg-slate-200",
    aspectBg: "bg-slate-400/70",
    opinionBg: "bg-slate-200/50",
    aspectRgb: [148, 163, 184],
    opinionRgb: [226, 232, 240],
    name: "slate",
  },
  {
    bg300: "bg-zinc-400",
    bg200: "bg-zinc-200",
    aspectBg: "bg-zinc-400/70",
    opinionBg: "bg-zinc-200/50",
    aspectRgb: [161, 161, 170],
    opinionRgb: [228, 228, 231],
    name: "zinc",
  },
  // Additional 7 colors to reach 25 total
  {
    bg300: "bg-blue-400",
    bg200: "bg-blue-200",
    aspectBg: "bg-blue-400/70",
    opinionBg: "bg-blue-200/50",
    aspectRgb: [96, 165, 250],
    opinionRgb: [191, 219, 254],
    name: "blue",
  },
  {
    bg300: "bg-stone-400",
    bg200: "bg-stone-200",
    aspectBg: "bg-stone-400/70",
    opinionBg: "bg-stone-200/50",
    aspectRgb: [168, 162, 158],
    opinionRgb: [231, 229, 228],
    name: "stone",
  },
  {
    bg300: "bg-neutral-400",
    bg200: "bg-neutral-200",
    aspectBg: "bg-neutral-400/70",
    opinionBg: "bg-neutral-200/50",
    aspectRgb: [163, 163, 163],
    opinionRgb: [229, 229, 229],
    name: "neutral",
  },
  {
    bg300: "bg-gray-400",
    bg200: "bg-gray-200",
    aspectBg: "bg-gray-400/70",
    opinionBg: "bg-gray-200/50",
    aspectRgb: [156, 163, 175],
    opinionRgb: [229, 231, 235],
    name: "gray",
  },
  {
    bg300: "bg-red-500",
    bg200: "bg-red-300",
    aspectBg: "bg-red-500/70",
    opinionBg: "bg-red-300/50",
    aspectRgb: [239, 68, 68],
    opinionRgb: [252, 165, 165],
    name: "red-dark",
  },
  {
    bg300: "bg-orange-500",
    bg200: "bg-orange-300",
    aspectBg: "bg-orange-500/70",
    opinionBg: "bg-orange-300/50",
    aspectRgb: [249, 115, 22],
    opinionRgb: [253, 186, 116],
    name: "orange-dark",
  },
  {
    bg300: "bg-emerald-500",
    bg200: "bg-emerald-300",
    aspectBg: "bg-emerald-500/70",
    opinionBg: "bg-emerald-300/50",
    aspectRgb: [16, 185, 129],
    opinionRgb: [110, 231, 183],
    name: "emerald-dark",
  },
];

// Get color classes for annotation by index, with smart random selection
export const getAnnotationColorClasses = (
  index: number,
  usedColors: Set<number> = new Set(),
): { colorEntry: ColorEntry; colorIndex: number } => {
  // Get available colors (not used yet)
  const availableIndices = [];
  for (let i = 0; i < tailwindColorClasses.length; i++) {
    if (!usedColors.has(i)) {
      availableIndices.push(i);
    }
  }

  let selectedIndex: number;

  // If we have available colors, pick a random one
  if (availableIndices.length > 0) {
    selectedIndex = availableIndices[Math.floor(Math.random() * availableIndices.length)];
  } else {
    // If all colors are used, pick a completely random one
    selectedIndex = Math.floor(Math.random() * tailwindColorClasses.length);
  }

  return {
    colorEntry: tailwindColorClasses[selectedIndex],
    colorIndex: selectedIndex,
  };
};

// Helper function to get used color indices from aspect list
export const getUsedColorIndices = (aspectList: AspectItem[]): Set<number> => {
  const usedColors = new Set<number>();

  aspectList.forEach((aspect) => {
    if (aspect.colorIndex !== undefined) {
      usedColors.add(aspect.colorIndex);
    }
  });

  return usedColors;
};

// Helper function to get color by index
export const getColorByIndex = (colorIndex: number): ColorEntry => {
  return tailwindColorClasses[colorIndex % tailwindColorClasses.length];
};

// Function to mix colors mathematically
export const mixColors = (
  aspectRgb: [number, number, number],
  opinionRgb: [number, number, number],
  aspectOpacity = 0.7,
  opinionOpacity = 0.5,
): string => {
  // Simple additive color mixing with opacity weighting
  const weight1 = aspectOpacity;
  const weight2 = opinionOpacity;
  const totalWeight = weight1 + weight2;

  const mixedR = Math.round((aspectRgb[0] * weight1 + opinionRgb[0] * weight2) / totalWeight);
  const mixedG = Math.round((aspectRgb[1] * weight1 + opinionRgb[1] * weight2) / totalWeight);
  const mixedB = Math.round((aspectRgb[2] * weight1 + opinionRgb[2] * weight2) / totalWeight);

  return `rgba(${mixedR}, ${mixedG}, ${mixedB}, 0.8)`;
};

// Create highlighting information for the displayed text
export const createTextHighlights = (
  displayedText: string,
  aspectList: AspectItem[],
  getColorByIndex: (colorIndex: number) => ColorEntry,
): TextHighlight[] => {
  if (!displayedText || aspectList.length === 0) return [];

  const highlights: TextHighlight[] = [];

  aspectList.forEach((annotation, index) => {
    // Use stored colorIndex or fallback to sequential assignment
    const colorIndex =
      annotation.colorIndex !== undefined ? annotation.colorIndex : index % tailwindColorClasses.length;
    const colorClasses = getColorByIndex(colorIndex);

    // Process aspect term
    if (
      annotation.aspect_term &&
      annotation.aspect_term !== "NULL" &&
      annotation.at_start !== undefined &&
      annotation.at_end !== undefined
    ) {
      highlights.push({
        start: annotation.at_start!,
        end: annotation.at_end!,
        type: "aspect",
        colorClasses: colorClasses,
        text: annotation.aspect_term,
        index: highlights.length,
        annotationIndex: index,
      });
    }

    // Process opinion term
    if (
      annotation.opinion_term &&
      annotation.opinion_term !== "NULL" &&
      annotation.ot_start !== undefined &&
      annotation.ot_end !== undefined
    ) {
      highlights.push({
        start: annotation.ot_start!,
        end: annotation.ot_end!,
        type: "opinion",
        colorClasses: colorClasses,
        text: annotation.opinion_term,
        index: highlights.length,
        annotationIndex: index,
      });
    }
  });

  // Sort by start position
  return highlights.sort((a, b) => a.start - b.start);
};

// Render highlighted text with color mixing for overlaps
export const renderHighlightedText = (displayedText: string, highlights: TextHighlight[]): any => {
  if (!displayedText) return displayedText;

  if (highlights.length === 0) return displayedText;

  const result: any[] = [];

  // Create character-level highlight map
  const charHighlights: TextHighlight[][] = new Array(displayedText.length).fill(null).map(() => []);

  highlights.forEach((highlight: TextHighlight) => {
    for (let i = highlight.start; i <= highlight.end; i++) {
      if (i >= 0 && i < displayedText.length) {
        charHighlights[i].push(highlight);
      }
    }
  });

  // Render character by character
  for (let i = 0; i < displayedText.length; i++) {
    const char = displayedText[i];
    const charHighlight = charHighlights[i];

    if (charHighlight.length === 0) {
      // No highlighting
      result.push(char);
    } else {
      // Apply highlighting
      const aspectHighlights = charHighlight.filter((h) => h.type === "aspect");
      const opinionHighlights = charHighlight.filter((h) => h.type === "opinion");

      if (aspectHighlights.length > 0 && opinionHighlights.length > 0) {
        // Overlapping aspect and opinion terms - can be from different annotations
        // Mix all colors that appear at this character position
        let totalR = 0,
          totalG = 0,
          totalB = 0,
          totalWeight = 0;

        // Add all aspect term colors
        aspectHighlights.forEach((highlight) => {
          const rgb = highlight.colorClasses.aspectRgb;
          const weight = 0.7; // aspect weight
          totalR += rgb[0] * weight;
          totalG += rgb[1] * weight;
          totalB += rgb[2] * weight;
          totalWeight += weight;
        });

        // Add all opinion term colors
        opinionHighlights.forEach((highlight) => {
          const rgb = highlight.colorClasses.opinionRgb;
          const weight = 0.5; // opinion weight
          totalR += rgb[0] * weight;
          totalG += rgb[1] * weight;
          totalB += rgb[2] * weight;
          totalWeight += weight;
        });

        // Calculate weighted average
        const mixedR = Math.round(totalR / totalWeight);
        const mixedG = Math.round(totalG / totalWeight);
        const mixedB = Math.round(totalB / totalWeight);

        result.push(
          <span key={i} style={{ backgroundColor: `rgb(${mixedR}, ${mixedG}, ${mixedB})`, opacity: 0.9 }}>
            {char}
          </span>,
        );
      } else if (aspectHighlights.length > 1) {
        // Multiple aspect terms overlapping
        let totalR = 0,
          totalG = 0,
          totalB = 0;
        aspectHighlights.forEach((highlight) => {
          const rgb = highlight.colorClasses.aspectRgb;
          totalR += rgb[0];
          totalG += rgb[1];
          totalB += rgb[2];
        });
        const mixedR = Math.round(totalR / aspectHighlights.length);
        const mixedG = Math.round(totalG / aspectHighlights.length);
        const mixedB = Math.round(totalB / aspectHighlights.length);

        result.push(
          <span key={i} style={{ backgroundColor: `rgba(${mixedR}, ${mixedG}, ${mixedB}, 0.7)` }}>
            {char}
          </span>,
        );
      } else if (opinionHighlights.length > 1) {
        // Multiple opinion terms overlapping
        let totalR = 0,
          totalG = 0,
          totalB = 0;
        opinionHighlights.forEach((highlight) => {
          const rgb = highlight.colorClasses.opinionRgb;
          totalR += rgb[0];
          totalG += rgb[1];
          totalB += rgb[2];
        });
        const mixedR = Math.round(totalR / opinionHighlights.length);
        const mixedG = Math.round(totalG / opinionHighlights.length);
        const mixedB = Math.round(totalB / opinionHighlights.length);

        result.push(
          <span key={i} style={{ backgroundColor: `rgba(${mixedR}, ${mixedG}, ${mixedB}, 0.5)` }}>
            {char}
          </span>,
        );
      } else if (aspectHighlights.length > 0) {
        // Single aspect term highlighting - more opaque
        const colorClasses = aspectHighlights[0].colorClasses;
        const rgb = colorClasses.aspectRgb;
        result.push(
          <span key={i} style={{ backgroundColor: `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, 0.7)` }}>
            {char}
          </span>,
        );
      } else if (opinionHighlights.length > 0) {
        // Single opinion term highlighting - more transparent
        const colorClasses = opinionHighlights[0].colorClasses;
        const rgb = colorClasses.opinionRgb;
        result.push(
          <span key={i} style={{ backgroundColor: `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, 0.5)` }}>
            {char}
          </span>,
        );
      }
    }
  }

  return result;
};
