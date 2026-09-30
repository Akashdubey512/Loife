import React, { useState } from 'react';

export interface IllustrationProps {
  src: string;
  alt: string;
  caption?: string;
  badge?: string;
  variant?: 'hero' | 'card' | 'banner' | 'side' | 'compact';
  aspectRatio?: '16:9' | '4:3' | '1:1' | '3:2' | 'auto';
  className?: string;
  imageClassName?: string;
}

export const Illustration: React.FC<IllustrationProps> = ({
  src,
  alt,
  caption,
  badge,
  variant = 'card',
  aspectRatio = 'auto',
  className = '',
  imageClassName = '',
}) => {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);

  const aspectClass =
    aspectRatio === '16:9'
      ? 'aspect-video'
      : aspectRatio === '4:3'
      ? 'aspect-4/3'
      : aspectRatio === '1:1'
      ? 'aspect-square'
      : aspectRatio === '3:2'
      ? 'aspect-3/2'
      : '';

  const variantContainerClasses = {
    hero: 'rounded-3xl overflow-hidden border border-[#F2C45A]/25 shadow-2xl shadow-[#174C3C]/30 relative group',
    card: 'rounded-2xl overflow-hidden border border-white/10 relative group bg-[#0C1410]/50 hover:border-[#77B7A5]/30 transition-all duration-300',
    banner: 'rounded-2xl overflow-hidden border border-[#F2C45A]/20 relative bg-gradient-to-r from-[#174C3C]/40 via-[#145B59]/30 to-[#0C1410]/50',
    side: 'rounded-2xl overflow-hidden border border-white/10 relative h-full bg-[#0C1410]/40',
    compact: 'rounded-xl overflow-hidden border border-white/10 relative',
  };

  return (
    <figure className={`flex flex-col ${variantContainerClasses[variant]} ${className}`}>
      <div className={`relative w-full overflow-hidden ${aspectClass}`}>
        {/* Warm shimmer skeleton while loading */}
        {!loaded && !error && (
          <div className="absolute inset-0 bg-gradient-to-br from-[#174C3C]/30 via-[#29332F]/50 to-[#145B59]/30 animate-pulse flex items-center justify-center">
            <span className="text-xs text-[#77B7A5]/70 font-medium">Loading Loife artwork...</span>
          </div>
        )}

        <img
          src={src}
          alt={alt}
          onLoad={() => setLoaded(true)}
          onError={() => setError(true)}
          loading="lazy"
          className={`w-full h-full object-cover transition-all duration-500 ${
            loaded ? 'opacity-100 scale-100' : 'opacity-0 scale-95'
          } ${imageClassName}`}
        />

        {/* Optional decorative tag */}
        {badge && (
          <div className="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-[#0C1410]/80 backdrop-blur-md border border-[#F2C45A]/30 text-[#F2C45A] text-[10px] font-bold tracking-wide uppercase shadow-lg">
            {badge}
          </div>
        )}

        {/* Soft subtle warm gradient overlay for natural blending */}
        <div className="absolute inset-0 pointer-events-none bg-gradient-to-t from-[#080b11]/60 via-transparent to-transparent opacity-60" />
      </div>

      {caption && (
        <figcaption className="p-3 text-center text-xs font-medium text-[#FFF6E8]/80 italic border-t border-white/5 bg-[#0C1410]/60 backdrop-blur-sm">
          "{caption}"
        </figcaption>
      )}
    </figure>
  );
};

export default Illustration;
