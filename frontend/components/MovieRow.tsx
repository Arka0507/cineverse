'use client';
import {useRef} from 'react';
import {ChevronLeft,ChevronRight,ArrowUpRight} from 'lucide-react';
import type {Movie} from '@/lib/types';
import NetflixCard from './NetflixCard';
export default function MovieRow({title,subtitle,movies,onOpen,onRate,ranked=false,id}: {title:string;subtitle?:string;movies:Movie[];onOpen:(m:Movie,play?:boolean)=>void;onRate:(m:Movie,r:number)=>void;ranked?:boolean;id?:string}) {
  const row=useRef<HTMLDivElement>(null);
  if(!movies.length)return null;
  const scroll=(direction:number)=>row.current?.scrollBy({left:direction*row.current.clientWidth*.8,behavior:'smooth'});
  return <section className="movie-section" id={id}><div className="section-heading"><div><h2>{title}<ArrowUpRight size={18}/></h2>{subtitle && <p>{subtitle}</p>}</div><div className="row-arrows"><button aria-label={`Scroll ${title} left`} onClick={()=>scroll(-1)}><ChevronLeft size={21}/></button><button aria-label={`Scroll ${title} right`} onClick={()=>scroll(1)}><ChevronRight size={21}/></button></div></div><div className="row-shell"><div className="movie-row" ref={row}>{movies.map((m,i)=><NetflixCard key={m.movie_id} movie={m} onOpen={onOpen} onRate={onRate} rank={ranked ? i+1:undefined}/>)}</div></div></section>;
}
