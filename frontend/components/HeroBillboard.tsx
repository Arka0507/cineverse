'use client';
import {useEffect,useState} from 'react';
import {AnimatePresence,motion,useReducedMotion} from 'framer-motion';
import {Play,Info,Pause} from 'lucide-react';
import type {Movie} from '@/lib/types';
import MovieArt from './MovieArt';
export default function HeroBillboard({movies,onOpen}: {movies:Movie[];onOpen:(movie:Movie,play?:boolean)=>void}) {
  const [index,setIndex]=useState(0),[paused,setPaused]=useState(false);
  const reduced=useReducedMotion();
  useEffect(()=>{if(paused || reduced || movies.length<2)return;const id=setInterval(()=>setIndex(i=>(i+1)%Math.min(movies.length,5)),10000);return()=>clearInterval(id);},[movies.length,paused,reduced]);
  const movie=movies[index%Math.max(1,movies.length)];
  if(!movie)return null;
  return <section className="hero" id="browse"><AnimatePresence mode="wait"><motion.div className="hero-art" key={movie.movie_id} initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} transition={{duration:reduced ? 0 : .8}}><MovieArt movie={movie} backdrop/></motion.div></AnimatePresence><div className="hero-shade"/><div className="hero-content" data-physics="hero"><div className="eyebrow"><span className="red-line"/> THE CINEVERSE SPOTLIGHT</div><motion.div key={movie.movie_id} initial={{opacity:0,y:12}} animate={{opacity:1,y:0}}><h1>{movie.title}</h1><div className="movie-meta">{movie.match != null ? <strong className="match" title="Recommendation score, not a probability">{movie.match}% match</strong> : <strong className="match">{movie.rating.toFixed(1)} / 5 audience rating</strong>}<span>{movie.year}</span><span className="quality">HD</span><span>{movie.genres.slice(0,2).join(' · ')}</span></div><p className="hero-overview">{movie.overview}</p><div className="hero-buttons"><button className="button button-white" onClick={()=>onOpen(movie,true)}><Play size={21} fill="currentColor"/>{movie.trailer_key ? 'Play trailer':'Explore movie'}</button><button className="button button-glass" onClick={()=>onOpen(movie)}><Info size={21}/>More info</button></div></motion.div><span className="hero-footnote">Your next great movie starts here.</span></div><div className="hero-pagination"><button className="icon-button" aria-label={paused ? 'Resume featured rotation':'Pause featured rotation'} onClick={()=>setPaused(!paused)}>{paused ? <Play size={14}/>:<Pause size={14}/>}</button>{movies.slice(0,5).map((m,i)=><button key={m.movie_id} aria-label={`Feature ${m.title}`} aria-current={i===index} onClick={()=>setIndex(i)} className={i===index ? 'selected':''}/>)}<span>0{index+1}<small> / 0{Math.min(5,movies.length)}</small></span></div></section>;
}
