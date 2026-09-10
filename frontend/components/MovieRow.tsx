'use client';
import {useRef, useState, useEffect} from 'react';
import {ChevronLeft, ChevronRight, Sparkles} from 'lucide-react';
import type {Movie} from '@/lib/types';
import NetflixCard from './NetflixCard';

export default function MovieRow({
  title,
  subtitle,
  movies,
  onOpen,
  onRate,
  ranked = false,
  id,
  highlight = false
}: {
  title: string;
  subtitle?: string;
  movies: Movie[];
  onOpen: (m: Movie, play?: boolean) => void;
  onRate: (m: Movie, r: number) => void;
  ranked?: boolean;
  id?: string;
  highlight?: boolean;
}) {
  const rowRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);

  const checkScroll = () => {
    if (!rowRef.current) return;
    const { scrollLeft, scrollWidth, clientWidth } = rowRef.current;
    setCanScrollLeft(scrollLeft > 20);
    setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 20);
  };

  useEffect(() => {
    checkScroll();
    const el = rowRef.current;
    if (el) {
      el.addEventListener('scroll', checkScroll, { passive: true });
      window.addEventListener('resize', checkScroll);
      return () => {
        el.removeEventListener('scroll', checkScroll);
        window.removeEventListener('resize', checkScroll);
      };
    }
  }, [movies.length]);

  if (!movies.length) return null;

  const scroll = (direction: number) => {
    if (!rowRef.current) return;
    const amount = rowRef.current.clientWidth * 0.75 * direction;
    rowRef.current.scrollBy({ left: amount, behavior: 'smooth' });
  };

  return (
    <section className={`movie-section ${highlight ? 'highlight-section' : ''}`} id={id}>
      <div className="section-heading">
        <div>
          <h2>
            {title}
            {highlight && <Sparkles size={16} className="highlight-icon" />}
          </h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
        <div className="row-arrows">
          <button
            className={`row-nav-btn prev ${!canScrollLeft ? 'disabled' : ''}`}
            aria-label={`Scroll ${title} left`}
            onClick={() => scroll(-1)}
            disabled={!canScrollLeft}
          >
            <ChevronLeft size={20} />
          </button>
          <button
            className={`row-nav-btn next ${!canScrollRight ? 'disabled' : ''}`}
            aria-label={`Scroll ${title} right`}
            onClick={() => scroll(1)}
            disabled={!canScrollRight}
          >
            <ChevronRight size={20} />
          </button>
        </div>
      </div>

      <div className="row-shell">
        <div className="movie-row" ref={rowRef}>
          {movies.map((m, i) => (
            <NetflixCard
              key={m.movie_id}
              movie={m}
              onOpen={onOpen}
              onRate={onRate}
              rank={ranked ? i + 1 : undefined}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
