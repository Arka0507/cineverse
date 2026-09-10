'use client';
import {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import dynamic from 'next/dynamic';
import {ArrowRight, Film, RefreshCw, SlidersHorizontal, Orbit, Sparkles, Flame, Trophy} from 'lucide-react';
import Navbar from '@/components/Navbar';
import HeroBillboard from '@/components/HeroBillboard';
import MovieRow from '@/components/MovieRow';
import NetflixCard from '@/components/NetflixCard';
import MovieModal from '@/components/MovieModal';
import {ApiError, catalog, newSession, rateMovie, recommendations, request, similarMovies} from '@/lib/api';
import type {Movie, Session} from '@/lib/types';

const AntiGravity = dynamic(() => import('@/components/AntiGravity'), {ssr: false});

export default function Home() {
  const [session, setSession] = useState<Session | null>(null);
  const [featured, setFeatured] = useState<Movie[]>([]);
  const [picks, setPicks] = useState<Movie[]>([]);
  const [popular, setPopular] = useState<Movie[]>([]);
  const [hindiMovies, setHindiMovies] = useState<Movie[]>([]);
  const [hollywoodMovies, setHollywoodMovies] = useState<Movie[]>([]);
  const [futureMovies, setFutureMovies] = useState<Movie[]>([]);
  const [movies, setMovies] = useState<Movie[]>([]);
  const [similar, setSimilar] = useState<Movie[]>([]);
  const [seed, setSeed] = useState<Movie | null>(null);

  const [genres, setGenres] = useState<string[]>([]);
  const [genre, setGenre] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');
  const [gravity, setGravity] = useState(false);
  const [demoEnabled, setDemoEnabled] = useState(false);
  const [selected, setSelected] = useState<{movie: Movie; play: boolean} | null>(null);

  const initialized = useRef(false);
  const feedbackVersion = useRef(0);
  const profileVersion = useRef(0);
  const sessionRef = useRef<Session | null>(null);

  const persist = (s: Session) => {
    sessionRef.current = s;
    setSession(s);
    try {
      localStorage.setItem('cineverse-session', JSON.stringify({...s, expires_at: Date.now() + s.expires_in * 1000}));
    } catch {
      /* Private browsing can disable storage */
    }
  };

  const boot = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      let s: Session | null = null;
      try {
        const saved = JSON.parse(localStorage.getItem('cineverse-session') || 'null');
        if (saved?.token && saved.expires_at > Date.now()) s = saved as Session;
      } catch {
        /* Start fresh session */
      }
      s = s || (await newSession());
      let recs: Movie[];
      try {
        recs = await recommendations(s);
      } catch (e) {
        if (e instanceof ApiError && e.status === 401) {
          s = await newSession();
          recs = await recommendations(s);
        } else throw e;
      }
      persist(s);

      const [result, hindiResult, allGenres, health] = await Promise.all([
        catalog('', '', 1, undefined, 60),
        catalog('', 'Hindi', 1, undefined, 60),
        request<string[]>('/api/genres'),
        request<{demo_profiles: boolean}>('/health')
      ]);

      setPicks(recs);
      setPopular(result.items);
      setHindiMovies(hindiResult.items);

      // Separate Hollywood movies and curate true Award Winners (strictly released films, NO upcoming!)
      const hollywoodOnly = result.items.filter(m => !m.genres.includes('Hindi'));
      const awardWinningTitles = [
        'Oppenheimer',
        'Everything Everywhere All at Once',
        'Parasite',
        'The Godfather',
        'Godfather, The',
        'The Godfather Part II',
        'Godfather: Part II, The',
        "Schindler's List",
        'Forrest Gump',
        'The Silence of the Lambs',
        'Silence of the Lambs, The',
        'Titanic',
        'Whiplash',
        'Slumdog Millionaire',
        'Inception',
        'Interstellar',
        'The Dark Knight',
        'Dark Knight, The',
        'The Shawshank Redemption',
        'Shawshank Redemption, The',
        'Pulp Fiction',
        'La La Land',
        '12 Years a Slave'
      ];
      const awardWinners = [
        ...result.items.filter(m => awardWinningTitles.includes(m.title)),
        ...hollywoodOnly.filter(m => (m.year || 0) <= 2024 && (m.rating || 0) >= 4.4 && !['War 2', 'Avengers: Doomsday', 'Spider-Man: Beyond the Spider-Verse', 'Superman', 'Avatar: Fire and Ash'].includes(m.title))
      ];
      setHollywoodMovies(Array.from(new Map(awardWinners.map(m => [m.movie_id, m])).values()));

      // Extract unreleased upcoming blockbusters (War 2 is a released film, so excluded!)
      const upcoming = [
        ...result.items.filter(m => m.title !== 'War 2' && ((m.year || 0) >= 2026 || ['Avatar: Fire and Ash', 'Superman'].includes(m.title))),
        ...hindiResult.items.filter(m => m.title !== 'War 2' && ((m.year || 0) >= 2026 || ['Avatar: Fire and Ash', 'Superman'].includes(m.title)))
      ];
      setFutureMovies(Array.from(new Map(upcoming.map(m => [m.movie_id, m])).values()));

      // Hero Billboard: User requested upcoming Spider-Man and Doomsday in spotlight + alternating Hindi hits
      const spiderManMovie = result.items.find(m => m.title === 'Spider-Man: Beyond the Spider-Verse') || hollywoodOnly.find(m => m.title.includes('Spider-Man'));
      const doomsdayMovie = result.items.find(m => m.title === 'Avengers: Doomsday') || hollywoodOnly.find(m => m.title.includes('Avengers'));
      const oppenheimerMovie = result.items.find(m => m.title === 'Oppenheimer') || hollywoodOnly[0];

      const hindiHeroPool = [
        ...hindiResult.items.filter(m => ['12th Fail', 'Dangal', 'Jawan', 'Andhadhun', 'Drishyam'].includes(m.title)),
        ...hindiResult.items
      ];
      const uniqueHindi = Array.from(new Map(hindiHeroPool.map(m => [m.movie_id, m])).values()).slice(0, 3);

      const alternatingHero = [
        spiderManMovie || hollywoodOnly[0], // 1. Spider-Man: Beyond the Spider-Verse (Upcoming)
        uniqueHindi[0],                     // 2. 12th Fail (Hindi)
        doomsdayMovie || hollywoodOnly[1],  // 3. Avengers: Doomsday (Upcoming)
        uniqueHindi[1],                     // 4. Dangal (Hindi)
        oppenheimerMovie,                   // 5. Oppenheimer (Hollywood Oscar Winner)
        uniqueHindi[2],                     // 6. Jawan (Hindi)
      ].filter(Boolean) as Movie[];

      setFeatured(alternatingHero);

      setMovies(result.items);
      setTotal(result.total);
      setGenres(allGenres);
      setDemoEnabled(health.demo_profiles);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to connect to the movie service.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;
    void boot();
  }, [boot]);

  // Catalog search & filter with smooth debounce
  useEffect(() => {
    if (!session) return;
    const controller = new AbortController();
    setCatalogLoading(true);
    const timer = setTimeout(() => {
      void catalog(search, genre, page, controller.signal)
        .then((result) => {
          setMovies(result.items);
          setTotal(result.total);
          setError('');
        })
        .catch((e) => {
          if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'Search failed');
        })
        .finally(() => {
          if (!controller.signal.aborted) setCatalogLoading(false);
        });
    }, 200);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [search, genre, page, session]);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(''), 3500);
    return () => clearTimeout(timer);
  }, [toast]);

  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'g' && !gravity) {
        e.preventDefault();
        setSelected(null);
        setGravity(true);
      }
    };
    window.addEventListener('keydown', key);
    return () => window.removeEventListener('keydown', key);
  }, [gravity]);

  const changeProfile = async (demo?: number) => {
    const version = ++profileVersion.current;
    ++feedbackVersion.current;
    try {
      const s = await newSession(demo);
      const recs = await recommendations(s);
      if (version !== profileVersion.current) return;
      persist(s);
      setPicks(recs);
      setSimilar([]);
      setSeed(null);
      setToast(demo ? 'MovieLens demo profile selected' : 'Your fresh profile is ready');
    } catch (e) {
      setToast(e instanceof Error ? e.message : 'Could not change profile');
    }
  };

  const rate = async (movie: Movie, rating: number) => {
    if (!sessionRef.current) return;
    const s = sessionRef.current;
    const version = ++feedbackVersion.current;
    try {
      await rateMovie(s, movie, rating);
      const [recs, related] = await Promise.all([recommendations(s), similarMovies(movie)]);
      if (version !== feedbackVersion.current || sessionRef.current?.user_id !== s.user_id) return;
      setPicks(recs);
      setSimilar(related);
      setSeed(movie);
      setToast(`Rated "${movie.title}" ${rating}/5. Your recommendations have adapted.`);
    } catch (e) {
      setToast(e instanceof Error ? e.message : 'Could not save your rating');
    }
  };

  const open = (movie: Movie, play = false) => setSelected({movie, play});
  const filtering = !!search || !!genre;

  // Segment curated rows from loaded popular catalog
  const recentHits = useMemo(() => {
    return popular.filter(m => (m.year || 0) >= 2018);
  }, [popular]);

  const sciFiAction = useMemo(() => {
    return popular.filter(m => m.genres.includes('Sci-Fi') || m.genres.includes('Action'));
  }, [popular]);

  const acclaimedDramas = useMemo(() => {
    return popular.filter(m => m.genres.includes('Drama') && (m.rating || 0) >= 4.0);
  }, [popular]);

  return (
    <>
      <div id="app-surface" aria-hidden={gravity || undefined}>
        <Navbar
          search={search}
          onSearch={(v) => {
            setSearch(v);
            setPage(1);
          }}
          onGravity={() => {
            setSelected(null);
            setGravity(true);
          }}
          userId={session?.user_id}
          onProfile={(demo) => void changeProfile(demo)}
          demoEnabled={demoEnabled}
        />

        {loading ? (
          <main className="loading-screen">
            <div className="loading-orbit">
              <Orbit size={44} />
            </div>
            <h1>Entering the Cineverse.</h1>
            <p>Hydrating 2,250+ blockbusters, Bollywood classics, ratings, and recommendations…</p>
          </main>
        ) : error && !movies.length ? (
          <main className="loading-screen">
            <Film size={48} />
            <h1>The cinema is taking a momentary pause.</h1>
            <p role="alert">{error}</p>
            <button className="button button-white" onClick={() => void boot()}>
              <RefreshCw size={18} />
              Try again
            </button>
          </main>
        ) : (
          <main>
            {!filtering && <HeroBillboard movies={featured} onOpen={open} />}

            <div className={`browse-content ${filtering ? 'search-content' : ''}`}>
              {!filtering && (
                <>
                  {/* Hit Hindi Cinema (2010–2026) Row */}
                  {hindiMovies.length > 0 && (
                    <MovieRow
                      id="hindi"
                      title="Hit Hindi Cinema (2010–2026)"
                      subtitle="500+ iconic Bollywood blockbusters, award-winning dramas, and timeless epics."
                      movies={hindiMovies.slice(0, 24)}
                      onOpen={open}
                      onRate={(m, r) => void rate(m, r)}
                      highlight
                    />
                  )}

                  {/* Upcoming Releases (2025-2026) Row */}
                  {futureMovies.length > 0 && (
                    <MovieRow
                      id="upcoming"
                      title="Upcoming Releases & Blockbusters (2025–2026)"
                      subtitle="Franchise titans, visionary spectacles, and anticipated theatrical debuts with official release dates."
                      movies={futureMovies}
                      onOpen={open}
                      onRate={(m, r) => void rate(m, r)}
                      highlight
                    />
                  )}

                  {/* Award-Winning Masterpieces & Global Legends Row */}
                  {hollywoodMovies.length > 0 && (
                    <MovieRow
                      id="hollywood"
                      title="Award-Winning Masterpieces & Global Legends"
                      subtitle="Oscar Best Picture winners, Cannes honorees, and timeless cinema icons (strictly released films)."
                      movies={hollywoodMovies.slice(0, 24)}
                      onOpen={open}
                      onRate={(m, r) => void rate(m, r)}
                      highlight
                    />
                  )}

                  {/* Recent Blockbusters Row */}
                  {recentHits.length > 0 && (
                    <MovieRow
                      id="recent"
                      title="Recently Hit Blockbusters (2020–2024)"
                      subtitle="Current global box office titans, festival winners, and modern epics."
                      movies={recentHits}
                      onOpen={open}
                      onRate={(m, r) => void rate(m, r)}
                    />
                  )}

                  {/* Personalized Recommendations Row */}
                  <MovieRow
                    id="picks"
                    title="Picked Just for Your Taste"
                    subtitle="Hybrid collaborative filtering tuned directly to your viewing style."
                    movies={picks}
                    onOpen={open}
                    onRate={(m, r) => void rate(m, r)}
                  />

                  {/* Dynamic Similar Row upon Rating */}
                  {seed && (
                    <MovieRow
                      title={`Because You Rated “${seed.title}”`}
                      subtitle="Titles sharing direct thematic and genre DNA."
                      movies={similar}
                      onOpen={open}
                      onRate={(m, r) => void rate(m, r)}
                      highlight
                    />
                  )}

                  {/* Audience Favorites Row */}
                  <MovieRow
                    title="Top Audience Favorites"
                    subtitle="Universally acclaimed cinematic benchmarks."
                    movies={popular.slice(0, 16)}
                    onOpen={open}
                    onRate={(m, r) => void rate(m, r)}
                    ranked
                  />

                  {/* Sci-Fi & Action Spectacles */}
                  {sciFiAction.length > 0 && (
                    <MovieRow
                      title="Sci-Fi & Action Spectacles"
                      subtitle="Mind-bending realities, high-stakes thrills, and visual grandeur."
                      movies={sciFiAction.slice(0, 14)}
                      onOpen={open}
                      onRate={(m, r) => void rate(m, r)}
                    />
                  )}

                  {/* Acclaimed Dramas */}
                  {acclaimedDramas.length > 0 && (
                    <MovieRow
                      title="Acclaimed Dramas & Stories"
                      subtitle="Deep character studies and unforgettable narratives."
                      movies={acclaimedDramas.slice(0, 14)}
                      onOpen={open}
                      onRate={(m, r) => void rate(m, r)}
                    />
                  )}
                </>
              )}

              {/* Full Interactive Paginated Catalog Grid */}
              <section className="catalog-section" id="catalog">
                <div className="section-heading catalog-heading">
                  <div>
                    <div className="eyebrow">EXPLORE THE COMPLETE VAULT</div>
                    <h2>{search ? `Results for “${search}”` : 'Every Film Tells a Story'}</h2>
                  </div>
                  <label className="genre-select">
                    <SlidersHorizontal size={16} />
                    <select
                      aria-label="Filter by genre"
                      value={genre}
                      onChange={(e) => {
                        setGenre(e.target.value);
                        setPage(1);
                      }}
                    >
                      <option value="">All genres</option>
                      {genres.map((g) => (
                        <option key={g}>{g}</option>
                      ))}
                    </select>
                  </label>
                </div>

                {/* Genre Filter Chips */}
                <div className="genre-chips">
                  {['', 'Hindi', 'Action', 'Adventure', 'Animation', 'Comedy', 'Crime', 'Drama', 'Sci-Fi', 'Thriller', 'Horror', 'Romance'].map((g) => (
                    <button
                      key={g}
                      onClick={() => {
                        setGenre(g);
                        setPage(1);
                      }}
                      className={genre === g ? 'active' : ''}
                    >
                      {g || 'All Categories'}
                    </button>
                  ))}
                </div>

                {error && (
                  <p role="alert" className="inline-error">
                    {error}
                    <button onClick={() => setError('')}>Dismiss</button>
                  </p>
                )}

                <p className="catalog-count" aria-live="polite">
                  {catalogLoading ? 'Filtering vault…' : `${total.toLocaleString()} masterpieces in collection`}
                </p>

                {!catalogLoading && !movies.length ? (
                  <div className="empty-state">
                    <Film size={40} />
                    <h3>No titles match your criteria</h3>
                    <p>Try searching for a different title or resetting the genre filters.</p>
                    <button
                      onClick={() => {
                        setSearch('');
                        setGenre('');
                      }}
                    >
                      Clear all filters
                    </button>
                  </div>
                ) : (
                  <div className={`catalog-grid ${catalogLoading ? 'is-loading' : ''}`}>
                    {movies.map((movie) => (
                      <NetflixCard
                        key={movie.movie_id}
                        movie={movie}
                        onOpen={open}
                        onRate={(m, r) => void rate(m, r)}
                      />
                    ))}
                  </div>
                )}

                {/* Smooth Pagination */}
                <div className="pagination">
                  <button
                    disabled={page === 1 || catalogLoading}
                    onClick={() => {
                      setPage((p) => p - 1);
                      document.getElementById('catalog')?.scrollIntoView({behavior: 'smooth'});
                    }}
                  >
                    Previous
                  </button>
                  <span>
                    Page {page} of {Math.max(1, Math.ceil(total / 24))}
                  </span>
                  <button
                    disabled={page * 24 >= total || catalogLoading}
                    onClick={() => {
                      setPage((p) => p + 1);
                      document.getElementById('catalog')?.scrollIntoView({behavior: 'smooth'});
                    }}
                  >
                    Next <ArrowRight size={15} />
                  </button>
                </div>
              </section>
            </div>
          </main>
        )}

        <footer>
          <a className="wordmark" href="#">
            CINEVERSE<span />
          </a>
          <p>The next era of cinema curation and physics-powered discovery.</p>
          <div>
            Hybrid Recommendation Engine (SVD Collaborative Filtering + TF-IDF Content Vectorization).
            <br />
            Curated 4K Cinema Metadata & High-Resolution TMDB Poster CDN.
          </div>
          <small>Interactive Anti-Gravity Sandbox powered by Matter.js. Full trailers streamed via official YouTube embeds.</small>
        </footer>
      </div>

      {selected && (
        <MovieModal
          key={selected.movie.movie_id}
          movie={selected.movie}
          autoplay={selected.play}
          onClose={() => setSelected(null)}
          onRate={(m, r) => void rate(m, r)}
        />
      )}

      {gravity && <AntiGravity onExit={() => setGravity(false)} />}
      {toast && (
        <div className="toast" role="status">
          {toast}
        </div>
      )}
    </>
  );
}
