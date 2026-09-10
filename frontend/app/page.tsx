'use client';
import {useCallback,useEffect,useRef,useState} from 'react';
import dynamic from 'next/dynamic';
import {ArrowRight,Film,RefreshCw,SlidersHorizontal,Orbit} from 'lucide-react';
import Navbar from '@/components/Navbar';
import HeroBillboard from '@/components/HeroBillboard';
import MovieRow from '@/components/MovieRow';
import NetflixCard from '@/components/NetflixCard';
import MovieModal from '@/components/MovieModal';
import {ApiError,catalog,newSession,rateMovie,recommendations,request,similarMovies} from '@/lib/api';
import type {Movie,Session} from '@/lib/types';
const AntiGravity=dynamic(()=>import('@/components/AntiGravity'),{ssr:false});
export default function Home(){
  const [session,setSession]=useState<Session|null>(null),[featured,setFeatured]=useState<Movie[]>([]),[picks,setPicks]=useState<Movie[]>([]),[popular,setPopular]=useState<Movie[]>([]),[movies,setMovies]=useState<Movie[]>([]),[similar,setSimilar]=useState<Movie[]>([]),[seed,setSeed]=useState<Movie|null>(null);
  const [genres,setGenres]=useState<string[]>([]),[genre,setGenre]=useState(''),[search,setSearch]=useState(''),[page,setPage]=useState(1),[total,setTotal]=useState(0),[loading,setLoading]=useState(true),[catalogLoading,setCatalogLoading]=useState(false),[error,setError]=useState(''),[toast,setToast]=useState(''),[gravity,setGravity]=useState(false),[demoEnabled,setDemoEnabled]=useState(false),[selected,setSelected]=useState<{movie:Movie;play:boolean}|null>(null);
  const initialized=useRef(false),feedbackVersion=useRef(0),profileVersion=useRef(0),sessionRef=useRef<Session|null>(null);
  const persist=(s:Session)=>{sessionRef.current=s;setSession(s);try{localStorage.setItem('cineverse-session',JSON.stringify({...s,expires_at:Date.now()+s.expires_in*1000}));}catch{/* Private browsing can disable persistence. */}};
  const boot=useCallback(async()=>{
    setLoading(true);setError('');
    try{
      let s:Session|null=null;
      try{const saved=JSON.parse(localStorage.getItem('cineverse-session')||'null');if(saved?.token && saved.expires_at>Date.now())s=saved as Session;}catch{/* Invalid local session starts a new profile. */}
      s=s || await newSession();
      let recs:Movie[];
      try{recs=await recommendations(s);}catch(e){if(e instanceof ApiError && e.status===401){s=await newSession();recs=await recommendations(s);}else throw e;}
      persist(s);
      const [result,allGenres,health]=await Promise.all([catalog(),request<string[]>('/api/genres'),request<{demo_profiles:boolean}>('/health')]);
      setPicks(recs);setFeatured(recs.slice(0,5));setPopular(result.items);setMovies(result.items);setTotal(result.total);setGenres(allGenres);setDemoEnabled(health.demo_profiles);
    }catch(e){setError(e instanceof Error?e.message:'Unable to connect to the movie service.');}finally{setLoading(false);}
  },[]);
  useEffect(()=>{if(initialized.current)return;initialized.current=true;void boot();},[boot]);
  useEffect(()=>{if(!session)return;const controller=new AbortController();setCatalogLoading(true);const timer=setTimeout(()=>{void catalog(search,genre,page,controller.signal).then(result=>{setMovies(result.items);setTotal(result.total);setError('');}).catch(e=>{if(!controller.signal.aborted)setError(e instanceof Error?e.message:'Search failed');}).finally(()=>{if(!controller.signal.aborted)setCatalogLoading(false);});},250);return()=>{clearTimeout(timer);controller.abort();};},[search,genre,page,session]);
  useEffect(()=>{if(!toast)return;const timer=setTimeout(()=>setToast(''),3500);return()=>clearTimeout(timer);},[toast]);
  useEffect(()=>{const key=(e:KeyboardEvent)=>{if((e.ctrlKey||e.metaKey)&&e.shiftKey&&e.key.toLowerCase()==='g'&&!gravity){e.preventDefault();setSelected(null);setGravity(true);}};window.addEventListener('keydown',key);return()=>window.removeEventListener('keydown',key);},[gravity]);
  const changeProfile=async(demo?:number)=>{const version=++profileVersion.current;++feedbackVersion.current;try{const s=await newSession(demo);const recs=await recommendations(s);if(version!==profileVersion.current)return;persist(s);setPicks(recs);setFeatured(recs.slice(0,5));setSimilar([]);setSeed(null);setToast(demo?'MovieLens demo profile selected':'Your fresh profile is ready');}catch(e){setToast(e instanceof Error?e.message:'Could not change profile');}};
  const rate=async(movie:Movie,rating:number)=>{if(!sessionRef.current)return;const s=sessionRef.current;const version=++feedbackVersion.current;try{await rateMovie(s,movie,rating);const [recs,related]=await Promise.all([recommendations(s),similarMovies(movie)]);if(version!==feedbackVersion.current || sessionRef.current?.user_id!==s.user_id)return;setPicks(recs);setSimilar(related);setSeed(movie);setToast(`Rated ${movie.title} ${rating}/5. Your picks are updated.`);}catch(e){setToast(e instanceof Error?e.message:'Could not save your rating');}};
  const open=(movie:Movie,play=false)=>setSelected({movie,play});
  const filtering=!!search || !!genre;
  return <><div id="app-surface" aria-hidden={gravity || undefined}><Navbar search={search} onSearch={v=>{setSearch(v);setPage(1);}} onGravity={()=>{setSelected(null);setGravity(true);}} userId={session?.user_id} onProfile={demo=>void changeProfile(demo)} demoEnabled={demoEnabled}/>
    {loading?<main className="loading-screen"><div className="loading-orbit"><Orbit size={40}/></div><h1>Finding your next favorite.</h1><p>Loading the Cineverse collection…</p></main>:error && !movies.length?<main className="loading-screen"><Film size={44}/><h1>The cinema is taking a break.</h1><p role="alert">{error}</p><button className="button button-white" onClick={()=>void boot()}><RefreshCw size={18}/>Try again</button></main>:<main>
      {!filtering && <HeroBillboard movies={featured} onOpen={open}/>}
      <div className={`browse-content ${filtering?'search-content':''}`}>
        {!filtering && <><MovieRow id="picks" title="Picked for your next movie night" subtitle="A little of what you love. A little of what’s next." movies={picks} onOpen={open} onRate={(m,r)=>void rate(m,r)}/>{seed && <MovieRow title={`Because you rated ${seed.title}`} movies={similar} onOpen={open} onRate={(m,r)=>void rate(m,r)}/>}<MovieRow title="The audience favorites" subtitle="Great stories that stay with you." movies={popular.slice(0,12)} onOpen={open} onRate={(m,r)=>void rate(m,r)} ranked/></>}
        <section className="catalog-section" id="catalog"><div className="section-heading catalog-heading"><div><div className="eyebrow">THE COLLECTION</div><h2>{search?`Results for “${search}”`:'There’s always another great story.'}</h2></div><label className="genre-select"><SlidersHorizontal size={16}/><select aria-label="Filter by genre" value={genre} onChange={e=>{setGenre(e.target.value);setPage(1);}}><option value="">All genres</option>{genres.map(g=><option key={g}>{g}</option>)}</select></label></div><div className="genre-chips">{['','Action','Comedy','Drama','Sci-Fi','Thriller','Romance'].map(g=><button key={g} onClick={()=>{setGenre(g);setPage(1);}} className={genre===g?'active':''}>{g||'All movies'}</button>)}</div>{error && <p role="alert" className="inline-error">{error}<button onClick={()=>setError('')}>Dismiss</button></p>}<p className="catalog-count" aria-live="polite">{catalogLoading?'Finding movies…':`${total.toLocaleString()} titles to explore`}</p>{!catalogLoading && !movies.length?<div className="empty-state"><Film size={36}/><h3>No titles found</h3><p>Try another title or choose a different genre.</p><button onClick={()=>{setSearch('');setGenre('');}}>Clear filters</button></div>:<div className={`catalog-grid ${catalogLoading?'is-loading':''}`}>{movies.map(movie=><NetflixCard key={movie.movie_id} movie={movie} onOpen={open} onRate={(m,r)=>void rate(m,r)}/>)}</div>}<div className="pagination"><button disabled={page===1||catalogLoading} onClick={()=>setPage(p=>p-1)}>Previous</button><span>Page {page} of {Math.max(1,Math.ceil(total/24))}</span><button disabled={page*24>=total||catalogLoading} onClick={()=>setPage(p=>p+1)}>Next <ArrowRight size={15}/></button></div></section>
      </div></main>}
      <footer><a className="wordmark" href="#">CINEVERSE<span/></a><p>Made for the love of movies.</p><div>Recommendations powered by MovieLens.<br/>This product uses the TMDB API but is not endorsed or certified by TMDB.</div><small>Match is a recommendation score, not a probability. Trailers only; full films are not streamed.</small></footer></div>
      {selected && <MovieModal key={selected.movie.movie_id} movie={selected.movie} autoplay={selected.play} onClose={()=>setSelected(null)} onRate={(m,r)=>void rate(m,r)}/>}
      {gravity && <AntiGravity onExit={()=>setGravity(false)}/>}
      {toast && <div className="toast" role="status">{toast}</div>}
    </>;
}
