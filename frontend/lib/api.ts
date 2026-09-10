import type {Catalog, Movie, Session} from './types';
function getBaseUrl(): string {
  if (typeof window !== 'undefined') {
    if (window.location.port === '3000' && window.location.hostname === 'localhost') {
      return process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    }
    return '';
  }
  return process.env.NEXT_PUBLIC_API_BASE_URL || '';
}

export class ApiError extends Error { constructor(message: string, public status: number) { super(message); } }
export async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const base = getBaseUrl();
  const response = await fetch(`${base}${path}`, {...options, signal: options.signal || AbortSignal.timeout(60000), headers:{'Content-Type':'application/json', ...(token ? {Authorization:`Bearer ${token}`} : {}), ...options.headers}});
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new ApiError(typeof data.detail === 'string' ? data.detail : `Request failed (${response.status})`, response.status);
  }
  return response.json() as Promise<T>;
}
export const catalog = (search = '', genre = '', page = 1, signal?: AbortSignal, page_size = 24) => request<Catalog>(`/api/movies?${new URLSearchParams({search, genre, page:String(page), page_size:String(page_size)})}`, {signal});
export const recommendations = (session: Session) => request<Movie[]>('/api/recommend/user', {method:'POST',body:JSON.stringify({user_id:session.user_id, top_k:24})}, session.token);
export const similarMovies = (movie: Movie) => request<Movie[]>('/api/recommend/item',{method:'POST',body:JSON.stringify({movie_id:movie.movie_id, top_k:16})});
export const rateMovie = (session: Session, movie: Movie, rating: number) => request('/api/rate',{method:'POST',body:JSON.stringify({user_id:session.user_id,movie_id:movie.movie_id,rating})},session.token);
export const newSession = (demoUserId?: number) => request<Session>('/api/session',{method:'POST',body:JSON.stringify(demoUserId ? {demo_user_id:demoUserId} : {})});
