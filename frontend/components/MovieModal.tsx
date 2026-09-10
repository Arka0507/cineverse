'use client';
import {useEffect, useRef, useState} from 'react';
import {X, Play, Star, Sparkles, Film} from 'lucide-react';
import {motion} from 'framer-motion';
import type {Movie} from '@/lib/types';
import MovieArt from './MovieArt';

export default function MovieModal({
  movie,
  autoplay,
  onClose,
  onRate
}: {
  movie: Movie;
  autoplay: boolean;
  onClose: () => void;
  onRate: (m: Movie, r: number) => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [playing, setPlaying] = useState(autoplay && !!movie.trailer_key);
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);

  useEffect(() => {
    const el = dialog.current;
    el?.showModal();
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      el?.close();
      document.body.style.overflow = previous;
    };
  }, []);

  return (
    <dialog
      ref={dialog}
      className="movie-dialog"
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.94, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96 }}
        transition={{ type: 'spring', stiffness: 350, damping: 28 }}
      >
        <button
          className="modal-close icon-button"
          aria-label="Close movie details"
          onClick={onClose}
        >
          <X size={20} />
        </button>

        <div className="modal-art">
          {playing && movie.trailer_key ? (
            <iframe
              src={`https://www.youtube-nocookie.com/embed/${movie.trailer_key}?autoplay=1&rel=0&modestbranding=1`}
              title={`${movie.title} trailer`}
              allow="autoplay; encrypted-media; fullscreen"
              allowFullScreen
            />
          ) : (
            <div className="modal-art-preview">
              <MovieArt movie={movie} backdrop />
              {movie.trailer_key && (
                <button
                  className="modal-play-overlay"
                  onClick={() => setPlaying(true)}
                  aria-label={`Play trailer for ${movie.title}`}
                >
                  <span className="play-pulse">
                    <Play size={28} fill="currentColor" />
                  </span>
                  <span>Play Trailer</span>
                </button>
              )}
            </div>
          )}
        </div>

        <div className="modal-body">
          <div className="eyebrow">
            <Sparkles size={13} /> CINEVERSE EXCLUSIVE OVERVIEW
          </div>

          <h2>{movie.title}</h2>

          <div className="movie-meta">
            <strong className="match">
              <Star size={14} fill="#f59e0b" color="#f59e0b" /> {movie.rating.toFixed(1)} / 5.0
            </strong>
            <span className="year-pill">{movie.year || 'Classic'}</span>
            <span className="quality">4K UHD</span>
            <span className="rating-count-pill">{movie.rating_count.toLocaleString()} Ratings</span>
          </div>

          <p className="modal-overview">{movie.overview}</p>

          <div className="genre-tags">
            {movie.genres.map((g) => (
              <span key={g}>{g}</span>
            ))}
          </div>

          {/* Interactive Rating Panel */}
          <div className="rating-panel">
            <div>
              <h3>Rate this Movie</h3>
              <p>Tune the hybrid recommender algorithm to your taste.</p>
            </div>
            <div className="stars" onMouseLeave={() => setHoverRating(0)}>
              {[1, 2, 3, 4, 5].map((n) => {
                const active = (hoverRating || rating) >= n;
                return (
                  <button
                    key={n}
                    aria-label={`Rate ${n} out of 5 stars`}
                    aria-pressed={rating === n}
                    onMouseEnter={() => setHoverRating(n)}
                    onClick={() => {
                      setRating(n);
                      onRate(movie, n);
                    }}
                  >
                    <Star
                      size={28}
                      fill={active ? '#e50914' : 'none'}
                      color={active ? '#e50914' : '#666'}
                    />
                  </button>
                );
              })}
            </div>
          </div>

          {/* Directors & Stars */}
          <div className="credits-section">
            {movie.directors && (
              <p className="credits">
                <b>Director:</b> {movie.directors}
              </p>
            )}
            {movie.actors && (
              <p className="credits">
                <b>Starring:</b> {movie.actors.split(',').slice(0, 8).join(', ')}
              </p>
            )}
            <p className="credits source-note">
              <Film size={12} />
              <span>
                {movie.metadata_source === 'curated'
                  ? 'Curated 4K blockbuster metadata & official trailer stream.'
                  : movie.metadata_source === 'tmdb'
                  ? 'Official metadata provided by TMDB.'
                  : 'Cineverse catalog edition with high-fidelity cinematic styling.'}
              </span>
            </p>
          </div>
        </div>
      </motion.div>
    </dialog>
  );
}
