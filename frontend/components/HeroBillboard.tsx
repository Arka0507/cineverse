'use client';
import {useEffect, useState} from 'react';
import {AnimatePresence, motion, useReducedMotion} from 'framer-motion';
import {Play, Info, Pause, Star, Sparkles} from 'lucide-react';
import type {Movie} from '@/lib/types';
import MovieArt from './MovieArt';

export default function HeroBillboard({
  movies,
  onOpen
}: {
  movies: Movie[];
  onOpen: (movie: Movie, play?: boolean) => void;
}) {
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const reduced = useReducedMotion();

  // Rotate every 8 seconds
  useEffect(() => {
    if (paused || reduced || movies.length < 2) return;
    const id = setInterval(() => {
      setIndex((i) => (i + 1) % Math.min(movies.length, 6));
    }, 8000);
    return () => clearInterval(id);
  }, [movies.length, paused, reduced]);

  const movie = movies[index % Math.max(1, movies.length)];
  if (!movie) return null;

  return (
    <section className="hero" id="browse">
      {/* Background cinematic art with subtle Ken Burns effect */}
      <div className="hero-art-wrapper">
        <AnimatePresence mode="wait">
          <motion.div
            className="hero-art"
            key={movie.movie_id}
            initial={{ opacity: 0, scale: reduced ? 1 : 1.05 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: reduced ? 1 : 0.98 }}
            transition={{ duration: reduced ? 0.2 : 0.9, ease: [0.25, 0.1, 0.25, 1.0] }}
          >
            <MovieArt movie={movie} backdrop />
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Cinematic multi-stop gradient shades */}
      <div className="hero-shade" />

      {/* Content overlay */}
      <div className="hero-content" data-physics="hero">
        <motion.div
          key={`content-${movie.movie_id}`}
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        >
          <div className="eyebrow">
            <span className="spotlight-badge">
              <Sparkles size={12} /> CINEVERSE SPOTLIGHT
            </span>
            {movie.year && movie.year >= 2022 && <span className="recent-hit-pill">GLOBAL HIT</span>}
          </div>

          <h1>{movie.title}</h1>

          <div className="movie-meta">
            {movie.match != null ? (
              <strong className="match-tag" title="Recommendation score based on your taste">
                {movie.match}% Match for You
              </strong>
            ) : (
              <strong className="rating-tag">
                <Star size={14} fill="#f59e0b" color="#f59e0b" /> {movie.rating.toFixed(1)} / 5.0
              </strong>
            )}
            <span className="year-tag">{movie.year || 'Cinema'}</span>
            <span className="quality-tag">4K ULTRA HD</span>
            <span className="audio-tag">DOLBY ATMOS</span>
            <span className="genres-tag">{movie.genres.slice(0, 3).join(' • ')}</span>
          </div>

          <p className="hero-overview">{movie.overview}</p>

          <div className="hero-buttons">
            <button
              className="button button-primary"
              onClick={() => onOpen(movie, true)}
              aria-label={`Play trailer for ${movie.title}`}
            >
              <Play size={19} fill="currentColor" />
              {movie.trailer_key ? 'Watch Trailer' : 'Play Preview'}
            </button>
            <button
              className="button button-glass"
              onClick={() => onOpen(movie)}
              aria-label={`More info about ${movie.title}`}
            >
              <Info size={19} />
              Movie Details
            </button>
          </div>
        </motion.div>

        <span className="hero-footnote">Handpicked cinematic masterpieces ready to stream.</span>
      </div>

      {/* Hero Pagination & Play/Pause Controls */}
      <div className="hero-pagination">
        <button
          className="icon-button pause-btn"
          aria-label={paused ? 'Resume rotation' : 'Pause rotation'}
          onClick={() => setPaused(!paused)}
        >
          {paused ? <Play size={13} fill="currentColor" /> : <Pause size={13} />}
        </button>
        <div className="pagination-bars">
          {movies.slice(0, 6).map((m, i) => (
            <button
              key={m.movie_id}
              aria-label={`Switch to ${m.title}`}
              aria-current={i === index}
              onClick={() => setIndex(i)}
              className={`pagination-bar ${i === index ? 'selected' : ''}`}
            />
          ))}
        </div>
        <span className="pagination-counter">
          0{index + 1}<small> / 0{Math.min(6, movies.length)}</small>
        </span>
      </div>
    </section>
  );
}
