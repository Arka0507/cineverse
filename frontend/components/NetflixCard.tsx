'use client';
import {useState} from 'react';
import {motion, useReducedMotion} from 'framer-motion';
import {Play, ThumbsUp, ChevronDown, Star} from 'lucide-react';
import type {Movie} from '@/lib/types';
import MovieArt from './MovieArt';

export default function NetflixCard({
  movie,
  onOpen,
  onRate,
  rank
}: {
  movie: Movie;
  onOpen: (movie: Movie, play?: boolean) => void;
  onRate: (movie: Movie, rating: number) => void;
  rank?: number;
}) {
  const reduced = useReducedMotion();
  const [isHovered, setIsHovered] = useState(false);

  return (
    <motion.article
      className="movie-card"
      data-physics="card"
      data-movie-id={movie.movie_id}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      whileHover={{
        scale: reduced ? 1 : 1.06,
        y: reduced ? 0 : -6,
        zIndex: 25
      }}
      whileTap={{ scale: 0.98 }}
      transition={{
        type: 'spring',
        stiffness: 380,
        damping: 26,
        mass: 0.8
      }}
    >
      <button
        className="card-cover"
        aria-label={`View details for ${movie.title}`}
        onClick={() => onOpen(movie)}
      >
        <MovieArt movie={movie} />
        {rank && <span className="rank-badge">{String(rank).padStart(2, '0')}</span>}
        <div className="card-badges">
          <span className="card-top-label">{movie.genres[0] || 'Movie'}</span>
          {movie.year && movie.year >= 2020 && <span className="card-new-badge">NEW</span>}
        </div>
      </button>

      <div className="card-description">
        <h3 title={movie.title}>{movie.title}</h3>
        <div className="card-meta-line">
          <span className="card-year">{movie.year || 'Classic'}</span>
          {movie.match != null ? (
            <span className="match">{movie.match}% Match</span>
          ) : (
            <span className="rating-pill">
              <Star size={11} fill="#f59e0b" color="#f59e0b" /> {movie.rating.toFixed(1)}
            </span>
          )}
          <span className="quality-pill">4K</span>
        </div>

        <div className="card-controls">
          <button
            className="icon-button light play-btn"
            title="Play Trailer"
            aria-label={`Play trailer for ${movie.title}`}
            onClick={(e) => {
              e.stopPropagation();
              onOpen(movie, true);
            }}
          >
            <Play size={13} fill="currentColor" />
          </button>
          <button
            className="icon-button rate-btn"
            title="Rate 5 Stars"
            aria-label={`Rate 5 stars for ${movie.title}`}
            onClick={(e) => {
              e.stopPropagation();
              onRate(movie, 5);
            }}
          >
            <ThumbsUp size={13} />
          </button>
          <div className="card-genres-short">
            {movie.genres.slice(0, 2).join(' • ')}
          </div>
          <button
            className="icon-button details-btn"
            title="More Info"
            aria-label={`Details for ${movie.title}`}
            onClick={(e) => {
              e.stopPropagation();
              onOpen(movie);
            }}
          >
            <ChevronDown size={14} />
          </button>
        </div>
      </div>
    </motion.article>
  );
}
