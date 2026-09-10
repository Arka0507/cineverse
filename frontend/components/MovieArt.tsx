'use client';
import {useState} from 'react';
import type {Movie} from '@/lib/types';
import {Film, Star} from 'lucide-react';

export default function MovieArt({movie, backdrop=false}: {movie: Movie; backdrop?: boolean}) {
  const [failed, setFailed] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const url = backdrop ? (movie.backdrop_url || movie.poster_url) : (movie.poster_url || movie.backdrop_url);
  const hue = ((movie.movie_id * 47) % 360);

  if (url && !failed) {
    return (
      <div className={`art-container ${backdrop ? 'backdrop-container' : 'poster-container'}`}>
        {/* Smooth shimmer skeleton while loading */}
        {!loaded && <div className="art-skeleton" />}
        <img
          className={`${backdrop ? 'backdrop-image' : 'poster-image'} ${loaded ? 'loaded' : 'loading'}`}
          src={url}
          alt={backdrop ? '' : `${movie.title} poster`}
          loading={backdrop ? 'eager' : 'lazy'}
          draggable={false}
          onLoad={() => setLoaded(true)}
          onError={() => setFailed(true)}
        />
        <div className="art-gradient-overlay" />
      </div>
    );
  }

  // Premium stylized cinematic fallback poster
  return (
    <div
      className={`catalog-art ${backdrop ? 'catalog-art-large' : ''}`}
      style={{'--art-hue': hue} as React.CSSProperties}
    >
      <div className="art-film-watermark">
        <Film size={backdrop ? 120 : 64} strokeWidth={1} />
      </div>
      <div className="art-header">
        <span className="art-edition">CINEVERSE PREMIERE</span>
        {movie.rating > 0 && (
          <span className="art-rating">
            <Star size={10} fill="#f59e0b" color="#f59e0b" /> {movie.rating.toFixed(1)}
          </span>
        )}
      </div>
      <strong className="art-title">{movie.title}</strong>
      <div className="art-year">
        <span>{movie.year || 'FEATURE'}</span>
        <i />
        <span>{movie.genres?.[0] || 'Cinema'}</span>
      </div>
      <div className="art-gradient-overlay" />
    </div>
  );
}
