export interface Movie {
  movie_id: number; title: string; year: number | null; genres: string[];
  rating: number; rating_count: number; score?: number | null; match?: number | null;
  reason?: string | null; poster_url?: string | null; backdrop_url?: string | null;
  overview: string; runtime?: number | null; trailer_key?: string | null;
  release_date?: string | null;
  directors?: string; actors?: string; metadata_source: 'tmdb' | 'fallback' | 'curated';
}
export interface Catalog { items: Movie[]; total: number; page: number; page_size: number }
export interface Session { user_id: number; token: string; expires_in: number }
