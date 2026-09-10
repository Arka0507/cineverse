'use client';
import {motion,useReducedMotion} from 'framer-motion';
import {Play,ThumbsUp,ChevronDown} from 'lucide-react';
import type {Movie} from '@/lib/types';
import MovieArt from './MovieArt';
export default function NetflixCard({movie,onOpen,onRate,rank}: {movie:Movie;onOpen:(movie:Movie,play?:boolean)=>void;onRate:(movie:Movie,rating:number)=>void;rank?:number}) {
  const reduced=useReducedMotion();
  return <motion.article className="movie-card" data-physics="card" data-movie-id={movie.movie_id} whileHover={{scale:reduced ? 1 : 1.35,zIndex:30}} whileFocus={{zIndex:30}} transition={{type:'spring',stiffness:280,damping:28}}><button className="card-cover" aria-label={`More info about ${movie.title}`} onClick={()=>onOpen(movie)}><MovieArt movie={movie}/>{rank && <span className="rank-badge">{String(rank).padStart(2,'0')}</span>}<span className="card-top-label">{movie.genres[0]}</span></button><div className="card-description"><h3>{movie.title}</h3><p><span>{movie.year}</span>{movie.match != null ? <span className="match">{movie.match}% match</span>:<span className="match">★ {movie.rating.toFixed(1)}</span>}</p><div className="card-controls"><button className="icon-button light" aria-label={`Play trailer for ${movie.title}`} onClick={()=>onOpen(movie,true)}><Play size={15} fill="currentColor"/></button><button className="icon-button" aria-label={`Like ${movie.title}`} onClick={()=>onRate(movie,5)}><ThumbsUp size={15}/></button><span>{movie.genres.slice(0,2).join(' · ')}</span><button className="icon-button" aria-label={`Details for ${movie.title}`} onClick={()=>onOpen(movie)}><ChevronDown size={17}/></button></div></div></motion.article>;
}
