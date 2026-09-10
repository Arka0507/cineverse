'use client';
import {useState} from 'react';
import type {Movie} from '@/lib/types';
export default function MovieArt({movie, backdrop=false}: {movie:Movie;backdrop?:boolean}) {
  const [failed,setFailed] = useState(false);
  const url = backdrop ? movie.backdrop_url || movie.poster_url : movie.poster_url;
  if (url && !failed) return <img className={backdrop ? 'backdrop-image' : 'poster-image'} src={url} alt={backdrop ? '' : `${movie.title} poster`} loading={backdrop ? 'eager':'lazy'} draggable={false} onError={()=>setFailed(true)}/>;
  return <div className={`catalog-art ${backdrop ? 'catalog-art-large':''}`} style={{'--art-hue':(movie.movie_id*47)%360} as React.CSSProperties}><span className="art-edition">CINEVERSE COLLECTION</span><strong>{movie.title}</strong><span className="art-year">{movie.year || 'CLASSIC'}<i />{movie.genres[0]}</span><span className="art-caption">CATALOG EDITION · ARTWORK UNAVAILABLE</span></div>;
}
